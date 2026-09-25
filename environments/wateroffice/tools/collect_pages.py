"""Author-side official page/asset capture; never installed in the serving image."""
import pathlib,subprocess,json,re,concurrent.futures,datetime,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]; BASE='https://wateroffice.ec.gc.ca'
PAGES={
'home':'/index_e.html','historical-search':'/search/historical_e.html','real-search':'/search/real_time_e.html',
'historical-results':'/search/historical_results_e.html?search_type=station_name&station_name=BULKLEY',
'real-results':'/search/real_time_results_e.html?search_type=province&province=all',
'availability':'/report/data_availability_e.html?station=08EE004&parameter_type=Flow%20and%20Level&type=historical',
'historical-report':'/report/historical_e.html?stn=08EE004','real-report':'/report/real_time_e.html?stn=01AF002',
'reference':'/station_metadata/reference_index_e.html?stnNum=08EE004',
'station-index':'/station_metadata/station_index_e.html?type=stationName&stationLike=B',
'map':'/map/index_e.html?type=historical','my-list':'/my_station_list/index_e.html','faq':'/contactus/faq_e.html'}
def get(url,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 r=subprocess.run(['curl','-fLsS','--connect-timeout','10','--max-time','60',url,'-o',str(p)],capture_output=True)
 return {'url':url,'file':str(p.relative_to(ROOT)),'ok':r.returncode==0,'error':r.stderr.decode()[:300],'captured':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 records=list(pool.map(lambda kv:get(BASE+kv[1],ROOT/'author/pages'/f'{kv[0]}.html'),PAGES.items()))
assets=set()
for p in (ROOT/'author/pages').glob('*.html'):
 r={'url':BASE+'/', 'file':str(p.relative_to(ROOT))}
 if p.stat().st_size:
  s=p.read_text(errors='replace')
  assets.update(urllib.parse.urljoin(r['url'],x) for x in re.findall(r'(?:src|href)=["\']([^"\']+)["\']',s) if re.search(r'\.(?:css|js|svg|png|jpg|ico)(?:\?|$)',x))
seen=set()
for depth in range(4):
 urls=sorted(u for u in assets-seen if urllib.parse.urlparse(u).hostname=='wateroffice.ec.gc.ca');seen.update(urls)
 if not urls:break
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  new=list(pool.map(lambda u:get(u,ROOT/'app/static'/urllib.parse.urlparse(u).path.lstrip('/')),urls))
 records.extend(new)
 for r in new:
  if r['ok'] and '.css' in r['file']:
   s=(ROOT/r['file']).read_text(errors='replace')
   assets.update(urllib.parse.urljoin(r['url'],x.strip('"\'')) for x in re.findall(r'url\(([^)]+)\)',s) if not x.startswith('data:'))
(ROOT/'author/page-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({'ok':sum(r['ok'] for r in records),'failed':[r for r in records if not r['ok']]},indent=2))
