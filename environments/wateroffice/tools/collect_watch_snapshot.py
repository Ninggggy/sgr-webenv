"""Capture official watch-list summaries in ordinary 50-station author sessions."""
import pathlib,json,gzip,subprocess,urllib.parse,concurrent.futures,datetime,re,html
R=pathlib.Path(__file__).resolve().parents[1];A=R/'author/watch-snapshot';A.mkdir(exist_ok=True);O=R/'data/watch-snapshot';O.mkdir(exist_ok=True)
ids=sorted({r['number'] for r in json.loads((R/'data/realtime-stations.json').read_text())['stations']});batches=[ids[i:i+50] for i in range(0,len(ids),50)]
def run(item):
 i,ids=item;output=O/f'{i:02}.json'
 if output.exists():return json.loads(output.read_text())
 jar=A/f'{i:02}.cookies'
 def get(path,data=None):
  cmd=['curl','-fLsS','--compressed','--connect-timeout','10','--max-time','45','--retry','2','-b',str(jar),'-c',str(jar)]
  if data:cmd+=['--data',urllib.parse.urlencode(data,doseq=True)]
  return subprocess.check_output(cmd+['https://wateroffice.ec.gc.ca'+path],stderr=subprocess.PIPE)
 archive=A/f'{i:02}.pages.json.gz'
 if archive.exists():
  with gzip.open(archive,'rt') as f:pages=json.load(f)
 else:
  get('/my_station_list/index_e.html');get('/disclaimer_e.html',{'disclaimer_action':'I Agree'});get('/my_station_list/index_e.html?agree=I+Agree');get('/my_station_list/watch_list_custom_e.html?search_type=province&province=all',{'add':'Add Stations','id[]':ids})
  pages=[]
  for page in range((len(ids)+4)//5):
   path='/my_station_list/index_e.html?watch_page='+str(page);b=get(path);pages.append({'source':path,'html':b.decode(),'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
  with gzip.open(archive,'wt') as f:json.dump(pages,f)
 s='\n'.join(p['html'] for p in pages);records={} 
 for chunk in s.split('<div class="watch-list panel panel-default">')[1:]:
  name=html.unescape(re.search(r'<h3[^>]*>(.*?)</h3>',chunk,re.S)[1]);n=re.search(r'\(([A-Z0-9]{7})\)$',name)[1]
  assert n in ids,(i,n)
  trends=[]
  for label in ('Last Month','Last Week','Last Day'):
   section=re.search(r'(?:<a href="([^"]+)">)?'+label+r':<br\s*/?>(.*?)</div>',chunk,re.S);assert section,(n,label)
   img=re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"',section[2])
   trends.append({'href':html.unescape(section[1]) if section[1] else None,'label':label,'image':img[1] if img else None,'text':html.unescape(img[2] if img else re.sub('<[^>]*>','',section[2])).strip()})
  current=re.search(r'>Current Value:</span><br\s*/?>(.*?)</div>',chunk,re.S)
  assert current,(n,'missing value');assert len(trends)==3,(n,trends)
  records[n]={'name':name,'trends':trends,'value':html.unescape(re.sub('<[^>]*>','',current[1])).strip()}
 assert set(records)==set(ids),(i,sorted(set(ids)-set(records)))
 result={'source':'https://wateroffice.ec.gc.ca/my_station_list/index_e.html','selected_stations':ids,'acquired_at':max(p['acquired_at'] for p in pages),'first_acquired':min(p['acquired_at'] for p in pages),'stations':records};output.write_text(json.dumps(result,ensure_ascii=False));return result
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for i,r in enumerate(pool.map(run,enumerate(batches)),1):rows.append(r);print(i,len(batches),flush=True)
(O/'manifest.json').write_text(json.dumps({'source':'Official Watch List summaries, archived independently from unit observations','stations':len(ids),'first_acquired':min(r.get('first_acquired',r['acquired_at']) for r in rows),'last_acquired':max(r['acquired_at'] for r in rows),'coverage':'Published month/week/day trend symbols and displayed value only; no additional monthly observation history is implied.'},indent=2))
