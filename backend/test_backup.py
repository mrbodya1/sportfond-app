import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from backup_data import snapshot
from app_store import Store
from recognition import validate_result
from test_recognition import VALID


class BackupTests(unittest.TestCase):
    def test_snapshot_restores_credit_and_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store(root/'data/app.sqlite3', 'x'*48)
            cid, code = store.challenge('fixture@example.test', {'registration':True,'name':'Fixture'})
            uid = store.user(store.verify(cid,code))['id']
            (root/'uploads').mkdir()
            image = b'private test image'
            (root/'uploads/fixture.png').write_bytes(image)
            store.record(uid,'hash','fixture.png',validate_result(VALID))
            target = snapshot(root)
            restored = Store(target/'app.sqlite3','x'*48)
            self.assertEqual(restored.overview()['total'],5.25)
            manifest = json.loads((target/'manifest.json').read_text())
            self.assertEqual(manifest['images'],1)
            self.assertEqual(manifest['files']['uploads/fixture.png'],hashlib.sha256(image).hexdigest())
            self.assertEqual((target/'uploads/fixture.png').read_bytes(),image)

    def test_missing_image_never_reports_complete_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store(root/'data/app.sqlite3', 'x'*48)
            with store.db() as db:
                db.execute("INSERT INTO users VALUES (1,'fixture@example.test','Fixture',0)")
            store.record(1,'hash','missing.png',validate_result(VALID))
            with self.assertRaises(RuntimeError):
                snapshot(root)
            self.assertEqual(list((root/'backups').glob('*/manifest.json')),[])
