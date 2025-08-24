import os, re, threading, uuid, json
from flask import Blueprint, request, jsonify, current_app
from core.utils_time import today_str, new_lesson_id
from core.utils_media import ensure_dir, transcode_to_wav16k_mono
from core.db import insert_lesson, get_lesson
from core.transcriber import run_transcribe
from core.paths import LESSONS_DIR

bp = Blueprint("lessons", __name__, url_prefix="/api/lessons")
NAME_RE = re.compile(r"^.{1,64}$")
COURSE_RE = re.compile(r"^[A-Za-z0-9_\-\.]{1,32}$")  # 课程短ID，如 CS101、Math_A

def _day_dir(base_dir, day):
    p = os.path.join(base_dir, day)
    ensure_dir(p)
    return p

@bp.post("/upload")
def upload():
    file = request.files.get("file")
    filename = (request.form.get("filename") or "").strip()
    course_id = (request.form.get("course_id") or "").strip() or "uncategorized"
    if not file:
        return jsonify({"status":"error","message":"missing file"}), 400
    if not filename or not NAME_RE.match(filename):
        return jsonify({"status":"error","message":"invalid filename length"}), 400
    if not COURSE_RE.match(course_id):
        return jsonify({"status":"error","message":"invalid course_id"}), 400

    base = LESSONS_DIR
    day = today_str()
    ddir = _day_dir(base, day)
    lid  = f"{new_lesson_id()}-{str(uuid.uuid4())[:8]}"

    orig_ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    orig_path = os.path.join(ddir, f"{lid}_orig{orig_ext}")
    file.save(orig_path)

    wav_path  = os.path.join(ddir, f"{lid}.wav")
    txt_path  = os.path.join(ddir, f"{lid}.txt")
    json_path = os.path.join(ddir, f"{lid}.segments.json")

    # 先插一个"排队中"的记录（wav 还没生成没关系，路径先占位即可）
    insert_lesson(lid, day, course_id, filename, {"wav": wav_path, "txt": txt_path, "json": json_path})

    # 在后台做重活：转码 -> 转写（保持你原有顺序与调用）
    app = current_app._get_current_object()
    
    def _bg_pipeline(app, lid_, orig_, wav_):
        with app.app_context():
            try:
                current_app.logger.info(f"[BG] transcode start lid={lid_}")
                transcode_to_wav16k_mono(orig_, wav_)
                current_app.logger.info(f"[BG] transcode done lid={lid_}, start transcribe")
                run_transcribe(lid_)
                current_app.logger.info(f"[BG] transcribe done lid={lid_}")
            except Exception as e:
                current_app.logger.exception(f"[BG] pipeline failed lid={lid_}: {e}")

    t = threading.Thread(target=_bg_pipeline, args=(app, lid, orig_path, wav_path), daemon=True)
    t.start()

    return jsonify({"status":"accepted","lesson_id":lid,"state":"queued",
                    "course_id": course_id,
                    "paths":{"wav":wav_path,"txt":txt_path,"json":json_path}}), 202

@bp.get("/status")
def status():
    lid = (request.args.get("lesson_id") or "").strip()
    if not lid:
        return jsonify({"status":"error","message":"missing lesson_id"}), 400
    row = get_lesson(lid)
    if not row:
        return jsonify({"status":"error","message":"lesson not found"}), 404

    preview = None
    seg_count = None
    if row["txt_path"] and os.path.exists(row["txt_path"]):
        try:
            with open(row["txt_path"], "r", encoding="utf-8") as f:
                preview = f.read(800)
        except: preview = None
    if row["json_path"] and os.path.exists(row["json_path"]):
        try:
            with open(row["json_path"], "r", encoding="utf-8") as f:
                obj = json.load(f)
                seg_count = len(obj.get("segments", []))
        except: seg_count = None

    return jsonify({
        "status":"ok",
        "lesson_id": row["id"],
        "course_id": row.get("course_id") or "uncategorized",
        "state": row["state"],
        "filename": row["filename"],
        "duration_sec": row["duration_sec"],
        "segments_count": seg_count,
        "paths": {"wav":row["wav_path"], "txt":row["txt_path"], "json":row["json_path"]},
        "error_msg": row["error_msg"],
        "text_preview": preview
    })
