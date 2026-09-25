"""Source update integration: preserve history while adding new versions/categories."""
import json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from import_snapshot import initialize,insert
from harvest import connect

class OaiUpdatesTests(unittest.TestCase):
 def test_incremental_merge_preserves_real_old_detail_and_adds_cross_listing(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);target=root/'base.sqlite';delta=root/'delta.sqlite'
   d=initialize(target)
   source={'id':'0704.0001','update_date':'2026-09-18','title':'Before','abstract':'Source abstract','authors':'A. Author','categories':'math.AG','versions':[{'version':'v1','created':'Sun, 1 Apr 2007 00:00:00 GMT'}]}
   insert(d,source)
   detail=json.dumps({'title':'Actual v1'})
   d.execute('UPDATE versions SET detail_json=?,detail_source=?',(detail,'official-api'))
   for g in ('cs','math','stat'):d.execute('INSERT INTO harvest_state VALUES (?,NULL,1,1,?,?)',(g+':'+g,'2026-09-19','2026-09-19'))
   d.commit();d.close()
   s=connect(delta)
   s.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',('0704.0001','2026-09-21',0,'After','New abstract','A. Author','math.AG cs.CG',None,None,None,None,None,None,None,'<official/>','2026-09-25'))
   for n,date in [(1,'2007-04-01T00:00:00+00:00'),(2,'2026-09-20T00:00:00+00:00')]:s.execute('INSERT INTO versions(paper_id,number,submitted_at) VALUES (?,?,?)',('0704.0001',n,date))
   for g in ('cs','math','stat'):s.execute('INSERT INTO harvest_state VALUES (?,NULL,1,1,?,?)',(g+':'+g,'2026-09-25','2026-09-25'))
   s.commit();s.close()
   args=[sys.executable,str(ROOT/'tools/apply_oai_updates.py'),'--database',str(target),'--updates',str(delta),'--report',str(root/'result.json')]
   subprocess.run(args,check=True,capture_output=True)
   d=sqlite3.connect(target)
   self.assertEqual(d.execute('SELECT title,source_xml FROM records').fetchone(),('After','<official/>'))
   self.assertEqual(d.execute('SELECT detail_json FROM versions WHERE number=1').fetchone()[0],detail)
   self.assertIsNone(d.execute('SELECT detail_json FROM versions WHERE number=2').fetchone()[0])
   self.assertEqual({x[0] for x in d.execute('SELECT source_set FROM membership')},{'cs:cs','math:math'})
   self.assertEqual(json.loads(d.execute('SELECT previous_json FROM metadata_updates').fetchone()[0])['title'],'Before')
   d.close()
   # Resumption must not replace the original observation with the updated one.
   subprocess.run(args,check=True,capture_output=True)
   d=sqlite3.connect(target)
   self.assertEqual(json.loads(d.execute('SELECT previous_json FROM metadata_updates').fetchone()[0])['title'],'Before')
   self.assertEqual(d.execute('SELECT count(*) FROM versions').fetchone()[0],2);d.close()
