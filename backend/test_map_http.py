import tempfile,unittest,threading,json,http.client,re
from pathlib import Path
from unittest.mock import patch
from app_server import make_handler,ThreadingHTTPServer
class MapHttpTest(unittest.TestCase):
 def test_separate_cookie_and_admin_gate(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);(p/'app.env').write_text('SESSION_SECRET='+'x'*40);(p/'empty').write_text('');messages=[]
   class SMTP:
    def __init__(self,*a,**k):pass
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def login(self,*a):pass
    def send_message(self,msg):messages.append(msg);return {}
   (p/'mail.env').write_text('SMTP_USERNAME=test@example.com\nSMTP_PASSWORD=test')
   srv=ThreadingHTTPServer(('127.0.0.1',0),make_handler(p/'empty',p/'mail.env',p/'app.env',p/'data',p/'uploads'));threading.Thread(target=srv.serve_forever,daemon=True).start()
   def request(path,data=None,cookie='',origin='http://127.0.0.1:4178'):
    c=http.client.HTTPConnection('127.0.0.1',srv.server_port);c.request('POST'if data is not None else'GET',path,json.dumps(data)if data is not None else None,{'Content-Type':'application/json','Origin':origin,'Cookie':cookie});r=c.getresponse();out=r.status,dict(r.getheaders()),json.load(r);c.close();return out
   try:
    with patch('app_server.smtplib.SMTP_SSL',SMTP):
     code,h,c=request('/api/map/auth/request',{'email':'organizer@example.com','consent':True});self.assertEqual(code,200);otp=re.search(r'\b\d{6}\b',messages[-1].get_content()).group()
     code,h,d=request('/api/map/auth/verify',{'challenge_id':c['challenge_id'],'code':otp,'is_admin':True});self.assertEqual(code,200);self.assertFalse(d['user']['is_admin']);cookie=h['Set-Cookie'];self.assertIn('Path=/api/map',cookie);self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie);self.assertNotIn('sf_session=',cookie)
     self.assertEqual(request('/api/map/admin',cookie=cookie)[0],403);self.assertEqual(request('/api/map/admin')[0],401)
     self.assertEqual(request('/api/auth/request',{},origin='http://127.0.0.1:4178')[0],403)
     self.assertEqual(request('/api/map/profile',{'is_admin':True},cookie=cookie,origin='https://evil.example')[0],403)
     self.assertEqual(request('/api/map/events')[2],{'events':[]})
     request('/api/map/logout',{},cookie=cookie);self.assertIsNone(request('/api/map/session',cookie=cookie)[2]['user'])
   finally:srv.shutdown();srv.server_close()
if __name__=='__main__':unittest.main()
