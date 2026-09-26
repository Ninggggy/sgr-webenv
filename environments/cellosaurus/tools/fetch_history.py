import urllib.request,gzip,json,datetime
from pathlib import Path
p=Path(__file__).resolve().parents[1];out={}
import shutil
assert shutil.disk_usage(p).free > 5*1024**3+2*1024**2, 'Keep 5 GiB free'
for v,record in [(53,'16878225'),(54,'18418061')]:
 url=f'https://zenodo.org/records/{record}/files/cellosaurus_name_conflicts.txt?download=1'
 b=urllib.request.urlopen(url,timeout=90).read();assert f'Version: {v}.0'.encode() in b[:2000],b[:200]
 dst=p/f'data/history/{v}/cellosaurus_name_conflicts.txt.gz';dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(gzip.compress(b))
 out[str(v)]={'source_url':url,'record_url':f'https://zenodo.org/records/{record}','release':f'{v}.0','raw_bytes':len(b),'compressed_bytes':dst.stat().st_size,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'complete':True}
 print(out[str(v)],flush=True)
(p/'data/history/sources.json').write_text(json.dumps(out,indent=2))
