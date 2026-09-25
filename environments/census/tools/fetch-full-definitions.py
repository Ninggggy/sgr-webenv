import concurrent.futures,datetime,json,pathlib,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def job(y,p):
 f=R/f'sources/api/{y}/{p}/variables.json';url=f'https://api.census.gov/data/{y}/acs/{p}/variables.json';side=f.with_suffix('.json.source.json')
 if f.exists():return
 b=urllib.request.urlopen(url,timeout=50).read();d=json.loads(b);assert len(d['variables'])>10000
 tmp=f.with_suffix('.part');tmp.write_bytes(b);tmp.replace(f);now=datetime.datetime.now(datetime.timezone.utc).isoformat();side.write_text(json.dumps({'url':url,'retrieved_utc':now,'checked_utc':now,'bytes':len(b)},indent=2));print(y,p,len(d['variables']),flush=True)
with concurrent.futures.ThreadPoolExecutor(4) as pool:list(pool.map(lambda x:job(*x),[(y,p) for y in range(2016,2020) for p in ['acs1','acs5']]))
