import calendar,csv,datetime,io,math

def value_text(value,parameter,precision=8):
 if value is None:return ''
 if parameter=='Level':
  if precision not in (8,9):raise ValueError('Unmapped published level precision')
  return format(value,'.3f' if precision==8 else '.2f')
 if 0<value<1:return f'{value:.3f}'
 if value==0:return '0.00'
 digits=2-int(math.floor(math.log10(abs(value))))
 return f'{round(value,digits):.{max(0,digits)}f}'

def daily_csv(db,numbers,form,missing=True):
 if form not in ('csv','ddf','jdf'):raise ValueError('Invalid daily download format')
 out=io.StringIO(newline='');out.write('\ufeff\ufeffDaily Discharge (m3/s) (PARAM = 1) and Daily Water Level (m) (PARAM = 2)\r\n');writer=csv.writer(out)
 if form=='csv':writer.writerow([' ID','PARAM','TYPE','YEAR','DD']+[v for month in calendar.month_abbr[1:] for v in (month,'SYM')])
 elif form=='ddf':writer.writerow([' ID','PARAM','Date','Value','SYM'])
 else:writer.writerow([' ID','PARAM','YEAR','DD','Value','SYM'])
 for number in numbers:
  db.station(number)
  for param,code,prefix in [('Flow',1,'FLOW'),('Level',2,'LEVEL')]:
   records=db.months(number,param)
   if not records:continue
   index={(r['YEAR'],r['MONTH']):r for r in records};lo=min(index)[0];hi=max(index)[0]
   if form=='csv':
    for year in range(lo,hi+1):
     present=[r for r in records if r['YEAR']==year];precision=1 if param=='Flow' else (present[0]['PRECISION_CODE'] if present else records[0]['PRECISION_CODE'])
     for day in range(1,32):
      row=[number,code,precision,year,f'{day:02d}']
      for month in range(1,13):
       r=index.get((year,month));valid=r is not None and day<=calendar.monthrange(year,month)[1]
       v=r[f'{prefix}{day}'] if valid else None;symbol=r.get(f'{prefix}_SYMBOL{day}') if valid else ''
       row.extend([value_text(v,param,r.get('PRECISION_CODE',8) if r else 8),symbol or ''])
      writer.writerow(row)
   else:
    days=[]
    for r in records:
     for day in range(1,calendar.monthrange(r['YEAR'],r['MONTH'])[1]+1):
      days.append((datetime.date(r['YEAR'],r['MONTH'],day),r[f'{prefix}{day}'],r.get(f'{prefix}_SYMBOL{day}') or '',r.get('PRECISION_CODE',8)))
    observed=[r for r in days if r[1] is not None]
    if not observed:continue
    first,last=observed[0][0],observed[-1][0]
    if missing and param=='Flow':last=datetime.date(hi,12,31)
    lookup={r[0]:r for r in days};date=first
    while date<=last:
     _,value,symbol,precision=lookup.get(date,(date,None,'',8))
     if missing or value is not None:
      date_fields=[date.strftime('%Y/%m/%d')] if form=='ddf' else [date.year,f'{date.timetuple().tm_yday:02d}']
      writer.writerow([number,code]+date_fields+[value_text(value,param,precision),symbol])
     date+=datetime.timedelta(days=1)
 return out.getvalue().encode('utf-8')

