#!/usr/bin/env python3
"""Stage official ACS data when an authorized API key is available. No automatic deployment."""
import argparse,datetime,json,os,re,time,urllib.parse,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--year',type=int,choices=range(2016,2020),required=True);p.add_argument('--product',choices=['acs5','acs1'],required=True);p.add_argument('--table',required=True);p.add_argument('--state',required=True);a=p.parse_args()
if not re.fullmatch(r'[BC]\d+[A-Z]?',a.table) or not re.fullmatch(r'\d{2}',a.state):p.error('Invalid table or state code')
key=os.environ.get('CENSUS_API_KEY')
if not key:raise SystemExit('Set CENSUS_API_KEY in this author process. Never put it in Compose, a build argument, or a browser request.')
root=Path(__file__).resolve().parents[1];folder=root/f'sources/api-data/{a.year}/{a.product}/{a.table}';folder.mkdir(parents=True,exist_ok=True)
for level in ['state','county']:
 params={'get':f'NAME,group({a.table})','for':f'state:{a.state}' if level=='state' else 'county:*'}
 if level=='county':params['in']='state:'+a.state
 public=f'https://api.census.gov/data/{a.year}/acs/{a.product}?'+urllib.parse.urlencode(params);secret_url=public+'&'+urllib.parse.urlencode({'key':key});path=folder/f'{a.state}-{level}.json';side=path.with_suffix('.source.json')
 def validate(b):
  d=json.loads(b)
  if not isinstance(d,list) or len(d)<2 or not isinstance(d[0],list) or 'state' not in d[0] or f'{a.table}_001E' not in d[0]:raise ValueError('Invalid API data structure or unavailable geography')
  ix=d[0].index('state')
  if any(len(r)!=len(d[0]) or r[ix]!=a.state for r in d[1:]):raise ValueError('Incomplete row or unexpected state')
  if level=='county' and 'county' not in d[0]:raise ValueError('Missing county identifier')
  return d
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
 if path.exists():
  validate(path.read_bytes());meta=json.loads(side.read_text())
  if meta['url']!=public:raise ValueError('Source release mismatch')
  meta['checked_utc']=now();side.write_text(json.dumps(meta,indent=2));print(path,'cache verified');continue
 for attempt in range(3):
  try:
   with urllib.request.urlopen(secret_url,timeout=40) as r:b=r.read(100000001)
   if len(b)>100000000:raise ValueError('Response too large for one staging batch')
   d=validate(b);break
  except Exception as e:
   if attempt==2:
    side.write_text(json.dumps({'url':public,'checked_utc':now(),'error':type(e).__name__+': data download or validation failed'},indent=2));raise SystemExit('Official data download failed; failure recorded without credentials.')
   time.sleep(attempt+1)
 tmp=path.with_suffix('.part');tmp.write_bytes(b);tmp.replace(path);side.write_text(json.dumps({'url':public,'retrieved_utc':now(),'checked_utc':now(),'rows':len(d)-1,'bytes':len(b),'deployment':'staged only; compare and import in an independent database before use'},indent=2));print(path,len(d)-1,'rows staged')
