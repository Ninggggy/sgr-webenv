import calendar,datetime,html,re
from downloads import value_text
from metadata import station_metadata
from graph_statistics import calculate
import extremes

def escape(v):return html.escape(str(v),quote=True)
def select(s,id,values,chosen):
 options=''.join(f'<option value="{escape(v)}"'+(' selected' if str(v)==str(chosen) else '')+f'>{escape(label)}</option>' for v,label in values)
 return re.sub(r'(<select\b[^>]*\bid="'+re.escape(id)+r'"[^>]*>).*?(</select>)',lambda m:m[1]+options+m[2],s,flags=re.S)
def field(s,name,value):
 return re.sub(r'(<input\b[^>]*\bname="'+re.escape(name)+r'"[^>]*\bvalue=")[^"]*(")',lambda m:m[1]+escape(value)+m[2],s)
def graph(db,q):
 parameter=q.get('parameter_type','flow').title()
 if parameter not in ('Flow','Level'):raise ValueError('Invalid parameter')
 if q.get('data_type') in ('annual_extremes','peak'):
  db.station(q.get('station',''));return extremes.graph(db,q['station'],parameter,q['data_type']=='peak')
 if q.get('data_type','daily') not in ('daily','monthly'):raise ValueError('This data type is not yet archived in the report workflow')
 number=q.get('station','');db.station(number)
 first=int(q['first_year']);last=int(q.get('last_year',first))
 if not 1850<=first<=last<=2100:raise ValueError('Invalid year range')
 if q.get('data_type')=='monthly':
  points=[[datetime.datetime(r['YEAR'],r['MONTH'],1,tzinfo=datetime.timezone.utc).timestamp()*1000,r['MONTHLY_MEAN']] for r in db.months(number,parameter,first,last)]
 else:
  points=[[datetime.datetime.fromisoformat(r['date']).replace(tzinfo=datetime.timezone.utc).timestamp()*1000,r['value']] for r in db.daily(number,parameter,f'{first}-01-01',f'{last}-12-31')]
 result={'provisional':points}
 requested=[target for source,target in [('maximum','maximum'),('minimum','minimum'),('mean','mean'),('median','median'),('upper','upper_quartile'),('lower','lower_quartile')] if q.get(source)=='1']
 if requested:
  start=int(q.get('start_year') or 1850);end=int(q.get('end_year') or 2026)
  if not 1850<=start<=end<=2100:raise ValueError('Invalid statistics period')
  result.update(calculate(db,number,parameter,q.get('data_type','daily'),last,start,end,requested))
 return result

