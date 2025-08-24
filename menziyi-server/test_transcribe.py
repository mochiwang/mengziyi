#!/usr/bin/env python3
"""
测试脚本：将已有的 WAV 文件转换为文字
使用方法：python test_transcribe.py <wav文件路径>
"""

import os
import sys
import time
import logging
from core.transcriber import _get_model
from core.utils_media import write_text, write_json

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s test :: %(message)s")
log = logging.getLogger("test")

def transcribe_wav(wav_path):
    """转写单个 WAV 文件"""
    if not os.path.exists(wav_path):
        log.error(f"文件不存在: {wav_path}")
        return None
    
    try:
        log.info(f"开始转写: {wav_path}")
        start_time = time.time()
        
        # 获取模型
        model = _get_model()
        log.info("模型加载完成")
        
        # 转写
        segments, info = model.transcribe(
            wav_path, 
            beam_size=5,
            vad_filter=True
        )
        
        # 处理结果
        lines, seg_list = [], []
        for s in segments:
            t = (s.text or "").strip()
            if t:
                lines.append(t)
                seg_list.append({"start": float(s.start), "end": float(s.end), "text": t})
        
        # 生成输出文件路径
        base_name = os.path.splitext(wav_path)[0]
        txt_path = f"{base_name}.txt"
        json_path = f"{base_name}.segments.json"
        
        # 写入文件
        write_text(txt_path, "\n".join(lines))
        write_json(json_path, {"segments": seg_list})
        
        end_time = time.time()
        duration = end_time - start_time
        
        log.info(f"转写完成！耗时: {duration:.2f}秒")
        log.info(f"文本文件: {txt_path}")
        log.info(f"分段文件: {json_path}")
        log.info(f"检测到语言: {info.language} (概率: {info.language_probability:.2f})")
        log.info(f"音频时长: {info.duration:.2f}秒")
        log.info(f"转写文本长度: {len(''.join(lines))}字符")
        
        # 显示前几行文本
        if lines:
            log.info("转写结果预览:")
            for i, line in enumerate(lines[:3]):
                log.info(f"  {i+1}. {line}")
            if len(lines) > 3:
                log.info(f"  ... 还有 {len(lines)-3} 行")
        
        return {
            "txt_path": txt_path,
            "json_path": json_path,
            "duration": duration,
            "language": info.language,
            "language_probability": info.language_probability,
            "text_length": len(''.join(lines)),
            "segments_count": len(seg_list)
        }
        
    except Exception as e:
        log.exception(f"转写失败: {e}")
        return None

def main():
    if len(sys.argv) != 2:
        print("使用方法: python test_transcribe.py <wav文件路径>")
        print("示例: python test_transcribe.py data/lessons/2025-08-19/20250819-220959-19ebfc7a.wav")
        sys.exit(1)
    
    wav_path = sys.argv[1]
    result = transcribe_wav(wav_path)
    
    if result:
        print(f"\n✅ 转写成功！")
        print(f"📄 文本文件: {result['txt_path']}")
        print(f"📊 分段文件: {result['json_path']}")
        print(f"⏱️  耗时: {result['duration']:.2f}秒")
        print(f"🌍 语言: {result['language']} (概率: {result['language_probability']:.2f})")
        print(f"📝 字符数: {result['text_length']}")
        print(f"🔢 分段数: {result['segments_count']}")
    else:
        print("❌ 转写失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()








