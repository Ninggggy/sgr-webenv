"""Check HTTP data against read-only source records, not a service-generated answer."""
import argparse,csv,gzip,io,json,sqlite3,urllib.request,urllib.parse,urllib.error,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--origin',default='http://cellosaurus-web:8080');p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();checks=[]
def get(path):
 try:r=urllib.request.urlopen(a.origin+path,timeout=180)
 except urllib.error.HTTPError as e:r=e
 with r:return r.status,r.read()
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
with sqlite3.connect('file:'+str(a.data/'cellosaurus.sqlite')+'?mode=ro',uri=True) as db:
 ids=[r[0] for r in db.execute('select ac from cell order by ac')]
 for i in range(92):
  ac=ids[i*(len(ids)-1)//91];raw=zlib.decompress(db.execute('select raw from cell where ac=?',(ac,)).fetchone()[0])
  status,body=get('/'+ac+'.txt');check('source TXT '+ac,status==200 and body==raw)
  status,body=get('/'+ac);check('detail '+ac,status==200 and ac.encode() in body)
  q=urllib.parse.quote(ac);status,body=get('/search/export?query='+q+'&format=csv')
  rows=list(csv.DictReader(io.StringIO(body.decode())));check('source present in search export '+ac,status==200 and any(r['Accession']==ac and r['Record'].encode()==raw for r in rows))
testdir=Path(__file__).resolve().parent
parts=json.loads((testdir/'search-partitions.json').read_text());complete_human=set().union(*(set(p['accessions']) for p in parts))
for case in json.loads((testdir/'search-expected.json').read_text()):
 expected=set(case['accessions']) if case['complete'] else complete_human
 url=a.origin+'/search/export?format=csv&query='+urllib.parse.quote(case['query'])
 with urllib.request.urlopen(url,timeout=180) as response:
  actual={r['Accession'] for r in csv.DictReader(io.TextIOWrapper(response,encoding='utf-8'))}
 check('official search candidate set '+case['query'],actual==expected and len(actual)==case['total'])
for name,meta in json.loads((a.data/'sources.json').read_text()).items():
 total=0
 with urllib.request.urlopen(a.origin+'/databases/cellosaurus/'+name,timeout=180) as response,gzip.open(a.data/(name+'.gz'),'rb') as source:
  while True:
   x=source.read(65536);y=response.read(65536);assert x==y,name;total+=len(y)
   if not x:break
 check('complete original download '+name,total==meta['raw_bytes'])
for version in ['53','54']:
 path='history/'+version+'/cellosaurus_name_conflicts.txt';status,body=get('/'+path)
 with gzip.open(a.data/(path+'.gz'),'rb') as f:expected=f.read()
 check('history '+version,status==200 and body==expected)
for path in ['/data/cellosaurus.sqlite','/.git/config','/app/server.py','/proc/self/environ','/%2e%2e/etc/passwd','/validation/task-checks.json']:
 status,_=get(path);check('private path denied '+path,status==404)
status,body=get('/str-search/api/database');meta=json.loads(body);check('CLASTR same release',status==200 and meta['version']=='56.0')
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'checks':checks,'passed':all(r['passed'] for r in checks)},indent=2)+'\n');print(len(checks),'source-to-HTTP checks passed')