def realtime_zip(data,numbers,code,fmt,start=None,end=None):
 import json,zipfile,xml.etree.ElementTree as ET
 from realtime import observations
 if code in ('3','6'):return realtime_daily_zip(data,numbers,code,fmt,start,end)
 if code not in ('46','47'):raise ValueError('Invalid real-time parameter')
 if fmt not in ('csv','txt','xml'):raise ValueError('Invalid real-time download format')
 meta={r['number']:r for r in json.loads((data/'realtime-stations.json').read_text())['stations']}
 mapmeta={r['station_id']:r for r in json.loads((data/'map-stations-real_time.json').read_text())}
 parameter,field,abbr,unit=('Level','LEVEL','HG','m') if code=='46' else ('Flow','DISCHARGE','QR','m3/s')
 result=io.BytesIO()
 with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED) as z:
  for number in numbers:
   if number not in meta:raise ValueError('Station not in real-time snapshot')
   rows=observations(data,number)
   if start or end:
    lo=datetime.date.fromisoformat(start or '2026-09-18');hi=datetime.date.fromisoformat(end or '2026-09-25')
    if not datetime.date(2026,9,18)<=lo<=hi<=datetime.date(2026,9,25):raise ValueError('Outside the archived real-time window')
    rows=[r for r in rows if lo<=datetime.date.fromisoformat(r['DATETIME_LST'][:10])<=hi]
   timezone=mapmeta.get(number,{}).get('timezone_abbr_en','Local standard time');station=meta[number]
   if fmt=='xml':
    root=ET.Element('realTimeData')
    for key,v in [('stationid',number),('fromdate',rows[0]['DATETIME_LST'] if rows else ''),('todate',rows[-1]['DATETIME_LST'] if rows else ''),('timezone',timezone)]:ET.SubElement(root,key).text=v
    records=ET.SubElement(root,'data')
    for r in rows:
     rec=ET.SubElement(records,'record')
     for key,v in [('datestamp',datetime.datetime.fromisoformat(r['DATETIME_LST']).strftime('%Y-%m-%d %H:%M:%S.000')),('code',abbr),('value',value_text(float(r[field]),parameter) if r[field] else ''),('approval',''),('grade',''),('qualifiers',r.get(field+'_SYMBOL_EN',''))]:ET.SubElement(rec,key).text=v
    body=ET.tostring(root,encoding='utf-8',xml_declaration=True)
   else:
    text=io.StringIO(newline='');sep=',' if fmt=='csv' else '\t';writer=csv.writer(text,delimiter=sep)
    text.write('\ufeffReal-time data - subject to revision\r\nCopyright Environment Canada(2026)\r\n\r\n')
    writer.writerow([f'Real-Time Hydrometric Data for {station["name"]} ({number}) [{station["province"]}]']);writer.writerow([]);writer.writerow([number,station['name']]);writer.writerow(['Description of parameters:']);writer.writerow([code,'Water level (unit values)' if code=='46' else 'Discharge (unit values)',unit]);writer.writerow([]);writer.writerow([f'Date ({timezone})','Parameter ',f'Value ({unit})','Approval','Grade','Qualifiers'])
    for r in rows:writer.writerow([datetime.datetime.fromisoformat(r['DATETIME_LST']).strftime('%Y-%m-%d %H:%M:%S'),code,value_text(float(r[field]),parameter) if r[field] else '','','',r.get(field+'_SYMBOL_EN','')])
    body=text.getvalue().encode('utf-8')
   z.writestr(f'{number}_{abbr}_20260925T0940.{fmt}',body)
  z.writestr('OFFLINE_SNAPSHOT.txt','Fixed observation window: 2026-09-18 09:40 UTC through 2026-09-25 09:40 UTC. Values and qualifier symbols come from the official GeoMet hydrometric-realtime collection. Approval and grade fields are not supplied by that source and are left empty, not inferred. The first and last local calendar dates may be partial. This package includes every selected station, independent of the visible result page.\n')
 return result.getvalue()

