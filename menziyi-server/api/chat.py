# menziyi-server/api/chat.py
import os, json, re, math
from typing import List, Dict, Tuple
from flask import Blueprint, request, jsonify
from core.notes_utils import get_chunk_text, get_collected_path

bp_chat = Blueprint("chat", __name__, url_prefix="/api")

def calculate_score(query: str, item: Dict) -> int:
    """计算查询词在项目中的匹配分数"""
    score = 0
    query_lower = query.lower()
    
    # 检查各个字段的匹配情况
    fields_to_check = [
        ("title", item.get("title", "")),
        ("bullets", " ".join(item.get("bullets", []))),
        ("keywords", " ".join(item.get("keywords", []))),
        ("zh_explain", item.get("zh_explain", ""))
    ]
    
    for field_name, field_content in fields_to_check:
        if not field_content:
            continue
            
        field_lower = field_content.lower()
        
        # 分词匹配（简单的中文分词）
        query_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query_lower)
        for word in query_words:
            if word in field_lower:
                score += 2
    
    return score

def get_en_excerpt(chunk_text: str, max_chars: int = 320) -> str:
    """获取英文摘要（取前320字符）"""
    if not chunk_text:
        return ""
    
    # 简单截取，尽量在句号处截断
    if len(chunk_text) <= max_chars:
        return chunk_text
    
    excerpt = chunk_text[:max_chars]
    
    # 尝试在句号处截断
    last_period = excerpt.rfind('。')
    if last_period > max_chars * 0.7:  # 如果句号在70%位置之后
        excerpt = excerpt[:last_period + 1]
    
    return excerpt

def extract_suggested_keywords(items: List[Dict], top_n: int = 5) -> List[str]:
    """提取建议的关键词"""
    keyword_freq = {}
    
    for item in items:
        keywords = item.get("keywords", [])
        for keyword in keywords:
            if keyword:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    # 按频率排序，取前N个
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, freq in sorted_keywords[:top_n]]

@bp_chat.post("/chat")
def chat():
    """关键词检索版聊天"""
    data = request.get_json() or {}
    lesson_id = data.get("lesson_id", "").strip()
    query = data.get("query", "").strip()
    k = data.get("k", 6)
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    if not query:
        return jsonify({"status": "error", "message": "missing query"}), 400
    
    try:
        # 读取收集的笔记数据
        collected_path = get_collected_path(lesson_id)
        if not collected_path or not os.path.exists(collected_path):
            return jsonify({"status": "error", "message": "no notes found for lesson"}), 404
        
        items = []
        with open(collected_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        items.append(item)
                    except json.JSONDecodeError:
                        continue
        
        if not items:
            return jsonify({"status": "error", "message": "no valid notes found"}), 404
        
        # 计算每个项目的分数
        scored_items = []
        for item in items:
            score = calculate_score(query, item)
            if score > 0:  # 只保留有匹配的项目
                scored_items.append((item, score))
        
        # 按分数排序，取top-k
        scored_items.sort(key=lambda x: x[1], reverse=True)
        top_items = scored_items[:k]
        
        # 构建响应
        chunks = []
        all_bullets = []
        
        for item, score in top_items:
            # 获取原文摘要
            chunk_text = get_chunk_text(lesson_id, item["chunk_id"])
            en_excerpt = get_en_excerpt(chunk_text) if chunk_text else ""
            
            chunks.append({
                "chunk_id": item["chunk_id"],
                "title": item["title"],
                "zh_explain": item["zh_explain"],
                "en_excerpt": en_excerpt,
                "score": score
            })
            
            # 收集要点用于合并答案
            all_bullets.extend(item.get("bullets", []))
        
        # 合并要点作为答案
        answer = "；".join(all_bullets[:10])  # 限制要点数量
        
        # 提取建议关键词
        suggested = extract_suggested_keywords(items)
        
        return jsonify({
            "status": "ok",
            "answer": answer,
            "chunks": chunks,
            "suggested": suggested
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
