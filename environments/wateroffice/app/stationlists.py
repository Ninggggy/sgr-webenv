import html,json,re,functools
from urllib.parse import urlencode
import realtime
from report import select
from downloads import value_text

def esc(x):return html.escape(str(x),quote=True)
def body_replace(s,body):return re.sub(r'(<h1[^>]*>.*?</h1></div>).*?(<section id="water-topics")',lambda m:m[1]+'<div class="container">'+body+'</div>'+m[2],s,count=1,flags=re.S)
def table_rows(rows,name,province=False):
 out=[]
 for i,r in enumerate(rows):
  out.append('<tr><td><input type="checkbox" id="station-'+str(i)+'" name="'+name+'" value="'+esc(r['number'])+'"></td><td><label for="station-'+str(i)+'">'+esc(r['name'])+'</label></td><td>'+esc(r['number'])+'</td>'+('<td>'+esc(r['province'])+'</td>' if province else '')+'</tr>')
 return ''.join(out)
def watch(data,state,q,raw,load):
 allrows=json.loads((data/'realtime-stations.json').read_text())['stations'];ids=state.setdefault('watch',[])
 if 'remove' in q:state['watch']=ids=[x for x in ids if x not in raw.get('id[]',[])]
 page=load('watch-added' if ids else 'watch-list-new')
 if ids:
  page=re.sub(r'<tbody>.*?</tbody>',lambda _:'<tbody>'+table_rows([r for r in allrows if r['number'] in ids],'id[]',True)+'</tbody>',page,count=1,flags=re.S)
 if q.get('search_type'):
  rows=[r for r in realtime.stations(data,q) if r['number'] not in ids]
  source=load('watch-nb-full');form=re.search(r'<form role="form" action="/my_station_list/watch_list_custom_e.html".*?</form>',source,re.S)[0]
  form=re.sub(r'<tbody>.*?</tbody>',lambda _:'<tbody>'+table_rows(rows,'id[]')+'</tbody>',form,flags=re.S)
  page=page.replace('<section id="water-topics"','<div class="container"><h2>Available Stations</h2>'+form+'</div><section id="water-topics"',1)
  for key in ['province','basin']:page=select(page,key,[(r[0],r[1]) for r in re.findall(r'<option value="([^"]+)"[^>]*>(.*?)</option>',re.search(r'<select id="'+key+r'".*?</select>',page,re.S)[0])],q.get(key,'all'))
 return page

