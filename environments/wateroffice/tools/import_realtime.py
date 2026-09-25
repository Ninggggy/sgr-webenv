import pathlib,json,csv,gzip,datetime,math,os
ROOT=pathlib.Path(__file__).resolve().parents[1];SRC=ROOT/'author/realtime-api';OUT=ROOT/'data/realtime';OUT.mkdir(parents=True,exist_ok=True)
ids={r['number'] for r in json.loads((ROOT/'data/realtime-stations.json').read_text())['stations']};window=json.loads((SRC/'window.json').read_text())
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
start,end=dt(window['from']),dt(window['to']);total=0;empty=[];failures=[]
for n in sorted(ids):
 try:
  meta=json.loads((SRC/(n+'.json')).read_text());assert meta['complete'] is True
  with gzip.open(SRC/(n+'.csv.gz'),'rt') as f:rows=list(csv.DictReader(f))
  assert len(rows)==meta['rows'];keys=set()
  for row in rows:
   assert row['STATION_NUMBER']==n and start<=dt(row['DATETIME'])<=end
   assert row['IDENTIFIER'] not in keys;keys.add(row['IDENTIFIER'])
   for k in ('LEVEL','DISCHARGE'):
    if row[k]!='':assert math.isfinite(float(row[k]))
  total+=len(rows)
  if not rows:empty.append(n)
  for ext in ['.csv.gz','.json']:
   src=SRC/(n+ext);dest=OUT/(n+ext)
   if not dest.exists():os.link(src,dest)
 except Exception as e:failures.append({'station':n,'error':str(e)})
if failures:raise RuntimeError(json.dumps(failures))
(OUT/'window.json').write_text(json.dumps(window,indent=2)+'\n')
report={'stations':len(ids),'observations':total,'official_zero_observation_stations':empty,'window':window,'all_stations_accounted_for':True,'checks':['station id','unique observation id','fixed UTC interval','finite values','metadata count','gzip integrity']}
(ROOT/'author/realtime-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
