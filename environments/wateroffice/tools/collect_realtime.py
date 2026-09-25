"""Stream official province files to dated seven-day gzip CSV snapshots."""
import csv,datetime,gzip,json,pathlib,subprocess,concurrent.futures,io
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'author/realtime';OUT.mkdir(exist_ok=True)
now=datetime.datetime.now(datetime.timezone.utc);cutoff=now-datetime.timedelta(days=7)
rows=list(csv.DictReader((ROOT/'author/realtime-stations.csv').open(encoding='utf-8-sig')))
ids=[r['ID'] for r in rows]
assert len(ids)==len(set(ids)),'duplicate station in official list'
station_ids=set(ids)
def collect(prov):
 url=f'https://dd.weather.gc.ca/today/hydrometric/csv/{prov}/daily/{prov}_daily_hydrometric.csv'
 p=OUT/(prov+'.csv.gz'); temp=p.with_suffix('.partial')
 proc=subprocess.Popen(['curl','-fLsS','--compressed','--connect-timeout','15','--max-time','1200',url],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8-sig')
 reader=csv.reader(proc.stdout);header=next(reader);count=0;seen=set();lo=None;hi=None
 with gzip.open(temp,'wt',newline='') as f:
  writer=csv.writer(f);writer.writerow(header)
  for row in reader:
   if len(row)!=10:raise ValueError(f'invalid row {prov}')
   t=datetime.datetime.fromisoformat(row[1]);assert t.tzinfo
   if cutoff<=t<=now and row[0] in station_ids:
    writer.writerow(row);count+=1;seen.add(row[0]);lo=min(lo or t,t);hi=max(hi or t,t)
 error=proc.stderr.read();rc=proc.wait()
 if rc:raise RuntimeError(f'{prov}: curl {rc}: {error}')
 temp.replace(p)
 return {'province':prov,'source':url,'count':count,'stations':sorted(seen),'first':str(lo),'last':str(hi),'file':p.name}
manifest={'started':now.isoformat(),'from':cutoff.isoformat(),'station_count':len(ids),'parts':[],'failures':[]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 tasks={pool.submit(collect,p):p for p in sorted({r['Prov/Terr'] for r in rows})}
 for task in concurrent.futures.as_completed(tasks):
  try:manifest['parts'].append(task.result());print(tasks[task],'complete',flush=True)
  except Exception as e:manifest['failures'].append({'province':tasks[task],'error':str(e)});print(str(e),flush=True)
  (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
manifest['missing_observation_stations']=sorted(station_ids-{s for p in manifest['parts'] for s in p['stations']})
manifest['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
