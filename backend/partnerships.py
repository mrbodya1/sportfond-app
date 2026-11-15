"""Private partnership enquiries. No presentation is emailed until one is configured."""
import re
import time
from recognition import RecognitionError
PARTNER_ORIGINS = {"https://sportfondhm.ru", "https://www.sportfondhm.ru"} | {f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (4176,4177)}
def init_partners(store):
    with store.db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS partnership_requests(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, source TEXT NOT NULL, consent_version TEXT NOT NULL, created REAL NOT NULL, ip_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'waiting_presentation')")
def submit_partner(store, data, ip):
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    source = data.get("source")
    if data.get("website"):
        return
    if not 2 <= len(name) <= 120 or any(ord(c)<32 for c in name):
        raise RecognitionError("invalid_name", 400)
    if len(email)>254 or not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+",email):
        raise RecognitionError("invalid_email", 400)
    if source not in ("portal", "woodtrail") or data.get("consent") is not True:
        raise RecognitionError("consent_required", 400)
    now=time.time(); ip_hash=store.digest("partner:"+ip)
    with store.db() as db:
        if db.execute("SELECT 1 FROM partnership_requests WHERE email=? AND source=? AND created>?",(email,source,now-86400)).fetchone():
            return
        if db.execute("SELECT COUNT(*) FROM partnership_requests WHERE ip_hash=? AND created>?",(ip_hash,now-3600)).fetchone()[0]>=10:
            raise RecognitionError("too_many_requests",429)
        db.execute("INSERT INTO partnership_requests(name,email,source,consent_version,created,ip_hash) VALUES(?,?,?,?,?,?)",(name,email,source,"partner-2026-11-15",now,ip_hash))
def partner_rows(store):
    with store.db() as db:
        return [dict(r) for r in db.execute("SELECT id,name,email,source,created,status FROM partnership_requests ORDER BY id DESC LIMIT 500")]
