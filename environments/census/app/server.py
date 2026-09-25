"""Local ACS table service. Author evidence and cross-table formulas are not served."""
import csv,io,json,math,mimetypes,os,re,sqlite3,zipfile,unicodedata
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
DATA=Path(os.environ.get('CENSUS_DATA','/data'));APP=Path(__file__).parent
VERSION='0.2.1'
import coverage
def db():
 c=sqlite3.connect(f'file:{DATA}/census.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c

def query(q):
 if 'task_id' in q:raise ValueError('Task identifiers are not a data query parameter')
 y=int(q.get('year',['2018'])[0]);p=q.get('product',['acs5'])[0];t=q.get('table',['B28002'])[0]
 if y not in range(2016,2020) or p not in ['acs5','acs1'] or not re.fullmatch('[BC][0-9A-Z]{5,8}',t):raise ValueError('Unsupported release, product or table ID')
 with db() as c:
  meta=c.execute('SELECT * FROM tables WHERE year=? AND product=? AND id=?',(y,p,t)).fetchone()
  if meta is None:raise LookupError(f'Table {t} is not listed in the official {y} {p} table catalog (https://api.census.gov/data/{y}/acs/{p}/groups.json). Your geography selections are retained.')
  variables=[dict(v) for v in c.execute('SELECT * FROM variables WHERE year=? AND product=? AND table_id=? ORDER BY id',(y,p,t))]
  gs=coverage.geographies(c,y,q.get('geo',[''])[0]);archived=coverage.index(c,y,p).get(t,set());rows=[]
  for ge in gs:
   cells=[dict(r) for r in c.execute('SELECT variable,estimate,moe,ea,ma FROM cells WHERE year=? AND product=? AND table_id=? AND geo=?',(y,p,t,ge['id']))]
   rows.append({**ge,'values':{v['variable']:v for v in cells},'available':ge['id'] in archived})
  result={'year':y,'product':p,'table':dict(meta),'variables':variables,'rows':rows,'coverage':coverage.describe(c,y,p,t,gs,archived),'version':VERSION}
  customization(result,q)
  return result

def customization(result,q):
 fs=json.loads(q.get('filters',['[]'])[0]);ids={v['id'] for v in result['variables']}
 if not isinstance(fs,list) or len(fs)>30:raise ValueError('Expected at most 30 table filters')
 for f in fs:
  if not isinstance(f,dict) or not isinstance(f.get('variable'),str) or f['variable'] not in ids or f.get('op') not in ['ge','gt','le','lt','eq','ne']:raise ValueError('Invalid table filter')
  value=f.get('value')
  if isinstance(value,bool) or not isinstance(value,(str,int,float)) or (isinstance(value,str) and not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',value.strip())):raise ValueError('Filter threshold must be a finite number')
  try:finite=math.isfinite(float(value))
  except (ValueError,OverflowError):finite=False
  if not finite:raise ValueError('Filter threshold must be a finite number')
 if q.get('sort',['name'])[0] not in ids|{'name'}:raise ValueError('Invalid sort variable')
 if q.get('direction',['asc'])[0] not in ['asc','desc']:raise ValueError('Invalid sort direction')
 for key in ['tp','moe']:
  if key in q and q[key][0] not in ['true','false']:raise ValueError('Invalid '+key+' setting')
 hidden=set(filter(None,q.get('hidden',[''])[0].split(',')))
 if not hidden<=ids:raise ValueError('Invalid hidden variable')
 return fs,hidden,set(filter(None,q.get('hiddenGeo',[''])[0].split(',')))

def namekey(name):
 return ''.join(x for x in unicodedata.normalize('NFD',name) if not unicodedata.category(x).startswith('M')).lower()

def selected(result,q,custom=True):
 variables=result['variables'];rows=[r for r in result['rows'] if r['available']]
 if custom:
  fs,hidden,hidden_geos=customization(result,q)
  for f in fs:
   v,op,value=f['variable'],f['op'],float(f['value'])
   if v not in [v['id'] for v in variables] or op not in ['ge','gt','le','lt','eq','ne']:raise ValueError('Invalid table filter')
   def match(r):
    x=r['values'].get(v,{}).get('estimate')
    return x is not None and not r['values'][v].get('ea') and {'ge':lambda:x>=value,'gt':lambda:x>value,'le':lambda:x<=value,'lt':lambda:x<value,'eq':lambda:x==value,'ne':lambda:x!=value}[op]()
   rows=[r for r in rows if match(r)]
  rows=[r for r in rows if r['id'] not in hidden_geos];variables=[v for v in variables if v['id'] not in hidden]
  sort=q.get('sort',['name'])[0];reverse=q.get('direction',['asc'])[0]=='desc'
  if sort=='name':rows.sort(key=lambda r:(r['level']!='state',namekey(r['name'])),reverse=reverse)
  elif sort in [v['id'] for v in result['variables']]:rows.sort(key=lambda r:(r['values'][sort]['estimate'] is not None and not r['values'][sort]['ea'],r['values'][sort]['estimate'] if r['values'][sort]['estimate'] is not None and not r['values'][sort]['ea'] else 0),reverse=reverse)
 return rows,variables

def rawvalue(c,key):
 a=c.get('ea' if key=='estimate' else 'ma');n=c.get(key)
 return a if a else (int(n) if n is not None and float(n).is_integer() else n if n is not None else '')
def export(result,q):
 fmt=q.get('format',['csv'])[0];rows,variables=selected(result,q,fmt!='zip');transpose=q.get('tp',['false'])[0]=='true';moe=q.get('moe',['true'])[0]=='true'
 if not rows:raise ValueError('No archived rows match the selected geography and export scope. '+result['coverage']['message'])
 if fmt=='zip':
  fields=['GEO_ID','NAME']+[v['id'][:-1]+s for v in variables for s in ['E','M','EA','MA']]
  matrix=[fields]
  for r in rows:
   row=[('0400000US' if r['level']=='state' else '0500000US')+r['id'],r['name']]
   for v in variables:
    c=r['values'][v['id']];row += [int(c[k]) if c[k] is not None and float(c[k]).is_integer() else c[k] for k in ['estimate','moe']]+[c['ea'],c['ma']]
   matrix.append(row)
 else:
  if transpose:
   matrix=[['Label (Grouping)']+[v['label'].removeprefix('Estimate!!') for v in variables]]
   for r in rows:
    matrix.append([r['name']]+['']*len(variables))
    for key in (['estimate','moe'] if moe else ['estimate']):matrix.append(['    '+('Estimate' if key=='estimate' else 'Margin of Error')]+[rawvalue(r['values'][v['id']],key) for v in variables])
  else:
   matrix=[['Label (Grouping)']+[r['name']+'!!'+k for r in rows for k in (['Estimate','Margin of Error'] if moe else ['Estimate'])]]
   for v in variables:matrix.append([v['label'].removeprefix('Estimate!!')]+[rawvalue(r['values'][v['id']],k) for r in rows for k in (['estimate','moe'] if moe else ['estimate'])])
 text=io.StringIO();csv.writer(text).writerows(matrix);b=('\ufeff'+text.getvalue()).encode()
 if fmt=='zip':
  stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('data.csv',b);z.writestr('variables.json',json.dumps(variables,indent=2));z.writestr('notes.txt',notes(result));z.writestr('coverage.json',json.dumps(result['coverage'],indent=2))
  return stream.getvalue(),'application/zip','zip'
 if fmt=='xlsx':
  # Minimal standards-based OOXML workbook; no runtime package installation.
  from xml.sax.saxutils import escape
  def cell(i,j,v):
   s='';j+=1
   while j:s=chr(65+(j-1)%26)+s;j=(j-1)//26
   a=f'{s}{i+1}'
   if isinstance(v,(int,float)):return f'<c r="{a}"><v>{v}</v></c>'
   return f'<c r="{a}" t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'
  xml='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join('<row r="'+str(i+1)+'">'+''.join(cell(i,j,v) for j,v in enumerate(row))+'</row>' for i,row in enumerate(matrix))+'</sheetData></worksheet>'
  stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
   coverage_xml='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1">'+cell(0,0,result['coverage']['message'])+'</row><row r="2">'+cell(1,0,notes(result))+'</row></sheetData></worksheet>'
   z.writestr('xl/worksheets/sheet2.xml',coverage_xml)
   z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
   z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
   z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="ACS table" sheetId="1" r:id="rId1"/><sheet name="Coverage" sheetId="2" r:id="rId2"/></sheets></workbook>')
   z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>');z.writestr('xl/worksheets/sheet1.xml',xml)
  return stream.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','xlsx'
 if fmt!='csv':raise ValueError('Unsupported export format')
 return b,'text/csv; charset=utf-8','csv'
def notes(r):return f"{r['year']} {r['product']} {r['table']['id']}\nUniverse: {r['table']['universe']}\nCoverage: {r['coverage']['message']}\nEstimates and 90% margins of error. Annotations and unavailable values are not zero. No derived MOE is supplied. Sources include official sequence Summary Files and historical formatted exports. CSV/Excel preserve selected customizations; ZIP contains all archived selected geography rows. Historical formatted exports may carry less precision than Census raw API data.\n"
class Handler(BaseHTTPRequestHandler):
 def send(self,b,status=200,ctype='application/json',filename=None,coverage_info=None):
  if not isinstance(b,bytes):b=json.dumps(b,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
  if coverage_info:self.send_header('X-Census-Coverage',json.dumps(coverage_info,ensure_ascii=True,separators=(',',':')))
  if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
  self.end_headers();self.wfile.write(b)
 def do_GET(self):
  try:
   u=urlsplit(self.path);q=parse_qs(u.query);path=u.path
   if path=='/health':return self.send({'status':'ok','version':VERSION,'database':(DATA/'census.sqlite').exists()})
   api=re.fullmatch(r'/data/(20(?:16|17|18|19))/acs/(acs[15])(?:/(.*))?',path)
   if api:
    from census_api import serve
    with db() as c:return self.send(serve(c,int(api[1]),api[2],api[3] or '',q))
   if path=='/api/catalog':
    with db() as c:
     year=int(q.get('year',['2018'])[0]);product=q.get('product',['acs5'])[0];term=q.get('q',[''])[0][:200]
     rows=c.execute('SELECT * FROM tables WHERE year=? AND product=? AND (id LIKE ? OR title LIKE ?) ORDER BY id',(year,product,'%'+term+'%','%'+term+'%')).fetchall()
     gs=coverage.geographies(c,year,q.get('geo',[''])[0]);idx=coverage.index(c,year,product)
     results=[]
     for row in rows:
      cov=coverage.describe(c,year,product,row['id'],gs,idx.get(row['id'],set()))
      results.append({**dict(row),'available':cov['archived']>0 if gs else bool(cov['scope']),'coverage':cov})
    return self.send(results)
   if path=='/api/geographies':
    with db() as c:r=c.execute('SELECT * FROM geographies WHERE year=? ORDER BY state,level DESC,name',(int(q.get('year',['2018'])[0]),)).fetchall()
    return self.send([dict(v) for v in r])
   if path=='/api/table':return self.send(query(q))
   if path=='/download':
    r=query(q);b,typ,ext=export(r,q);return self.send(b,ctype=typ,filename=f"ACSDT{5 if r['product']=='acs5' else 1}Y{r['year']}.{r['table']['id']}.{ext}",coverage_info=r['coverage'])
   if path=='/api/coverage':
    with db() as c:r=[dict(x) for x in c.execute('SELECT year,product,table_id,count(*) geographies,max(variables) variables FROM table_coverage GROUP BY year,product,table_id ORDER BY year,product,table_id')]
    return self.send(r)
   if path.startswith('/boundaries/') and re.fullmatch(r'/boundaries/20(16|17|18|19)\.json',path):
    f=DATA/path.lstrip('/')
    if not f.exists():raise LookupError('Boundary source not archived')
    return self.send(f.read_bytes())
   if path in ['/','/data.html','/advanced','/search','/help'] or re.fullmatch(r'/table/ACSDT[15]Y20(16|17|18|19)\.[BC][0-9A-Z]{5,8}',path):return self.send((APP/'index.html').read_bytes(),ctype='text/html; charset=utf-8')
   if path in ['/app.js','/style.css','/logo.svg']:return self.send((APP/path[1:]).read_bytes(),ctype=mimetypes.guess_type(path)[0])
   raise LookupError('Not available in this offline environment')
  except (ValueError,KeyError,TypeError) as e:self.send({'error':str(e)},400)
  except LookupError as e:self.send({'error':str(e)},404)
  except Exception as e:self.log_error('%s',e);self.send({'error':'Local data could not be read'},500)
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
