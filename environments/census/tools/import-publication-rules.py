import json,sqlite3,pathlib,sys,shutil
R=pathlib.Path(__file__).resolve().parents[1];db=pathlib.Path(sys.argv[1]);assert db.resolve()!=(R/'data/census.sqlite').resolve()
c=sqlite3.connect(db);c.execute('CREATE TABLE IF NOT EXISTS table_publication(year INTEGER,product TEXT,table_id TEXT,universe TEXT,restriction TEXT,source TEXT,PRIMARY KEY(year,product,table_id))')
if 'title' not in [r[1] for r in c.execute('PRAGMA table_info(table_publication)')]:c.execute('ALTER TABLE table_publication ADD COLUMN title TEXT')
for y in range(2016,2020):
 for p in ['acs5','acs1']:
  f=R/f'validation/repair-20260917/independent-{y}-{p}-restrictions.json';d=json.loads(f.read_text());dest=R/f'sources/summary/{y}/{p}';dest.mkdir(exist_ok=True,parents=True)
  original=pathlib.Path(d['local_source']);cached=dest/original.name
  if original.exists() and original.resolve()!=cached.resolve():shutil.copy2(original,cached)
  if not cached.exists():raise FileNotFoundError('Missing archived appendix: '+str(cached))
  (dest/'appendix-fields.json').write_text(json.dumps(d,indent=2))
  c.execute('DELETE FROM table_publication WHERE year=? AND product=?',(y,p))
  for row in d['tables']:
   c.execute('INSERT OR REPLACE INTO table_publication VALUES (?,?,?,?,?,?,?)',(y,p,row['table_id'],row['universe'],row['restrictions'],d['url'],row['title']))
c.commit();c.close()
