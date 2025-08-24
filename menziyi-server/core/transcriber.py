import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import traceback
from .db import update_state, get_lesson
from .utils_media import write_text, write_json, probe_duration
from faster_whisper import WhisperModel

_model = None
def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel("small", compute_type="int8")
    return _model

def run_transcribe(lesson_id):
    try:
        row = get_lesson(lesson_id)
        if not row: return
        update_state(lesson_id, state="running", dur=None)
        model = _get_model()
        segments, info = model.transcribe(row["wav_path"], beam_size=1, vad_filter=True)

        lines, seg_list = [], []
        for s in segments:
            t = (s.text or "").strip()
            if t:
                lines.append(t)
                seg_list.append({"start": float(s.start), "end": float(s.end), "text": t})

        # 一定写出 txt 与 segments.json（后续切片/证据卡依赖）
        write_text(row["txt_path"], "\n".join(lines))
        write_json(row["json_path"], {"segments": seg_list})

        dur = probe_duration(row["wav_path"])
        update_state(lesson_id, state="done", dur=dur)
    except Exception as e:
        update_state(lesson_id, state="error",
                     err=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
