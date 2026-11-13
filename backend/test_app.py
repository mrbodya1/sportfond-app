import base64
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from app_server import make_handler
from app_store import Store
from recognition import RecognitionError, validate_result
from test_recognition import VALID


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'app.sqlite3'
        self.store = Store(self.path, 'x' * 48)
        self.cid, self.code = self.store.challenge('owner@example.test', {'registration': True, 'name': 'Owner', 'consent': True})
        self.token = self.store.verify(self.cid, self.code)
        self.uid = self.store.user(self.token)['id']

    def evidence(self, **updates):
        return validate_result({**VALID, **updates})

    def test_one_time_code_session_hash_and_persistence(self):
        with self.assertRaises(RecognitionError):
            self.store.verify(self.cid, self.code)
        reopened = Store(self.path, 'x' * 48)
        self.assertEqual(reopened.user(self.token)['id'], self.uid)
        with reopened.db() as db:
            self.assertNotEqual(db.execute('SELECT token_hash FROM sessions').fetchone()[0], self.token)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM consents').fetchone()[0], 1)
        reopened.logout(self.token)
        self.assertIsNone(reopened.user(self.token))

    def test_code_attempt_limit_and_expiry(self):
        cid, code = self.store.challenge('other@example.test', {'registration': True, 'name': 'Other'})
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(5):
            with self.assertRaises(RecognitionError):
                self.store.verify(cid, wrong)
        with self.assertRaises(RecognitionError):
            self.store.verify(cid, code)
        cid, code = self.store.challenge('third@example.test', {'registration': True, 'name': 'Third'})
        with self.store.db() as db:
            db.execute('UPDATE challenges SET created=0 WHERE id=?', (cid,))
        with self.assertRaises(RecognitionError):
            self.store.verify(cid, code)

    def test_auto_credit_duplicate_and_delete_restore(self):
        wid, duplicate = self.store.record(self.uid, 'hash1', 'image.png', self.evidence())
        self.assertFalse(duplicate)
        self.assertEqual(self.store.rows(self.uid)[0]['status'], 'approved')
        self.assertEqual(self.store.overview()['total'], 5.25)
        self.assertEqual(self.store.record(self.uid, 'hash1', 'image.png', self.evidence()), (wid, True))
        self.assertEqual(self.store.overview()['total'], 5.25)
        self.store.delete(wid, self.uid)
        self.assertEqual(self.store.overview()['total'], 0)
        self.assertEqual(self.store.record(self.uid, 'hash1', 'image.png', self.evidence()), (wid, True))
        self.assertEqual(self.store.overview()['total'], 0)
        self.store.delete(wid, self.uid, restore=True)
        self.store.delete(wid, self.uid, restore=True)
        self.assertEqual(self.store.overview()['total'], 5.25)
        self.assertEqual(Store(self.path, 'x'*48).overview()['total'], 5.25)

    def test_distance_is_credited_to_hundredths(self):
        self.store.record(self.uid, "rounded", "1.png", self.evidence(distance_km=5.255))
        self.assertEqual(self.store.overview()["total"], 5.26)

    def test_ambiguous_and_similar_not_credited(self):
        self.store.record(self.uid, 'hash1', '1.png', self.evidence())
        self.store.record(self.uid, 'hash2', '2.png', self.evidence())
        self.store.record(self.uid, 'hash3', '3.png', self.evidence(distance_km=None))
        self.assertEqual([r['status'] for r in self.store.rows(self.uid)].count('pending'), 2)
        self.assertEqual(self.store.overview()['total'], 5.25)
        with self.assertRaises(RecognitionError):
            self.store.record(self.uid + 1, 'hash1', '1.png', self.evidence())

    def test_admin_rules_and_rejection_missing_fields(self):
        wid, _ = self.store.record(self.uid, 'hash', '1.png', self.evidence(workout_date=None, distance_km=None))
        self.store.decision(wid, self.uid, {'status': 'rejected', 'reason': 'Дата не читается'})
        self.assertEqual(self.store.rows(self.uid)[0]['status'], 'rejected')
        for changes in ({'date':'2026-10-28'}, {'gpsConfirmed':False}, {'distance':-1}):
            with self.assertRaises(RecognitionError):
                self.store.decision(wid, self.uid, {'status':'approved','date':'2026-10-29','distance':5.25,'gpsConfirmed':True, **changes})
        self.store.decision(wid, self.uid, {'status':'approved','date':'2026-10-29','distance':5.25,'gpsConfirmed':True})
        self.assertEqual(self.store.overview()['total'], 5.25)
        with self.assertRaises(RecognitionError):
            self.store.delete(wid, self.uid + 1)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for name, text in [('app.env', 'SESSION_SECRET='+'s'*48+'\nADMIN_EMAILS=admin@example.test\n'), ('ai.env','OPENAI_API_KEY=fake-not-real\n'), ('mail.env','SMTP_USERNAME=noreply@example.test\nSMTP_PASSWORD=fake\n')]:
            (root/name).write_text(text)
        handler = make_handler(root/'ai.env', root/'mail.env', root/'app.env', root/'data', root/'uploads')
        self.server = ThreadingHTTPServer(('127.0.0.1',0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.cookie = ''
        self.smtp = patch('app_server.smtplib.SMTP_SSL').start()
        self.addCleanup(patch.stopall)
        self.smtp.return_value.__enter__.return_value.send_message.return_value = {}
        self.recognize = patch('app_server.recognize', return_value=validate_result(VALID)).start()

    def request(self, path, data=None, origin='http://127.0.0.1:4174'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Cookie':self.cookie,'Origin':origin,'Content-Type':'application/json'}
        conn.request('GET' if data is None else 'POST', '/api'+path, None if data is None else json.dumps(data), headers)
        response = conn.getresponse()
        status, cookie, raw = response.status, response.getheader('Set-Cookie'), response.read()
        conn.close()
        if cookie:
            self.cookie = cookie.split(';')[0]
        return status, json.loads(raw)

    def signup(self, email):
        status, data = self.request('/auth/request', {'email':email,'name':'Fixture','registration':True,'rules':True,'consent':True})
        self.assertEqual(status,200)
        message = self.smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        import re
        code = re.search(r': (\d{6})', message.get_content()).group(1)
        self.assertNotIn(code, json.dumps(data))
        self.assertEqual(self.request('/auth/verify', {'challenge_id':data['challenge_id'],'code':code})[0],200)

    def test_auth_origin_admin_and_real_credit(self):
        image = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()
        payload = {'image':image,'allow_openai_processing':True}
        self.assertEqual(self.request('/recognition',payload)[0],401)
        self.assertEqual(self.request('/auth/request',{},origin='https://evil.example')[0],403)
        self.signup('owner@example.test')
        self.assertFalse(self.request('/session')[1]['user']['is_admin'])
        self.assertEqual(self.request('/admin/audit')[0],403)
        self.assertEqual(self.request('/workouts/'+'a'*24+'/decision',{'status':'approved'})[0],403)
        status, data = self.request('/recognition',payload)
        self.assertEqual(status,200)
        self.assertEqual(data['total'],5.25)
        self.assertEqual(data['workouts'][0]['status'],'approved')
        self.assertEqual(self.request('/recognition',payload)[1]['total'],5.25)
        self.assertEqual(self.recognize.call_count,1)
        self.assertEqual(self.request('/session')[1]['total'],5.25)
        self.signup('admin@example.test')
        state = self.request('/session')[1]
        self.assertTrue(state['user']['is_admin'])
        self.assertEqual(len(state['workouts']),0)
        self.assertEqual(len(state['admin_workouts']),1)
        self.assertEqual(self.request('/admin/audit')[0],200)
        self.assertEqual(self.request('/recognition',payload)[0],409)
