"""Authenticated workout API; public deployment requires a TLS reverse proxy."""
from contextlib import closing
import argparse
import hashlib
import json
import re
import smtplib
import sqlite3
import ssl
import threading
import time
from email.message import EmailMessage
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from app_store import Store, LEGAL_VERSION
from recognition import recognize, validate_result, decode_image, load_config, RecognitionError

ORIGINS = {f"http://{host}:{port}" for host in ("127.0.0.1", "localhost") for port in (4174, 4175)}
gate = threading.BoundedSemaphore(1)


def make_handler(ai_env, smtp_env, app_env, data_dir, upload_dir):
    cfg = load_config(app_env)
    secret = cfg.get("SESSION_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("SESSION_SECRET must be configured")
    store = Store(Path(data_dir) / "app.sqlite3", secret)
    cache_path = Path(data_dir) / "recognition.sqlite3"
    uploads = Path(upload_dir); uploads.mkdir(parents=True, exist_ok=True)
    admins = {e.strip().lower() for e in cfg.get("ADMIN_EMAILS", "").split(",") if e.strip()}
    public_origin = cfg.get("APP_PUBLIC_ORIGIN", "").strip().rstrip("/")
    if public_origin and public_origin != "https://app.sportfondhm.ru":
        raise RuntimeError("Unsupported public origin")
    origins = {public_origin} if public_origin else ORIGINS
    secure_cookie = bool(public_origin)
    ip_attempts = []

    def send_code(email, code):
        mail = load_config(smtp_env)
        msg = EmailMessage()
        msg["From"] = "Спортфонд <" + mail["SMTP_USERNAME"] + ">"
        msg["To"] = email
        msg["Reply-To"] = "sportfondhm@ya.ru"
        msg["Subject"] = "Спортфонд — код входа"
        msg.set_content(f"Код входа в приложение «9000 км»: {code}\n\nКод действует 10 минут. Никому его не сообщайте. Если вы не запрашивали вход, проигнорируйте письмо.")
        with smtplib.SMTP_SSL("smtp.beget.com", 465, timeout=20, context=ssl.create_default_context()) as smtp:
            smtp.login(mail["SMTP_USERNAME"], mail["SMTP_PASSWORD"])
            if smtp.send_message(msg):
                raise RuntimeError("recipient_refused")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, data, status=200, cookie=None):
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)

        def end_headers(self):
            origin = self.headers.get("Origin", "")
            if origin in origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
            super().end_headers()

        def do_OPTIONS(self):
            if self.headers.get("Origin") not in origins:
                self.reply({"error": "origin_not_allowed"}, 403); return
            requested = {h.strip().lower() for h in self.headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()}
            if self.headers.get("Access-Control-Request-Method") not in {"GET", "POST"} or not requested.issubset({"content-type"}):
                self.reply({"error": "request_not_allowed"}, 403); return
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "GET, POST")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def session_cookie(self, token, age):
            return f"sf_session={token}; Path=/api; HttpOnly; SameSite=Strict; Max-Age={age}" + ("; Secure" if secure_cookie else "")

        def token(self):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get("Cookie", ""))
                return cookie["sf_session"].value if "sf_session" in cookie else ""
            except Exception:
                return ""

        def user(self, admin=False):
            user = store.user(self.token())
            if not user:
                raise RecognitionError("authentication_required", 401)
            user["is_admin"] = user["email"] in admins
            if admin and not user["is_admin"]:
                raise RecognitionError("admin_required", 403)
            return user

        def state(self, user):
            return {"user": {k: user[k] for k in ("id", "name", "email", "is_admin")}, "workouts": store.rows(user["id"]), "admin_workouts": store.rows(admin=True) if user["is_admin"] else [], **store.overview(user["id"])}

        def do_GET(self):
            try:
                origin = self.headers.get("Origin")
                if origin and origin not in origins:
                    raise RecognitionError("origin_not_allowed", 403)
                if self.path == "/api/health":
                    self.reply({"status": "ok"}); return
                if self.path == "/api/session":
                    user = store.user(self.token())
                    if not user:
                        self.reply({"user": None, "workouts": [], **store.overview()}); return
                    user["is_admin"] = user["email"] in admins
                    self.reply(self.state(user)); return
                if self.path == "/api/overview":
                    self.reply({"total": store.overview()["total"]}); return
                if self.path == "/api/recognition/status":
                    self.reply({"available": bool(load_config(ai_env).get("OPENAI_API_KEY")), "provider": "OpenAI"}); return
                user = self.user()
                image_match = re.fullmatch(r"/api/workouts/([a-f0-9]{24})/image", self.path)
                if image_match:
                    row = store.workout(image_match[1])
                    if not row or row["deleted"] or (row["user_id"] != user["id"] and not user["is_admin"]):
                        raise RecognitionError("not_found", 404)
                    file = uploads / row["image_file"]
                    content = file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}[file.suffix])
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers(); self.wfile.write(content); return
                if self.path == "/api/admin/audit":
                    self.user(admin=True)
                    with store.db() as db:
                        records = db.execute("SELECT a.*,u.name FROM audit a JOIN users u ON u.id=a.actor ORDER BY a.created DESC LIMIT 100").fetchall()
                    self.reply({"records": [dict(r) for r in records]}); return
                raise RecognitionError("not_found", 404)
            except RecognitionError as exc:
                self.reply({"error": exc.code}, exc.status)
            except Exception:
                self.reply({"error": "internal_error"}, 500)

        def do_POST(self):
            try:
                if self.headers.get("Origin") not in origins:
                    raise RecognitionError("origin_not_allowed", 403)
                if self.headers.get_content_type() != "application/json":
                    raise RecognitionError("json_required", 415)
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 7 * 1024 * 1024:
                    raise RecognitionError("request_too_large", 413)
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise RecognitionError("invalid_request", 400)
                if self.path == "/api/auth/request":
                    now = time.time()
                    ip_attempts[:] = [t for t in ip_attempts if t > now - 3600]
                    if len(ip_attempts) >= 20:
                        raise RecognitionError("email_hourly_limit", 429)
                    email = str(data.get("email", "")).strip().lower()
                    if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+", email) or len(email) > 254:
                        raise RecognitionError("invalid_email", 400)
                    registration = data.get("registration") is True
                    name = str(data.get("name", "")).strip()
                    if registration and (not 2 <= len(name) <= 100 or data.get("rules") is not True or data.get("consent") is not True):
                        raise RecognitionError("registration_consent_required", 400)
                    cid, code = store.challenge(email, {"registration": registration, "name": name, "consent": registration})
                    ip_attempts.append(now)
                    try:
                        send_code(email, code)
                    except Exception:
                        store.cancel_challenge(cid)
                        raise RecognitionError("email_delivery_failed", 503) from None
                    self.reply({"sent": True, "challenge_id": cid, "expires_in": 600, "resend_after": 60, "legal_version": LEGAL_VERSION}); return
                if self.path == "/api/auth/verify":
                    cid, code = str(data.get("challenge_id", "")), str(data.get("code", ""))
                    if not re.fullmatch(r"\d{6}", code) or len(cid) > 100:
                        raise RecognitionError("invalid_code", 400)
                    token = store.verify(cid, code)
                    self.reply({"authenticated": True}, cookie=self.session_cookie(token, 2592000)); return
                user = self.user()
                if self.path == "/api/auth/logout":
                    store.logout(self.token())
                    self.reply({"ok": True}, cookie=self.session_cookie("", 0)); return
                match = re.fullmatch(r"/api/workouts/([a-f0-9]{24})/(delete|restore|decision)", self.path)
                if match:
                    wid, action = match.groups()
                    if action == "decision":
                        self.user(admin=True); store.decision(wid, user["id"], data)
                    else:
                        store.delete(wid, user["id"], user["is_admin"], restore=action == "restore")
                    self.reply(self.state(user)); return
                if self.path != "/api/recognition":
                    raise RecognitionError("not_found", 404)
                if data.get("allow_openai_processing") is not True:
                    raise RecognitionError("processing_confirmation_required", 400)
                image, mime = decode_image(data.get("image"))
                digest = hashlib.sha256(image).hexdigest()
                old = store.by_hash(digest)
                if old:
                    if old["user_id"] != user["id"]:
                        raise RecognitionError("duplicate_image", 409)
                    self.reply({"duplicate": True, "workout_id": old["id"], "deleted": bool(old["deleted"]), **self.state(user)}); return
                if not gate.acquire(blocking=False):
                    raise RecognitionError("recognition_busy", 429)
                try:
                    with closing(sqlite3.connect(cache_path)) as cache:
                        cache.execute("CREATE TABLE IF NOT EXISTS results(hash TEXT PRIMARY KEY,result TEXT NOT NULL)")
                        cache.execute("CREATE TABLE IF NOT EXISTS attempts(time REAL NOT NULL)")
                        cached = cache.execute("SELECT result FROM results WHERE hash=?", (digest,)).fetchone()
                        if cached:
                            evidence = validate_result({k: json.loads(cached[0])[k] for k in ("workout_date", "distance_km", "gps_route", "activity", "readable", "notes")})
                        else:
                            now = time.time()
                            cache.execute("DELETE FROM attempts WHERE time<?", (now - 3600,))
                            if cache.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= 10:
                                raise RecognitionError("recognition_hourly_limit", 429)
                            cache.execute("INSERT INTO attempts VALUES (?)", (now,)); cache.commit()
                            evidence = recognize(data["image"], load_config(ai_env))
                            cache.execute("INSERT OR REPLACE INTO results VALUES (?,?)", (digest, json.dumps(evidence, ensure_ascii=False)))
                        cache.commit()
                    filename = digest + {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime]
                    file = uploads / filename
                    if not file.exists():
                        with file.open("xb") as target:
                            target.write(image)
                    wid, duplicate = store.record(user["id"], digest, filename, evidence)
                    self.reply({"duplicate": duplicate, "workout_id": wid, "recognition": evidence, **self.state(user)})
                finally:
                    gate.release()
            except RecognitionError as exc:
                self.reply({"error": exc.code}, exc.status)
            except (ValueError, TypeError, AttributeError):
                self.reply({"error": "invalid_request"}, 400)
            except Exception:
                self.reply({"error": "internal_error"}, 500)

    return Handler


class BoundedHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    slots = threading.BoundedSemaphore(32)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(30)
        return request, address

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("ai-env", "smtp-env", "app-env", "data-dir", "upload-dir"):
        p.add_argument("--" + flag, required=True)
    p.add_argument("--port", type=int, default=18766)
    p.add_argument("--bind", default="127.0.0.1")
    args = p.parse_args()
    BoundedHTTPServer((args.bind, args.port), make_handler(args.ai_env, args.smtp_env, args.app_env, args.data_dir, args.upload_dir)).serve_forever()
