import tempfile, unittest
from pathlib import Path
from app_store import Store
from recognition import RecognitionError
from partnerships import init_partners,submit_partner,partner_rows
class PartnersTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(Path(self.tmp.name)/'app.sqlite3','x'*40);init_partners(self.s)
 def tearDown(self):self.tmp.cleanup()
 def payload(self):return dict(name='Проверка формы',email='test@example.com',source='woodtrail',consent=True)
 def test_persists_and_deduplicates(self):
  d=self.payload();submit_partner(self.s,d,'127.0.0.1');submit_partner(self.s,d,'127.0.0.1');r=partner_rows(self.s);self.assertEqual(len(r),1);self.assertEqual(r[0]['status'],'waiting_presentation')
 def test_rejects_invalid_consent_source_email(self):
  for k,v in [('consent',False),('source','evil'),('email','no-email'),('name','x')]:
   with self.assertRaises(RecognitionError):submit_partner(self.s,self.payload()|{k:v},'127.0.0.1')
 def test_rate_limit(self):
  for i in range(10):submit_partner(self.s,self.payload()|{'email':f't{i}@example.com'},'127.0.0.1')
  with self.assertRaises(RecognitionError):submit_partner(self.s,self.payload(),'127.0.0.1')
 def test_honeypot(self):
  submit_partner(self.s,self.payload()|{'website':'spam'},'127.0.0.1');self.assertEqual(partner_rows(self.s),[])
if __name__=='__main__':unittest.main()
