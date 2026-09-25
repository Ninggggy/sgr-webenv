"""Official river order and hierarchy; never sort stations geographically."""
import csv,io,json,re

def load(path):return json.loads(path.read_text())['rows']
def page(rows,q,size=100):
 if q.get('stnNum'):
  start=next((i for i,r in enumerate(rows) if r['Station Number']==q['stnNum']),None)
  if start is None:raise KeyError(q['stnNum'])
 else:start=int(q.get('stnIndex','0'))
 if not 0<=start<len(rows):raise ValueError('Invalid reference index')
 return start,rows[start:start+size]
def index(rows,q):
 typ=q.get('type','stationNumber');term=q.get('stationLike','01' if typ=='stationNumber' else 'A').upper()
 if typ not in ('stationNumber','stationName'):raise ValueError('Invalid index type')
 seen=set();out=[]
 for r in rows:
  number=r['Station Number'];name=r['Water Course'].lstrip('.')
  if not number or number in seen:continue
  seen.add(number)
  if (number if typ=='stationNumber' else name.upper()).startswith(term):out.append((number,name))
 return sorted(out,key=lambda r:(r[0] if typ=='stationNumber' else r[1],r[0]))

import functools
@functools.lru_cache(maxsize=1)
def display_rows(path):return json.loads(path.read_text())['rows']
def display_page(path,q):
 rows=display_rows(path)
 if q.get('stnNum'):
  start=next((i for i,r in enumerate(rows) if r['number']==q['stnNum']),None)
  if start is None:raise KeyError(q['stnNum'])
 else:start=int(q.get('stnIndex') or 0)
 if not 0<=start<len(rows):raise ValueError('Invalid reference index')
 count=0;end=start
 for i in range(start,len(rows)):
  end=i;count+=bool(rows[i]['number'])
  if count==100:break
 previous=start;count=0
 for i in range(start,-1,-1):
  previous=i;count+=bool(rows[i]['number'])
  if count==100:break
 output=[]
 for r in rows[start:end+1]:
  row=re.sub(r'<tr\b[^>]*>','<tr class="info">' if r['number'] and r['number']==q.get('stnNum') else '<tr>',r['html'],count=1)
  output.append(row)
 return ''.join(output),previous if start else None,end if end<len(rows)-1 else None
