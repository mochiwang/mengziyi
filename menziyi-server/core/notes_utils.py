# menziyi-server/core/notes_utils.py
import os
import json
import re
from typing import List, Dict, Optional, Tuple
from .paths import LESSONS_DIR, NOTES_DIR, NOTES_INBOX, NOTES_COLLECTED

# 目录常量
LESSON_DIR = LESSONS_DIR
INBOX_DIR = NOTES_INBOX
PROCESSED_DIR = os.path.join(NOTES_DIR, "Processed")
COLLECTED_DIR = NOTES_COLLECTED

def ensure_notes_dirs():
    """确保笔记目录存在"""
    for dir_path in [NOTES_DIR, INBOX_DIR, PROCESSED_DIR, COLLECTED_DIR]:
        os.makedirs(dir_path, exist_ok=True)

def chunk_text(lesson_id: str, max_chars: int = 800) -> int:
    """智能切片课程文本"""
    # 从数据库获取课程信息以获取正确的txt_path
    from .db import get_lesson
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise FileNotFoundError(f"Lesson not found: {lesson_id}")
    
    txt_path = lesson["txt_path"]
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Text file not found: {txt_path}")
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        return 0
    
    # 创建切片目录
    chunk_dir = os.path.join(INBOX_DIR, lesson_id)
    os.makedirs(chunk_dir, exist_ok=True)
    
    # 智能切片：按段落和句号分割
    paragraphs = re.split(r'\n\s*\n', content)
    chunks = []
    current_chunk = ""
    chunk_id = 1
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # 如果段落本身就很长，按句号分割
        if len(para) > max_chars:
            sentences = re.split(r'[。！？]', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk) + len(sentence) <= max_chars:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence + "。"
                    else:
                        # 单个句子就超过限制，强制分割
                        chunks.append(sentence[:max_chars] + "。")
        else:
            # 检查添加这个段落是否会超过限制
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
                else:
                    # 单个段落就超过限制，强制分割
                    chunks.append(para[:max_chars])
    
    # 添加最后一个切片
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # 写入切片文件
    index_data = []
    for i, chunk_content in enumerate(chunks, 1):
        chunk_id_str = f"chunk_{i:03d}"
        chunk_file = os.path.join(chunk_dir, f"{chunk_id_str}.txt")
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk_content)
        
        index_data.append({
            "chunk_id": chunk_id_str,
            "chars": len(chunk_content),
            "file": f"{chunk_id_str}.txt"
        })
    
    # 写入索引文件
    index_file = os.path.join(chunk_dir, "index.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    return len(chunks)

def list_chunks_with_status(lesson_id: str) -> List[Dict]:
    """列出切片及其处理状态"""
    chunk_dir = os.path.join(INBOX_DIR, lesson_id)
    index_file = os.path.join(chunk_dir, "index.json")
    
    if not os.path.exists(index_file):
        return []
    
    with open(index_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # 检查处理状态
    processed_dir = os.path.join(PROCESSED_DIR, lesson_id)
    for chunk in chunks:
        processed_file = os.path.join(processed_dir, f"{chunk['chunk_id']}.json")
        chunk['processed'] = os.path.exists(processed_file)
    
    return chunks

def get_chunk_text(lesson_id: str, chunk_id: str) -> Optional[str]:
    """获取切片文本"""
    chunk_file = os.path.join(INBOX_DIR, lesson_id, f"{chunk_id}.txt")
    
    if not os.path.exists(chunk_file):
        return None
    
    with open(chunk_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def save_label_item(lesson_id: str, item: Dict) -> Tuple[bool, str]:
    """保存标签项目"""
    # 校验必要字段
    required_fields = ["chunk_id", "title", "bullets", "keywords", "zh_explain"]
    for field in required_fields:
        if field not in item:
            return False, f"Missing field: {field}"
    
    # 获取原文进行关键词校验
    chunk_text = get_chunk_text(lesson_id, item["chunk_id"])
    if not chunk_text:
        return False, "Chunk text not found"
    
    # 关键词校验：至少命中一个
    keywords = item.get("keywords", [])
    if keywords:
        text_for_check = chunk_text + " " + item.get("zh_explain", "")
        found_keywords = []
        for keyword in keywords:
            if keyword in text_for_check:
                found_keywords.append(keyword)
        
        if not found_keywords:
            return False, f"No keywords found in text: {keywords}"
    
    # 保存到Processed目录
    processed_dir = os.path.join(PROCESSED_DIR, lesson_id)
    os.makedirs(processed_dir, exist_ok=True)
    
    processed_file = os.path.join(processed_dir, f"{item['chunk_id']}.json")
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(item, f, ensure_ascii=False, indent=2)
    
    # 刷新收集文件
    collect_jsonl(lesson_id)
    
    return True, "OK"

def collect_jsonl(lesson_id: str) -> int:
    """汇总为JSONL文件"""
    processed_dir = os.path.join(PROCESSED_DIR, lesson_id)
    collected_file = os.path.join(COLLECTED_DIR, f"{lesson_id}.jsonl")
    
    if not os.path.exists(processed_dir):
        return 0
    
    # 收集所有处理后的项目
    items = []
    seen_chunk_ids = set()
    
    for filename in os.listdir(processed_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(processed_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                item = json.load(f)
                chunk_id = item.get('chunk_id')
                if chunk_id and chunk_id not in seen_chunk_ids:
                    items.append(item)
                    seen_chunk_ids.add(chunk_id)
    
    # 按chunk_id排序
    items.sort(key=lambda x: x.get('chunk_id', ''))
    
    # 写入JSONL文件
    with open(collected_file, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    return len(items)

def save_summary(lesson_id: str, summary_obj: Dict) -> Tuple[bool, str]:
    """保存课程总结"""
    try:
        summary_file = os.path.join(COLLECTED_DIR, f"{lesson_id}.summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_obj, f, ensure_ascii=False, indent=2)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def get_collected_path(lesson_id: str) -> str:
    """获取收集文件路径"""
    return os.path.join(COLLECTED_DIR, f"{lesson_id}.jsonl")

# 兼容性函数（用于API调用）
def chunk_lesson_text(lesson_id: str, txt_path: str, max_chars: int = 800) -> List[str]:
    """切片课程文本（API兼容版本）"""
    # 直接使用传入的txt_path，而不是从数据库重新获取
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Text file not found: {txt_path}")
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    # 创建切片目录
    chunk_dir = os.path.join(INBOX_DIR, lesson_id)
    os.makedirs(chunk_dir, exist_ok=True)
    
    # 智能切片：按段落和句号分割
    paragraphs = re.split(r'\n\s*\n', content)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # 如果段落本身就很长，按句号分割
        if len(para) > max_chars:
            sentences = re.split(r'[。！？]', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk) + len(sentence) <= max_chars:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence + "。"
                    else:
                        # 单个句子就超过限制，强制分割
                        chunks.append(sentence[:max_chars] + "。")
        else:
            # 检查添加这个段落是否会超过限制
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
                else:
                    # 单个段落就超过限制，强制分割
                    chunks.append(para[:max_chars])
    
    # 添加最后一个切片
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # 写入切片文件
    index_data = []
    for i, chunk_content in enumerate(chunks, 1):
        chunk_id_str = f"chunk_{i:03d}"
        chunk_file = os.path.join(chunk_dir, f"{chunk_id_str}.txt")
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk_content)
        
        index_data.append({
            "chunk_id": chunk_id_str,
            "chars": len(chunk_content),
            "file": f"{chunk_id_str}.txt"
        })
    
    # 写入索引文件
    index_file = os.path.join(chunk_dir, "index.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    return chunks

def get_chunks_list(lesson_id: str) -> List[Dict]:
    """获取切片列表（API兼容版本）"""
    return list_chunks_with_status(lesson_id)

def get_chunk_text_with_prompt(lesson_id: str, chunk_id: str) -> Tuple[str, str]:
    """获取切片文本和提示词"""
    text = get_chunk_text(lesson_id, chunk_id)
    if not text:
        raise FileNotFoundError(f"Chunk not found: {chunk_id}")
    
    # Prompt-A
    prompt = (
        '你是课堂笔记助手。仅依据"片段原文"抽取要点并只输出一个 JSON（不要解释、不要多余字段）：\n'
        "{\n"
        f'  "chunk_id": "{chunk_id}",\n'
        '  "title": "中文标题 ≤20字",\n'
        '  "bullets": ["3-5条要点，每条≤40字，中文，来自原文"],\n'
        '  "keywords": ["3-8个术语，来自原文"],\n'
        '  "zh_explain": "80-150字中文解释，来自原文，不得编造"\n'
        "}\n"
        "——— 片段原文开始 ———\n"
        f"{text}\n"
        "——— 片段原文结束 ———\n"
    )
    
    return text, prompt

def save_processed_chunk(lesson_id: str, item: Dict):
    """保存处理后的切片（API兼容版本）"""
    success, message = save_label_item(lesson_id, item)
    if not success:
        raise ValueError(message)

def refresh_collected_jsonl(lesson_id: str):
    """刷新收集文件（API兼容版本）"""
    collect_jsonl(lesson_id)

def collect_processed_items(lesson_id: str) -> int:
    """收集处理后的项目（API兼容版本）"""
    return collect_jsonl(lesson_id)

def save_lesson_summary(lesson_id: str, summary_obj: Dict):
    """保存课程总结（API兼容版本）"""
    success, message = save_summary(lesson_id, summary_obj)
    if not success:
        raise ValueError(message)
