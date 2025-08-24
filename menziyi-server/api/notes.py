# menziyi-server/api/notes.py
import os, json
from flask import Blueprint, request, jsonify
from core.db import get_lesson
from core.notes_utils import (
    chunk_lesson_text, get_chunks_list, get_chunk_text_with_prompt,
    save_processed_chunk, refresh_collected_jsonl, collect_processed_items,
    save_lesson_summary
)

bp = Blueprint("notes", __name__, url_prefix="/api/notes")

@bp.post("/chunk")
def chunk():
    """自动切片课程文本"""
    data = request.get_json() or {}
    lesson_id = data.get("lesson_id", "").strip()
    max_chars = data.get("max_chars", 800)
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    # 获取课程信息
    lesson = get_lesson(lesson_id)
    if not lesson:
        return jsonify({"status": "error", "message": "lesson not found"}), 404
    
    if lesson["state"] != "done":
        return jsonify({"status": "error", "message": "lesson not ready"}), 400
    
    try:
        # 执行切片
        chunks = chunk_lesson_text(lesson_id, lesson["txt_path"], max_chars)
        return jsonify({
            "status": "ok",
            "chunks": len(chunks)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.get("/chunks")
def list_chunks():
    """列出课程的所有切片"""
    lesson_id = request.args.get("lesson_id", "").strip()
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    try:
        chunks = get_chunks_list(lesson_id)
        return jsonify({
            "status": "ok",
            "chunks": chunks
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.get("/chunk_text")
def get_chunk_text():
    """获取切片文本和提示词"""
    lesson_id = request.args.get("lesson_id", "").strip()
    chunk_id = request.args.get("chunk_id", "").strip()
    
    if not lesson_id or not chunk_id:
        return jsonify({"status": "error", "message": "missing lesson_id or chunk_id"}), 400
    
    try:
        text, prompt = get_chunk_text_with_prompt(lesson_id, chunk_id)
        return jsonify({
            "status": "ok",
            "text": text,
            "prompt": prompt
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post("/label")
def label():
    """保存处理后的切片标签"""
    data = request.get_json() or {}
    lesson_id = data.get("lesson_id", "").strip()
    item = data.get("item")
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    if not item or not isinstance(item, dict):
        return jsonify({"status": "error", "message": "invalid item format"}), 400
    
    # 校验必要字段
    required_fields = ["chunk_id", "title", "bullets", "keywords", "zh_explain"]
    for field in required_fields:
        if field not in item:
            return jsonify({"status": "error", "message": f"missing field: {field}"}), 400
    
    try:
        # 保存处理后的切片
        save_processed_chunk(lesson_id, item)
        # 刷新收集文件
        refresh_collected_jsonl(lesson_id)
        
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post("/collect")
def collect():
    """重新汇总处理后的项目"""
    data = request.get_json() or {}
    lesson_id = data.get("lesson_id", "").strip()
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    try:
        items_count = collect_processed_items(lesson_id)
        return jsonify({
            "status": "ok",
            "items_count": items_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post("/summary")
def summary():
    """保存课程总结"""
    data = request.get_json() or {}
    lesson_id = data.get("lesson_id", "").strip()
    summary_obj = data.get("summary")
    
    if not lesson_id:
        return jsonify({"status": "error", "message": "missing lesson_id"}), 400
    
    if not summary_obj or not isinstance(summary_obj, dict):
        return jsonify({"status": "error", "message": "invalid summary format"}), 400
    
    try:
        save_lesson_summary(lesson_id, summary_obj)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
