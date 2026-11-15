import tempfile,unittest
from pathlib import Path
from app_store import Store
from recognition import RecognitionError
from map_service import MapService,ADMIN_EMAIL
class MapTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.s=Store(p/'db.sqlite3','x'*40);(p/'uploads').mkdir();self.m=MapService(self.s,p/'uploads');self.codes=[]
 def tearDown(self):self.tmp.cleanup()
 def login(self,email):
  c=self.m.challenge({'email':email,'consent':True},lambda e,code:self.codes.append(code));token=self.m.verify({'challenge_id':c['challenge_id'],'code':self.codes[-1]});return self.m.user(token),token
 def profile(self):return dict(organization='Беговой клуб',type='club',full_name='Иванов Иван Иванович',phone='+79991234567',city='Ханты-Мансийск',description='Организуем спортивные старты и тренировки для любителей спорта.',sports=['run'],consent=True)
 def event(self):return dict(title='Проверочный старт',sport='run',date='2027-08-01',time='10:00',city='Ханты-Мансийск',address='Калинина, 1',description='Описание проверочного спортивного события для теста модерации.',lat=61,lon=69,distances='10 км',age='18+',registration_url='https://example.com/register')
 def test_role_and_ownership(self):
  u,t=self.login('organizer@example.com');a,_=self.login(ADMIN_EMAIL);self.assertFalse(u['is_admin']);self.assertTrue(a['is_admin'])
  with self.assertRaises(RecognitionError):self.m.admin_state(u)
  self.m.save_profile(u,self.profile());eid=self.m.save_event(u,self.event());v,_=self.login('other@example.com');self.m.save_profile(v,self.profile())
  with self.assertRaises(RecognitionError):self.m.save_event(v,self.event()|{'id':eid,'version':1})
 def approve_profile(self,u,a):
  p=self.m.profile(u['id']);self.m.review(a,dict(kind='profile',action='approve',id=u['id'],updated=p['updated']))
 def test_review_and_published_revision(self):
  u,_=self.login('organizer@example.com');a,_=self.login(ADMIN_EMAIL);self.m.save_profile(u,self.profile());eid=self.m.save_event(u,self.event())
  with self.assertRaises(RecognitionError):self.m.submit(u,dict(id=eid,version=1))
  self.approve_profile(u,a);self.m.submit(u,dict(id=eid,version=1));self.m.review(a,dict(kind='event',action='approve',id=eid,version=2))
  self.assertEqual(len(self.m.event_rows(public=True)),1);pub=self.m.event_rows(public=True)[0];self.assertNotIn('phone',str(pub));self.assertNotIn('full_name',str(pub));self.assertEqual(pub['organizer_email'],'')
  self.m.save_event(u,self.event()|{'id':eid,'version':3,'title':'Изменённый заголовок'});self.assertEqual(self.m.event_rows(public=True)[0]['data']['title'],'Проверочный старт')
  with self.assertRaises(RecognitionError):self.m.review(a,dict(kind='event',action='approve',id=eid,version=2))
  self.m.review(a,dict(kind='event',action='unpublish',id=eid,version=4));self.assertEqual(self.m.event_rows(public=True),[])
 def test_otp_attempts_and_logout(self):
  c=self.m.challenge({'email':'wrong@example.com','consent':True},lambda e,code:self.codes.append(code))
  for i in range(5):
   with self.assertRaises(RecognitionError):self.m.verify({'challenge_id':c['challenge_id'],'code':'notnum'})
  # Valid-shaped wrong codes must persist attempts, even when verification fails.
  for i in range(5):
   with self.assertRaises(RecognitionError):self.m.verify({'challenge_id':c['challenge_id'],'code':'000000' if self.codes[-1]!='000000' else '111111'})
  with self.s.db()as db:self.assertEqual(db.execute('SELECT attempts FROM map_challenges WHERE id=?',(c['challenge_id'],)).fetchone()[0],5)
  u,t=self.login('logout@example.com');self.m.post('/api/map/logout',{},t,None);self.assertIsNone(self.m.user(t,False))
 def test_urls_and_missing_auth(self):
  with self.assertRaises(RecognitionError):self.m.event_data(self.event()|{'registration_url':'javascript:alert(1)'})
  with self.assertRaises(RecognitionError):self.m.event_data(self.event()|{'lat':float('nan')})
  with self.assertRaises(RecognitionError):self.m.get('/api/map/admin','')
  self.assertEqual(self.m.get('/api/map/events',''),{'events':[]})
 def test_backup_includes_map_poster(self):
  import base64
  from backup_data import snapshot
  runtime=Path(self.tmp.name)/'runtime';(runtime/'uploads').mkdir(parents=True)
  store=Store(runtime/'data'/'app.sqlite3','x'*40);service=MapService(store,runtime/'uploads')
  user={'id':'u','email':'u@example.com','is_admin':False};service.save_profile(user,self.profile())
  image='data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()
  service.save_event(user,self.event()|{'poster':image})
  target=snapshot(runtime);self.assertEqual(len(list((target/'uploads').glob('map-*.png'))),1)
if __name__=='__main__':unittest.main()