def historical_csv(db,numbers,product,form='csv'):
 if product=='dd':return daily_csv(db,numbers,form)
 if product not in ('md','ae','pd','rmk') or form not in (('csv','ddf') if product=='md' else ('csv',)):raise ValueError('Invalid historical download product or format')
 out=io.StringIO(newline='');writer=csv.writer(out)
 titles={'md':'Monthly Mean Discharge (m3/s) (PARAM = 1) and Monthly Mean Water Level (m) (PARAM = 2)','ae':'Annual Maximum and Minimum Daily Discharge (m3/s) (PARAM = 1) and Annual Maximum and Minimum Daily Water Level (m) (PARAM = 2)','pd':'Annual Maximum and Minimum Instantaneous Discharge (m3/s) (PARAM = 1) and Annual Maximum and Minimum Instantaneous Water Level (m) (PARAM = 2)'}
 if product=='rmk':
  out.write('\ufeff\ufeffAnnual hydrometric remarks (2)\r\nHistorical discharge remarks (4)\r\nHistorical water level remarks (5)\r\n\r\n');writer.writerow(['ID','REMARK TYPE','YEAR','REMARKS'])
 else:
  out.write('\ufeff\ufeff'+titles[product]+'\r\n')
  if product=='md':writer.writerow([' ID','PARAM','MM--YYYY','Value'] if form=='ddf' else [' ID','PARAM','TYPE','Year']+[v for month in calendar.month_abbr[1:] for v in (month,'SYM')]+['Mean'])
  elif product=='ae':writer.writerow([' ID','PARAM','Year','MM--DD','MAX','SYM','MM--DD','MIN','SYM'])
  else:writer.writerow([' ID','PARAM','Year','TIMEZONE','HH:MM','MM--DD','MAX','SYM','HH:MM','MM--DD','MIN','SYM'])
 with db.connect() as c:
  for number in numbers:
   db.station(number)
   if product=='rmk':
    for r in c.execute('SELECT * FROM STN_REMARKS WHERE STATION_NUMBER=? AND REMARK_TYPE_CODE IN (2,4,5) ORDER BY REMARK_TYPE_CODE,YEAR',(number,)):
     writer.writerow([number,r['REMARK_TYPE_CODE'],r['YEAR'],r['REMARK_EN']])
    continue
   for param,code,dt in [('Flow',1,'Q'),('Level',2,'H')]:
    months=db.months(number,param)
    if not months:continue
    index={(r['YEAR'],r['MONTH']):r for r in months};lo=min(index)[0];hi=max(index)[0]
    annual={r['YEAR']:dict(r) for r in c.execute('SELECT * FROM ANNUAL_STATISTICS WHERE STATION_NUMBER=? AND DATA_TYPE=?',(number,dt))}
    peaks={(r['YEAR'],r['PEAK_CODE']):dict(r) for r in c.execute('SELECT * FROM ANNUAL_INSTANT_PEAKS WHERE STATION_NUMBER=? AND DATA_TYPE=?',(number,dt))}
    means=[(k,r['MONTHLY_MEAN']) for k,r in sorted(index.items()) if r['MONTHLY_MEAN'] is not None]
    for year in range(lo,hi+1):
     present=[r for r in months if r['YEAR']==year];precision=1 if param=='Flow' else (present[0]['PRECISION_CODE'] if present else months[0]['PRECISION_CODE'])
     fmt=lambda v:value_text(v,param,precision)
     if product=='md':
      vals=[index.get((year,m),{}).get('MONTHLY_MEAN') for m in range(1,13)]
      if form=='csv':writer.writerow([number,code,precision,year]+[v for n in vals for v in (fmt(n),'')]+[fmt(annual.get(year,{}).get('MEAN'))])
      elif means:
       for m,v in enumerate(vals,1):
        if means[0][0]<=(year,m)<=((hi,12) if param=='Flow' else means[-1][0]):writer.writerow([number,code,f'{m:02d}--{year}',fmt(v)])
     elif product=='ae':
      a=annual.get(year,{});row=[number,code,year]
      for k in ('MAX','MIN'):
       v=a.get(k);date=f'{a[k+"_MONTH"]:02d}--{a[k+"_DAY"]:02d}' if v is not None and a.get(k+'_MONTH') and a.get(k+'_DAY') else ''
       row.extend([date,fmt(v),(a.get(k+'_SYMBOL') or '').strip()])
      writer.writerow(row)
     else:
      high=peaks.get((year,'H'),{});low=peaks.get((year,'L'),{});row=[number,code,year,high.get('TIME_ZONE') or low.get('TIME_ZONE') or '']
      for a in (high,low):
       v=a.get('PEAK');date=f'{a["MONTH"]:02d}--{a["DAY"]:02d}' if a.get('MONTH') and a.get('DAY') else '';time=f'{a["HOUR"]:02d}:{a["MINUTE"]:02d}' if a.get('HOUR') is not None and a.get('MINUTE') is not None else ''
       row.extend([time,date,value_text(v,param,a.get('PRECISION_CODE',precision)),(a.get('SYMBOL') or '').strip()])
      writer.writerow(row)
 return out.getvalue().encode('utf-8')


