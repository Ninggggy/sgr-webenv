"""Annual extrema from the same national HYDAT tables used by the original downloads."""
import datetime,html
from downloads import value_text

def records(db,number,parameter,peak=False):
 months=db.months(number,parameter)
 if not months:return []
 precision=months[-1].get('PRECISION_CODE',8);dt='Q' if parameter=='Flow' else 'H';out=[]
 with db.connect() as c:
  source={r['YEAR']:dict(r) for r in c.execute('SELECT * FROM ANNUAL_STATISTICS WHERE STATION_NUMBER=? AND DATA_TYPE=?',(number,dt))} if not peak else {(r['YEAR'],r['PEAK_CODE']):dict(r) for r in c.execute('SELECT * FROM ANNUAL_INSTANT_PEAKS WHERE STATION_NUMBER=? AND DATA_TYPE=?',(number,dt))}
 for year in range(min(r['YEAR'] for r in months),max(r['YEAR'] for r in months)+1):
  row={'year':year}
  for label,code in [('maximum','MAX'),('minimum','MIN')]:
   r=source.get((year,'H' if code=='MAX' else 'L'),{}) if peak else source.get(year,{})
   value=r.get('PEAK' if peak else code);month=r.get('MONTH' if peak else code+'_MONTH');day=r.get('DAY' if peak else code+'_DAY');date=str(year)
   if month and day:date=f'{year}-{month:02d}-{day:02d}'
   if peak and r.get('HOUR') is not None and r.get('MINUTE') is not None:date+=f' {r["HOUR"]:02d}:{r["MINUTE"]:02d}'
   row[label]={'value':value_text(value,parameter,r.get('PRECISION_CODE',precision)) if value is not None else None,'date':date,'symbol':(r.get('SYMBOL' if peak else code+'_SYMBOL') or '').strip(),'timezone':r.get('TIME_ZONE') or ''}
  out.append(row)
 return out

def graph(db,number,parameter,peak=False):
 out={k:[] for k in ('provisional','maximum','minimum','mean','median','upper_quartile','lower_quartile')}
 for row in records(db,number,parameter,peak):
  for key in ('maximum','minimum'):
   value=row[key]['value']
   if peak and value is not None:
    if '.' in value:value=value.rstrip('0').rstrip('.')
    if value.startswith('0.'):value=value[1:]
    elif value.startswith('-0.'):value='-'+value[2:]
   out[key].append([int(datetime.datetime(row['year'],1,1,tzinfo=datetime.timezone.utc).timestamp()*1000),value])
 return out

def tbody(db,number,parameter,peak=False):
 out=[]
 for row in records(db,number,parameter,peak):
  cells=[]
  for key in ('maximum','minimum'):
   r=row[key];value=r['value'] or ''
   pieces=value.split('.') if value else [];display=(format(int(pieces[0]),',')+('.'+pieces[1] if len(pieces)>1 else '')) if pieces else ''
   cells.append('<td>'+html.escape(r['date'])+'</td>')
   if peak:cells.append('<td>'+html.escape(r['timezone'])+'</td>')
   cells.append('<td data-sort="'+html.escape(value,quote=True)+'">'+html.escape(display)+'&#160;'+html.escape(r['symbol'])+'</td>')
  out.append('<tr>'+''.join(cells)+'</tr>')
 return '<tbody>'+''.join(out)+'</tbody>'
