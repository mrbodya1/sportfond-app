"""Bounded OpenFreeMap relay; accepts resource paths, never arbitrary URLs."""
import gzip
import re
import threading
import urllib.request
from collections import OrderedDict
from urllib.parse import unquote, quote

_cache = OrderedDict()
_lock = threading.Lock()
_slots = threading.BoundedSemaphore(4)
_size = 0
_MAX = 32 * 1024 * 1024

def resource(path):
    global _size
    path = unquote(path)
    tile = re.fullmatch(r"/planet/(\d{8}_\d{6}_pt)/(\d{1,2})/(\d+)/(\d+)\.pbf", path)
    raster = re.fullmatch(r"/natural_earth/ne2sr/(\d)/(\d+)/(\d+)\.png", path)
    font = re.fullmatch(r"/fonts/([A-Za-z0-9 ,_-]{1,200})/(\d{1,6})-(\d{1,6})\.pbf", path)
    if not (tile or raster or font): raise ValueError("Unsupported map resource")
    if tile or raster:
        z,x,y=map(int,(tile.groups()[1:] if tile else raster.groups()))
        if z>14 or x>=2**z or y>=2**z: raise ValueError("Invalid tile coordinates")
    with _lock:
        if path in _cache:
            _cache.move_to_end(path)
            return _cache[path]
    if not _slots.acquire(timeout=15): raise RuntimeError("Map is busy")
    try:
        parts=[]; offset=0; total=1
        while offset<total:
            req=urllib.request.Request(("https://raw.githubusercontent.com/maplibre/demotiles/gh-pages/font/"+quote(font[1])+"/"+font[2]+"-"+font[3]+".pbf" if font else "https://tiles.openfreemap.org"+quote(path,safe="/,_-")),headers={"User-Agent":"SportfondMap/1.0 (+https://sportfondhm.ru/)","Accept-Encoding":"gzip","Range":f"bytes={offset}-{offset+16383}"})
            with urllib.request.urlopen(req,timeout=10) as response:
                data=response.read(2*1024*1024+1)
                if response.status==200:
                    if offset: raise RuntimeError("Unexpected range response")
                    parts=[data];break
                match=re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",response.headers.get("Content-Range",""))
                if not match or int(match[1])!=offset or len(data)!=int(match[2])-offset+1: raise RuntimeError("Invalid range response")
                total=int(match[3])
                if total>2*1024*1024: raise RuntimeError("Map resource too large")
                parts.append(data);offset+=len(data)
        data=b"".join(parts)
        if data.startswith(b"\x1f\x8b"): data=gzip.decompress(data)
        if len(data)>4*1024*1024: raise RuntimeError("Map resource too large")
        result=(data,"image/png" if raster else "application/octet-stream")
        with _lock:
            if path not in _cache:
                while _cache and _size+len(data)>_MAX:
                    _,old=_cache.popitem(last=False);_size-=len(old[0])
                _cache[path]=result;_size+=len(data)
        return result
    finally: _slots.release()
