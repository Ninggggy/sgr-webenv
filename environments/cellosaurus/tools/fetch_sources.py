import urllib.request,gzip,json,os,time,shutil,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data';D.mkdir(exist_ok=True)
BASE='https://ftp.expasy.org/databases/cellosaurus/'
NAMES=['README','cellosaurus_relnotes.txt','cellosaurus.txt','cellosaurus_refs.txt','cellosaurus.xml','cellosaurus.xsd','cellosaurus_xrefs.txt','cellosaurus_deleted_ACs.txt','cellosaurus_name_conflicts.txt','cellopub.txt','cellosaurus.obo','cellosaurus_faq.txt']
def reserve():
 if shutil.disk_usage(D).free<5*1024**3+64*1024**2:raise RuntimeError('Disk reserve reached; no further acquisition')
m=json.loads((D/'sources.json').read_text()) if (D/'sources.json').exists() else {}
for name in NAMES:
 if m.get(name,{}).get('complete'):continue
 reserve();url=BASE+name;part=D/(name+'.gz.part');raw=0;t=time.time()
 head=urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=60)
 expected=int(head.headers.get('Content-Length','0'));modified=head.headers.get('Last-Modified');head.close()
 if expected>8*1024**2:
  step=2*1024**2
  def chunk(offset):
   end=min(expected,offset+step)-1
   for attempt in range(4):
    try:
     req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-{end}'})
     with urllib.request.urlopen(req,timeout=90) as r:
      if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {offset}-{end}/{expected}':raise RuntimeError('Range mismatch')
      data=r.read()
      if len(data)!=end-offset+1:raise RuntimeError('Short range')
      return data
    except Exception:
     if attempt==3:raise
     time.sleep(attempt+1)
  with concurrent.futures.ThreadPoolExecutor(6) as pool,gzip.open(part,'wb',compresslevel=6) as out:
   for data in pool.map(chunk,range(0,expected,step)):
    out.write(data);raw+=len(data);reserve();print(name,'progress',raw,expected,flush=True)
 else:
  with urllib.request.urlopen(url,timeout=90) as r,gzip.open(part,'wb',compresslevel=6) as out:
   while True:
    b=r.read(1024**2)
    if not b:break
    out.write(b);raw+=len(b);reserve()
 if expected and expected!=raw:raise RuntimeError('Incomplete '+name)
 if name in ['README','cellosaurus_relnotes.txt']:
  s=gzip.open(part,'rt').read()
  if name=='cellosaurus_relnotes.txt' and not ('56' in s and '2026' in s):raise RuntimeError('Unexpected release; obtain release56 archive')
 os.replace(part,D/(name+'.gz'))
 m[name]={'url':url,'release':'56','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'raw_bytes':raw,'compressed_bytes':(D/(name+'.gz')).stat().st_size,'last_modified':modified,'complete':True}
 (D/'sources.json').write_text(json.dumps(m,indent=2));print(name,raw,'seconds',round(time.time()-t,2),'free',shutil.disk_usage(D).free,flush=True)
