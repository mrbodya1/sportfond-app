"""Loopback-only operator test service. Not a public participant API."""
import argparse
import hashlib
import json
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from recognition import recognize, decode_image, load_config, RecognitionError

ALLOWED_ORIGINS = {"http://127.0.0.1:4174", "http://127.0.0.1:4175", "http://localhost:4174", "http://localhost:4175"}
MAX_BODY = 7 * 1024 * 1024
gate = threading.BoundedSemaphore(1)


def make_handler(env_file, db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS results (hash TEXT PRIMARY KEY, result TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS attempts (time REAL NOT NULL)")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/api/recognition/status":
                self.reply({"error": "not_found"}, 404)
                return
            cfg = load_config(env_file)
            self.reply({"available": bool(cfg.get("OPENAI_API_KEY")), "provider": "OpenAI", "test_only": True})

        def do_POST(self):
            if self.path != "/api/recognition":
                self.reply({"error": "not_found"}, 404)
                return
            if self.headers.get("Origin") not in ALLOWED_ORIGINS:
                self.reply({"error": "origin_not_allowed"}, 403)
                return
            if self.headers.get_content_type() != "application/json":
                self.reply({"error": "json_required"}, 415)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_BODY:
                    raise RecognitionError("request_too_large", 413)
                data = json.loads(self.rfile.read(size))
                if data.get("allow_openai_processing") is not True:
                    raise RecognitionError("processing_confirmation_required", 400)
                image, _ = decode_image(data.get("image"))
                digest = hashlib.sha256(image).hexdigest()
                if not gate.acquire(blocking=False):
                    raise RecognitionError("recognition_busy", 429)
                try:
                    with sqlite3.connect(db_path) as db:
                        old = db.execute("SELECT result FROM results WHERE hash=?", (digest,)).fetchone()
                        if old:
                            self.reply({**json.loads(old[0]), "cached": True})
                            return
                        now = time.time()
                        db.execute("DELETE FROM attempts WHERE time<?", (now - 3600,))
                        if db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= 10:
                            raise RecognitionError("test_hourly_limit", 429)
                        db.execute("INSERT INTO attempts VALUES (?)", (now,))
                    result = recognize(data["image"], load_config(env_file))
                    result.update(recognition_id=digest[:24], test_only=True, cached=False)
                    with sqlite3.connect(db_path) as db:
                        db.execute("INSERT OR REPLACE INTO results VALUES (?,?)", (digest, json.dumps(result, ensure_ascii=False)))
                    self.reply(result)
                finally:
                    gate.release()
            except RecognitionError as exc:
                self.reply({"error": exc.code}, exc.status)
            except (ValueError, TypeError, AttributeError):
                self.reply({"error": "invalid_request"}, 400)
            except Exception:
                self.reply({"error": "internal_error"}, 500)

    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--port", type=int, default=18766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.env_file, str(Path(args.data_dir) / "recognition.sqlite3")))
    server.serve_forever()
