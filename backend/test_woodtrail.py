import unittest
from woodtrail import project,GROUPS
class ProjectionTest(unittest.TestCase):
 def row(self):return {"raceGroupGuid":GROUPS["10km"],"isComplete":True,"registrationNumber":12,"customFields":{"firstName":"Имя","lastName":"Фамилия","city":"Город","email":"private@example.com","cellPhone":"secret","birthday":"2000-01-01"},"account":{"firstName":"Покупатель","email":"secret"}}
 def test_public_allowlist(self):
  r=project([self.row()],"10km")[0];self.assertEqual(set(r),{"number","name","city","club","team"});self.assertEqual(r["name"],"Фамилия Имя");self.assertNotIn("secret",str(r))
 def test_filters_distance_completion_and_deleted(self):
  self.assertEqual(project([self.row()],"3km"),[])
  for change in [{"isComplete":False},{"isDeleted":True},{"customFields":{}}]:self.assertEqual(project([self.row()|change],"10km"),[])
if __name__=='__main__':unittest.main()
