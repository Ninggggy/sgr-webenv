#!/usr/bin/env python3
"""Fixed-release source preparation. No runtime network access."""
import argparse,concurrent.futures,csv,datetime,json,os,re,sqlite3,time,urllib.request
from pathlib import Path
ROOT=Path(os.environ.get('CENSUS_PREPARE_ROOT',Path(__file__).resolve().parents[1]))
CORE='B01001 B28002 B11010 B08201 B19013 B25003 C16002 B25070 B25014 B16004 B28011 B09010 B18105 B25044 B25024'.split()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def fetch(url,path,kind,table=None,refresh=False):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);side=path.with_suffix(path.suffix+'.source.json')
 def validate(raw):
  if not 50<len(raw)<50000000:raise ValueError('Invalid source size')
  d=json.loads(raw)
  if kind=='groups' and (not isinstance(d.get('groups'),list) or not d['groups']):raise ValueError('Missing catalog')
  if kind=='variables' and not any(k.startswith(table+'_') for k in d.get('variables',{})):raise ValueError('Wrong table')
  if kind=='geo' and ('features' not in d or 'error' in d or d.get('exceededTransferLimit')):raise ValueError('Invalid or truncated geographic response')
  return d
 if path.exists() and not refresh:
  d=validate(path.read_bytes());m=json.loads(side.read_text())
  if m['url']!=url:raise ValueError('Cache release/source mismatch')
  m['checked_utc']=now();side.write_text(json.dumps(m,indent=2));return d
 raw=None
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=40) as r:raw=r.read(50000001)
   d=validate(raw);break
  except Exception as e:
   if attempt==2:
    path.with_suffix(path.suffix+'.failure.json').write_text(json.dumps({'url':url,'checked_utc':now(),'error':str(e)}));raise
   time.sleep(attempt+1)
 tmp=path.with_suffix(path.suffix+'.part');tmp.write_bytes(raw);tmp.replace(path)
 side.write_text(json.dumps({'url':url,'retrieved_utc':now(),'checked_utc':now(),'bytes':len(raw)},indent=2));return d

def metadata():
 releases=[(y,p) for y in range(2016,2020) for p in ['acs5','acs1']]
 def catalog(item):
  y,p=item
  d=fetch(f'https://api.census.gov/data/{y}/acs/{p}/groups.json',ROOT/f'sources/api/{y}/{p}/groups.json','groups')
  return y,p,{g['name'] for g in d['groups']}
 catalogs=list(concurrent.futures.ThreadPoolExecutor(4).map(catalog,releases))
 jobs=[]
 for y,p,names in catalogs:
  for t in CORE:
   if t in names:jobs.append((f'https://api.census.gov/data/{y}/acs/{p}/groups/{t}.json',ROOT/f'sources/api/{y}/{p}/{t}.json','variables',t))
   else:print(y,p,t,'not published in official catalog',flush=True)
 def job(j):
  try:fetch(*j);return str(j[1].relative_to(ROOT)),True
  except Exception as e:return str(j[1].relative_to(ROOT)),str(e)
 results=list(concurrent.futures.ThreadPoolExecutor(4).map(job,jobs))
 for result in results:print(result,flush=True)
 if any(ok is not True for _,ok in results):raise RuntimeError('Metadata preparation incomplete; see individual failure records')

def norm(s):return re.sub(r'[^a-z0-9]','',s.lower().replace('estimate!!',''))
def numeric(s):
 s=s.strip().replace(',','').replace('±','')
 if re.fullmatch(r'-?\d+(\.\d+)?',s):
  n=float(s);return (int(n) if n.is_integer() else n),None
 return None,s or None

