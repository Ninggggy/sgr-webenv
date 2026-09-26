"""Wateroffice offline application. Serves only templates/static and read-only data."""
import calendar,csv,datetime,html,io,json,mimetypes,os,pathlib,re,sqlite3,secrets,time,threading,functools
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit,urlencode,unquote
from hydat import Hydat,month_evidence
import realtime_snapshot
import reference, report, realtime, mapview, downloads, stationlists, remarks, realtime_metadata, datums
from metadata import station_metadata
ROOT=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(os.environ.get('WATEROFFICE_DATA','/data'))
DB=Hydat(DATA/'Hydat.sqlite3')
VERSION='0.1.0'
SESSIONS={}
SESSION_LOCK=threading.RLock()
def esc(v):return html.escape('' if v is None else str(v),quote=True)
def template(name):
 s=(ROOT/'templates'/f'{name}.html').read_text()
 return s.replace('<section class="pagedetails container">','<p class="container small"><a href="/offline-coverage.html">Offline archive: data versions and coverage</a></p><section class="pagedetails container">')
def content_page(name,title,body):
 s=template(name)
 s=re.sub(r'(<h1\b[^>]*>).*?(</h1>)',lambda m:m[1]+esc(title)+m[2],s,count=1,flags=re.S)
 s=re.sub(r'(</h1></div>).*?(<section id="water-topics")',lambda m:m[1]+'\n<div class="container">'+body+'</div>\n'+m[2],s,count=1,flags=re.S)
 return s

def replace_body(table,body):
 out,n=re.subn(r'(<tbody\b[^>]*>).*?(</tbody>)',lambda m:m[1]+body+m[2],table,count=1,flags=re.S)
 if n!=1:raise ValueError('Source table body is missing')
 return out
@functools.lru_cache(maxsize=1)
def reference_metadata():
 return {r["Station Number"]:r["records"][0] for r in reversed(reference.load(DATA/"reference.json")) if r["Station Number"]}

def coords(value,latitude):
 if value is None:return ''
 v=abs(value);d=int(v);m=int((v-d)*60);sec=round(((v-d)*60-m)*60)
 if sec==60:sec=0;m+=1
 if m==60:m=0;d+=1
 return f'{d}&deg;{m:02d}\'{sec:02d}" '+(('N' if value>=0 else 'S') if latitude else ('E' if value>=0 else 'W'))

def results(q):
 rows=DB.search(q);source=template('historical-results-full')
 block=re.search(r'<form action="/search/relay_e.html".*?</form>',source,re.S)[0]
 out=[]
 with DB.connect() as db:
  for i,s in enumerate(rows,1):
   number=s['STATION_NUMBER'];ref=reference_metadata().get(number,{})
   spans=[]
   for param,table in [('Flow','DLY_FLOWS'),('Level','DLY_LEVELS')]:
    r=db.execute(f'SELECT MIN(YEAR),MAX(YEAR) FROM {table} WHERE STATION_NUMBER=?',(number,)).fetchone()
    if r[0] is not None:spans.append((param,r[0],r[1]))
   first=min(r[1] for r in spans);last=max(r[2] for r in spans);params=' and '.join(r[0] for r in spans)
   link='/report/data_availability_e.html?'+urlencode({'type':'historical','station':number,'parameter_type':params})
   vals=[f'<input type="checkbox" id="check{i}" name="check[]" value="{esc(number)},{i},{first},{last},{esc(params)}"/>',f'<label for="check{i}">{esc(s["STATION_NAME"])}</label>',f'{first}-{last}',esc(s['PROV_TERR_STATE_LOC']),esc(number),f'<a href="{esc(link)}">{esc(params)}</a>',esc(ref['Latitude'])+' N' if ref.get('Latitude') else coords(s['LATITUDE'],True),esc(ref['Longitude'])+' W' if ref.get('Longitude') else coords(s['LONGITUDE'],False),esc(format(float(ref.get('Gross Drainage Area (km2)') or s['DRAINAGE_AREA_GROSS']),',g') if ref.get('Gross Drainage Area (km2)') or s['DRAINAGE_AREA_GROSS'] is not None else '')]
   out.append('<tr>'+''.join(('<td data-order="'+esc(s['LATITUDE'] if j==6 else abs(s['LONGITUDE']) if j==7 else s['DRAINAGE_AREA_GROSS'])+'">' if j in (6,7,8) else '<td>')+v+'</td>' for j,v in enumerate(vals))+'</tr>')
 block=replace_body(block,''.join(out))
 return content_page('historical-results-full','Historical Hydrometric Data Search Results',f'<p>Found {len(rows)} stations that matched your search.</p>'+block)

