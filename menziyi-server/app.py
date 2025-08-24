# app.py
from __future__ import annotations

import os
CLASSROOM_MODE_ENABLED = os.getenv("CLASSROOM_MODE_ENABLED", "0") == "1"

import time
import json
import signal
import logging
import uuid
from typing import Optional, Tuple
from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException

# --- Optional: CORS (auto-disable if not installed) ---
try:
    from flask_cors import CORS
    _CORS_AVAILABLE = True
except Exception:
    _CORS_AVAILABLE = False

# --- Your modules ---
from core.db import init_db
from ClassroomArchive.lessons import bp as lessons_bp
from api.notes import bp as notes_bp
from api.chat import bp_chat as chat_bp


# -----------------------------
# Settings & Logging
# -----------------------------
class Settings:
    def __init__(self) -> None:
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
        self.PORT: int = int(os.getenv("PORT", "5001"))
        self.ENABLE_CORS: bool = os.getenv("ENABLE_CORS", "1") in ("1", "true", "True")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.VERSION: str = os.getenv("APP_VERSION", "0.1.0")
        self.GIT_SHA: str = os.getenv("GIT_SHA", "")

def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )


# -----------------------------
# App Factory
# -----------------------------
def create_app(settings: Optional[Settings] = None) -> Flask:
    settings = settings or Settings()
    configure_logging(settings.LOG_LEVEL)

    # 启动标记
    BOOT_ID = f"{time.strftime('%Y-%m-%d %H:%M:%S')}#{uuid.uuid4().hex[:8]}"
    
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=False,
        ENV=settings.APP_ENV,
        APP_VERSION=settings.VERSION,
        GIT_SHA=settings.GIT_SHA,
    )

    # 启动日志
    app.logger.info(f"[BOOT] app starting BOOT_ID={BOOT_ID}")
    
    # 路径信息
    from core.paths import LESSONS_DIR
    app.logger.info(f"[PATH] LESSONS_DIR={LESSONS_DIR}")
    
    if settings.ENABLE_CORS and _CORS_AVAILABLE:
        # 只开放 /api/*，更安全；若需要全放开，resources={r"*": {"origins": "*"}}
        CORS(app, resources={r"/api/*": {"origins": "*"}})
        app.logger.info("CORS enabled for /api/*")
    elif settings.ENABLE_CORS and not _CORS_AVAILABLE:
        app.logger.warning("ENABLE_CORS=1 but flask_cors not installed; skip CORS.")

    # -------- Middlewares: request timing --------
    @app.before_request
    def _start_timer():
        g._t0 = time.time()

    @app.after_request
    def _add_timing(resp):
        try:
            t0 = getattr(g, "_t0", None)
            if t0 is not None:
                resp.headers["X-Process-Time"] = f"{(time.time() - t0):.3f}s"
        except Exception:
            pass
        return resp

    # -------- Error handlers: JSON everywhere --------
    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        payload = {
            "ok": False,
            "error": {
                "type": "http_error",
                "code": err.code,
                "name": err.name,
                "message": err.description,
                "path": request.path,
            }
        }
        app.logger.warning(f"HTTP {err.code} on {request.path}: {err.description}")
        return jsonify(payload), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception(f"Unhandled error on {request.path}: {err}")
        payload = {
            "ok": False,
            "error": {
                "type": "server_error",
                "message": "Internal server error",
                "path": request.path,
            }
        }
        return jsonify(payload), 500

    # -------- Register blueprints (with prefixes to avoid collision) --------
    app.register_blueprint(lessons_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(chat_bp)

    # -------- Temporary compatibility redirect (1-2 weeks) --------
    @app.route("/v1/<path:rest>", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
    def v1_redirect(rest):
        from flask import redirect, request
        app.logger.warning(f"[DEPRECATION] redirect /v1/{rest} -> /api/{rest}")
        code = 308 if request.method in ("GET", "HEAD") else 307
        return redirect(f"/api/{rest}", code=code)

    # -------- Health & Meta --------
    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "status": "healthy"})

    @app.get("/readyz")
    def readyz():
        # 如果需要检查 DB / 模型 / 队列可在这里做探活
        return jsonify({"ok": True, "status": "ready"})

    @app.get("/version")
    def version():
        return jsonify({
            "ok": True,
            "env": app.config.get("ENV"),
            "version": app.config.get("APP_VERSION"),
            "git_sha": app.config.get("GIT_SHA"),
        })

    # -------- DB init inside app context --------
    with app.app_context():
        try:
            init_db()
            app.logger.info("Database initialized.")
        except Exception as e:
            app.logger.exception(f"init_db failed: {e}")
            # 不直接 raise，让 /readyz 失败即可；也可以选择终止进程
            # raise

    # -------- Graceful shutdown (Ctrl+C / SIGTERM) --------
    def _graceful_shutdown(signum, frame):
        app.logger.info(f"Received signal {signum}, shutting down gracefully...")
        # 这里可清理资源（连接池、临时文件等）
        # 注意：Flask 内置 server 对 SIGTERM 支持一般，生产要用 gunicorn 等
        os._exit(0)

    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # -------- Print all routes (development only) --------
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        app.logger.info(f"[ROUTE] {','.join(rule.methods)} {rule.rule}")

    return app


# -----------------------------
# Dev entrypoint
# -----------------------------
if __name__ == "__main__":
    s = Settings()
    app = create_app(s)
    # 研发环境建议不开 reloader，避免双启动导致“看起来很慢”
    app.run(host="0.0.0.0", port=s.PORT, debug=False, use_reloader=False, threaded=True)
