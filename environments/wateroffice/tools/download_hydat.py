"""Author-only bounded, resumable HTTP-range acquisition of an official release."""
import concurrent.futures, pathlib, subprocess, time, json, zipfile, os
ROOT=pathlib.Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'author/hydat-release.json').read_text())
size=meta['compressed_bytes']; step=4*1024*1024
out=ROOT/'author/Hydat_sqlite3_20260717.zip'
parts=ROOT/'author/hydat-parts'; parts.mkdir(exist_ok=True)
def fetch(start):
 end=min(size,start+step)-1; p=parts/str(start)
 for attempt in range(12):
  have=p.stat().st_size if p.exists() else 0
  if have==end-start+1:return
  if have>end-start+1:raise RuntimeError('oversized range')
  tmp=p.with_suffix('.part')
  r=subprocess.run(['curl','-fLsS','--connect-timeout','15','--max-time','120','-r',f'{start+have}-{end}',meta['source'],'-o',str(tmp)],capture_output=True)
  if tmp.exists():
   with p.open('ab') as dst, tmp.open('rb') as src:
    while b:=src.read(1024*1024):dst.write(b)
   tmp.unlink()
  if p.exists() and p.stat().st_size==end-start+1:return
  time.sleep(2)
 raise RuntimeError(f'failed range {start}')
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 for n,_ in enumerate(pool.map(fetch,range(0,size,step)),1): print(f'completed {n}/{(size+step-1)//step}',flush=True)
with out.open('wb') as dst:
 for start in range(0,size,step):
  p=parts/str(start)
  with p.open('rb') as src:
   while b:=src.read(1024*1024):dst.write(b)
  p.unlink()
with zipfile.ZipFile(out) as z:
 assert [(i.filename,i.file_size) for i in z.infolist()]==[('Hydat.sqlite3',1296893952)]
 assert z.testzip() is None
print('Verified ZIP integrity and size',flush=True)
