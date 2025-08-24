# menziyi-server/workers/transcribe_worker.py
import os, sys, logging

# 独立进程也设置防冲突
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s worker :: %(message)s")
log = logging.getLogger("worker")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 这里按你现有工程导入：transcode_to_wav16k_mono / run_transcribe / 以及 DB 函数等
from core.utils_media import transcode_to_wav16k_mono
from core.db import init_db
from core.transcriber import run_transcribe

def main():
    if len(sys.argv) != 4:
        print("usage: transcribe_worker.py <lesson_id> <orig_path> <wav_path>", file=sys.stderr)
        sys.exit(2)
    lid, orig_path, wav_path = sys.argv[1:]
    try:
        # 如需 DB，可以自行 init；不要依赖 Flask current_app/g
        try:
            init_db()
        except Exception as e:
            log.warning(f"init_db failed or not needed: {e}")

        log.info(f"[PROC] transcode start lid={lid}")
        transcode_to_wav16k_mono(orig_path, wav_path)
        log.info(f"[PROC] transcode done lid={lid}, start transcribe")
        run_transcribe(lid)
        log.info(f"[PROC] transcribe done lid={lid}")
    except Exception as e:
        log.exception(f"[PROC] pipeline failed lid={lid}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
