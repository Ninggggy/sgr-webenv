"""Author-side bounded NRCan Toporama tile snapshot. Basemap differs from Google."""
import math,pathlib,json,urllib.parse,subprocess,concurrent.futures,threading
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'data/map';OUT.mkdir(parents=True,exist_ok=True)
regions={'Canada':(-141,41,-52,84),'Bulkley':(-128.0,54.2,-126.1,55.5),'Thompson':(-121.6,50.35,-119.4,51.1),'Columbia':(-119.5,48.9,-115.5,52.0),'Peace':(-119.3,55.4,-114.0,59.1),'Saint John':(-69.1,45.1,-65.8,47.6)}
def xy(lon,lat,z):return ((lon+180)/360*2**z,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
tiles=set()
for name,(west,south,east,north) in regions.items():
 for z in (range(2,6) if name=='Canada' else range(6,11)):
  x0,y0=xy(west,north,z);x1,y1=xy(east,south,z)
  tiles.update((z,x,y) for x in range(int(x0),int(x1)+1) for y in range(int(y0),int(y1)+1))
print('Tiles',len(tiles),flush=True)
lock=threading.Lock();usage=sum(p.stat().st_size for p in OUT.rglob('*.png'))
def fetch(tile):
 global usage
 z,x,y=tile;p=OUT/str(z)/str(x)/(str(y)+'.png');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n':return {'tile':tile,'ok':True}
 world=20037508.342789244;step=2*world/2**z
 bbox=[-world+x*step,world-(y+1)*step,-world+(x+1)*step,world-y*step]
 url='https://maps.geogratis.gc.ca/wms/toporama_en?'+urllib.parse.urlencode({'service':'WMS','request':'GetMap','version':'1.1.1','layers':'WMS-Toporama','styles':'','srs':'EPSG:3857','bbox':','.join(map(str,bbox)),'width':256,'height':256,'format':'image/png'})
 r=subprocess.run(['curl','-fLsS','--compressed','--connect-timeout','10','--max-time','45',url],capture_output=True)
 if r.returncode or not r.stdout.startswith(b'\x89PNG\r\n\x1a\n'):return {'tile':tile,'ok':False,'error':r.stderr.decode()[:150] or r.stdout[:150].decode(errors='replace')}
 with lock:
  if usage+len(r.stdout)>256*1024**2:raise RuntimeError('Map budget exceeded')
  usage+=len(r.stdout)
 p.write_bytes(r.stdout);return {'tile':tile,'ok':True}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,r in enumerate(pool.map(fetch,sorted(tiles)),1):
  results.append(r)
  if i%50==0:print(i,'/',len(tiles),'bytes',usage,flush=True)
manifest={'source':'NRCan Toporama WMS','license':'Open Government Licence - Canada','date':'2026-09-25','regions':regions,'tiles':results,'bytes':usage,'appearance_difference':'NRCan Toporama replaces the original Google Maps basemap; visual equivalence not established'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
