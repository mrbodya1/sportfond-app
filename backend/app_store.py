"""Persistent accounts, sessions and workout credit. No sample records."""
from contextlib import contextmanager
import datetime as dt
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from recognition import FIRST_DATE, RecognitionError

LEGAL_VERSION = "2026-11-13-gps-29oct"


class Store:
    def __init__(self, path, secret):
        self.path, self.secret = str(path), secret.encode()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS challenges(id TEXT PRIMARY KEY, email TEXT NOT NULL, code_hash TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS consents(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, version TEXT NOT NULL, accepted REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS workouts(id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, image_hash TEXT UNIQUE NOT NULL, image_file TEXT NOT NULL, workout_date TEXT, distance TEXT, gps INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL, evidence TEXT NOT NULL, created REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor INTEGER NOT NULL, workout_id TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL, created REAL NOT NULL);
            ''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def digest(self, text):
        return hmac.new(self.secret, text.encode(), hashlib.sha256).hexdigest()

    def challenge(self, email, payload):
        now = time.time()
        with self.db() as db:
            db.execute("DELETE FROM challenges WHERE created<?", (now - 86400,))
            last = db.execute("SELECT MAX(created),COUNT(*) FROM challenges WHERE email=? AND created>?", (email, now - 3600)).fetchone()
            if last[0] and now - last[0] < 60:
                raise RecognitionError("resend_cooldown", 429)
            if last[1] >= 5:
                raise RecognitionError("email_hourly_limit", 429)
            cid, code = secrets.token_urlsafe(24), f"{secrets.randbelow(1000000):06d}"
            db.execute("INSERT INTO challenges(id,email,code_hash,payload,created) VALUES (?,?,?,?,?)", (cid, email, self.digest(cid + code), json.dumps(payload), now))
        return cid, code

    def cancel_challenge(self, cid):
        with self.db() as db:
            db.execute("DELETE FROM challenges WHERE id=?", (cid,))

    def verify(self, cid, code):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM challenges WHERE id=?", (cid,)).fetchone()
            if not row or row["used"] or now - row["created"] >= 600 or row["attempts"] >= 5:
                raise RecognitionError("code_expired", 400)
            if not hmac.compare_digest(row["code_hash"], self.digest(cid + code)):
                db.execute("UPDATE challenges SET attempts=attempts+1 WHERE id=?", (cid,))
                db.commit()
                raise RecognitionError("invalid_code", 400)
            payload = json.loads(row["payload"])
            user = db.execute("SELECT * FROM users WHERE email=?", (row["email"],)).fetchone()
            if not user:
                if not payload.get("registration"):
                    raise RecognitionError("registration_required", 400)
                db.execute("INSERT INTO users(email,name,created) VALUES (?,?,?)", (row["email"], payload["name"], now))
                user = db.execute("SELECT * FROM users WHERE email=?", (row["email"],)).fetchone()
            if payload.get("consent"):
                db.execute("INSERT INTO consents(user_id,version,accepted) VALUES (?,?,?)", (user["id"], LEGAL_VERSION, now))
            token = secrets.token_urlsafe(32)
            db.execute("UPDATE challenges SET used=1 WHERE id=?", (cid,))
            db.execute("INSERT INTO sessions VALUES (?,?,?)", (self.digest(token), user["id"], now + 30 * 86400))
            db.execute("DELETE FROM sessions WHERE expires<?", (now,))
        return token

    def user(self, token):
        if not token:
            return None
        with self.db() as db:
            row = db.execute("SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?", (self.digest(token), time.time())).fetchone()
        return dict(row) if row else None

    def logout(self, token):
        with self.db() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (self.digest(token),))

    def by_hash(self, digest):
        with self.db() as db:
            row = db.execute("SELECT * FROM workouts WHERE image_hash=?", (digest,)).fetchone()
        return dict(row) if row else None

    def record(self, user_id, digest, image_file, evidence):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM workouts WHERE image_hash=?", (digest,)).fetchone()
            if existing:
                if existing["user_id"] != user_id:
                    raise RecognitionError("duplicate_image", 409)
                return existing["id"], True
            date, distance = evidence["workout_date"], evidence["distance_km"]
            if distance is not None:
                distance = float(Decimal(str(distance)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            status = {"eligible_preview": "approved", "manual_review": "pending", "rejected": "rejected"}[evidence["decision"]]
            reason = evidence["reason"]
            if distance is not None and distance <= 0:
                status, reason = "rejected", "Дистанция меньше точности учёта — 0,01 км."
            if status == "approved":
                reason = "Дата, дистанция и GPS подтверждены автоматически."
                # Same date+distance is a suspicion, not proof: two separate runs can match.
                previous = db.execute("SELECT distance FROM workouts WHERE user_id=? AND workout_date=? AND status IN ('approved','pending')", (user_id, date)).fetchall()
                if any(r[0] and Decimal(r[0]) == Decimal(str(distance)) for r in previous):
                    status, reason = "pending", "Похожая тренировка за эту дату уже есть. Проверяем возможный повтор."
            wid = secrets.token_hex(12)
            db.execute("INSERT INTO workouts VALUES (?,?,?,?,?,?,?,?,?,?,?,0)", (wid, user_id, digest, image_file, date, str(distance) if distance is not None else None, int(evidence["gps_route"] == "present"), status, reason, json.dumps(evidence, ensure_ascii=False), time.time()))
            db.execute("INSERT INTO audit(actor,workout_id,action,details,created) VALUES (?,?,?,?,?)", (user_id, wid, "auto_" + status, json.dumps({"date": date, "distance": distance}), time.time()))
        return wid, False

    def rows(self, user_id=None, admin=False):
        with self.db() as db:
            sql = "SELECT w.*,u.name,u.email FROM workouts w JOIN users u ON u.id=w.user_id WHERE w.deleted=0"
            found = db.execute(sql + ("" if admin else " AND w.user_id=?") + " ORDER BY w.created DESC", () if admin else (user_id,)).fetchall()
        return [{"id": r["id"], "date": r["workout_date"], "distance": float(r["distance"]) if r["distance"] else None,
                 "status": r["status"], "reason": r["reason"], "decision": r["reason"], "person": r["name"],
                 "email": r["email"] if admin else "", "gpsConfirmed": bool(r["gps"]), "gps": "Маршрут подтверждён" if r["gps"] else "Требует просмотра",
                 "activity": "Бег с GPS", "hash": r["image_hash"], "image": f"/api/workouts/{r['id']}/image"} for r in found]

    def workout(self, wid):
        with self.db() as db:
            row = db.execute("SELECT * FROM workouts WHERE id=?", (wid,)).fetchone()
        return dict(row) if row else None

    def delete(self, wid, actor, admin=False, restore=False):
        with self.db() as db:
            row = db.execute("SELECT * FROM workouts WHERE id=?", (wid,)).fetchone()
            if not row or (row["user_id"] != actor and not admin):
                raise RecognitionError("not_found", 404)
            db.execute("UPDATE workouts SET deleted=? WHERE id=?", (0 if restore else 1, wid))
            db.execute("INSERT INTO audit(actor,workout_id,action,details,created) VALUES (?,?,?,?,?)", (actor, wid, "restore" if restore else "delete", "{}", time.time()))

    def decision(self, wid, actor, data):
        status, date = data.get("status"), data.get("date")
        if status not in {"approved", "rejected", "pending"}:
            raise RecognitionError("invalid_status", 400)
        try:
            distance = Decimal(str(data.get("distance")))
            distance = distance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if not distance.is_finite() or distance <= 0:
                distance = None
        except Exception:
            distance = None
        try:
            parsed = dt.date.fromisoformat(date)
        except Exception:
            parsed, date = None, None
        if status == "approved" and (distance is None or parsed is None or parsed < FIRST_DATE or parsed > dt.datetime.now(dt.timezone(dt.timedelta(hours=5))).date() or data.get("gpsConfirmed") is not True):
            raise RecognitionError("workout_rules_failed", 400)
        reason = str(data.get("reason", "")).strip()[:1000]
        if status == "rejected" and len(reason) < 5:
            raise RecognitionError("rejection_reason_required", 400)
        with self.db() as db:
            if not db.execute("SELECT id FROM workouts WHERE id=? AND deleted=0", (wid,)).fetchone():
                raise RecognitionError("not_found", 404)
            db.execute("UPDATE workouts SET status=?,workout_date=?,distance=?,gps=?,reason=? WHERE id=?", (status, date, str(distance) if distance is not None else None, int(bool(data.get("gpsConfirmed"))), reason or "Подтверждено модератором.", wid))
            db.execute("INSERT INTO audit(actor,workout_id,action,details,created) VALUES (?,?,?,?,?)", (actor, wid, status, json.dumps(data), time.time()))

    def overview(self, current_id=None):
        with self.db() as db:
            users = db.execute("SELECT id,name FROM users ORDER BY id").fetchall()
            rows = db.execute("SELECT user_id,distance FROM workouts WHERE status='approved' AND deleted=0").fetchall()
        out, total = [], Decimal(0)
        for user in users:
            values = [Decimal(r["distance"]) for r in rows if r["user_id"] == user["id"] and r["distance"]]
            distance = sum(values, Decimal(0)); total += distance
            out.append({"id": "me" if user["id"] == current_id else str(user["id"]), "name": user["name"] if user["id"] == current_id else f"Участник {user['id']}", "distance": float(distance), "count": len(values)})
        return {"total": float(total), "participants": sorted(out, key=lambda x: -x["distance"])}
