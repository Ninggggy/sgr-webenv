import sqlite3,zlib
from import_data import D,fields
c=sqlite3.connect(D/'cellosaurus.sqlite')
with c:
 c.execute("CREATE INDEX IF NOT EXISTS alias_ac ON alias(ac,kind)")
 c.execute("DELETE FROM alias WHERE kind='synonym'")
 for ac,raw in c.execute('SELECT ac,raw FROM cell'):
  for v in fields(zlib.decompress(raw).decode()).get('SY',[]):
   for name in v.split('; '):
    if name.strip():c.execute('INSERT OR IGNORE INTO alias VALUES(?,?,?)',(name.strip(),ac,'synonym'))
print('Repaired synonym boundaries')