def home(data,state,q,load):
 page=load('my-list-created');meta={r['number']:r for r in json.loads((data/'realtime-stations.json').read_text())['stations']}
 lists=state.get('quick',{})
 if lists:
  current=q.get('id',next(iter(lists)));item=lists.get(current)
  if not item:raise ValueError('Unknown quick graph list')
  if q.get('days','7')!='7':raise ValueError('Only the archived seven-day snapshot is available')
  source=load('my-list-with-quick')
  form=re.search(r'<form role="form" action="/my_station_list/index_e.html".*?</form>',source,re.S)[0]
  form=select(form,'list-id',[(k,v['name']) for k,v in lists.items()],current)
  controls='<a class="btn btn-primary mrgn-bttm-md hidden-print" href="/my_station_list/quick_graph_list/configure_e.html">Edit Quick Graph List</a>'+form
  for n,params in item['stations'].items():
   combined='46' in params and '47' in params
   groups=([['46','47']] if combined else [])+[[code] for code in params if not (combined and code in ('46','47'))]
   for group in groups:
    controls+='<section class="mrgn-tp-lg graph"><h3 class="h5 mrgn-bttm-sm mrgn-tp-0">'+esc(meta[n]['name'])+' (<span data-stationid="'+esc(n)+'">'+esc(n)+'</span>)<br>'
    for i,code in enumerate(group):
     unit,title=('m','metre') if code in ('3','46') else ('m³/s','cubic metre per second')
     attrs=('class="axis y y1" data-parameterid="'+code+'"' if i==0 else 'class="combine axis y y2" data-combined="true" data-parameterid2="'+code+'"') if len(group)==2 else 'data-parameterid="'+code+'"'
     controls+='<span '+attrs+'><small>'+realtime.label(code)+' (<abbr title="'+title+'">'+unit+'</abbr>)</small></span>'
    controls+='</h3><a href="/report/real_time_e.html?'+esc(urlencode({'stn':n,'prm1':group[0],'prm2':group[1] if len(group)==2 else '-1','startDate':'2026-09-18','endDate':'2026-09-25'}))+'"><div class="quick-graph"></div></a></section>'
  scripts=''.join('<script src="/vendor/js/flot/'+name+'.js"></script>' for name in ['jquery.flot','jquery.flot.resize','jquery.flot.time'])+'<script src="/js/quick_graph.js"></script>'
  page=page.replace('</body>',scripts+'</body>')
  page=page.replace('<p>No quick graph list is available</p>',controls).replace('<a class="btn btn-primary" href="/my_station_list/quick_graph_list/new_e.html">Create New Quick Graph List</a>','')
 if state.get('watch'):
  ids=state['watch'];current=int(q.get('watch_page','0'));pages=(len(ids)+4)//5
  if not 0<=current<pages:raise ValueError('Invalid watch-list page')
  cards='<a class="btn btn-primary mrgn-bttm-md hidden-print" href="/my_station_list/watch_list_custom_e.html">Edit Watch List</a>'
  snapshot=watch_snapshot(data) if (data/'watch-snapshot/manifest.json').exists() else None
  if snapshot:cards+='<p class="small">Published Watch List summaries captured '+esc(snapshot['manifest']['first_acquired'])+' through '+esc(snapshot['manifest']['last_acquired'])+'. These summary timestamps are separate from the unit-value archive; the month-long observation graph is outside the seven-day archive.</p>'
  window=json.loads((data/'realtime/window.json').read_text());end=window['to'][:10]
  import datetime
  for n in ids[current*5:(current+1)*5]:
   summary=snapshot['stations'][n] if snapshot else None
   cards+='<div class="watch-list panel panel-default"><div class="panel-heading"><h3 class="panel-title">'+esc(meta[n]['name'])+' ('+esc(n)+')</h3></div><div class="panel-body"><div class="row">'
   for i,(label,days) in enumerate([('Last Month',31),('Last Week',7),('Last Day',1)]):
    start=str(datetime.date.fromisoformat(end)-datetime.timedelta(days=days));link='/report/real_time_e.html?'+urlencode({'stn':n,'startDate':start,'endDate':end,'prm1':'46','prm2':'-1'})
    if summary:
     trend=summary['trends'][i];link=trend['href'];display=('<img class="img-responsive center-block" src="'+esc(trend['image'])+'" alt="'+esc(trend['text'])+'" title="'+esc(trend['text'])+'">') if trend['image'] else '<p class="mrgn-bttm-0">'+esc(trend['text'])+'</p>'
    else:display='<span class="small">'+('Outside archive' if days>7 else 'Trend unavailable')+'</span>'
    inner=label+':<br>'+display
    if link:inner='<a href="'+esc(link)+'">'+inner+'</a>'
    cards+='<div class="col-md-3 col-sm-6 col-xs-12 padding-rght-0 mrgn-bttm-sm"><div class="text-center">'+inner+'</div></div>'
   if summary:value=summary['value']
   else:
    rows=realtime.observations(data,n);values=[r for r in rows if r['LEVEL']];last=values[-1] if values else None;value=value_text(float(last['LEVEL']),'Level')+'M' if last else 'N/A'
   cards+='<div class="col-md-3 col-sm-6 col-xs-12 padding-rght-0 text-center"><span class="less-mrgn-hor">Snapshot Value:</span><br>'+esc(value)+'</div></div></div></div>'
  if pages>1:cards+='<ul class="pagination pagination-sm mrgn-tp-0 mrgn-bttm-0">'+''.join('<li'+(' class="active"' if i==current else '')+'><a href="/my_station_list/index_e.html?'+esc(urlencode({**q,'watch_page':i}))+'">'+str(i+1)+'</a></li>' for i in range(pages))+'</ul>'
  page=page.replace('<p>No watch list is available</p>',cards).replace('<a class="btn btn-primary" href="/my_station_list/watch_list_custom_e.html">Create New Watch List</a>','')
 return page

