import os, sqlite3
from .utils_time import now_iso

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "index.sqlite")
DB_PATH = os.path.abspath(DB_PATH)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons(
          id TEXT PRIMARY KEY,
          date TEXT,
          course_id TEXT,
          filename TEXT,
          wav_path TEXT,
          txt_path TEXT,
          json_path TEXT,
          duration_sec REAL,
          state TEXT,
          created_at TEXT,
          updated_at TEXT,
          error_msg TEXT
        );""")
        # 轻量迁移：若老表没有 course_id 列就补上
        cols = [r[1] for r in conn.execute("PRAGMA table_info(lessons);").fetchall()]
        if "course_id" not in cols:
            conn.execute("ALTER TABLE lessons ADD COLUMN course_id TEXT DEFAULT 'uncategorized';")
        conn.commit()

def insert_lesson(id, date, course_id, filename, paths):
    with _conn() as conn:
        conn.execute("""INSERT INTO lessons
          (id,date,course_id,filename,wav_path,txt_path,json_path,
           duration_sec,state,created_at,updated_at,error_msg)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (id, date, course_id, filename, paths["wav"], paths["txt"], paths["json"],
           None, "queued", now_iso(), now_iso(), None))
        conn.commit()

def update_state(id, state=None, dur=None, err=None):
    with _conn() as conn:
        if state == "error":
            conn.execute("UPDATE lessons SET state=?, error_msg=?, updated_at=? WHERE id=?",
                         (state, err, now_iso(), id))
        elif state in ("queued","running","done"):
            conn.execute("UPDATE lessons SET state=?, duration_sec=?, updated_at=? WHERE id=?",
                         (state, dur, now_iso(), id))
        conn.commit()

def get_lesson(id):
    with _conn() as conn:
        r = conn.execute("SELECT * FROM lessons WHERE id=?", (id,)).fetchone()
        return dict(r) if r else None