def availability(q):
 number=q.get('station','');s=DB.station(number)
 source=template('availability');tables=re.findall(r'<table\b.*?</table>',source,re.S)
 body=f'<a class="btn btn-primary pull-right mrgn-bttm-sm" href="/report/historical_e.html?stn={esc(number)}">View Report</a><a class="btn btn-default pull-right mrgn-bttm-sm mrgn-rght-sm" href="/download/index_e.html?results_type=historical&amp;stn={esc(number)}">Download?</a><div class="clearfix"></div>'
 for param,tab in zip(['Flow','Level'],tables):
  ev=DB.availability(number,param)
  if not ev:continue
  index={(r['year'],r['month']):r for r in ev};out=[]
  for year in range(min(r['year'] for r in ev),max(r['year'] for r in ev)+1):
   cells=[]
   for month in range(1,13):
    e=index.get((year,month));state=e['published'] if e else '-'
    title='Published completeness differs from non-null daily observation count' if e and e['conflict'] else ''
    cells.append(f'<td title="{title}">{state}</td>')
   out.append(f'<tr><th>{year}</th>'+''.join(cells)+'</tr>')
  body+=f'<h2 class="text-center">{param} Data Availability</h2><div class="table-responsive">'+replace_body(tab,''.join(out))+'</div>'
 body+='<p>C: Complete month; P: Partial month; -: No data.</p>'
 return content_page('availability',f'Daily Discharge and Water Level Data Availability for {s["STATION_NAME"]} ({number})',body)

def reference_page(q):
 rows,previous,following=reference.display_page(DATA/'reference-display.json',q)
 source=template('reference');tab=re.search(r'<table\b.*?</table>',source,re.S)[0]
 body=re.sub(r'<table\b.*?</table>',lambda _:replace_body(tab,rows),source,count=1,flags=re.S)
 pager='<ul class="pager">'
 if previous is not None:pager+=f'<li class="previous"><a href="/station_metadata/reference_index_e.html?stnIndex={previous}" rel="prev">Previous</a></li>'
 if following is not None:pager+=f'<li class="next"><a href="/station_metadata/reference_index_e.html?stnIndex={following}" rel="next">Next</a></li>'
 return re.sub(r'<ul class="pager">.*?</ul>',lambda _:pager+'</ul>',body,flags=re.S)

def real_results(q):
 rows=realtime.stations(DATA,q);source=template('real-results-complete')
 form=re.search(r'<form action="/search/relay_e.html".*?</form>',source,re.S)[0];out=[]
 for i,r in enumerate(rows,1):
  number=esc(r['number']);vals=[f'<input type="checkbox" id="check{i}" name="check[]" value="{number},{i},,,"/>',f'<label for="check{i}">{esc(r["name"])}</label>',esc(r['province']),f'<a href="/report/real_time_e.html?stn={number}">{number}</a>',esc(r['recent_data']),esc(r['operation'])]
  out.append('<tr>'+''.join(('<td class="'+('icon-green' if r['recent_data']=='Yes' else 'icon-red')+' image-center">' if j==4 else '<td>')+v+'</td>' for j,v in enumerate(vals))+'</tr>')
 form=replace_body(form,''.join(out))
 return content_page('real-results-complete','Real-Time Hydrometric Data Search Results',f'<p>Found {len(rows)} stations that matched your search.</p>'+form)

def station_index_page(q):
 import string
 rows=reference.load(DATA/'reference.json');selected=reference.index(rows,q);kind=q.get('type','stationNumber');isname=kind=='stationName';term=q.get('stationLike','A' if isname else '01')
 source=template('station-index');tab=re.search(r'<table\b.*?</table>',source,re.S)[0]
 out=[]
 for number,name in selected:
  link=f'<a href="/station_metadata/reference_index_e.html?stnNum={esc(number)}">{esc(name if isname else number)}</a>'
  out.append('<tr><td>'+link+'</td><td>'+esc(number if isname else name)+'</td></tr>')
 tab=replace_body(tab,''.join(out))
 if not isname:tab=tab.replace('Station Name</th>','TEMP</th>').replace('Station Number</th>','Station Name</th>').replace('TEMP</th>','Station Number</th>').replace('alphabetic order by station name','order by station number')
 nav='<ul class="nav nav-pills mrgn-bttm-md"><li><a href="reference_index_e.html">Station Reference Index</a></li><li><a href="station_index_e.html?type=stationNumber&amp;stationLike=01">Station Number Index</a></li><li><a href="station_index_e.html?type=stationName&amp;stationLike=A">Station Name Index</a></li></ul>'
 letters=string.ascii_uppercase if isname else [f'{i:02d}' for i in range(1,12)]
 nav+='<ul class="nav nav-pills mrgn-bttm-md">'+''.join(f'<li'+(' class="active"' if letter==term else '')+f'><a class="btn btn-sm btn-default ui-link" href="?type={kind}&amp;stationLike={letter}">{letter}</a></li>' for letter in letters)+'</ul>'
 return content_page('station-index','Hydrometric Station '+('Name' if isname else 'Number')+' Index',nav+'<div class="table-responsive">'+tab+'</div>')

def report_selection(page,numbers,number,q,kind):
 if not 1<=len(numbers)<=50:raise ValueError('Select between 1 and 50 stations')
 page=report.select(page,'station',[(n,n) for n in numbers],number)
 page=re.sub(r'<select\b[^>]*id="station"[^>]*>',lambda m:re.sub(r'\sdisabled(?:="[^"]*")?','',m[0]),page)
 hidden='<input type="hidden" name="stations" value="'+esc(','.join(numbers))+'">'
 page=re.sub(r'(<form\b[^>]*action="/report/[^"?]+"[^>]*>)',lambda m:m[1]+hidden,page)
 def mode_link(m):
  target=urlsplit(html.unescape(m[1]));params={k:v[-1] for k,v in parse_qs(target.query).items()}
  if params.get('mode') not in ('Graph','Table'):return m[0]
  params={**q,'stn':number,'stations':','.join(numbers),'mode':params['mode']}
  return 'href="'+esc(target.path+'?'+urlencode(params))+'"'
 return re.sub(r'href="(/report/'+kind+r'_e.html\?[^"<>]+)"',mode_link,page)

