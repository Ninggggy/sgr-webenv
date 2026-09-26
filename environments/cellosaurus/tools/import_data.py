"""Stream the complete TXT sources into a compact relational archive."""
import gzip,json,re,sqlite3,zlib,time,resource,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data'
sys.path.insert(0,str(R/'app'))
from search_text import search_body
SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE cell(ac TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,species TEXT NOT NULL,raw BLOB NOT NULL);
CREATE TABLE alias(name TEXT,ac TEXT REFERENCES cell(ac),kind TEXT,PRIMARY KEY(name,ac,kind));
CREATE INDEX alias_name ON alias(name COLLATE NOCASE);
CREATE INDEX alias_ac ON alias(ac,kind);
CREATE TABLE relation(src TEXT REFERENCES cell(ac),dst TEXT,kind TEXT,PRIMARY KEY(src,dst,kind));
CREATE INDEX relation_dst ON relation(dst,kind);
CREATE TABLE membership(ac TEXT REFERENCES cell(ac),kind TEXT,label TEXT,PRIMARY KEY(ac,kind,label));
CREATE INDEX membership_label ON membership(kind,label);
CREATE TABLE reference(id INTEGER PRIMARY KEY,raw TEXT);
CREATE TABLE ref_alias(name TEXT,id INTEGER REFERENCES reference(id),PRIMARY KEY(name,id));
CREATE TABLE cellref(ac TEXT REFERENCES cell(ac),ref TEXT,PRIMARY KEY(ac,ref));
CREATE INDEX cellref_ref ON cellref(ref);
CREATE VIRTUAL TABLE search USING fts5(ac UNINDEXED,body,tokenize="unicode61 remove_diacritics 2 tokenchars '_'",detail=full);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
'''
def records(path,start):
 with gzip.open(path,'rt',encoding='utf-8') as f:
  buf=None
  for line in f:
   if line.startswith(start+'   ') and buf is None:buf=[]
   if buf is not None:buf.append(line)
   if line.startswith('//') and buf is not None:
    yield ''.join(buf);buf=None
  if buf:raise ValueError('Unterminated record')
def fields(s):
 d={}
 for line in s.splitlines():
  if len(line)>4 and line[2:5]=='   ':d.setdefault(line[:2],[]).append(line[5:])
 return d
def reference_ids(value):
 # DOI identifiers can contain semicolons; only a following namespace starts a new ID.
 return [v.strip() for v in re.split(r";\s+(?=[A-Za-z]+=)",value.rstrip(";")) if v.strip()]
def reserve():
 if shutil.disk_usage(D).free<5*1024**3+128*1024**2:raise RuntimeError('Disk reserve reached; import stopped')
def main():
 start=time.time();reserve();p=D/'cellosaurus.sqlite'
 if p.exists():raise RuntimeError('Existing database preserved; explicit recovery needed')
 for name in ['cellosaurus.txt','cellosaurus_refs.txt']:
  with gzip.open(D/(name+'.gz'),'rt') as f:head=f.read(1200)
  assert 'Version: 56.0' in head,name
 db=sqlite3.connect(p);db.executescript(SCHEMA);db.execute('PRAGMA cache_size=-32768');db.execute('PRAGMA temp_store=FILE')
 for i,s in enumerate(records(D/'cellosaurus_refs.txt.gz','RX'),1):
  d=fields(s);db.execute('INSERT INTO reference VALUES(?,?)',(i,s))
  for rx in reference_ids(d['RX'][0]):
   if rx.strip():db.execute('INSERT INTO ref_alias VALUES(?,?)',(rx.strip(),i))
 db.commit();unknown={};count=0
 for s in records(D/'cellosaurus.txt.gz','ID'):
  d=fields(s);ac=d['AC'][0];count+=1
  db.execute('INSERT INTO cell VALUES(?,?,?,?,?)',(ac,d['ID'][0],d['CA'][0],' / '.join(d.get('OX',[])),zlib.compress(s.encode())))
  for code,kind in [('ID','name'),('SY','synonym'),('AS','secondary')]:
   for names in d.get(code,[]):
    for name in ([names] if code=='ID' else names.split('; ')):
     if name.strip():db.execute('INSERT OR IGNORE INTO alias VALUES(?,?,?)',(name.strip(),ac,kind))
  for code,kind in [('HI','parent'),('OI','same_individual')]:
   for v in d.get(code,[]):
    dst=v.split()[0];db.execute('INSERT OR IGNORE INTO relation VALUES(?,?,?)',(ac,dst,kind))
  for v in d.get('CC',[]):
   if v.startswith(('Group: ','Part of: ')):
    kind,label=v.split(': ',1);db.execute('INSERT OR IGNORE INTO membership VALUES(?,?,?)',(ac,kind,label.rstrip('.')))
  for v in d.get('RX',[]):
   for rx in reference_ids(v):
    if rx.strip():db.execute('INSERT OR IGNORE INTO cellref VALUES(?,?)',(ac,rx.strip()))
  for code in d:
   if code not in 'ID AC AS SY DR RX WW CC ST DI OX HI OI SX AG CA DT'.split():unknown[code]=unknown.get(code,0)+1
  if count%2000==0:db.commit();reserve();print('cells',count,flush=True)
 db.commit();assert count==168970,count
 for i,(ac,raw) in enumerate(db.execute('SELECT ac,raw FROM cell'),1):
  refs=[r[0] for r in db.execute('SELECT DISTINCT r.raw FROM cellref c JOIN ref_alias a ON a.name=c.ref JOIN reference r ON r.id=a.id WHERE c.ac=?',(ac,))]
  body=search_body(zlib.decompress(raw).decode(),refs)
  db.execute('INSERT INTO search VALUES(?,?)',(ac,body))
  if i%2000==0:db.commit();reserve();print('indexed',i,flush=True)
 db.execute('INSERT INTO metadata VALUES(?,?)',('release','56.0'));db.commit()
 report={'cells':count,'references':db.execute('SELECT count(*) FROM reference').fetchone()[0],'duplicate_reference_aliases':db.execute('SELECT name,count(*) FROM ref_alias GROUP BY name HAVING count(*)>1').fetchall(),'unknown_codes':unknown,'dangling_relations':db.execute('SELECT src,dst,kind FROM relation WHERE dst NOT IN (SELECT ac FROM cell)').fetchall(),'unresolved_references':db.execute('SELECT DISTINCT ref FROM cellref WHERE ref NOT IN (SELECT name FROM ref_alias)').fetchall(),'foreign_keys':db.execute('PRAGMA foreign_key_check').fetchall(),'seconds':time.time()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_bytes':p.stat().st_size}
 db.close();(R/'validation').mkdir(exist_ok=True);(R/'validation/import.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
