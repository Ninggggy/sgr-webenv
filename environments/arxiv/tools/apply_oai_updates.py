"""Merge a completed dated OAI collection into an unpublished author database.
Preserve previous observations and the exact official XML for every update.
"""
import argparse,json,sqlite3,sys
from pathlib import Path
from harvest import check_space,utc
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root/'runtime'),str(root/'upstream/arxiv-base')]
from source_scope import groups,equivalent_categories,announcement_month
p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--updates',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
s=sqlite3.connect('file:'+str(a.updates)+'?mode=ro',uri=True);s.row_factory=sqlite3.Row
states=[dict(r) for r in s.execute('SELECT * FROM harvest_state')]
if len(states)!=3 or not all(r['complete'] for r in states):raise SystemExit('Dated OAI collection is not complete')
d=sqlite3.connect(a.database);d.row_factory=sqlite3.Row;d.execute('PRAGMA foreign_keys=ON')
d.executescript('CREATE INDEX IF NOT EXISTS catalog_paper ON catalog(paper_id); CREATE TABLE IF NOT EXISTS metadata_updates(paper_id TEXT PRIMARY KEY, previous_json TEXT, previous_latest INTEGER, source_updated TEXT, applied_at TEXT);')
count=0;added=0;ids=[]
for r in s.execute('SELECT * FROM records ORDER BY id'):
 check_space(root,reserve=256*1024**2) if count%1000==0 else None
 pid=r['id'];before=d.execute('SELECT * FROM records WHERE id=?',(pid,)).fetchone();oldnum=d.execute('SELECT max(number) FROM versions WHERE paper_id=?',(pid,)).fetchone()[0]
 incoming=[dict(v) for v in s.execute('SELECT * FROM versions WHERE paper_id=? ORDER BY number',(pid,))]
 if incoming and oldnum and incoming[-1]['number']<oldnum:raise ValueError('Source unexpectedly removed versions '+pid)
 with d:
  d.execute('INSERT OR IGNORE INTO metadata_updates VALUES (?,?,?,?,?)',(pid,json.dumps(dict(before)) if before else None,oldnum,r['oai_modified'],utc()))
  columns=list(r.keys());d.execute('INSERT INTO records VALUES ('+','.join('?' for _ in columns)+') ON CONFLICT(id) DO UPDATE SET '+','.join(c+'=excluded.'+c for c in columns if c!='id'),tuple(r))
  for v in incoming:
   d.execute('INSERT INTO versions(paper_id,number,submitted_at,source_size,source_type) VALUES (?,?,?,?,?) ON CONFLICT(paper_id,number) DO UPDATE SET submitted_at=excluded.submitted_at,source_size=excluded.source_size,source_type=excluded.source_type,detail_json=CASE WHEN versions.submitted_at=excluded.submitted_at THEN versions.detail_json ELSE NULL END,detail_source=CASE WHEN versions.submitted_at=excluded.submitted_at THEN versions.detail_source ELSE NULL END',(pid,v['number'],v['submitted_at'],v['source_size'],v['source_type']))
  d.execute('DELETE FROM membership WHERE paper_id=?',(pid,));d.execute('DELETE FROM catalog WHERE paper_id=?',(pid,))
  if not r['deleted']:
   cats=r['categories'] or '';contexts=set()
   for c in cats.split():
    for e in equivalent_categories(c):contexts.add(e);contexts.add(e.split('.')[0])
   d.executemany('INSERT INTO membership VALUES (?,?)',[(pid,g+':'+g) for g in groups(cats)])
   d.executemany('INSERT INTO catalog VALUES (?,?,?)',[(pid,c,announcement_month(pid)) for c in sorted(contexts)])
  count+=1;added+=int(before is None);ids.append(pid)
 if count%1000==0:print(json.dumps({'updated':count,'added':added}),flush=True)
# This is completion of incremental harvesting, not a claim of an instantaneous snapshot.
with d:
 for state in states:d.execute('UPDATE harvest_state SET response_date=?,updated_at=? WHERE source_set=?',(state['response_date'],utc(),state['source_set']))
report={'source_states':states,'updated':count,'added':added,'paper_ids':ids,'records':d.execute('SELECT count(*) FROM records WHERE deleted=0').fetchone()[0],'collected_over_time':True}
a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='paper_ids'}))
