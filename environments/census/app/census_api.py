"""Bounded Census request syntax over the same archived cells as the UI."""
import re
class Unsupported(LookupError):pass
def serve(c,year,product,path,q):
 if year not in range(2016,2020) or product not in ['acs5','acs1']:raise Unsupported('Release not supported')
 if path=='groups.json':return {'groups':[{'name':r['id'],'description':r['title'],'variables':f'/data/{year}/acs/{product}/groups/{r["id"]}.json'} for r in c.execute('SELECT * FROM tables WHERE year=? AND product=? ORDER BY id',(year,product))]}
 m=re.fullmatch(r'groups/([BC]\d+[A-Z]{0,3})\.json',path)
 if m:
  rows=c.execute('SELECT * FROM variables WHERE year=? AND product=? AND table_id=? ORDER BY id',(year,product,m[1])).fetchall()
  if not rows:raise Unsupported('Variable definitions not archived for this table')
  variables={}
  for r in rows:
   for suffix,prefix in [('E','Estimate'),('M','Margin of Error'),('EA','Annotation of Estimate'),('MA','Annotation of Margin of Error')]:variables[r['id'][:-1]+suffix]={'label':r['label'].replace('Estimate',prefix,1),'group':m[1],'predicateType':'string' if suffix.endswith('A') else 'int'}
  return {'variables':variables}
 if path:raise Unsupported('API endpoint outside supported scope')
 allowed={'get','for','in'}
 if set(q)-allowed:raise ValueError('Supported API parameters: get, for, in')
 get=q.get('get',[''])[0].split(',');cols=[]
 for v in get:
  m=re.fullmatch(r'group\(([BC]\d+[A-Z]{0,3})\)',v)
  if m:
   vs=[r[0] for r in c.execute('SELECT id FROM variables WHERE year=? AND product=? AND table_id=? ORDER BY id',(year,product,m[1]))]
   if not vs:raise Unsupported('Variable definitions not archived')
   cols.extend([v[:-1]+suffix for v in vs for suffix in ['E','M','EA','MA']]);cols+=['NAME','GEO_ID']
  else:cols.append(v)
 cols=list(dict.fromkeys(cols))
 if not cols or len(cols)>2000:raise ValueError('Invalid variable selection')
 for v in cols:
  if v not in ['NAME','GEO_ID'] and not re.fullmatch(r'[BC]\d+[A-Z]{0,3}_\d+(E|M|EA|MA)',v):raise ValueError('Unsupported variable')
 geo=q.get('for',[''])[0];parent=q.get('in',[''])[0];m=re.fullmatch(r'(state|county):(\d{2,3}|\*)',geo)
 if not m:raise ValueError('Use for=state:SS or for=county:CCC&in=state:SS')
 level,code=m.groups()
 if level=='state':
  if parent:raise ValueError('A state query has no parent geography')
  gs=c.execute("SELECT * FROM geographies WHERE year=? AND level='state'"+('' if code=='*' else ' AND id=?')+' ORDER BY id',(year,) if code=='*' else (year,code)).fetchall();keys=['state']
 else:
  par=re.fullmatch(r'state:(\d{2})',parent)
  if not par:raise ValueError('A county query requires one explicit state')
  gs=c.execute('SELECT * FROM geographies WHERE year=? AND level="county" AND state=?'+('' if code=='*' else ' AND id=?')+' ORDER BY id',(year,par[1]) if code=='*' else (year,par[1],par[1]+code)).fetchall();keys=['state','county']
 if not gs:raise Unsupported('Geography not in archived geography release')
 rows=[cols+keys]
 needed=list(dict.fromkeys(re.sub(r'(EA|MA|M)$','E',v) for v in cols if v not in ['NAME','GEO_ID']))
 for g in gs:
  cells={r['variable']:r for r in c.execute('SELECT * FROM cells WHERE year=? AND product=? AND geo=?'+(' AND variable IN ('+','.join('?' for _ in needed)+')' if needed else ' LIMIT 1'),(year,product,g['id'],*needed))};row=[]
  if not cells:raise Unsupported('No numerical geography coverage archived for this release/product')
  for v in cols:
   if v=='NAME':
    x=g['name']
    if level=='county' and ', ' not in x:x+=', '+c.execute('SELECT name FROM geographies WHERE year=? AND id=?',(year,g['state'])).fetchone()[0]
   elif v=='GEO_ID':x=('0400000US' if level=='state' else '0500000US')+g['id']
   else:
    m=re.fullmatch(r'(.+_\d+)(E|M|EA|MA)',v);cell=cells.get(m[1]+'E')
    if cell is None:raise Unsupported('Requested numerical coverage not archived; no partial response is returned')
    x=cell[{'E':'estimate','M':'moe','EA':'ea','MA':'ma'}[m[2]]]
    if isinstance(x,float) and x.is_integer():x=int(x)
   row.append(None if x is None else str(x))
  rows.append(row+[g['state']]+([g['id'][2:]] if level=='county' else []))
 return rows
