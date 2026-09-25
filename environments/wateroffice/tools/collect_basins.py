import pathlib,subprocess,concurrent.futures,json,gzip,shutil
R=pathlib.Path(__file__).resolve().parents[1];A=R/'author/basins';O=R/'data/map/basins';A.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def run(code):
 url=f'https://wateroffice.ec.gc.ca/data/map/geojson/basin_{code}_simplified.json';p=A/(code+'.json');out=O/(code+'.json.gz')
 if not p.exists():
  temp=p.with_suffix('.partial');subprocess.run(['curl','-fLsS','--compressed','--max-time','180','--max-filesize','134217728',url,'-o',str(temp)],check=True);temp.rename(p)
 obj=json.loads(p.read_text());assert obj['type']=='FeatureCollection';features=obj['features'];assert all('StationNum' in f['properties'] for f in features)
 with p.open('rb') as src,gzip.open(out,'wb') as dst:shutil.copyfileobj(src,dst)
 r={'basin':code,'source':url,'features':len(features),'raw_bytes':p.stat().st_size,'stored_bytes':out.stat().st_size};print(r,flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(run,[f'{i:02}' for i in range(1,12)]))
assert sum(x['stored_bytes'] for x in results)<192*1024**2
(O/'manifest.json').write_text(json.dumps({'capture_date':'2026-09-25','sources':results},indent=2))
