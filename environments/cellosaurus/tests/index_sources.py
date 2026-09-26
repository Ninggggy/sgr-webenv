import sqlite3,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];t=time.time();c=sqlite3.connect('file:'+str(R/'data/cellosaurus.sqlite')+'?mode=ro',uri=True)
c.execute('PRAGMA cache_size=-16384')
count=c.execute('SELECT count(*) FROM cell').fetchone()[0]
indexed=c.execute('SELECT count(*),count(DISTINCT ac) FROM search').fetchone()
# Set comparison avoids repeated scans of an unindexed virtual-table column.
source={r[0] for r in c.execute('SELECT ac FROM cell')};derived={r[0] for r in c.execute('SELECT ac FROM search')}
checks=c.execute('PRAGMA integrity_check').fetchall();foreign=c.execute('PRAGMA foreign_key_check').fetchall()
d={'release':c.execute("SELECT value FROM metadata WHERE key='release'").fetchone()[0],'core_records':count,'indexed_records':indexed[0],'unique_index_accessions':indexed[1],'unindexed':sorted(source-derived),'unknown':sorted(derived-source),'integrity_check':checks,'foreign_key_errors':foreign,'seconds':time.time()-t,'passed':count==indexed[0]==indexed[1]==168970 and source==derived and checks==[('ok',)] and not foreign}
(R/'validation/index-checks.json').write_text(json.dumps(d,indent=2));print(json.dumps(d));assert d['passed']