def render(db,q,load):
 number=q.get('stn','');station=db.station(number)
 parameter=q.get('parameterType','Flow')
 if parameter not in ('Flow','Level'):raise ValueError('Invalid parameter')
 mode=q.get('mode','Graph');kind=q.get('dataType','Daily')
 if mode not in ('Graph','Table') or kind not in ('Daily','Monthly','Annual Extremes','Peak'):raise ValueError('This report mode is not yet included')
 months=db.months(number,parameter);years=sorted({r['YEAR'] for r in months})
 if not years:return None
 first=int(q.get('first_year',q.get('year',years[-1])));last=int(q.get('last_year',first))
 year=int(q.get('year',first))
 if last<first or not 1850<=first<=last<=2100:raise ValueError('Invalid year range')
 s=load(('annual-extremes' if kind=='Annual Extremes' else 'peak')+'-'+mode.lower()) if kind in ('Annual Extremes','Peak') else load('historical-report-accepted' if mode=='Graph' else ('historical-table' if kind=='Daily' else 'monthly-table'))
 s=s.replace('08EE004',escape(number)).replace('BULKLEY RIVER AT QUICK',escape(station['STATION_NAME']))
 s=re.sub(r'(?<=\[)BC(?=\])',escape(station['PROV_TERR_STATE_LOC']),s)
 s=s.replace('Daily Discharge',('Daily Discharge' if parameter=='Flow' else 'Daily Water Level'))
 if kind=='Monthly':s=s.replace('Daily Discharge','Monthly Discharge').replace('Daily Water Level','Monthly Water Level')
 s=select(s,'station',[(number,number)],number)
 s=select(s,'data-type',[('Daily','Daily'),('Monthly','Monthly'),('Annual Extremes','Annual Daily Extremes Data'),('Peak','Annual Instantaneous Extremes Data'),('Real-Time','Real-Time')],kind)
 s=select(s,'parameter-type',[('Flow','Flow'),('Level','Level')],parameter)
 for id,chosen in [('first-year',first),('last-year',last),('year',year)]:s=select(s,id,[(y,y) for y in sorted(set(years+[chosen]))],chosen)
 for key,value in [('first_year',first),('last_year',last),('year',year),('parameterType',parameter),('dataType',kind)]:
  s=field(s,key,value)
  s=re.sub(r'([?&](?:amp;)?'+key+r'=)[^&"<>]+',lambda m:m[1]+escape(value),s)
 for key in ('start_year','end_year'):
  if q.get(key):s=field(s,key,int(q[key]))
 for key in ('y1Max','y1Min','mean1','median1','upper1','lower1'):
  s=re.sub(r'<input\b[^>]*name="'+key+r'"[^>]*>',lambda m:re.sub(r'\schecked(?:="[^"]*")?','',m[0])[:-1]+(' checked>' if q.get(key)=='1' else '>'),s)
 if mode=='Table' and kind=='Daily':
  tab=re.search(r'<table\b.*?</table>',s,re.S)[0];records={(r['YEAR'],r['MONTH']):r for r in months};prefix=parameter.upper()
  cells=[]
  for day in range(1,32):
   row=f'<tr><th scope="row" class="text-center">{day}</th>'
   for month in range(1,13):
    r=records.get((year,month));value=None if not r or day>calendar.monthrange(year,month)[1] else r.get(f'{prefix}{day}')
    symbol='' if value is None else (r.get(f'{prefix}_SYMBOL{day}') or '')
    row+='<td>'+('-' if value is None else escape(value_text(value,parameter,r.get('PRECISION_CODE',8)))+'&#160;'+escape(symbol))+'</td>'
   cells.append(row+'</tr>')
  tab=re.sub(r'<tbody>.*?</tbody>','<tbody>'+''.join(cells)+'</tbody>',tab,count=1,flags=re.S)
  s=re.sub(r'<table\b.*?</table>',lambda _:tab,s,count=1,flags=re.S)
  summary=[]
  for label,key,factor in [('Mean','MONTHLY_MEAN',1),('Max','MAX',1),('Min','MIN',1)]+([('Total','MONTHLY_TOTAL',1),('Total <abbr title="Cubic decametre(s)">Dam<sup>3</sup></abbr>','MONTHLY_TOTAL',86.4)] if parameter=='Flow' else []):
   row='<tr><th scope="row" class="text-center">'+label+'</th>'
   for month in range(1,13):
    r=records.get((year,month),{});v=r.get(key)
    row+='<td>'+('-' if v is None else escape(format(float(value_text(v*factor,parameter,r.get('PRECISION_CODE',8))),',.0f') if key=='MONTHLY_TOTAL' else value_text(v*factor,parameter,r.get('PRECISION_CODE',8))))+'&#160;</td>'
   summary.append(row+'</tr>')
  s=re.sub(r'<tfoot>.*?</tfoot>','<tfoot>'+''.join(summary)+'</tfoot>',s,count=1,flags=re.S)
  with db.connect() as conn:
   annual=conn.execute('SELECT * FROM ANNUAL_STATISTICS WHERE STATION_NUMBER=? AND DATA_TYPE=? AND YEAR=?',(number,'Q' if parameter=='Flow' else 'H',year)).fetchone()
  def annual_table(match):
   table=match[0]
   if 'annual statistics of daily data' not in table:return table
   values=[]
   for key in ['MEAN','MAX','MIN']:
    value=annual[key] if annual else None
    cell='-' if value is None else value_text(value,parameter)
    if value is not None and key!='MEAN':
     cell+=' '+(annual[key+'_SYMBOL'] or '')+' on '+calendar.month_name[annual[key+'_MONTH']]+' '+str(annual[key+'_DAY'])
    values.append(cell)
   if parameter=='Flow':
    totals=[records.get((year,m),{}).get('MONTHLY_TOTAL') for m in range(1,13)]
    total=sum(totals) if all(v is not None for v in totals) else None
    values += ['-' if total is None else value_text(total*f,'Flow') for f in [1,86.4]]
   body='<tbody class="text-center"><tr>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr></tbody>'
   table=re.sub(r'<tbody\b[^>]*>.*?</tbody>',body,table,flags=re.S)
   if parameter=='Level':
    table=re.sub(r'<th[^>]*>Total Discharge.*?</th>','',table,flags=re.S)
    table=table.replace('Cubic metre(s) per second','Metres').replace('m<sup>3</sup>/s','m')
   return table
  s=re.sub(r'<table\b.*?</table>',annual_table,s,flags=re.S)
 if mode=='Table' and kind=='Monthly':
  with db.connect() as conn:
   annual={r['YEAR']:dict(r) for r in conn.execute('SELECT * FROM ANNUAL_STATISTICS WHERE STATION_NUMBER=? AND DATA_TYPE=?',(number,'Q' if parameter=='Flow' else 'H'))}
  records={(r['YEAR'],r['MONTH']):r for r in months};out=[]
  yearly_means={}
  for y in years:
   vs=[r['MONTHLY_MEAN'] for r in months if r['YEAR']==y and r['MONTHLY_MEAN'] is not None]
   if vs:yearly_means[y]=sum(vs)/len(vs)
  for y in range(min(years),max(years)+1):
   row=f'<tr><th scope="row">{y}</th>'
   for month in range(1,13):
    r=records.get((y,month),{});value=r.get('MONTHLY_MEAN')
    row+='<td>'+('-' if value is None else escape(value_text(value,parameter,r.get('PRECISION_CODE',8))))+'</td>'
   value=yearly_means.get(y) if all(records.get((y,m),{}).get('MONTHLY_MEAN') is not None for m in range(1,13)) else None;row+='<td>'+('-' if value is None else escape(value_text(value,parameter)))+'</td></tr>';out.append(row)
  def monthly_table(m):
   tab=m[0]
   if 'monthly mean value' not in tab:return tab
   tab=re.sub(r'<tbody>.*?</tbody>',lambda _:'<tbody>'+''.join(out)+'</tbody>',tab,flags=re.S)
   foot=[]
   for label,fn in [('Mean',lambda vs:sum(vs)/len(vs)),('Max',max),('Min',min)]:
    row='<tr><th scope="row">'+label+'</th>'
    for month in range(1,14):
     vs=[r['MONTHLY_MEAN'] for r in months if r['MONTH']==month and r['MONTHLY_MEAN'] is not None] if month<=12 else [fn(vs2) for m in range(1,13) if (vs2:=[r['MONTHLY_MEAN'] for r in months if r['MONTH']==m and r['MONTHLY_MEAN'] is not None])]
     row+='<td>'+('-' if not vs else escape(value_text(fn(vs) if month<=12 else sum(vs)/len(vs),parameter)))+'</td>'
    foot.append(row+'</tr>')
   return re.sub(r'<tfoot>.*?</tfoot>',lambda _:'<tfoot>'+''.join(foot)+'</tfoot>',tab,flags=re.S)
  s=re.sub(r'<table\b.*?</table>',monthly_table,s,flags=re.S)
 if kind in ('Annual Extremes','Peak'):
  if parameter=='Level':s=s.replace('Discharge','Water Level').replace('Cubic metre(s) per second','Metre(s)').replace('m<sup>3</sup>/s','m')
  if mode=='Table':s=re.sub(r'<tbody>.*?</tbody>',lambda _:extremes.tbody(db,number,parameter,kind=='Peak'),s,count=1,flags=re.S)
 vals,history=station_metadata(db,station)
 for name in ['active','province','latitude','longitude','gross-drainage','effective-drainage','record-length','record-period','regulation-type','regulation-length','realtime-data','sediment-data','water-body','rhbn','regional-office','operation-schedule','contributed-by','operation-period','published-data','datum-data']:
  val=vals.get(name,'Not yet mapped from the archived station metadata')
  rendered=escape('' if val is None else val)
  if name=='datum-data':rendered='<a href="/report/datum_e.html?stn='+escape(number)+'&amp;mode='+escape(mode)+'">More information</a>'
  s=re.sub(r'(<div aria-labelledby="'+name+r'"[^>]*>).*?(</div>)',lambda m:m[1]+rendered+m[2],s,flags=re.S)
 # Never retain example-station program history.
 def history_table(match):
  table=match[0]
  if 'Operation schedule' not in table:return table
  body='<tbody>'+''.join('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>' for row in history)+'</tbody>'
  return re.sub(r'<tbody>.*?</tbody>',lambda _:body,table,flags=re.S)
 s=re.sub(r'<table\b.*?</table>',history_table,s,flags=re.S)
 return s
