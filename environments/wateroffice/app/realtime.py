import csv,datetime,gzip,json,collections
import realtime_metadata
import realtime_snapshot as snapshot

def stations(data,q):
 source=json.loads((data/'realtime-stations.json').read_text());rows=source['stations']
 kind=q.get('search_type','station_name')
 if kind=='province':
  if q.get('province','all')!='all':rows=[r for r in rows if r['province']==q['province']]
 elif kind=='station_name':rows=[r for r in rows if q.get('station_name','').upper() in r['name'].upper()]
 elif kind=='station_number':
  term=q.get('station_number','').upper()
  rows=[r for r in rows if r['number'] in term.split(',')] if ',' in term else [r for r in rows if term in r['number']]
 elif kind=='coordinate':rows=realtime_metadata.coordinate_filter(data,rows,q)
 elif kind=='basin':rows=[r for r in rows if r['number'].startswith(q.get('basin',''))]
 else:raise ValueError('This real-time search type is pending validation')
 rows=realtime_metadata.area_filter(data,rows,q)
 catalog_path=data/'realtime-filter-membership.json'
 catalog=json.loads(catalog_path.read_text())['filters'] if catalog_path.exists() else {}
 allowed={'parameter_type':{'all','3','6','46','47'},'regulation':{'all','R','N'},'operation_schedule':{'all','C','S','M'}}
 for key in ('parameter_type','regulation','operation_schedule','operating_agency'):
  value=q.get(key,'all')
  if value=='all':continue
  if key in allowed and value not in allowed[key]:raise ValueError('Invalid '+key)
  item=catalog.get(key,{}).get(value)
  if item is None:raise ValueError('This '+key+' selection has not yet been archived and validated')
  remaining=collections.Counter(item['stations']);filtered=[]
  for row in rows:
   if remaining[row['number']]>0:filtered.append(row);remaining[row['number']]-=1
  rows=filtered
 return rows

def observations(data,number,start=None,end=None):
 if snapshot.is_official_csv(data,number):
  w=snapshot.window(data);lo=snapshot.timestamp(start or w['from']);hi=snapshot.timestamp(end or w['to'])
  if not snapshot.timestamp(w['from'])<=lo<=hi<=snapshot.timestamp(w['to']):raise ValueError('Outside the archived real-time window')
  metadata=json.loads((data/'realtime'/f'{number}.json').read_text());merged={}
  if not metadata.get('complete'):raise OSError('This station snapshot is incomplete')
  if not metadata['parameters']:return []
  local_lo,local_hi=snapshot.bounds(data,number)
  for code,field in [('46','LEVEL'),('47','DISCHARGE')]:
   if code not in metadata['parameters']:continue
   for r in snapshot.records(data,number,code,str(local_lo.date()),str(local_hi.date())):
    if not lo<=snapshot.timestamp(r['utc'])<=hi:continue
    row=merged.setdefault(r['utc'],{'STATION_NUMBER':number,'DATETIME':r['utc'],'DATETIME_LST':snapshot.timestamp(r['utc']).astimezone(snapshot.timezone(data,number)).isoformat(),'LEVEL':'','DISCHARGE':'','LEVEL_SYMBOL_EN':'','DISCHARGE_SYMBOL_EN':''})
    row[field]=r['value'];row[field+'_SYMBOL_EN']=r['qualifiers'];row[field+'_APPROVAL']=r['approval'];row[field+'_GRADE']=r['grade']
  return [merged[k] for k in sorted(merged)]
 path=data/'realtime'/f'{number}.csv.gz';meta=data/'realtime'/f'{number}.json'
 if not path.exists() or not meta.exists():raise OSError('This station has not been completely archived')
 window=snapshot.window(data,number)
 start=start or window['from'];end=end or window['to']
 def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 if dt(start)<dt(window['from']) or dt(end)>dt(window['to']):raise ValueError('Outside the archived real-time window')
 if dt(end)<dt(start):raise ValueError('Invalid date interval')
 with gzip.open(path,'rt') as f:rows=list(csv.DictReader(f))
 return [r for r in rows if dt(start)<=dt(r['DATETIME'])<=dt(end)]

def axes(number):
 return [{'stationid':number,'parameterid':str(code),'units_en':unit,'units_fr':unit,'units_name_en':name,'units_name_fr':name,'description_en':'','description_fr':''} for code,unit,name in [(3,'m','metre'),(6,'m³/s','cubic metre per second'),(46,'m','metre'),(47,'m³/s','cubic metre per second')]]

def graph(data,q):
 import calendar
 if any(q.get(k) in ('1','true') for k in q if any(word in k.lower() for word in ('mean','median','upper','lower','maximum','minimum'))):raise ValueError('Historical statistics are not included in the real-time snapshot')
 number=q.get('station','')
 if snapshot.is_official_csv(data,number):
  result={}
  for key in ('param1','param2'):
   code=q.get(key)
   if code in (None,'','0','-1'):continue
   result[code]=snapshot.graph_series(data,number,code,q.get('start_date'),q.get('end_date'))
  return result
 rows=observations(data,number)
 window=snapshot.window(data,number)
 # Date controls express local standard dates; first and final dates are partial.
 dates=[datetime.datetime.fromisoformat(r['DATETIME_LST']).date() for r in rows]
 lower=min(dates) if dates else datetime.date.fromisoformat(window['from'][:10]);upper=max(dates) if dates else datetime.date.fromisoformat(window['to'][:10])
 start=datetime.date.fromisoformat(q.get('start_date',str(lower)));end=datetime.date.fromisoformat(q.get('end_date',str(upper)))
 if start<datetime.date.fromisoformat(window['from'][:10]) or end>datetime.date.fromisoformat(window['to'][:10]) or start>end:raise ValueError('Dates outside the archived real-time snapshot')
 result={}
 for key in ['param1','param2']:
  code=q.get(key)
  if code in (None,'','0','-1'):continue
  if code in ('3','6'):
   result[code]=daily(data,number,code,start,end)
   continue
  if code not in ('46','47'):raise ValueError('Invalid real-time parameter')
  field='LEVEL' if code=='46' else 'DISCHARGE';symbol=field+'_SYMBOL_EN';values=[]
  for r in rows:
   t=datetime.datetime.fromisoformat(r['DATETIME_LST'])
   if start<=t.date()<=end:
    values.append([t.strftime('%Y-%m-%d %H:%M:%S'),float(r[field]) if r[field] else None,None,None,None,None,r.get(symbol,'')])
  result[code]={k:[] for k in ('final','measurements','maximum','minimum','mean','median','upper_quartile','lower_quartile')};result[code]['provisional']=values
 return result


def daily(data,number,code,start,end):
 path=data/'realtime-daily'/f'{number}.json.gz'
 if not (data/'realtime-daily/manifest.json').exists():raise OSError('The national daily-mean archive is not yet complete')
 membership=json.loads((data/'realtime-filter-membership.json').read_text())['filters']['parameter_type']
 if number not in membership[code]['stations']:raise ValueError('This parameter is not published for the selected station in the official station list')
 if not path.exists():raise OSError('Daily-mean resource not archived')
 with gzip.open(path,'rt') as f:source=json.load(f)
 if code not in source:raise OSError('Daily-mean parameter not archived')
 return {key:[row for row in rows if str(start)<=row[0][:10]<=str(end)] for key,rows in source[code].items()}

def label(code):
 return {'3':'Water level (daily mean values)','6':'Discharge (daily mean values)','46':'Water level (unit values)','47':'Discharge (unit values)'}[code]