def build():
 existing=ROOT/'data/census.sqlite'
 if existing.exists():
  with sqlite3.connect(existing) as check:
   if check.execute("SELECT 1 FROM sqlite_master WHERE name='publication_scopes'").fetchone():raise ValueError('Expanded database exists. Use tools/prepare-data --output for an independent complete rebuild; legacy-only replacement is refused.')
 data=ROOT/'data';data.mkdir(exist_ok=True);tmp=data/'census.next.sqlite'
 if tmp.exists():raise ValueError('Independent import already exists; inspect before retry')
 db=sqlite3.connect(tmp)
 db.executescript('''
 CREATE TABLE releases(year INTEGER,product TEXT,PRIMARY KEY(year,product));
 CREATE TABLE tables(year INTEGER,product TEXT,id TEXT,title TEXT,universe TEXT,PRIMARY KEY(year,product,id));
 CREATE TABLE variables(year INTEGER,product TEXT,table_id TEXT,id TEXT,label TEXT,unit TEXT,PRIMARY KEY(year,product,id));
 CREATE TABLE geographies(year INTEGER,id TEXT,state TEXT,name TEXT,level TEXT,PRIMARY KEY(year,id));
 CREATE TABLE cells(year INTEGER,product TEXT,table_id TEXT,geo TEXT,variable TEXT,estimate REAL,moe REAL,ea TEXT,ma TEXT,PRIMARY KEY(year,product,geo,variable));
 CREATE INDEX lookup ON cells(year,product,table_id,geo);
 CREATE TABLE sources(file TEXT PRIMARY KEY,year INTEGER,product TEXT,table_id TEXT,geographies INTEGER,variables INTEGER);
 ''')
 universes=json.loads((ROOT/'sources/universes.json').read_text()) if (ROOT/'sources/universes.json').exists() else {}
 for y in range(2016,2020):
  for p in ['acs5','acs1']:
   d=ROOT/f'sources/api/{y}/{p}';db.execute('INSERT INTO releases VALUES (?,?)',(y,p))
   catalog=json.loads((d/'groups.json').read_text())
   for g in catalog['groups']:
    db.execute('INSERT INTO tables VALUES (?,?,?,?,?)',(y,p,g['name'],g['description'],universes.get(f'{y}/{g["name"]}', 'Definition not yet archived')))
   for t in CORE:
    f=d/f'{t}.json'
    if not f.exists():continue
    for k,v in json.loads(f.read_text())['variables'].items():
     if re.fullmatch(t+r'_\d+E',k):db.execute('INSERT INTO variables VALUES (?,?,?,?,?,?)',(y,p,t,k,v['label'],'US dollars' if t=='B19013' else 'Count'))
 report=[]
 # Official geographic crosswalk is mandatory; do not invent FIPS from alphabetical position.
 geo_files=list((ROOT/'sources/geography').glob('*.json')) if (ROOT/'sources/geography').exists() else []
 cross={}
 for f in geo_files:
  if '.source.' in f.name or '.failure.' in f.name:continue
  y=int(f.name[:4]);d=json.loads(f.read_text())
  for feature in d.get('features',[]):
   a=feature.get('properties',feature.get('attributes'));gid=a['GEOID'];name=a['NAME'];state=a.get('STATE',a.get('STATEFP',gid[:2]));level='state' if len(gid)==2 else 'county'
   suffix={'06':' County','15':' Parish','04':' Borough','05':' Census Area','25':' city','03':' City and Borough','12':' Municipality','13':' Municipio'}.get(a.get('LSAD'),'') if level=='county' else ''
   name+=suffix
   cross[y,name,state]=gid
   db.execute('INSERT OR IGNORE INTO geographies VALUES (?,?,?,?,?)',(y,gid,state,name,level))
 states={'2018':('37','North Carolina'),'2019':('35','New Mexico'),'2017':('06','California'),'2016':('42','Pennsylvania')}
 for f in sorted((ROOT/'sources/historical').glob('*.csv')):
  m=re.match(r'ACSDT5Y(\d+)\.([BC]\d+)',f.name);y,t=int(m[1]),m[2];sf,st=states[str(y)]
  rows=list(csv.reader(f.open(encoding='utf-8-sig')))
  defs=dict(db.execute('SELECT id,label FROM variables WHERE year=? AND product=? AND table_id=?',(y,'acs5',t)))
  labels={norm(v):k for k,v in defs.items()}; observations=[]
  if rows[1][0].strip() in ['Total:','Total','Median household income in the past 12 months (in 2016 inflation-adjusted dollars)','Median household income in the past 12 months (in 2017 inflation-adjusted dollars)'] or rows[0][1].endswith('!!Estimate'):
   # Original orientation: header Geography!!Estimate / Geography!!Margin of Error.
   hierarchy=[]
   for r in rows[1:]:
    raw=r[0];depth=(len(raw)-len(raw.lstrip()))//4
    hierarchy=hierarchy[:depth]+[raw.strip()]
    label='!!'.join(hierarchy);key=labels.get(norm(label))
    if not key:raise ValueError(f'Unmatched label {f.name}: {label}')
    for col in range(1,len(rows[0]),2):
     name=rows[0][col].split('!!')[0];observations.append((name,key,r[col],r[col+1]))
  else:
   for col,label in enumerate(rows[0][1:],1):
    key=labels.get(norm(label))
    if not key:raise ValueError(f'Unmatched label {f.name}: {label}')
    for row in range(1,len(rows),3):observations.append((rows[row][0],key,rows[row+1][col],rows[row+2][col]))
  geos=set();vars=set()
  for name,key,e,m in observations:
   bare=name[:-(len(st)+2)] if name.endswith(', '+st) else name;gid=cross.get((y,bare,sf))
   if bare==st:gid=sf
   if not gid:raise ValueError(f'Official GEOID missing: {y} {name}')
   db.execute('INSERT OR IGNORE INTO geographies VALUES (?,?,?,?,?)',(y,gid,sf,name,'state' if gid==sf else 'county'))
   ev,ea=numeric(e);mv,ma=numeric(m)
   db.execute('INSERT INTO cells VALUES (?,?,?,?,?,?,?,?,?)',(y,'acs5',t,gid,key,ev,mv,ea,ma));geos.add(gid);vars.add(key)
  expected_geos={g[0] for g in db.execute('SELECT id FROM geographies WHERE year=? AND state=?',(y,sf))}
  if geos!=expected_geos:raise ValueError(f'Incomplete geography set for {y} {t}: missing {sorted(expected_geos-geos)}')
  if set(defs)!=vars:raise ValueError(f'Incomplete table {t}: {set(defs)-vars}')
  db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?)',(f.name,y,'acs5',t,len(geos),len(vars)))
  report.append({'file':f.name,'year':y,'table':t,'geographies':len(geos),'variables':len(vars)})
 db.commit()
 if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite import failed')
 db.close();tmp.replace(data/'census.sqlite');(ROOT/'validation/import.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['metadata','build']);args=parser.parse_args();globals()[args.action]()
