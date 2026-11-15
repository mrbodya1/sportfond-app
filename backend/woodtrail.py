"""Read-only LIMETIME participant projection; credentials never leave this service."""
import json
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from recognition import load_config, RecognitionError
STAGE = "d8f85b33-603b-4983-b82c-bc8e2cf10b7e"
GROUPS = {"700m":"67486ace-8e1a-4185-8e5b-2fb4bbeb6495","1500m":"aae9f2fb-5720-486e-859a-7ea0de559597","3km":"61dd0419-d6c5-4d22-a397-b54b29497e00","10km":"e3a695ee-6295-472c-9dc1-f6d3f9451789","30km":"67d75b8f-b186-4640-befc-031c8eaaeda5","relay":"f2736a28-b44d-42bb-8b6c-029c3f6f2382"}
_lock=threading.Lock()
_cache={"at":0,"rows":[]}
def text(value):
    return str(value).strip()[:120] if isinstance(value,(str,int,float)) and not isinstance(value,bool) else ""
def project(rows, slug):
    output=[]
    for row in rows:
        if row.get("raceGroupGuid")!=GROUPS[slug] or row.get("isDeleted") or row.get("isComplete") is not True:
            continue
        cf=row.get("customFields") or {}
        if not isinstance(cf,dict):continue
        # Participant data only. Never fall back to purchaser account details.
        name=" ".join(filter(None,[text(cf.get("lastName")),text(cf.get("firstName")),text(cf.get("middleName"))]))
        if not name:continue
        output.append({"number":text(row.get("registrationNumber")),"name":name,"city":text(cf.get("city")),"club":text(cf.get("club")),"team":text(row.get("teamName"))})
    return sorted(output,key=lambda r:(not r["number"].isdigit(),int(r["number"]) if r["number"].isdigit() else 0,r["name"]))
def participants(data_dir,slug):
    if slug not in GROUPS:raise RecognitionError("not_found",404)
    with _lock:
        if time.time()-_cache["at"]<120:return {"participants":project(_cache["rows"],slug),"updated_at":_cache["at"]}
        key=load_config(Path(data_dir).parent/"private"/"limetime.env").get("LIMETIME_ACCESS_KEY","")
        if not key:raise RecognitionError("participants_not_configured",503)
        try:
            rows=[]
            for offset in range(0,5000,200):
                query=urllib.parse.urlencode({"raceStageGuid":STAGE,"limit":200,"offset":offset})
                req=urllib.request.Request("https://api.limetime.io/v3/RaceStageRegistrations/List?"+query,headers={"X-Access-Key":key,"Accept":"application/json"})
                with urllib.request.urlopen(req,timeout=12) as r:
                    raw=r.read(4*1024*1024+1)
                    if len(raw)>4*1024*1024:raise ValueError("upstream_too_large")
                    response=json.loads(raw)
                if response.get("isSuccess") is not True:raise ValueError("upstream_error")
                data=response.get("data") or {};items=data.get("items")
                if not isinstance(items,list) or not all(isinstance(r,dict) for r in items):raise ValueError("invalid_items")
                if offset and data.get("offset")!=offset:raise ValueError("pagination_not_supported")
                rows.extend(items)
                if len(rows)>=data.get("total",len(rows)) or not items:break
            else:raise ValueError("too_many_rows")
            # Cache only public projection and grouping metadata, not contact fields.
            safe=[]
            for row in rows:
                cf=row.get("customFields") or {}
                safe.append({k:row.get(k) for k in ("raceGroupGuid","registrationNumber","isComplete","isDeleted","teamName")} | {"customFields":{k:cf.get(k) for k in ("lastName","firstName","middleName","city","club")} if isinstance(cf,dict) else {}})
            _cache.update(at=time.time(),rows=safe)
            return {"participants":project(safe,slug),"updated_at":_cache["at"]}
        except Exception:
            raise RecognitionError("participants_unavailable",503) from None
