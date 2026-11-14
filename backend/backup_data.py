"""Create a consistent, private snapshot of SQLite and its referenced images."""
import argparse
import datetime as dt
import hashlib
import json
import shutil
import sqlite3
import time
from pathlib import Path


def snapshot(runtime):
    runtime = Path(runtime).resolve()
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = runtime / 'backups' / ('snapshot-' + stamp)
    target.mkdir(parents=True, exist_ok=False)
    records = []
    for name in ('app.sqlite3', 'recognition.sqlite3'):
        source = runtime / 'data' / name
        if not source.exists():
            continue
        src = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
        dst = sqlite3.connect(target / name)
        try:
            src.backup(dst)
            if dst.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('Snapshot integrity check failed')
            if name == 'app.sqlite3':
                records = [r[0] for r in dst.execute('SELECT DISTINCT image_file FROM workouts')]
        finally:
            src.close()
            dst.close()
    images = target / 'uploads'
    images.mkdir()
    for name in records:
        if Path(name).name != name:
            raise RuntimeError('Invalid stored image name')
        source = runtime / 'uploads' / name
        if not source.is_file():
            raise RuntimeError('Referenced image is missing')
        shutil.copyfile(source, images / name)
    manifest = {'created_utc': stamp, 'images': len(records), 'files': {}}
    for file in target.rglob('*'):
        if file.is_file():
            manifest['files'][file.relative_to(target).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return target


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', required=True)
    p.add_argument('--interval', type=int, default=0)
    args = p.parse_args()
    while True:
        target = snapshot(args.runtime)
        print('Snapshot completed:', target.name, flush=True)
        if not args.interval:
            break
        time.sleep(max(args.interval, 3600))

