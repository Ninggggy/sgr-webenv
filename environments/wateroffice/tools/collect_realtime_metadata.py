"""Archive public station metadata for the complete real-time station list."""
import pathlib,json,gzip,re,html,subprocess,concurrent.futures,datetime,time
R=pathlib.Path(__file__).resolve().parents[1];A=R/'author/realtime-metadata';A.mkdir(exist_ok=True);O=R/'data/realtime-metadata';O.mkdir(exist_ok=True)
jar=A/'cookies.txt'
def curl(url,extra=()):return subprocess.check_output(['curl','-fLsS','--compressed','--connect-timeout','10','--max-time','45','-b',str(jar),*extra,url],stderr=subprocess.PIPE)
curl('https://wateroffice.ec.gc.ca/report/real_time_e.html?stn=08EE004',('-c',str(jar)))
curl('https://wateroffice.ec.gc.ca/disclaimer_e.html',('-c',str(jar),'--data-urlencode','disclaimer_action=I Agree'))
ids=sorted({x['number'] for x in json.loads((R/'data/realtime-stations.json').read_text())['stations']})
def run(n):
 p=O/(n+'.json')
 if p.exists():return json.loads(p.read_text())
 url='https://wateroffice.ec.gc.ca/report/real_time_e.html?stn='+n+'&mode=Graph'
 for attempt in range(3):
  try:
   b=curl(url);s=b.decode();fields=dict(re.findall(r'<div aria-labelledby="([^"]+)"[^>]*>(.*?)</div>',s,re.S))
   assert all(k in fields for k in ('latitude','longitude','gross-drainage','effective-drainage')),n
   assert re.search(r'id="station-id"\s+value="'+re.escape(n)+r'"',s),n
   texts={k:html.unescape(re.sub('<[^>]*>','',v)).strip() for k,v in fields.items()}
   history=next((t for t in re.findall(r'<table\b.*?</table>',s,re.S) if 'Operation schedule' in t),None)
   row={'station':n,'source':url,'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fields':fields,'text':texts,'history_html':history}
   with gzip.open(A/(n+'.html.gz'),'wb') as f:f.write(b)
   p.write_text(json.dumps(row,ensure_ascii=False));return row
  except Exception as e:
   if attempt==2:return {'station':n,'error':str(e)}
   time.sleep(2)
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,r in enumerate(pool.map(run,ids),1):
  rows.append(r)
  if i%100==0:print(i,len(ids),'errors',sum('error' in x for x in rows),flush=True)
(A/'results.json').write_text(json.dumps([{'station':r['station'],'error':r.get('error')} for r in rows],indent=2))
assert not any('error' in r for r in rows),[r for r in rows if 'error' in r][:5]
(O/'manifest.json').write_text(json.dumps({'source':'Official real-time report station-information fields','stations':len(ids),'first_acquired':min(r['acquired_at'] for r in rows),'last_acquired':max(r['acquired_at'] for r in rows)},indent=2))
print('complete',len(rows),flush=True)
