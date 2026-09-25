"""Resumable author-only seven-day national snapshot, one complete station at a time."""
import concurrent.futures,csv,datetime,gzip,io,json,pathlib,subprocess,time,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'author/realtime-api';OUT.mkdir(exist_ok=True)
start='2026-09-18T09:40:00Z';end='2026-09-25T09:40:00Z'
ids=sorted({r['number'] for r in json.loads((ROOT/'data/realtime-stations.json').read_text())['stations']})
(OUT/'window.json').write_text(json.dumps({'from':start,'to':end,'station_count':len(ids),'source':'MSC GeoMet hydrometric-realtime'},indent=2)+'\n')
def get(number):
 p=OUT/(number+'.csv.gz');meta=OUT/(number+'.json')
 if p.exists() and meta.exists():return json.loads(meta.read_text())
 rows=[];offset=0;header=None;sources=[]
 while True:
  url='https://api.weather.gc.ca/collections/hydrometric-realtime/items?'+urllib.parse.urlencode({'f':'csv','STATION_NUMBER':number,'datetime':start+'/'+end,'limit':10000,'offset':offset})
  for attempt in range(3):
   r=subprocess.run(['curl','-fLsS','--compressed','--connect-timeout','15','--max-time','90',url],capture_output=True)
   if r.returncode==0:break
   time.sleep(2)
  if r.returncode:raise RuntimeError(number+': '+r.stderr.decode()[:200])
  parsed=list(csv.reader(io.StringIO(r.stdout.decode('utf-8-sig'))))
  if not parsed or 'STATION_NUMBER' not in parsed[0]:raise ValueError('Unexpected API response '+number)
  if header is None:header=parsed[0]
  assert header==parsed[0]
  sources.append(url);rows.extend(parsed[1:])
  if len(parsed)-1<10000:break
  offset+=10000
  if offset>100000:raise ValueError('Unexpected seven-day observation count')
 idx=header.index('IDENTIFIER');keys=[row[idx] for row in rows]
 assert len(keys)==len(set(keys)),f'Duplicate observations: {number}'
 sn=header.index('STATION_NUMBER');dt=header.index('DATETIME')
 assert all(row[sn]==number and start<=row[dt]<=end for row in rows)
 with gzip.open(p,'wt',newline='') as f:w=csv.writer(f);w.writerow(header);w.writerows(rows)
 result={'station':number,'rows':len(rows),'sources':sources,'fetched':datetime.datetime.now(datetime.timezone.utc).isoformat(),'complete':True}
 meta.write_text(json.dumps(result,indent=2)+'\n');return result
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 tasks={pool.submit(get,n):n for n in ids};completed=0
 for f in concurrent.futures.as_completed(tasks):
  try:r=f.result();completed+=1
  except Exception as e:r={'station':tasks[f],'error':str(e)}
  with (OUT/'progress.jsonl').open('a') as out:out.write(json.dumps(r)+'\n')
  if completed%25==0 or 'error' in r:print(completed,'/',len(ids),r.get('error',''),flush=True)
