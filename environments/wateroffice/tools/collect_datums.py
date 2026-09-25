"""Capture datum pages for the national HYDAT/realtime union, not task-selected sites."""
import pathlib,sqlite3,json,gzip,subprocess,re,concurrent.futures,datetime,time
R=pathlib.Path(__file__).resolve().parents[1];O=R/'data/datums';O.mkdir(exist_ok=True);A=R/'author/datums';A.mkdir(exist_ok=True)
with sqlite3.connect('file:'+str(R/'data/Hydat.sqlite3')+'?mode=ro',uri=True) as db:ids={r[0] for r in db.execute('select STATION_NUMBER from STATIONS')}
ids.update(r['number'] for r in json.loads((R/'data/realtime-stations.json').read_text())['stations'])
def run(n):
 p=O/(n+'.json');raw=A/(n+'.html.gz');url='https://wateroffice.ec.gc.ca/report/'+('datum_faq_e.html' if n=='faq' else 'datum_e.html?stn='+n+'&mode=Graph')
 if p.exists():return json.loads(p.read_text())
 for attempt in range(3):
  try:
   b=subprocess.check_output(['curl','-fLsS','--compressed','--connect-timeout','10','--max-time','40',url],stderr=subprocess.PIPE);s=b.decode()
   match=re.search(r'<h1\b[^>]*>(.*?)</h1></div>\s*(.*?)<section id="water-topics"',s,re.S)
   assert match and (n=='faq' or 'information for '+n in match[1]),n
   row={'station':n,'source':url,'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'title':match[1],'body':match[2]}
   with gzip.open(raw,'wb') as f:f.write(b)
   p.write_text(json.dumps(row,ensure_ascii=False));return row
  except Exception as e:
   if attempt==2:return {'station':n,'error':str(e)}
   time.sleep(1)
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for i,r in enumerate(pool.map(run,['faq']+sorted(ids)),1):
  rows.append(r)
  if i%200==0:print(i,len(ids)+1,'errors',sum('error' in x for x in rows),flush=True)
(A/'results.json').write_text(json.dumps([{'station':r['station'],'error':r.get('error')} for r in rows],indent=2))
assert not any('error' in r for r in rows),[r for r in rows if 'error' in r][:5]
(O/'manifest.json').write_text(json.dumps({'stations':len(ids),'source':'National HYDAT and realtime union; original published datum pages and FAQ','first_acquired':min(r['acquired_at'] for r in rows),'last_acquired':max(r['acquired_at'] for r in rows)},indent=2))
print('complete',len(ids),flush=True)