class Handler(BaseHTTPRequestHandler):
 def session(self):
  cookies=SimpleCookie()
  try:cookies.load(self.headers.get('Cookie',''))
  except Exception:pass
  sid=cookies.get('wateroffice_session');sid=sid.value if sid else None
  with SESSION_LOCK:
   if sid not in SESSIONS:
    sid=secrets.token_urlsafe(24);SESSIONS[sid]={'stations':[],'selected':[],'accepted':False,'seen':time.time()}
    self.new_cookie='wateroffice_session='+sid+'; Path=/; HttpOnly; SameSite=Lax'
   SESSIONS[sid]['seen']=time.time()
   if len(SESSIONS)>1000:
    for key,value in list(SESSIONS.items()):
     if value['seen']<time.time()-86400:SESSIONS.pop(key,None)
   return SESSIONS[sid]
 def redirect(self,path):return self.send('',303,extra={'Location':path})
 def do_POST(self):
  size=int(self.headers.get('Content-Length','0'))
  if not 0<=size<=65536:return self.send('Request too large',413)
  q=parse_qs(self.rfile.read(size).decode());state=self.session()
  if self.path=='/my_station_list/watch_list_custom_e.html':
   valid={r['number'] for r in realtime.stations(DATA,{'search_type':'province','province':'all'})};numbers=q.get('id[]',[])
   if not numbers or len(numbers)>1000 or any(n not in valid for n in numbers):return self.send('Invalid watch-list selection',400)
   selected=list(dict.fromkeys(state.get('watch',[])+numbers))
   if len(selected)>50:return self.send('A Watch List supports at most 50 stations.',400)
   state['watch']=selected;return self.redirect('/my_station_list/watch_list_custom_e.html')
  if self.path in ('/my_station_list/quick_graph_list/create_e.html','/my_station_list/quick_graph_list/rename_e.html'):
   name=q.get('list_name',[''])[0].strip()
   if not name or len(name)>50:return self.send('Invalid list name',400)
   lists=state.setdefault('quick',{})
   if 'rename' in self.path:
    key=q.get('id',[''])[0]
    if key not in lists:return self.send('Unknown list',400)
    lists[key]['name']=name
   else:
    key='first' if not lists else secrets.token_hex(4);lists[key]={'name':name,'stations':{}}
   return self.redirect('/my_station_list/index_e.html')
  if self.path=='/my_station_list/quick_graph_list/destroy_e.html':
   lists=state.get('quick',{});key=q.get('id',[''])[0]
   if key not in lists or q.get('delete')!=['Yes']:return self.send('Invalid list deletion',400)
   lists.pop(key);return self.redirect('/my_station_list/quick_graph_list/configure_e.html')
  if self.path=='/my_station_list/quick_graph_list/update_e.html':
   item=state.get('quick',{}).get(q.get('id',[''])[0]);valid={r['number'] for r in realtime.stations(DATA,{'search_type':'province','province':'all'})};updates={}
   if item is None:return self.send('Unknown list',400)
   if 'rename' in q:
    name=q.get('list_name',[''])[0].strip()
    if not name or len(name)>50:return self.send('Invalid list name',400)
    item['name']=name;return self.redirect('/my_station_list/quick_graph_list/configure_e.html')
   for key,values in q.items():
    match=re.fullmatch(r'param\[([^]]+)\]\[\]',key)
    if match:
     if match[1] not in valid or any(v not in ('3','6','46','47') for v in values):return self.send('Invalid station or parameter.',400)
     updates[match[1]]=values
   if 'confirm' in q:
    if q['confirm']!=['Yes'] or any(n not in item['stations'] or any(v not in item['stations'][n] for v in values) for n,values in updates.items()):return self.send('Invalid parameter deletion',400)
    for n,values in updates.items():
     item['stations'][n]=[v for v in item['stations'][n] if v not in values]
     if not item['stations'][n]:item['stations'].pop(n)
   else:
    for n,values in updates.items():item['stations'][n]=list(dict.fromkeys(item['stations'].get(n,[])+values))
   return self.redirect('/my_station_list/quick_graph_list/edit_e.html?'+urlencode({'id':q.get('id',[''])[0]}))
  if self.path=='/search/create_station_list_e.html':
   name=q.get('saved_list',[''])[0];kind=q.get('list_type',['historical'])[0];numbers=q.get('stations[]',[])
   if not re.fullmatch(r'[A-Za-z0-9]{1,50}',name) or kind not in ('historical','real_time') or not 1<=len(numbers)<=50:return self.send('Invalid station list',400)
   valid={r['number'] for r in json.loads((DATA/'realtime-stations.json').read_text())['stations']}
   try:
    for n in numbers:
     if kind=='historical':DB.station(n)
     elif n not in valid:raise KeyError(n)
   except KeyError:return self.send('Unknown station',400)
   state.setdefault('saved_lists',{}).setdefault(kind,{})[name]=list(dict.fromkeys(numbers))
   return self.redirect('/search/'+kind+'_e.html')
  if self.path!='/disclaimer_e.html':return self.send('Method not allowed',405)
  if q.get('disclaimer_action')==['I Agree']:
   state['accepted']=True;return self.redirect(state.pop('return_to','/index_e.html'))
  return self.redirect('/index_e.html')
 def send(self,body,status=200,kind='text/html; charset=utf-8',extra=None):
  if isinstance(body,str):body=body.encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
  if getattr(self,'new_cookie',None):self.send_header('Set-Cookie',self.new_cookie)
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'")
  for k,v in (extra or {}).items():self.send_header(k,v)
  self.end_headers();self.wfile.write(body)
 def do_GET(self):
  try:
   self.new_cookie=None
   u=urlsplit(self.path);path=unquote(u.path);raw=parse_qs(u.query,keep_blank_values=True);q={k:v[-1] for k,v in raw.items()}
   if u.netloc or '\\' in path or '..' in path.split('/') or '\x00' in path:return self.send('Forbidden',403)
   if path=='/offline-coverage.html' and realtime_snapshot.is_official_csv(DATA):
    return self.send(content_page('home','Wateroffice offline environment','<p>Search stations, choose historical or realtime observations, and use the table, graph, map and download controls.</p><p>Station pages show observation dates, units and source quality fields. Saved lists and query parameters are retained in the browser session.</p>'))
   if path=='/offline-coverage.html':return self.send(content_page('home','Wateroffice offline environment','<p>Search stations, choose historical or realtime observations, and use the table, graph, map and download controls.</p><p>Station pages show observation dates, units and source quality fields. Saved lists and query parameters are retained in the browser session.</p>'))
   if path=='/health':return self.send(json.dumps({'version':VERSION,'historical_database':DB.path.is_file(),'release_ready':bool(realtime_snapshot.window(DATA).get('complete'))}),kind='application/json')
   if path.startswith(('/vendor/','/custom/','/js/','/images/','/data/pco-fetch/')):
    p=(ROOT/'static'/path.lstrip('/')).resolve()
    if not p.is_relative_to((ROOT/'static').resolve()) or not p.is_file():return self.send('Asset not archived',404)
    return self.send(p.read_bytes(),kind=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
   pages={'/':'home','/index_e.html':'home','/search/historical_e.html':'historical-search','/search/real_time_e.html':'real-search','/contactus/faq_e.html':'faq'}
   if path in pages:
    page=template(pages[path])
    if path in ('/search/historical_e.html','/search/real_time_e.html'):
     state=self.session();kind='historical' if 'historical' in path else 'real_time';saved=state.get('saved_lists',{}).get(kind,{})
     if saved:
      body='<summary><h2 class="h3">Saved List</h2></summary><ul class="saved-list mrgn-tp-sm mrgn-bttm-sm">'+''.join('<li><a href="/report/'+kind+'_e.html?'+esc(urlencode({'saved_list':name}))+'">'+esc(name)+'</a> <a class="pull-right" href="/search/delete_station_list_e.html?'+esc(urlencode({'saved_list':name,'list_type':kind}))+'">Delete</a></li>' for name in saved)+'</ul>'
      page=re.sub(r'(<details id="saved-list">).*?(</details>)',lambda m:m[1]+body+m[2],page,flags=re.S)
    return self.send(page)
   if re.fullmatch(r'/mainmenu/(?:real_time_data|historical_data|station_and_network_data|tools_and_downloads|partnerships|resources)_index_e.html',path):return self.send(template(path.rsplit('/',1)[-1].removesuffix('.html')))
   if path=='/station_metadata/reference_index_help_e.html':return self.send(template('reference_index_help_e'))
   if path=='/disclaimer_info_e.html':return self.send(template('disclaimer_info_e'))
   if path=='/news_e.html':return self.send(template('news_e'))
   if path=='/map/index_e.html':return self.send(mapview.render(template,q.get("type","historical")))
   if path=='/api/map-coverage':
    m=json.loads((DATA/'map/manifest.json').read_text());return self.send(json.dumps({'regions':m['regions']}),kind='application/json')
   if path=='/api/map-stations':return self.send(json.dumps(mapview.stations(DB,DATA,q.get('type','historical'))),kind='application/json')
   if re.fullmatch(r'/data/map/geojson/basin_(?:0[1-9]|1[01])_simplified.json',path):
    basin=path.split('basin_')[1][:2];p=DATA/'map/basins'/(basin+'.json.gz')
    if not p.is_file():return self.send('This official drainage-basin archive is not available locally; it is not an empty basin.',503)
    return self.send(p.read_bytes(),kind='application/json',extra={'Content-Encoding':'gzip'})
   if path.startswith('/map/tiles/'):
    if not re.fullmatch(r'/map/tiles/\d{1,2}/\d{1,5}/\d{1,5}\.png',path):return self.send('Invalid tile',400)
    p=DATA/'map'/path.removeprefix('/map/tiles/')
    if not p.is_file():return self.send('Map tile outside archived coverage',404)
    return self.send(p.read_bytes(),kind='image/png')
   if path=='/search/relay_e.html':
    selected=[v.split(',')[0] for v in raw.get('check[]',[])]
    if not selected or len(selected)>50 or any(not re.fullmatch(r'\d{2}(?:[A-Z]{2}\d{3}|[A-Z]{3}\d{2})',v) for v in selected):return self.send(content_page('historical-results-full','Station selection','<div class="alert alert-warning">Please select between 1 and 50 stations.</div>'),400)
    state=self.session();state['selected']=list(dict.fromkeys(selected));state['results_type']=q.get('results_type','historical')
    if state['results_type'] not in ('historical','real_time'):raise ValueError('Invalid result type')
    selection=urlencode({'stations':','.join(state['selected'])})
    if 'save_list' in q:
     return self.send(template('my-list-saved').replace('value="historical"','value="'+esc(state['results_type'])+'"'))
    if 'map_location' in q:return self.redirect('/map/index_e.html?'+urlencode({'type':state['results_type'],'station_number':','.join(selected)}))
    if 'download' in q:return self.redirect('/download/index_e.html?results_type='+state['results_type']+'&'+selection)
    return self.redirect('/report/'+('real_time' if state['results_type']=='real_time' else 'historical')+'_e.html?stn='+selected[0]+'&'+selection)
   if path=='/search/save_list_name_e.html':
    state=self.session()
    if 'disagree' in q:return self.redirect('/search/'+state.get('results_type','historical')+'_e.html')
    page=template('save-list-name');numbers=state['selected']
    page=re.sub(r'(<p>Selected Station Identifiers</p>\s*<ul>).*?(</ul>)',lambda m:m[1]+''.join('<li>'+esc(n)+'</li>' for n in numbers)+m[2],page,flags=re.S)
    page=re.sub(r'<input type="hidden" name="stations\[\]"[^>]*>',lambda _:''.join('<input type="hidden" name="stations[]" value="'+esc(n)+'"/>' for n in numbers),page,count=1)
    page=page.replace('value="historical"','value="'+esc(state.get('results_type','historical'))+'"')
    return self.send(page)
   if path=='/search/delete_station_list_e.html':
    state=self.session();kind=q.get('list_type','historical')
    if kind not in ('historical','real_time'):raise ValueError('Invalid list type')
    state.get('saved_lists',{}).get(kind,{}).pop(q.get('saved_list'),None)
    return self.redirect('/search/'+kind+'_e.html')
   if path=='/download/csv_help_e.html':return self.send(template('csv_help_e'))
   if path=='/download/report_e.html':
    state=self.session();numbers=q['stations'].split(',') if q.get('stations') else state['selected'] or ([state.get('report_query',{}).get('stn')] if state.get('report_query',{}).get('stn') else [])
    if not 1<=len(numbers)<=50:raise ValueError('Please select between 1 and 50 stations')
    if q.get('results_type',state.get('results_type'))=='real_time':
     b=downloads.realtime_zip(DATA,numbers,q.get('dt'),q.get('df','csv'),q.get('startDate'),q.get('endDate'))
     return self.send(b,kind='application/zip',extra={'Content-Disposition':'attachment; filename="realtime_snapshot.zip"'})
    product=q.get('dt','dd')
    b=downloads.daily_csv(DB,numbers,q.get('df','csv'),q.get('md','1')=='1') if product=='dd' else downloads.historical_csv(DB,numbers,product,q.get('df','csv'))
    return self.send(b,kind='text/csv; charset=utf-8',extra={'Content-Disposition':'attachment; filename="historical_'+product+'.csv"'})
   if path=='/download/index_e.html':
    state=self.session()
    if q.get('results_type') in ('historical','real_time'):state['results_type']=q['results_type']
    if q.get('stations'):state['selected']=q['stations'].split(',')
    elif q.get('stn'):state['selected']=[q['stn']]
    if not state['selected'] and state.get('report_query',{}).get('stn'):state['selected']=[state['report_query']['stn']]
    if not state['selected']:return self.send(content_page('download-selected','Hydrometric Data Download','<p>Please select at least one station.</p>'))
    page=template('realtime-download' if state.get('results_type')=='real_time' else 'download-selected')
    selection=urlencode({'stations':','.join(state['selected']),'results_type':state.get('results_type','historical'),**{k:q[k] for k in ('startDate','endDate') if q.get(k)}})
    page=re.sub(r'(/download/report_e.html\?[^"]+)',lambda m:m[1]+'&amp;'+esc(selection),page)
    return self.send(page)
   if path=='/my_station_list/index_e.html':return self.send(stationlists.home(DATA,self.session(),q,template))
   if path=='/my_station_list/watch_list_custom_e.html':return self.send(stationlists.watch(DATA,self.session(),q,raw,template))
   if path=='/my_station_list/quick_graph_list/new_e.html':return self.send(template('quick-list-new'))
   if path=='/my_station_list/quick_graph_list/configure_e.html':
    lists=self.session().get('quick',{});return self.send(report.select(template('quick-configure'),'list',[(k,v['name']) for k,v in lists.items()],q.get('id',next(iter(lists),''))))
   if path=='/my_station_list/quick_graph_list/relay_e.html':
    state=self.session();lists=state.setdefault('quick',{});key=q.get('id','')
    if key not in lists:raise ValueError('Unknown quick graph list')
    if 'delete' in q:return self.redirect('/my_station_list/quick_graph_list/delete_e.html?'+urlencode({'id':key}))
    if 'rename' in q:return self.redirect('/my_station_list/quick_graph_list/rename_e.html?'+urlencode({'id':key}))
    return self.redirect('/my_station_list/quick_graph_list/edit_e.html?'+urlencode({'id':key}))
   if path in ('/my_station_list/quick_graph_list/rename_e.html','/my_station_list/quick_graph_list/delete_e.html'):
    key=q.get('id','');item=self.session().get('quick',{}).get(key)
    if item is None:raise ValueError('Unknown quick graph list')
    name='quick-rename' if path.endswith('rename_e.html') else 'quick-delete'
    return self.send(template(name).replace('OfflineEvidence',esc(item['name'])).replace('value="first"','value="'+esc(key)+'"'))
   if path=='/my_station_list/quick_graph_list/edit_e.html':
    state=self.session();key=q.get('id','');item=state.get('quick',{}).get(key)
    if item is None:raise ValueError('Unknown quick graph list')
    if q.get('remove'):item['stations'].pop(q['remove'],None)
    page=template('quick-edit-nb' if q.get('search_type') else 'quick-edit').replace('OfflineEvidence',esc(item['name'])).replace('value="first"','value="'+esc(key)+'"')
    if item['stations']:
     page=page.replace('<p>Your list has no locations added; please add a location using the search function.</p>',stationlists.quick_existing(DATA,item,key,template))
    if q.get('search_type'):
     rows=[r for r in realtime.stations(DATA,q) if r['number'] not in item['stations']]
     matches=list(re.finditer(r'<tbody>.*?</tbody>',page,re.S));last=matches[-1]
     page=page[:last.start()]+'<tbody>'+stationlists.table_rows(rows,'station_number[]')+'</tbody>'+page[last.end():]
    if q.get('search_type'):
     for field in ('province','basin'):
      match=re.search(r'<select id="'+field+r'".*?</select>',page,re.S)
      if match:page=report.select(page,field,re.findall(r'<option value="([^"]+)"[^>]*>(.*?)</option>',match[0]),q.get(field,'all' if field=='province' else '01'))
     page=re.sub(r'<input type="radio"[^>]*name="search_type"[^>]*>',lambda m:re.sub(r'\schecked(?:="[^"]*")?','',m[0]).replace('>',' checked>' if 'value="'+q['search_type']+'"' in m[0] else '>'),page)
    return self.send(page)
   if path=='/my_station_list/quick_graph_list/update_e.html':
    key=q.get('id','');item=self.session().get('quick',{}).get(key)
    if item is None:raise ValueError('Unknown quick graph list')
    selected={}
    for name,values in raw.items():
     match=re.fullmatch(r'param\[([^]]+)\]\[\]',name)
     if match:
      n=match[1]
      if n not in item['stations'] or any(v not in item['stations'][n] for v in values):raise ValueError('Invalid selected parameter')
      selected[n]=values
    if 'remove' in q:return self.send(stationlists.quick_remove(DATA,key,selected,template))
    if 'edit' in q:return self.redirect('/my_station_list/quick_graph_list/parameters_e.html?'+urlencode(raw,doseq=True))
    raise ValueError('Choose Edit Parameters or Delete Parameters')
   if path=='/my_station_list/quick_graph_list/parameters_e.html':
    key=q.get('id','');state=self.session()
    if key not in state.get('quick',{}):raise ValueError('Unknown quick graph list')
    numbers=raw.get('station_number[]',[]);meta={r['number']:r for r in realtime.stations(DATA,{'search_type':'province','province':'all'})}
    if not numbers:numbers=[m[1] for k in raw if (m:=re.fullmatch(r'param\[([^]]+)\]\[\]',k))]
    if not 1<=len(numbers)<=50 or any(n not in meta for n in numbers):raise ValueError('Select 1 to 50 known stations')
    return self.send(stationlists.quick_parameters(DATA,state['quick'][key],key,numbers,template))
   if path=='/search/real_time_results_e.html':return self.send(real_results(q))
   if path=='/services/real_time_graph_axes/json/inline':return self.send(json.dumps(realtime.axes(q.get('station_id',''))),kind='application/json')
   if path=='/services/real_time_graph/json/inline':return self.send(json.dumps(realtime.graph(DATA,q)),kind='application/json')
   if path=='/report/remarks_e.html':return self.send(remarks.render(DB,q,template))
   if path=='/report/real_time_e.html':
    state=self.session()
    if not state['accepted']:
     state['return_to']=self.path;return self.send(template('real-report'))
    number=q.get('stn','');meta=next((r for r in json.loads((DATA/'realtime-stations.json').read_text())['stations'] if r['number']==number),None)
    if meta is None:return self.redirect('/report/historical_e.html?'+urlencode({'stn':number}))
    state['results_type']='real_time'
    if q.get('stations'):state['selected']=q['stations'].split(',')
    if number not in state['selected']:state['selected']=[number]
    default_start,default_end=realtime_snapshot.dates(DATA,number)
    start_date=q.get('startDate',str(default_start));end_date=q.get('endDate',str(default_end))
    realtime_snapshot.dates(DATA,number,start_date,end_date)
    table_mode=q.get('mode')=='Table'
    page=template('real-table' if table_mode else 'real-report-accepted').replace('01AF002',esc(number)).replace('SAINT JOHN RIVER AT GRAND FALLS',esc(meta['name']))
    parameters=list(dict.fromkeys(q.get(k,default) for k,default in [('prm1','46'),('prm2','47')]))
    if any(p not in ('3','6','46','47','-1') for p in parameters):raise ValueError('Invalid real-time parameter')
    parameters=[p for p in parameters if p!='-1']
    if not parameters:raise ValueError('Select at least one parameter')
    for key,default in [('prm1','46'),('prm2','47')]:
     ident='y1-type' if key=='prm1' else 'y2-type'
     options=[('46','Water level (unit values)'),('47','Discharge (unit values)'),('6','Discharge (daily mean values)'),('3','Water level (daily mean values)')]
     if key=='prm2':options.insert(0,('-1','(Second Parameter)'))
     page=report.select(page,ident,options,q.get(key,default))
    if table_mode:
     if realtime_snapshot.is_official_csv(DATA,number):
      series={p:{r[0]:r for r in realtime_snapshot.table_series(DATA,number,p,start_date,end_date)} for p in parameters}
     else:
      graph=realtime.graph(DATA,{'station':number,'start_date':start_date,'end_date':end_date,'param1':q.get('prm1','46'),'param2':q.get('prm2','47')})
      series={p:{r[0]:r for k in ('final','provisional') for r in graph[p][k]} for p in parameters}
     rows=[]
     for timestamp in sorted({t for values in series.values() for t in values}):
      if all(values.get(timestamp,[None,None])[1] is None for values in series.values()):continue
      cells=[esc(timestamp).replace(' ','&nbsp;')]
      for code in parameters:
       a=series[code].get(timestamp)
       value='' if a is None or a[1] is None else downloads.value_text(a[1],'Level' if code in ('3','46') else 'Flow')
       if value:
        integer,dot,fraction=value.partition('.')
        value=format(int(integer),',')+(dot+fraction if dot else '')
       cells.append(esc(value))
       if code in ('46','47'):cells.extend([esc(realtime_snapshot.approval_label(a[2])) if a else '',esc(a[4]) if a else '',esc(a[6]) if a else ''])
      rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in cells)+'</tr>')
     page=replace_body(page,''.join(rows))
     # Numeric sorting applies only to the selected value columns. Status
     # columns are text, and a single daily parameter has only two columns.
     numeric_columns=[]; column=1
     for code in parameters:
      numeric_columns.append(column); column+=4 if code in ('46','47') else 1
     page=page.replace('"targets": [1, 2]', '"targets": '+json.dumps(numeric_columns),1)
     heading='<tr><th scope="col">Date (AST)</th>'
     for code in parameters:
      heading+='<th scope="col">'+realtime.label(code)+(' (m)' if code in ('3','46') else ' (m³/s)')+'</th>'
      if code in ('46','47'):heading+='<th scope="col">Approval</th><th scope="col">Grade</th><th scope="col">Qualifiers</th>'
     page=re.sub(r'<thead>.*?</thead>',lambda _:'<thead>'+heading+'</tr></thead>',page,count=1,flags=re.S)
     if not realtime_snapshot.is_official_csv(DATA,number) and any(p in ('46','47') for p in parameters):page=page.replace('</caption>',' Approval flags are not supplied by the archived GeoMet source.</caption>',1)
     if not rows:
      page=re.sub(r'<table\b[^>]*class="[^"]*wb-tables[^"]*".*?</table>','<p>No data available for the selected time period.</p>',page,count=1,flags=re.S)

    page=page.replace('[NB]','['+esc(meta['province'])+']')
    coverage=realtime_snapshot.window(DATA,number)
    note=('30-day official CSV snapshot; quality fields retained.' if realtime_snapshot.is_official_csv(DATA,number) else '7-day GeoMet snapshot; unit-value Approval and Grade unavailable.')
    if 'covered_stations' in realtime_snapshot.window(DATA):page=page.replace('</h1>','</h1><p class="small">'+note+' <a href="/offline-coverage.html">Data coverage</a></p>',1)
    mapmeta=next((r for r in json.loads((DATA/'map-stations-real_time.json').read_text()) if r['station_id']==number),{})
    timezone=mapmeta.get('timezone_abbr_en','Local standard time')
    timezone_name=realtime_snapshot.TIMEZONE_NAMES.get(timezone,'Local standard time')
    page=page.replace('Atlantic Standard Time (AST)',esc(timezone_name+' ('+timezone+')')).replace('>AST<','>'+esc(timezone)+'<').replace('Date (AST)','Date (<abbr title="'+esc(timezone_name)+'">'+esc(timezone)+'</abbr>)')
    if (DATA/'realtime-metadata/manifest.json').exists():
     source=realtime_metadata.catalog(DATA)[number];values={k:realtime_metadata.render_field(v) for k,v in source['fields'].items()};history=[]
     if source.get('history_html'):
      body=re.search(r'<tbody>(.*?)</tbody>',source['history_html'],re.S)[1]
      for row in re.findall(r'<tr>(.*?)</tr>',body,re.S):history.append([html.unescape(re.sub('<[^>]*>','',v)).strip() for v in re.findall(r'<td[^>]*>(.*?)</td>',row,re.S)])
    else:
     try:values,history=station_metadata(DB,DB.station(number))
     except KeyError:values,history={},[]
     values={k:esc(v) for k,v in values.items()}
    page=re.sub(r'(<div aria-labelledby="([^"]+)"[^>]*>).*?(</div>)',lambda m:m[1]+values.get(m[2],'Not included in this archive')+m[3],page,flags=re.S)
    def history_table(m):
     if 'Operation schedule' not in m[0]:return m[0]
     body='<tbody>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in history)+'</tbody>'
     return re.sub(r'<tbody>.*?</tbody>',lambda _:body,m[0],flags=re.S)
    page=re.sub(r'<table\b.*?</table>',history_table,page,flags=re.S)
    # Field-visit measurements/rating shifts in the source template are station-specific.
    page=re.sub(r'<p>The most recent .*?(?=<section>)','<p>Observations shown are the dated offline snapshot. Field-visit measurements and rating-shift commentary are not part of this archive.</p>',page,flags=re.S)
    for id,value in [('start-date',q.get('startDate',str(default_start))),('end-date',q.get('endDate',str(default_end)))]:
     datetime.date.fromisoformat(value)
     page=re.sub(r'(<input[^>]*id="'+id+r'"[^>]*value=")[^"]*',lambda m:m[1]+esc(value),page)
     lo,hi=realtime_snapshot.bounds(DATA,number)
     page=re.sub(r'<input\b[^>]*id="'+id+r'"[^>]*>',lambda m:re.sub(r'\s(?:min|max)="[^"]*"','',m[0])[:-1]+' min="'+str(lo.date())+'" max="'+str(hi.date())+'">',page)
    for key,ident in [('y1Max','y1-max'),('y1Min','y1-min'),('y2Max','y2-max'),('y2Min','y2-min')]:
     if q.get(key):
      import math
      if not math.isfinite(float(q[key])):raise ValueError('Invalid graph axis limit')
      page=re.sub(r'<input\b[^>]*id="'+ident+r'"[^>]*>',lambda m:m[0][:-1]+' value="'+esc(q[key])+'">',page)
    if not table_mode:page=page.replace('</body>','<script src="/js/offline-real-state.js"></script></body>')
    state['report_query']=q.copy()

    page=page.replace('/download/index_e.html?results_type=real_time','/download/index_e.html?'+esc(urlencode({'results_type':'real_time','stations':','.join(state['selected']),**{k:q[k] for k in ('startDate','endDate') if q.get(k)}})))
    page=report_selection(page,state['selected'],number,q,'real_time')
    return self.send(page)
   if path=='/services/historical_graph/json/inline':return self.send(json.dumps(report.graph(DB,q)),kind='application/json')
   if path=='/report/historical_e.html':
    state=self.session()
    if not state['accepted']:
     state['return_to']=self.path;return self.send(template('historical-report'))
    if q.get('saved_list'):
     state['selected']=state.get('saved_lists',{}).get('historical',{}).get(q['saved_list'],[])
     if not state['selected']:raise ValueError('Saved list not found in this session')
     q.setdefault('stn',state['selected'][0])
    state['results_type']='historical'
    if q.get('stations'):state['selected']=q['stations'].split(',')
    if q.get('stn') not in state['selected']:state['selected']=[q.get('stn')]
    state['report_query']=q.copy()
    page=report.render(DB,q,template)
    if page:
     page=page.replace('/download/index_e.html?results_type=historical','/download/index_e.html?'+esc(urlencode({'results_type':'historical','stations':','.join(state['selected'])})))
    if page and q.get('stn') in state['selected']:
     page=report_selection(page,state['selected'],q['stn'],q,'historical')
    return self.send(page if page else content_page('availability','Historical Hydrometric Data','<p>No data available for the selected parameter.</p>'))
   if path in ('/report/datum_e.html','/report/datum_faq_e.html'):return self.send(datums.render(DATA,q,template,faq=path.endswith('datum_faq_e.html')))
   if path=='/station_metadata/station_index_e.html':return self.send(station_index_page(q))
   if path=='/station_metadata/reference_index_download_e.html':return self.send((DATA/'reference-index.csv').read_bytes(),kind='text/csv; charset=utf-8',extra={'Content-Disposition':'attachment; filename=station_reference_index.csv'})
   if path=='/station_metadata/reference_index_e.html':return self.send(reference_page(q))
   if path=='/search/historical_results_e.html':return self.send(results(q))
   if path=='/report/data_availability_e.html':return self.send(availability(q))
   return self.send('This page has not yet passed offline implementation and validation. This is not an empty query result.',503)
  except (ValueError,KeyError) as e:self.send(content_page('home','Query could not be completed','<div class="alert alert-warning">'+esc(str(e))+'</div><p><a href="/offline-coverage.html">Offline archive coverage</a></p>'),400)
  except (OSError,sqlite3.Error) as e:
   self.log_error('%s',e);self.send('Archived data is unavailable. This is not an empty query result.',503)
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
