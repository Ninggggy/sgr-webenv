import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'runtime'),str(ROOT/'upstream/arxiv-base')]
from import_snapshot import initialize,insert
from build_index import documents

class HistoricalIndexTests(unittest.TestCase):
 def test_old_version_search_never_inherits_latest_fields(self):
  with tempfile.TemporaryDirectory() as directory:
   d=initialize(Path(directory)/'metadata.sqlite');d.row_factory=sqlite3.Row
   insert(d,{'id':'0704.0001','update_date':'2026-09-19','title':'New title','abstract':'Latest abstract','authors':'Alice Smith','categories':'cs.AI','comments':'Latest accepted venue','report-no':'LATEST-ONLY','versions':[{'version':'v1','created':'Sun, 1 Apr 2007 00:00:00 GMT'},{'version':'v2','created':'Mon, 2 Apr 2007 00:00:00 GMT'}]})
   current=list(documents(d));self.assertEqual(len(current),1);self.assertEqual(current[0]['id'],'0704.0001v2');self.assertTrue(current[0]['is_current'])
   with self.assertRaises(ValueError):list(documents(d,include_historical=True))
   d.execute('UPDATE versions SET detail_json=? WHERE number=1',(json.dumps({'title':'Old title','abstract':'Historical abstract','authors':'Bob Jones','categories':'cs.LG','comments':None}),))
   docs=list(documents(d,include_historical=True));old=docs[1]
   self.assertEqual(old['id'],'0704.0001v1');self.assertFalse(old['is_current']);self.assertEqual(old['title'],'Old title')
   self.assertEqual(old['authors'][0]['full_name'],'Bob Jones');self.assertEqual(old['primary_classification']['category']['id'],'cs.LG')
   self.assertNotIn('comments',old);self.assertNotIn('report_num',old)
   self.assertIsNone(old['submitted_date_all']);self.assertEqual(old['submitted_date_first'],'2007-04-01T00:00:00+00:00')
   self.assertEqual(old['submitted_date_latest'],'2007-04-02T00:00:00+00:00');self.assertEqual(old['latest_version'],2)
   self.assertEqual([x['id'] for x in documents(d,historical_only=True)],['0704.0001v1'])
   d.close()
