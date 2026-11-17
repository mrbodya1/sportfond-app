import tempfile,unittest
from pathlib import Path
from app_store import Store
class LeaderboardTests(unittest.TestCase):
 def test_names_only_in_authenticated_overview(self):
  with tempfile.TemporaryDirectory() as directory:
   store=Store(Path(directory)/"app.sqlite3","x"*48)
   with store.db() as db:
    db.execute("INSERT INTO users(id,email,name,created) VALUES(1,'one@example.test','Анна Иванова',0),(2,'two@example.test','Иван Петров',0)")
   rows=store.overview(1)["participants"]
   self.assertEqual([r["name"] for r in rows],["Анна Иванова","Иван Петров"])
   self.assertEqual(rows[0]["id"],"me")
   self.assertEqual([r["name"] for r in store.overview()["participants"]],["Участник 1","Участник 2"])
   self.assertTrue(all(set(r)=={"id","name","distance","count"} for r in rows))
