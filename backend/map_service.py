"""Organizer identity, profiles, event review. Separate namespace, server-only roles."""
import datetime as dt
import hashlib
import json
import re
import secrets
import time
from urllib.parse import urlsplit
from recognition import RecognitionError, decode_image
ADMIN_EMAIL = "89821575459@ya.ru"
MAP_ORIGINS = {"https://map.sportfondhm.ru", "https://www.map.sportfondhm.ru", "http://127.0.0.1:4178", "http://localhost:4178"}
SPORTS = {"run", "ski", "bike", "triathlon", "other"}
CONSENT = "map-organizer-2026-11-15"
def fail(code,status=400): raise RecognitionError(code,status)
def txt(data,key,lo=0,hi=500):
    v=data.get(key,"")
    if not isinstance(v,str):fail("invalid_"+key)
    v=v.strip()
    if not lo<=len(v)<=hi or any(ord(c)<32 and c not in "\n\t" for c in v):fail("invalid_"+key)
    return v
def url(data,key):
    v=txt(data,key,0,500)
    if v:
        u=urlsplit(v)
        if u.scheme!="https" or not u.hostname or u.username or u.password:fail("invalid_"+key)
    return v
class MapService:
    def __init__(self,store,uploads):
        self.store,self.uploads=store,uploads
        with store.db() as db:db.executescript("""
        CREATE TABLE IF NOT EXISTS map_users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_challenges(id TEXT PRIMARY KEY,email TEXT NOT NULL,code_hash TEXT NOT NULL,created REAL NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,used INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS map_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_profiles(user_id TEXT PRIMARY KEY,data TEXT NOT NULL,status TEXT NOT NULL,note TEXT NOT NULL DEFAULT '',updated REAL NOT NULL,consent_version TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS map_events(id TEXT PRIMARY KEY,owner TEXT NOT NULL,data TEXT NOT NULL,poster TEXT NOT NULL DEFAULT '',status TEXT NOT NULL,note TEXT NOT NULL DEFAULT '',version INTEGER NOT NULL DEFAULT 1,published_data TEXT,published_poster TEXT NOT NULL DEFAULT '',updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS map_audit(id INTEGER PRIMARY KEY,actor TEXT NOT NULL,target TEXT NOT NULL,action TEXT NOT NULL,created REAL NOT NULL);
        """)
        with store.db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS map_organizations(id TEXT PRIMARY KEY,owner TEXT NOT NULL,data TEXT NOT NULL,status TEXT NOT NULL,note TEXT NOT NULL DEFAULT '',updated REAL NOT NULL,consent_version TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS map_organizations_owner ON map_organizations(owner)")
            db.execute("INSERT OR IGNORE INTO map_organizations SELECT user_id,user_id,data,status,note,updated,consent_version FROM map_profiles")
            columns={r[1] for r in db.execute("PRAGMA table_info(map_events)")}
            for column in ("organization_id","published_organization_id"):
                if column not in columns:db.execute("ALTER TABLE map_events ADD COLUMN "+column+" TEXT")
            db.execute("UPDATE map_events SET organization_id=owner WHERE organization_id IS NULL")
            db.execute("UPDATE map_events SET published_organization_id=organization_id WHERE published_data IS NOT NULL AND published_organization_id IS NULL")
    def audit(self,db,actor,target,action):db.execute("INSERT INTO map_audit(actor,target,action,created) VALUES(?,?,?,?)",(actor,target,action,time.time()))
    def user(self,token,required=True,admin=False):
        with self.store.db() as db:r=db.execute("SELECT u.id,u.email FROM map_users u JOIN map_sessions s ON s.user_id=u.id WHERE s.token_hash=?",(self.store.digest("map:"+token),)).fetchone()
        if not r:
            if required:fail("authentication_required",401)
            return None
        u=dict(r);u["is_admin"]=u["email"]==ADMIN_EMAIL
        if admin and not u["is_admin"]:fail("admin_required",403)
        return u
    def challenge(self,data,send):
        email=txt(data,"email",3,254).lower()
        if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+",email):fail("invalid_email")
        if data.get("consent") is not True:fail("consent_required")
        now=time.time();cid=secrets.token_urlsafe(24);code=f"{secrets.randbelow(1000000):06}"
        with self.store.db() as db:
            if db.execute("SELECT COUNT(*) FROM map_challenges WHERE email=? AND created>?",(email,now-3600)).fetchone()[0]>=5 or db.execute("SELECT COUNT(*) FROM map_challenges WHERE created>?",(now-3600,)).fetchone()[0]>=40:fail("email_hourly_limit",429)
            if db.execute("SELECT 1 FROM map_challenges WHERE email=? AND created>?",(email,now-60)).fetchone():fail("resend_wait",429)
            db.execute("INSERT INTO map_challenges(id,email,code_hash,created) VALUES(?,?,?,?)",(cid,email,self.store.digest("map-code:"+cid+code),now))
        try:send(email,code)
        except Exception:
            with self.store.db() as db:db.execute("UPDATE map_challenges SET used=1 WHERE id=?",(cid,))
            fail("email_delivery_failed",503)
        return {"challenge_id":cid,"expires_in":600,"resend_after":60}
    def verify(self,data):
        cid=txt(data,"challenge_id",5,100);code=txt(data,"code",6,6)
        if not code.isdigit():fail("invalid_code")
        invalid=False
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            r=db.execute("SELECT * FROM map_challenges WHERE id=?",(cid,)).fetchone()
            if not r or r["used"] or time.time()-r["created"]>600 or r["attempts"]>=5:fail("invalid_or_expired_code")
            if not secrets.compare_digest(r["code_hash"],self.store.digest("map-code:"+cid+code)):
                db.execute("UPDATE map_challenges SET attempts=attempts+1 WHERE id=?",(cid,));invalid=True
            else:
                db.execute("UPDATE map_challenges SET used=1 WHERE id=?",(cid,))
                uid=secrets.token_hex(12)
                db.execute("INSERT OR IGNORE INTO map_users VALUES(?,?,?)",(uid,r["email"],time.time()))
                uid=db.execute("SELECT id FROM map_users WHERE email=?",(r["email"],)).fetchone()[0]
                token=secrets.token_urlsafe(32);db.execute("INSERT INTO map_sessions VALUES(?,?,?)",(self.store.digest("map:"+token),uid,time.time()))
        if invalid:fail("invalid_code")
        return token
    def profile(self,uid,db=None,organization_id=None):
        if db is None:
            with self.store.db() as conn:return self.profile(uid,conn,organization_id)
        if organization_id:r=db.execute("SELECT * FROM map_organizations WHERE owner=? AND id=?",(uid,organization_id)).fetchone()
        else:r=db.execute("SELECT * FROM map_organizations WHERE owner=? ORDER BY CASE WHEN id=owner THEN 0 ELSE 1 END,updated,id LIMIT 1",(uid,)).fetchone()
        return {"id":r["id"],"owner":r["owner"],"data":json.loads(r["data"]),"status":r["status"],"note":r["note"],"updated":r["updated"]}if r else None
    def profiles(self,uid):
        with self.store.db() as db:
            return [{"id":r["id"],"owner":r["owner"],"data":json.loads(r["data"]),"status":r["status"],"note":r["note"],"updated":r["updated"]} for r in db.execute("SELECT * FROM map_organizations WHERE owner=? ORDER BY CASE WHEN id=owner THEN 0 ELSE 1 END,updated,id",(uid,))]
    def save_profile(self,u,data):
        p={k:txt(data,k,lo,hi)for k,lo,hi in [("organization",2,150),("type",2,30),("full_name",3,120),("phone",7,30),("city",2,100),("description",30,2000),("inn",0,12),("ogrn",0,15),("address",0,300),("experience",0,1500)]}
        if p["type"] not in {"club","ngo","company","individual","sole_trader"}:fail("invalid_type")
        if not re.fullmatch(r"[+0-9 ()-]{7,30}",p["phone"]) or not 7<=len(re.sub(r"\D","",p["phone"]))<=15:fail("invalid_phone")
        if p["inn"] and not re.fullmatch(r"(?:\d{10}|\d{12})",p["inn"]):fail("invalid_inn")
        if p["ogrn"] and not re.fullmatch(r"(?:\d{13}|\d{15})",p["ogrn"]):fail("invalid_ogrn")
        p["website"]=url(data,"website");p["social"]=url(data,"social")
        sports=data.get("sports")
        if not isinstance(sports,list) or not sports or not all(isinstance(x,str) and x in SPORTS for x in sports):fail("invalid_sports")
        p["sports"]=list(dict.fromkeys(sports));p["public_email"]=data.get("public_email") is True
        if data.get("consent") is not True:fail("consent_required")
        oid=txt(data,"organization_id",0,32)
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old=None
            if oid:
                old=db.execute("SELECT * FROM map_organizations WHERE id=?",(oid,)).fetchone()
                if not old or old["owner"]!=u["id"]:fail("forbidden",403)
            elif data.get("create") is not True:
                old=db.execute("SELECT * FROM map_organizations WHERE owner=? ORDER BY CASE WHEN id=owner THEN 0 ELSE 1 END,updated,id LIMIT 1",(u["id"],)).fetchone()
                if old:oid=old["id"]
            if not old:
                count=db.execute("SELECT COUNT(*) FROM map_organizations WHERE owner=?",(u["id"],)).fetchone()[0]
                if count>=20:fail("organization_limit",429)
                oid=u["id"] if count==0 else secrets.token_hex(12)
                db.execute("INSERT INTO map_organizations(id,owner,data,status,updated,consent_version) VALUES(?,?,?,'pending',?,?)",(oid,u["id"],json.dumps(p,ensure_ascii=False),time.time(),CONSENT))
            else:
                db.execute("UPDATE map_organizations SET data=?,status='pending',note='',updated=?,consent_version=? WHERE id=?",(json.dumps(p,ensure_ascii=False),time.time(),CONSENT,oid))
            self.audit(db,u["id"],oid,"organization_submitted")
        return oid
    def event_data(self,data):
        e={k:txt(data,k,lo,hi)for k,lo,hi in [("title",3,150),("sport",2,20),("date",10,10),("time",0,5),("city",2,100),("address",3,300),("description",30,5000),("distances",0,200),("age",0,150),("price",0,150),("public_contact",0,200)]}
        if e["sport"] not in SPORTS:fail("invalid_sport")
        try:dt.date.fromisoformat(e["date"])
        except ValueError:fail("invalid_date")
        if e["time"] and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",e["time"]):fail("invalid_time")
        for k,lo,hi in [("lat",-90,90),("lon",-180,180)]:
            try:e[k]=float(data[k])
            except (KeyError,ValueError,TypeError):fail("invalid_coordinates")
            if not lo<=e[k]<=hi:fail("invalid_coordinates")
        e["registration_url"]=url(data,"registration_url");e["website"]=url(data,"website")
        return e
    def route(self, segments):
        if segments is None:
            return None
        if not isinstance(segments, list) or not 1 <= len(segments) <= 128:
            fail("invalid_route")
        count = 0
        for segment in segments:
            if not isinstance(segment, list) or len(segment) < 2:
                fail("invalid_route")
            count += len(segment)
            if count > 20000:
                fail("invalid_route")
            for point in segment:
                if (not isinstance(point, list) or len(point) != 2
                        or any(type(value) not in (int, float) for value in point)
                        or not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90):
                    fail("invalid_route")
        return segments

    def poster(self,data):
        image,mime=decode_image(data);suffix={"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}[mime]
        valid=(mime=="image/png"and image.startswith(b"\x89PNG\r\n\x1a\n"))or(mime=="image/jpeg"and image.startswith(b"\xff\xd8\xff"))or(mime=="image/webp"and image.startswith(b"RIFF")and image[8:12]==b"WEBP")
        if not valid:fail("invalid_image")
        name="map-"+hashlib.sha256(image).hexdigest()+suffix;path=self.uploads/name
        if not path.exists():path.write_bytes(image)
        return name
    def save_event(self,u,data):
        e=self.event_data(data);eid=txt(data,"id",0,32)or secrets.token_hex(12)
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM map_events WHERE id=?",(eid,)).fetchone()
            if old and old["owner"]!=u["id"]:fail("forbidden",403)
            if "route" in data:
                e["route"] = self.route(data["route"])
            elif old and "route" in json.loads(old["data"]):
                e["route"] = json.loads(old["data"])["route"]
            oid=txt(data,"organization_id",0,32)or(old["organization_id"]if old else"")
            if not oid:
                organizations=db.execute("SELECT id FROM map_organizations WHERE owner=?",(u["id"],)).fetchall()
                if not organizations:fail("profile_required",403)
                if len(organizations)>1:fail("organization_required")
                oid=organizations[0]["id"]
            organization=self.profile(u["id"],db,oid)
            if not organization:fail("forbidden",403)
            if old and data.get("version")!=old["version"]:fail("version_conflict",409)
            if not old and db.execute("SELECT COUNT(*) FROM map_events WHERE owner=?",(u["id"],)).fetchone()[0]>=100:fail("event_limit",429)
            poster=self.poster(data["poster"])if data.get("poster")else(old["poster"]if old else"")
            if old:db.execute("UPDATE map_events SET data=?,poster=?,organization_id=?,status='draft',note='',version=version+1,updated=? WHERE id=?",(json.dumps(e,ensure_ascii=False),poster,oid,time.time(),eid))
            else:db.execute("INSERT INTO map_events(id,owner,organization_id,data,poster,status,updated) VALUES(?,?,?,?,?,'draft',?)",(eid,u["id"],oid,json.dumps(e,ensure_ascii=False),poster,time.time()))
            self.audit(db,u["id"],eid,"event_saved")
        return eid
    def event_rows(self,uid=None,admin=False,public=False):
        with self.store.db() as db:
            if public:rows=db.execute("SELECT e.*,p.data profile,u.email organizer_email FROM map_events e JOIN map_organizations p ON p.id=e.published_organization_id JOIN map_users u ON u.id=e.owner WHERE e.published_data IS NOT NULL AND p.status='approved' ORDER BY e.updated DESC").fetchall()
            else:
                query="SELECT e.*,p.data profile,u.email organizer_email FROM map_events e JOIN map_organizations p ON p.id=e.organization_id JOIN map_users u ON u.id=e.owner"
                rows=db.execute(query+(""if admin else" WHERE e.owner=?")+" ORDER BY e.updated DESC",()if admin else(uid,)).fetchall()
            out=[]
            for r in rows:
                profile=json.loads(r["profile"])
                if public:
                    e=json.loads(r["published_data"]);out.append({"id":r["id"],"organization_id":r["published_organization_id"],"data":e,"poster":("/api/map/posters/"+r["published_poster"])if r["published_poster"]else"","organizer":profile["organization"],"organizer_email":r["organizer_email"]if profile.get("public_email")else""})
                else:
                    item={k:r[k]for k in("id","owner","organization_id","status","note","version","updated")};item.update(data=json.loads(r["data"]),poster=("/api/map/posters/"+r["poster"])if r["poster"]else"",published=bool(r["published_data"]),organizer=profile["organization"])
                    if admin:item.update(organizer_email=r["organizer_email"])
                    out.append(item)
            return out
    def state(self,u):
        return {"user":u,"profile":self.profile(u["id"]),"profiles":self.profiles(u["id"]),"events":self.event_rows(u["id"])}
    def admin_state(self,u):
        if not u["is_admin"]:fail("admin_required",403)
        with self.store.db() as db:profiles=[{"id":r["id"],"owner":r["owner"],"email":r["email"],"data":json.loads(r["data"]),"status":r["status"],"note":r["note"],"updated":r["updated"]}for r in db.execute("SELECT p.*,u.email FROM map_organizations p JOIN map_users u ON u.id=p.owner ORDER BY p.updated DESC")]
        return {"profiles":profiles,"events":self.event_rows(admin=True)}
    def review(self,u,data):
        if not u["is_admin"]:fail("admin_required",403)
        kind=txt(data,"kind",1,15);action=txt(data,"action",1,15);target=txt(data,"id",1,32);note=txt(data,"note",0,1000)
        if action=="reject"and not note:fail("reason_required")
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if kind=="profile"and action in("approve","reject"):
                p=db.execute("SELECT updated FROM map_organizations WHERE id=?",(target,)).fetchone()
                if not p:fail("not_found",404)
                if data.get("updated")!=p["updated"]:fail("version_conflict",409)
                db.execute("UPDATE map_organizations SET status=?,note=? WHERE id=?",("approved"if action=="approve"else"rejected",note,target))
            elif kind=="event"and action in("approve","reject","unpublish"):
                r=db.execute("SELECT * FROM map_events WHERE id=?",(target,)).fetchone()
                if not r:fail("not_found",404)
                if data.get("version")!=r["version"]:fail("version_conflict",409)
                if action=="approve":
                    if r["status"]!="pending"or self.profile(r["owner"],db,r["organization_id"])["status"]!="approved":fail("not_pending",409)
                    db.execute("UPDATE map_events SET status='published',published_data=data,published_poster=poster,published_organization_id=organization_id,note=?,version=version+1 WHERE id=?",(note,target))
                elif action=="unpublish":db.execute("UPDATE map_events SET published_data=NULL,published_poster='',published_organization_id=NULL,status='draft',note=?,version=version+1 WHERE id=?",(note,target))
                else:
                    if r["status"]!="pending":fail("not_pending",409)
                    db.execute("UPDATE map_events SET status='rejected',note=?,version=version+1 WHERE id=?",(note,target))
            else:fail("invalid_action")
            self.audit(db,u["id"],target,kind+":"+action)
    def submit(self,u,data):
        eid=txt(data,"id",1,32)
        with self.store.db() as db:
            r=db.execute("SELECT * FROM map_events WHERE id=? AND owner=?",(eid,u["id"])).fetchone()
            if not r:fail("not_found",404)
            p=self.profile(u["id"],db,r["organization_id"])
            if not p or p["status"]!="approved":fail("organizer_not_approved",403)
            if data.get("version")!=r["version"]:fail("version_conflict",409)
            if r["status"]not in("draft","rejected"):fail("invalid_status",409)
            db.execute("UPDATE map_events SET status='pending',note='',version=version+1 WHERE id=?",(eid,));self.audit(db,u["id"],eid,"event_submitted")
    def hide_event(self, user, data):
        event_id = txt(data, "id", 1, 32)
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            event = db.execute(
                "SELECT version,published_data FROM map_events WHERE id=? AND owner=?",
                (event_id, user["id"]),
            ).fetchone()
            if not event:
                fail("not_found", 404)
            if data.get("version") != event["version"]:
                fail("version_conflict", 409)
            if event["published_data"] is None:
                fail("invalid_status", 409)
            db.execute(
                """UPDATE map_events SET published_data=NULL,published_poster='',
                   published_organization_id=NULL,status='draft',note='',version=version+1
                   WHERE id=?""",
                (event_id,),
            )
            self.audit(db, user["id"], event_id, "event:hidden_by_owner")

    def get(self,path,token):
        if path=="/api/map/events":return {"events":self.event_rows(public=True)}
        if path=="/api/map/session":
            u=self.user(token,False);return self.state(u)if u else{"user":None,"profile":None,"profiles":[],"events":[]}
        u=self.user(token)
        if path=="/api/map/admin":return self.admin_state(u)
        fail("not_found",404)
    def post(self,path,data,token,send):
        if path=="/api/map/auth/request":return self.challenge(data,send),None
        if path=="/api/map/auth/verify":
            new=self.verify(data);return self.state(self.user(new)),new
        u=self.user(token)
        if path=="/api/map/logout":
            with self.store.db() as db:db.execute("DELETE FROM map_sessions WHERE token_hash=?",(self.store.digest("map:"+token),))
            return {"ok":True},""
        if path=="/api/map/profile":self.save_profile(u,data)
        elif path=="/api/map/events/save":self.save_event(u,data)
        elif path=="/api/map/events/submit":self.submit(u,data)
        elif path=="/api/map/events/hide":self.hide_event(u,data)
        elif path=="/api/map/admin/review":self.review(u,data);return self.admin_state(u),None
        else:fail("not_found",404)
        return self.state(u),None
    def image_path(self,name,token):
        if not re.fullmatch(r"map-[a-f0-9]{64}\.(?:jpg|png|webp)",name):fail("not_found",404)
        u=self.user(token,False)
        with self.store.db() as db:
            public=db.execute("SELECT 1 FROM map_events e JOIN map_organizations p ON p.id=e.published_organization_id WHERE e.published_poster=? AND e.published_data IS NOT NULL AND p.status='approved'",(name,)).fetchone()
            private=u and db.execute("SELECT 1 FROM map_events WHERE poster=? AND(owner=? OR ?=1)",(name,u["id"],int(u["is_admin"]))).fetchone()
        if not public and not private:fail("not_found",404)
        f=self.uploads/name
        if not f.is_file():fail("not_found",404)
        return f
