import datetime

def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def new_lesson_id():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
