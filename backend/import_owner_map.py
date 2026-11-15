"""One-time owner-authorized import. No auth tokens or consent checkboxes fabricated."""
import argparse,json,sqlite3,time
from pathlib import Path

def run(db_path,payload_path):
    p=json.loads(Path(payload_path).read_text(encoding="utf-8"));db=sqlite3.connect(db_path);db.row_factory=sqlite3.Row
    if p["owner_email"]!="89821575459@ya.ru" or p["event_id"]!="woodtrail2027":raise RuntimeError("Unexpected import target")
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            owner=db.execute("SELECT id FROM map_users WHERE email=?",(p["owner_email"],)).fetchone()
            if not owner:raise RuntimeError("Owner must have verified an account first")
            uid=owner["id"];now=time.time()
            existing=db.execute("SELECT data FROM map_profiles WHERE user_id=?",(uid,)).fetchone()
            if existing and json.loads(existing[0])["organization"]!=p["profile"]["organization"]:raise RuntimeError("Existing different organization; nothing changed")
            if not existing:
                name=db.execute("SELECT name FROM users WHERE email=?",(p["owner_email"],)).fetchone()
                if name:p["profile"]["full_name"]=name[0]
                db.execute("INSERT INTO map_profiles VALUES(?,?, 'approved', '', ?, 'owner-request-2026-11-15')",(uid,json.dumps(p["profile"],ensure_ascii=False),now))
                db.execute("INSERT INTO map_audit(actor,target,action,created) VALUES(?,?,?,?)",(uid,uid,"organization_imported_at_owner_request",now))
            existing_event=db.execute("SELECT owner FROM map_events WHERE id=?",(p["event_id"],)).fetchone()
            if existing_event and existing_event["owner"]!=uid:raise RuntimeError("Event belongs to another organizer")
            if not existing_event:
                duplicates=db.execute("SELECT data FROM map_events").fetchall()
                if any(json.loads(r[0]).get("title","").casefold()==p["event"]["title"].casefold() and json.loads(r[0]).get("date")==p["event"]["date"] for r in duplicates):raise RuntimeError("Possible duplicate event; nothing changed")
                data=json.dumps(p["event"],ensure_ascii=False)
                if Path(p["poster"]).name!=p["poster"] or not (Path(db_path).parent.parent/"uploads"/p["poster"]).is_file():raise RuntimeError("Poster missing")
                db.execute("INSERT INTO map_events(id,owner,data,poster,status,published_data,published_poster,updated) VALUES(?,?,?,?,'published',?,?,?)",(p["event_id"],uid,data,p["poster"],data,p["poster"],now))
                db.execute("INSERT INTO map_audit(actor,target,action,created) VALUES(?,?,?,?)",(uid,p["event_id"],"event_imported_and_attached_at_owner_request",now))
        print("Owner organization and WOOD TRAIL attached; existing records preserved.")
    finally:db.close()
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--db",required=True);parser.add_argument("--payload",required=True);args=parser.parse_args();run(args.db,args.payload)
