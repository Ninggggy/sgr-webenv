#!/usr/bin/env python3
"""Construction-only, resumable official CDC downloads; never used by runtime."""
import argparse,concurrent.futures,json,pathlib,subprocess,time,zipfile
p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('output');p.add_argument('--size',type=int,required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args()
out=pathlib.Path(a.output);parts=out.parent/(out.name+'.parts');parts.mkdir(parents=True,exist_ok=True);chunk=2*1024*1024

def fetch(i):
 start=i*chunk;end=min(a.size,start+chunk)-1;f=parts/str(i)
 if f.exists() and f.stat().st_size==end-start+1:return
 r=subprocess.run(['curl','-fLsS','--retry','3','--connect-timeout','20','--max-time','600','--range',f'{start}-{end}',a.url,'-o',str(f)])
 if r.returncode or not f.exists() or f.stat().st_size!=end-start+1:raise RuntimeError(f'Failed range {start}-{end}')
 print(json.dumps({'chunk':i,'bytes':end-start+1,'time':time.time()}),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(fetch,range((a.size+chunk-1)//chunk)))
tmp=out.with_suffix(out.suffix+'.assembled')
with tmp.open('wb') as w:
 for i in range((a.size+chunk-1)//chunk):w.write((parts/str(i)).read_bytes())
with zipfile.ZipFile(tmp) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('ZIP CRC failed: '+bad)
tmp.replace(out)
for f in parts.iterdir():f.unlink()
parts.rmdir()
out.with_suffix(out.suffix+'.source.json').write_text(json.dumps({'url':a.url,'bytes':a.size,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'validation':'complete ZIP CRC','import_version':'0.1'},indent=2))
print('COMPLETE',out,flush=True)
