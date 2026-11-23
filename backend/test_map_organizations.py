import json
import unittest
import test_map_service as fixtures
from map_service import MapService,ADMIN_EMAIL
from recognition import RecognitionError

class OrganizationTest(unittest.TestCase):
 setUp=fixtures.MapTest.setUp
 tearDown=fixtures.MapTest.tearDown
 login=fixtures.MapTest.login
 profile=fixtures.MapTest.profile
 event=fixtures.MapTest.event
 def organization(self,u,name,create=False):
  self.m.save_profile(u,self.profile()|{"organization":name,"create":create})
  return next(p for p in self.m.profiles(u["id"]) if p["data"]["organization"]==name)
 def approve(self,p,a):self.m.review(a,dict(kind="profile",action="approve",id=p["id"],updated=p["updated"]))
 def publish(self,u,a,oid,title):
  eid=self.m.save_event(u,self.event()|{"title":title,"organization_id":oid})
  self.m.submit(u,dict(id=eid,version=1));self.m.review(a,dict(kind="event",action="approve",id=eid,version=2));return eid
 def test_independent_organizations_and_moderation(self):
  u,_=self.login("multi@example.com");a,_=self.login(ADMIN_EMAIL)
  p1=self.organization(u,"Первый организатор");self.approve(p1,a);e1=self.publish(u,a,p1["id"],"Первый старт")
  p2=self.organization(u,"Второй организатор",True)
  self.assertEqual(len(self.m.profiles(u["id"])),2)
  self.assertEqual([e["id"] for e in self.m.event_rows(public=True)],[e1])
  e2=self.m.save_event(u,self.event()|{"organization_id":p2["id"]})
  with self.assertRaises(RecognitionError):self.m.submit(u,dict(id=e2,version=1))
  self.approve(p2,a);self.m.submit(u,dict(id=e2,version=1));self.m.review(a,dict(kind="event",action="approve",id=e2,version=2))
  self.m.save_profile(u,self.profile()|{"organization_id":p1["id"],"organization":"Изменённая первая"})
  self.assertEqual([e["id"] for e in self.m.event_rows(public=True)],[e2])
  self.assertEqual(self.m.profile(u["id"],organization_id=p2["id"])["status"],"approved")
 def test_foreign_organization_is_forbidden(self):
  u,_=self.login("mine@example.com");v,_=self.login("foreign@example.com")
  mine=self.organization(u,"Моя организация");other=self.organization(v,"Чужая организация")
  with self.assertRaises(RecognitionError):self.m.save_profile(u,self.profile()|{"organization_id":other["id"]})
  with self.assertRaises(RecognitionError):self.m.save_event(u,self.event()|{"organization_id":other["id"]})
  eid=self.m.save_event(u,self.event()|{"organization_id":mine["id"]})
  with self.assertRaises(RecognitionError):self.m.save_event(u,self.event()|{"id":eid,"version":1,"organization_id":other["id"]})
  self.assertEqual(len(self.m.state(u)["profiles"]),1)
 def test_published_organization_changes_only_after_review(self):
  u,_=self.login("move@example.com");a,_=self.login(ADMIN_EMAIL)
  one=self.organization(u,"Организация один");two=self.organization(u,"Организация два",True)
  self.approve(one,a);self.approve(two,a);eid=self.publish(u,a,one["id"],"Смена организатора")
  self.m.save_event(u,self.event()|{"id":eid,"version":3,"organization_id":two["id"]})
  self.assertEqual(self.m.event_rows(public=True)[0]["organization_id"],one["id"])
  self.m.submit(u,dict(id=eid,version=4));self.m.review(a,dict(kind="event",action="approve",id=eid,version=5))
  self.assertEqual(self.m.event_rows(public=True)[0]["organization_id"],two["id"])
  with self.assertRaises(RecognitionError):self.m.save_event(u,self.event())
 def test_legacy_migration_is_idempotent(self):
  u,_=self.login("legacy@example.com")
  with self.s.db() as db:
   db.execute("INSERT INTO map_profiles VALUES(?,?, 'approved','',1,'legacy')",(u["id"],json.dumps(self.profile())))
   db.execute("INSERT INTO map_events(id,owner,data,status,published_data,updated) VALUES(?,?,?,'published',?,1)",("legacy-event",u["id"],json.dumps(self.event()),json.dumps(self.event())))
  migrated=MapService(self.s,self.m.uploads);again=MapService(self.s,self.m.uploads)
  self.assertEqual(len(again.profiles(u["id"])),1)
  self.assertEqual(again.event_rows(public=True)[0]["organization_id"],u["id"])
  self.assertEqual(again.profile(u["id"])["status"],"approved")

 def test_owner_hides_published_event_without_losing_draft(self):
  owner,_=self.login("owner-hide@example.com");other,_=self.login("other-hide@example.com");admin,_=self.login(ADMIN_EMAIL)
  profile=self.organization(owner,"Организация");self.approve(profile,admin)
  eid=self.publish(owner,admin,profile["id"],"Опубликованный старт")
  with self.assertRaises(RecognitionError):self.m.hide_event(other,{"id":eid,"version":3})
  with self.assertRaises(RecognitionError):self.m.hide_event(owner,{"id":eid,"version":2})
  self.assertEqual(len(self.m.event_rows(public=True)),1)
  self.m.hide_event(owner,{"id":eid,"version":3})
  self.assertEqual(self.m.event_rows(public=True),[])
  event=self.m.event_rows(owner["id"])[0]
  self.assertEqual((event["status"],event["published"],event["data"]["title"]),("draft",False,"Опубликованный старт"))
  self.m.submit(owner,{"id":eid,"version":event["version"]})
  self.assertEqual(self.m.event_rows(owner["id"])[0]["status"],"pending")