@functools.lru_cache(maxsize=2)
def watch_snapshot(data):
 folder=data/'watch-snapshot';manifest=json.loads((folder/'manifest.json').read_text());stations={}
 for p in folder.glob('*.json'):
  if p.name!='manifest.json':stations.update(json.loads(p.read_text())['stations'])
 if len(stations)!=manifest['stations']:raise OSError('Incomplete Watch List snapshot')
 return {'manifest':manifest,'stations':stations}

def quick_parameters(data,item,key,numbers,load):
 meta={r['number']:r for r in realtime.stations(data,{'search_type':'province','province':'all'})}
 if not 1<=len(numbers)<=50 or any(n not in meta for n in numbers):raise ValueError('Select 1 to 50 known stations')
 s=load('quick-parameters');fields=[]
 for n in dict.fromkeys(numbers):
  fields.append('<fieldset><legend class="h2 mrgn-tp-md">'+esc(meta[n]['name'])+' ['+esc(meta[n]['province'])+'] '+esc(n)+'</legend>')
  for code in ('3','6','46','47'):
   fields.append('<div class="checkbox"><label><input type="checkbox" name="param['+esc(n)+'][]" value="'+code+'"'+(' disabled checked' if code in item['stations'].get(n,[]) else '')+'>'+esc(realtime.label(code))+'</label></div>')
  fields.append('</fieldset>')
 s=re.sub(r'<fieldset>.*?</fieldset>',lambda _:''.join(fields),s,count=1,flags=re.S)
 if all(set(('3','6','46','47')).issubset(item['stations'].get(n,[])) for n in numbers):s=re.sub(r'<input\b[^>]*name="add"[^>]*>','',s)
 return s.replace('value="first"','value="'+esc(key)+'"').replace('edit_e.html?id=first','edit_e.html?id='+esc(key))

def quick_existing(data,item,key,load):
 meta={r['number']:r for r in realtime.stations(data,{'search_type':'province','province':'all'})}
 s=load('quick-edit-filled');form=re.search(r'<form action="/my_station_list/quick_graph_list/update_e.html".*?</form>',s,re.S)[0];rows=[]
 for n,params in item['stations'].items():
  for code in params:
   ident='param'+n+code
   vals=['<input type="checkbox" id="'+ident+'" name="param['+esc(n)+'][]" value="'+esc(code)+'">','<label for="'+ident+'">'+esc(meta[n]['name'])+'</label>',esc(n),esc(meta[n]['province']),esc(realtime.label(code))]
   rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in vals)+'</tr>')
 form=re.sub(r'<tbody>.*?</tbody>',lambda _:'<tbody>'+''.join(rows)+'</tbody>',form,count=1,flags=re.S)
 return form.replace('value="first"','value="'+esc(key)+'"')

def quick_remove(data,key,selected,load):
 if not selected:raise ValueError('Select at least one parameter')
 meta={r['number']:r for r in realtime.stations(data,{'search_type':'province','province':'all'})}
 source=load('quick-remove');items=[];inputs=[]
 for n,values in selected.items():
  for code in values:
   items.append('<li>'+esc(meta[n]['name'])+' ['+esc(n)+'] '+esc(realtime.label(code))+'</li>')
   inputs.append('<input type="hidden" name="param['+esc(n)+'][]" value="'+esc(code)+'">')
 body='<p>Are you sure you want to remove</p><ul>'+''.join(items)+'</ul><p>from your list?</p>'
 body+='<form action="/my_station_list/quick_graph_list/update_e.html" method="post">'+''.join(inputs)+'<input type="hidden" name="id" value="'+esc(key)+'"><input type="submit" name="confirm" value="Yes" class="btn btn-primary mrgn-rght-sm"><a href="/my_station_list/quick_graph_list/edit_e.html?id='+esc(key)+'" class="btn btn-default">No</a></form>'
 return body_replace(source,body)