def realtime_daily_zip(data,numbers,code,fmt,start,end):
 import json,zipfile,xml.etree.ElementTree as ET
 from realtime import graph,label
 if fmt not in ('csv','txt','xml'):raise ValueError('Invalid real-time download format')
 meta={r['number']:r for r in json.loads((data/'realtime-stations.json').read_text())['stations']}
 mapmeta={r['station_id']:r for r in json.loads((data/'map-stations-real_time.json').read_text())}
 parameter,abbr,unit=('Level','HGD','m') if code=='3' else ('Flow','QRD','m³/s')
 result=io.BytesIO()
 with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED) as z:
  for number in numbers:
   if number not in meta:raise ValueError('Station not in real-time snapshot')
   series=graph(data,{'station':number,'param1':code,'start_date':start or '2026-09-18','end_date':end or '2026-09-25'})[code]
   rows=sorted(series['final']+series['provisional'],key=lambda r:r[0]);station=meta[number];timezone=mapmeta.get(number,{}).get('timezone_abbr_en','Local standard time')
   if fmt=='xml':
    root=ET.Element('realTimeData')
    for k,v in [('stationid',number),('fromdate',rows[0][0]+'.000' if rows else ''),('todate',rows[-1][0]+'.000' if rows else ''),('timezone',timezone)]:ET.SubElement(root,k).text=v
    records=ET.SubElement(root,'data')
    for row in rows:
     rec=ET.SubElement(records,'record')
     for k,v in [('datestamp',row[0]+'.000'),('code',abbr),('value',value_text(row[1],parameter) if row[1] is not None else '')]:ET.SubElement(rec,k).text=v
    body=ET.tostring(root,encoding='utf-8',xml_declaration=True)
   else:
    text=io.StringIO(newline='');writer=csv.writer(text,delimiter=',' if fmt=='csv' else '\t')
    text.write('\ufeffReal-time data - subject to revision\r\nCopyright Environment Canada(2026)\r\n\r\n')
    writer.writerow([f'Real-Time Hydrometric Data for {station["name"]} ({number}) [{station["province"]}]']);writer.writerow([]);writer.writerow([number,station['name']]);writer.writerow(['Description of parameters:']);writer.writerow([code,label(code),unit]);writer.writerow([]);writer.writerow([f'Date ({timezone})','Parameter ',f'Value ({unit})'])
    for row in rows:writer.writerow([row[0],code,value_text(row[1],parameter) if row[1] is not None else ''])
    body=text.getvalue().encode('utf-8')
   z.writestr(f'{number}_{abbr}_20260925_snapshot.{fmt}',body)
  manifest=json.loads((data/'realtime-daily/manifest.json').read_text())
  z.writestr('OFFLINE_SNAPSHOT.txt','Official daily means for local dates September 18–25, 2026. Collection completed: '+manifest['collection_finished']+'. September 25 is partial and reflects per-station acquisition time. These values are independently archived official products, not means recomputed from the unit-value snapshot. All selected stations are included. Original quality metadata remains available in the graph data; these download columns follow the original daily-mean format.\n')
 return result.getvalue()
