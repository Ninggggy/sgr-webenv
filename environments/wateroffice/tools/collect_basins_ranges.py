"""Resume official GeoJSON acquisition in bounded byte ranges on the author workstation."""
import pathlib,subprocess,concurrent.futures,json,gzip,shutil,re,time
R=pathlib.Path(__file__).resolve().parents[1];A=R/'author/basins';O=R/'data/map/basins';A.mkdir(exist_ok=True);O.mkdir(exist_ok=True);STEP=1024*1024
sizes=json.loads((A/"sizes.json").read_text()) if (A/"sizes.json").exists() else {}
for n in range(1,12):
 code=f'{n:02}';p=A/(code+'.json');url=f'https://wateroffice.ec.gc.ca/data/map/geojson/basin_{code}_simplified.json'
 if p.exists():sizes[code]=p.stat().st_size;continue
 if code in sizes:continue
 headers=subprocess.check_output(['curl','-fsSI','--max-time','30',url],text=True);sizes[code]=int(re.search(r'(?im)^Content-Length: (\d+)',headers)[1]);assert sizes[code]<128*1024**2
(A/'sizes.json').write_text(json.dumps(sizes))
work=[]
for code,size in sizes.items():
 if (A/(code+'.json')).exists():continue
 directory=A/(code+'-parts');directory.mkdir(exist_ok=True)
 # Seed safely from the already downloaded contiguous prefix.
 old=A/(code+'.partial')
 if old.exists():
  with old.open('rb') as src:
   for start in range(0,size,STEP):
    data=src.read(min(STEP,size-start))
    if not data:break
    dest=directory/str(start)
    if not dest.exists():dest.write_bytes(data)
 for start in range(0,size,STEP):work.append((code,start,min(size,start+STEP)-1))
def fetch(job):
 code,start,end=job;p=A/(code+'-parts')/str(start);url=f'https://wateroffice.ec.gc.ca/data/map/geojson/basin_{code}_simplified.json'
 for attempt in range(10):
  have=p.stat().st_size if p.exists() else 0
  if have==end-start+1:return
  assert have<end-start+1
  tmp=p.with_suffix('.incoming');headers=p.with_suffix('.headers')
  result=subprocess.run(['curl','-fLsS','--connect-timeout','15','--max-time','90','-D',str(headers),'-r',f'{start+have}-{end}',url,'-o',str(tmp)],capture_output=True)
  h=headers.read_text() if headers.exists() else ''
  if tmp.exists() and re.search(rf'(?im)^Content-Range: bytes {start+have}-',h):
   with p.open('ab') as dst,tmp.open('rb') as src:shutil.copyfileobj(src,dst)
   tmp.unlink()
  elif tmp.exists():raise RuntimeError('Server did not honor byte range: '+code)
  if p.exists() and p.stat().st_size==end-start+1:return
  time.sleep(1)
 raise RuntimeError('Failed range '+str(job))
work.sort(key=lambda job:(job[0]!='08',job[0],job[1]))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for i,_ in enumerate(pool.map(fetch,work),1):
  if i%10==0:print('ranges',i,'/',len(work),flush=True)
results=[]
for code,size in sizes.items():
 p=A/(code+'.json')
 if not p.exists():
  with p.open('wb') as dst:
   for start in range(0,size,STEP):
    with (A/(code+'-parts')/str(start)).open('rb') as src:shutil.copyfileobj(src,dst)
 assert p.stat().st_size==size
 obj=json.loads(p.read_text());assert obj['type']=='FeatureCollection';assert all('StationNum' in f['properties'] for f in obj['features'])
 out=O/(code+'.json.gz')
 with p.open('rb') as src,gzip.open(out,'wb') as dst:shutil.copyfileobj(src,dst)
 row={'basin':code,'source':f'https://wateroffice.ec.gc.ca/data/map/geojson/basin_{code}_simplified.json','features':len(obj['features']),'raw_bytes':size,'stored_bytes':out.stat().st_size};results.append(row);print(row,flush=True)
assert sum(r['stored_bytes'] for r in results)<192*1024**2
(O/'manifest.json').write_text(json.dumps({'capture_date':'2026-09-25','sources':results},indent=2))
