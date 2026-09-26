"""Rebuild only the derived FTS index, using the complete existing core records."""
import sqlite3,zlib
from import_data import D,reserve,SCHEMA,search_body
reserve();d=sqlite3.connect(D/'cellosaurus.sqlite');d.execute('PRAGMA cache_size=-32768')
d.execute('DROP TABLE search');d.execute(next(x for x in SCHEMA.split(';') if 'CREATE VIRTUAL TABLE search' in x));d.commit()
for i,(ac,raw) in enumerate(d.execute('SELECT ac,raw FROM cell'),1):
 refs=[r[0] for r in d.execute('SELECT DISTINCT r.raw FROM cellref c JOIN ref_alias a ON a.name=c.ref JOIN reference r ON r.id=a.id WHERE c.ac=?',(ac,))]
 body=search_body(zlib.decompress(raw).decode(),refs)
 d.execute('INSERT INTO search VALUES(?,?)',(ac,body))
 if i%2000==0:d.commit();reserve();print(i,flush=True)
d.commit();d.close();print('Indexed',i)
