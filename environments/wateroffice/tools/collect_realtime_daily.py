"""Archive official daily-mean products separately from the unit-value snapshot."""
import pathlib,json,gzip,subprocess,urllib.parse,concurrent.futures,datetime,time
R=pathlib.Path(__file__).resolve().parents[1];O=R/'data/realtime-daily';O.mkdir(exist_ok=True);A=R/'author/realtime-daily';A.mkdir(exist_ok=True)
ids=sorted({x['number'] for x in json.loads((R/'data/realtime-stations.json').read_text())['stations']});start='2026-09-18';end='2026-09-25';began=datetime.datetime.now(datetime.timezone.utc).isoformat()
membership=json.loads((R/'data/realtime-filter-membership.json').read_text())['filters']['parameter_type']
def run(n):
 p=O/(n+'.json.gz');meta=A/(n+'.json')
 if p.exists() and meta.exists():return json.loads(meta.read_text())
 codes=[c for c in ('3','6') if n in membership[c]['stations']]
 if not codes:return {'station':n,'unavailable_parameters':['3','6'],'observations':0,'bytes':0}
 q={'station':n,'start_date':start,'end_date':end,'param1':codes[0],'param2':codes[1] if len(codes)>1 else '-1'};url='https://wateroffice.ec.gc.ca/services/real_time_graph/json/inline?'+urllib.parse.urlencode(q)
 for attempt in range(3):
  try:
   b=subprocess.check_output(['curl','-fLsS','--compressed','--connect-timeout','10','--max-time','45',url],stderr=subprocess.PIPE);j=json.loads(b);assert set(j)==set(codes),str(j)[:100]
   for code,series in j.items():
    for k,rows in series.items():
     assert isinstance(rows,list)
     for r in rows:assert (len(r)>=7 or (len(r)==2 and r[1] is None)) and start<=r[0][:10]<=end
   with gzip.open(p,'wb') as dst:dst.write(b)
   record={'station':n,'url':url,'available_parameters':codes,'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observations':sum(len(j[k]['provisional'])+len(j[k]['final']) for k in j),'bytes':p.stat().st_size};meta.write_text(json.dumps(record,indent=2));return record
  except Exception as e:
   if attempt==2:return {'station':n,'error':str(e)[:300]}
   time.sleep(2)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,row in enumerate(pool.map(run,ids),1):
  results.append(row)
  if i%100==0:print(i,len(ids),'errors',sum('error' in x for x in results),flush=True)
errors=[x for x in results if 'error' in x];(A/'results.json').write_text(json.dumps(results,indent=2))
if errors:raise RuntimeError(str(errors[:5]))
(O/'manifest.json').write_text(json.dumps({'source':'Official Wateroffice real_time_graph daily-mean products 3 and 6','first_date':start,'last_date':end,'collection_started':min(r['acquired_at'] for r in results if 'acquired_at' in r),'station_acquisition':{r['station']:r.get('acquired_at') for r in results},'collection_finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stations':len(ids),'stations_without_daily_parameters':[r['station'] for r in results if r.get('unavailable_parameters')],'observations':sum(r['observations'] for r in results),'bytes':sum(r['bytes'] for r in results),'last_day':'Provisional partial-day daily means reflect each station acquisition time; they do not share the earlier unit-value snapshot cutoff.'},indent=2))
print('complete',len(ids),flush=True)
