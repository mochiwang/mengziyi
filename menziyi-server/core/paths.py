import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # menziyi-server/
DATA_DIR = os.environ.get("MZY_DATA_DIR", os.path.join(BASE_DIR, "data"))
LESSONS_DIR = os.path.join(DATA_DIR, "lessons")

# 如果你仍然需要 notes 视角：
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # = /Users/edison/mengziyi
NOTES_DIR = os.path.join(PROJECT_ROOT, "notes")
NOTES_INBOX = os.path.join(NOTES_DIR, "Inbox")
NOTES_COLLECTED = os.path.join(NOTES_DIR, "Collected")







