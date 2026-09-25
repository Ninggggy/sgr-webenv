import io,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from import_snapshot import selected,initialize,insert,consume
from atom_versions import parse
from source_scope import announcement_month,primary_category

class SnapshotTests(unittest.TestCase):
 def sample(self):
  path=Path(__file__).resolve().parents[1]/'tests/fixtures/kaggle-sample.jsonl'
  with path.open() as f:
   for line in f:
    r=json.loads(line)
    if selected(r):return r
 def test_cross_listing_selects_whole_record(self):
  self.assertTrue(selected({'categories':'hep-th math-ph math.AG'}))
  self.assertTrue(selected({'categories':'math-ph hep-th'}))
  self.assertTrue(selected({'categories':'cmp-lg'}))
  self.assertFalse(selected({'categories':'hep-th'}))
 def test_import_retains_source_fields_and_real_timeline(self):
  with tempfile.TemporaryDirectory() as t:
   d=initialize(Path(t)/'a.sqlite');self.addCleanup(d.close);r=self.sample();insert(d,r)
   got=d.execute('select title,categories,abstract,source_xml from records').fetchone()
   self.assertEqual(got,(r['title'],r['categories'],r['abstract'],''))
   self.assertEqual(d.execute('select count(*) from versions').fetchone()[0],len(r['versions']))
   self.assertEqual(d.execute('select count(*) from versions where detail_json is not null').fetchone()[0],0)
 def test_truncated_stream_rolls_back_uncommitted_page(self):
  with tempfile.TemporaryDirectory() as t:
   d=initialize(Path(t)/'a.sqlite');self.addCleanup(d.close);r=self.sample()
   with self.assertRaises(ValueError):consume(d,io.BytesIO((json.dumps({'line':1,'byte_offset':100,'record':r})+'\n').encode()),Path(t))
   self.assertEqual(d.execute('select count(*) from records').fetchone()[0],0)
 def test_api_returns_true_old_version(self):
  body=(Path(__file__).resolve().parents[1]/'tests/fixtures/api-batch-probe.xml').read_bytes()
  rows=parse(body,['2101.01097v1','2203.11171v1'])
  self.assertTrue(rows['2101.01097v1']['submitted_at'].startswith('2020-12-30'))
  self.assertEqual(rows['2101.01097v1']['primary_category'],'cs.CV')
  with self.assertRaises(ValueError):parse(body,['2101.01097v2','2203.11171v1'])

 def test_announcement_month_is_not_submission_month(self):
  self.assertEqual(announcement_month('2101.01097'),'2021-01')
  self.assertEqual(announcement_month('cmp-lg/9804005v1'),'1998-04')
  self.assertEqual(announcement_month('math/0301001'),'2003-01')
  with self.assertRaises(ValueError):announcement_month('2113.00001')
 def test_aliases_preserve_primary_semantics(self):
  self.assertEqual(primary_category('cmp-lg cs.AI'),'cs.CL')
  self.assertEqual(primary_category('cs.CV cs.LG'),'cs.CV')

 def test_lexically_ordered_v10_is_not_missing_timeline(self):
  with tempfile.TemporaryDirectory() as t:
   d=initialize(Path(t)/'a.sqlite');self.addCleanup(d.close);r=self.sample()
   r['versions']=[{'version':'v'+str(i),'created':'Tue, 17 Apr 2007 12:40:35 GMT'} for i in (1,10,2,3,4,5,6,7,8,9)]
   insert(d,r)
   self.assertEqual(d.execute('select max(number) from versions').fetchone()[0],10)

 def test_duplicate_uses_explicit_latest_metadata_date(self):
  with tempfile.TemporaryDirectory() as t:
   d=initialize(Path(t)/'a.sqlite');self.addCleanup(d.close);r=self.sample()
   r['update_date']='2020-01-01';self.assertTrue(insert(d,r))
   self.assertFalse(insert(d,r))
   r['update_date']='2021-01-01';r['journal-ref']='Revised publication'
   self.assertFalse(insert(d,r))
   self.assertEqual(d.execute('select journal_ref from records').fetchone()[0],'Revised publication')
   self.assertEqual(d.execute('select count(*) from snapshot_revisions').fetchone()[0],1)
   r['journal-ref']='Conflicting same-date value'
   with self.assertRaises(ValueError):insert(d,r)

 def test_daily_events_match_actual_source_sections(self):
  from announcement_details import parse as announcements
  from collections import Counter
  body=(Path(__file__).resolve().parents[1]/'tests/fixtures/catchup-source.html').read_text()
  rows=announcements(body,'cs','2026-09-18')
  self.assertEqual(Counter(x['event_type'] for x in rows),{'new':748,'cross':76,'replace':379})
  self.assertEqual(sum(x['version'] is None for x in rows),91)
  with self.assertRaises(ValueError):announcements(body,'cs','2026-09-17')
  with self.assertRaises(ValueError):announcements(body[:len(body)//2],'cs','2026-09-18')

 def test_actual_paginated_announcement_is_complete_only_after_two_pages(self):
  import gzip
  from collections import Counter
  from announcement_details import parse as announcements
  directory=Path(__file__).resolve().parents[1]/'build/announcements'
  if not (directory/'cs-2026-09-15.page2.html.gz').exists():self.skipTest('Author source fixture not present')
  pages=[gzip.open(directory/f'cs-2026-09-15.page{i}.html.gz','rt').read() for i in (1,2)]
  with self.assertRaises(ValueError):announcements(pages[0],'cs','2026-09-15')
  results=[announcements(s,'cs','2026-09-15',allow_partial=True) for s in pages]
  self.assertEqual([len(x['events']) for x in results],[2000,186])
  rows=[e for p in results for e in p['events']]
  self.assertEqual(len({(r['paper_id'],r['event_type']) for r in rows}),2186)
  self.assertEqual(Counter(r['event_type'] for r in rows),{'new':1330,'cross':142,'replace':714})
