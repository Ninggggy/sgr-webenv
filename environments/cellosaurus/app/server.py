import os,re,json,sqlite3,zlib,gzip,html,csv,io,mimetypes,urllib.parse,urllib.request,urllib.error
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from query import search,QueryError
DATA=Path(os.environ.get('DATA_DIR','/data'));STATIC=Path(__file__).resolve().parent/'static';CLASTR=os.environ.get('CLASTR_URL','http://cellosaurus-clastr:8080')
FILES=['README','cellosaurus_relnotes.txt','cellosaurus.txt','cellosaurus_refs.txt','cellosaurus.xml','cellosaurus.xsd','cellosaurus_xrefs.txt','cellosaurus_deleted_ACs.txt','cellosaurus_name_conflicts.txt','cellopub.txt','cellosaurus.obo','cellosaurus_faq.txt']
def esc(s):return html.escape(str(s),quote=True)
def fields(s):
 d={}
 for l in s.splitlines():
  if len(l)>4 and l[2:5]=='   ':d.setdefault(l[:2],[]).append(l[5:])
 return d
def conn():
 d=sqlite3.connect('file:'+str(DATA/'cellosaurus.sqlite')+'?mode=ro',uri=True);d.execute('PRAGMA cache_size=-16384');return d
def linkify(s):
 parts=re.split(r'(CVCL_[A-Za-z0-9]+|https?://[^\s<>]+)',s);out=[]
 for p in parts:
  if re.fullmatch('CVCL_[A-Za-z0-9]+',p):out.append('<a href="/'+p+'">'+p+'</a>')
  elif p.startswith(('http://','https://')):out.append('<a href="/outside?url='+urllib.parse.quote(p,safe='')+'">'+esc(p)+'</a>')
  else:out.append(esc(p))
 return ''.join(out)
def str_profile(lines,name):
 rows=[];params={'name':name}
 for line in lines:
  marker,value=line.split(': ',1)
  if marker=='Source(s)':
   rows.append('<tr><th>Sources</th><td>'+linkify(value)+'</td></tr>');continue
  alleles=value.split(' (',1)[0]
  rows.append('<tr><th>'+esc(marker)+'</th><td>'+linkify(value)+'</td></tr>')
  # Official detail links choose the most alleles, with later source rows breaking ties.
  # All source-specific rows remain visible; this does not alter the CLASTR database profiles.
  if marker not in params or len(alleles.split(','))>=len(params[marker].split(',')):params[marker]=alleles
 return '<details open><summary>STR profile and sources</summary><table class="str-profile">'+''.join(rows)+'</table></details><p><a class="clastr-prefill" href="/cellosaurus-str-search/?'+esc(urllib.parse.urlencode(params))+'">Compare using CLASTR</a></p>'
def page(title,content,query=''):
 return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'''+esc(title)+''' — Cellosaurus offline</title><link rel="stylesheet" href="/css/normalize.css"><link rel="stylesheet" href="/css/expasy_geneva.css"><link rel="stylesheet" href="/offline.css"></head><body><div class="offline-banner">Independent offline research environment · Release 56 · <a href="/coverage">Coverage and known differences</a></div><header><a href="/"><img alt="Cellosaurus" src="/images/cellosaurus/cellosaurus.png"></a><nav><a href="/">Home</a><details><summary>Browse</summary><a href="/browse_by_group">Cell line groups</a><a href="/browse_by_panel">Cell line panels</a><a href="/search?query=%22problematic%20cell%20line%22">Problematic cell lines</a></details><a href="/str-search/">CLASTR</a><a href="/download">Download</a><details><summary>Help</summary><a href="/description.html">Description</a><a href="/cellosaurus_relnotes.txt">Release notes</a><a href="/faq">FAQ</a><a href="/coverage">Offline coverage</a></details></nav></header><main><h1>'''+esc(title)+'''</h1><form action="/search" method="get"><input aria-label="Search Cellosaurus" name="query" value="'''+esc(query)+'''" size="40"><button type="submit">Search</button><button type="reset">Clear</button></form>'''+content+'''</main><footer>Cellosaurus data © CALIPHO group, SIB Swiss Institute of Bioinformatics · <a href="/license">CC BY 4.0</a>. Independent interface and offline adaptations; not an official service. <a href="#">Back to top</a></footer><script src="/site.js"></script></body></html>'''
def rows_html(rows):
 return '<table class="results"><thead><tr><th>Accession</th><th>Name</th><th>Species</th></tr></thead><tbody>'+''.join('<tr><td><a href="/'+esc(ac)+'">'+esc(ac)+'</a></td><td>'+esc(n)+'</td><td>'+esc(re.sub(r'NCBI_TaxID=\d+; ! ','',sp))+'</td></tr>' for ac,n,sp in rows)+'</tbody></table>'
class Handler(BaseHTTPRequestHandler):
 server_version='CellosaurusOffline/0.1.0'
 def log_message(self,fmt,*args):pass
 def send(self,status,data,ctype='text/html; charset=utf-8',headers=None):
  b=data if isinstance(data,bytes) else data.encode();self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'")
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers()
  try:self.wfile.write(b)
  except (BrokenPipeError,ConnectionResetError):pass
 def json(self,status,obj):self.send(status,json.dumps(obj),'application/json')
 def do_POST(self):self.handle_request(True)
 def do_GET(self):self.handle_request(False)
 def handle_request(self,post=False):
  u=urllib.parse.urlsplit(self.path);path=urllib.parse.unquote(u.path);q=urllib.parse.parse_qs(u.query,keep_blank_values=True)
  if any(x in path for x in ['..','\\','\x00']):self.json(404,{'error':'Not found'});return
  if path in ['/str-search/api/query','/str-search/api/batch','/str-search/api/conversion','/str-search/api/database']:
   return self.proxy(path,u.query,post)
  if post:self.json(405,{'error':'Method not allowed'});return
  try:
   if path=='/health':
    with conn() as db:version=db.execute('SELECT value FROM metadata WHERE key="release"').fetchone()[0]
    self.json(200,{'application':'0.1.0','release':version});return
   if path in ['/cellosaurus-str-search','/cellosaurus-str-search/']:
    self.send(302,'',headers={'Location':'/str-search/'+('?' + u.query if u.query else '')});return
   if path in ['/str-search','/str-search/']:path='/str-search/index.html'
   f=STATIC/path.lstrip('/')
   if f.is_file() and f.resolve().is_relative_to(STATIC.resolve()):
    self.send(200,f.read_bytes(),mimetypes.guess_type(str(f))[0] or 'application/octet-stream');return
   if path in ['/download','/databases/cellosaurus','/databases/cellosaurus/']:
    m=json.loads((DATA/'sources.json').read_text());body='<p>Complete archived release files. These downloads ignore search and table filters.</p><ul>'
    for name in FILES:
     v=m.get(name,{})
     if v.get('complete'):body+='<li><a href="/databases/cellosaurus/'+name+'">'+name+'</a> · '+str(v['raw_bytes'])+' bytes</li>'
    self.send(200,page('Download Cellosaurus release 56',body+'</ul><p><a href="/history">Historical name-conflict files (releases 53 and 54)</a></p>'));return
   legacy_archive=re.fullmatch(r'/records/(16878225|18418061)(/files/cellosaurus_name_conflicts\.txt)?',path)
   if legacy_archive:
    version='53' if legacy_archive[1]=='16878225' else '54'
    if legacy_archive[2]:return self.download_file('history/'+version+'/cellosaurus_name_conflicts.txt')
    self.send(200,page('Cellosaurus release '+version+' archive','<p>Offline copy of the complete name-conflict file from the official deposited release. Other Zenodo files are outside this archive.</p><a download href="'+path+'/files/cellosaurus_name_conflicts.txt">cellosaurus_name_conflicts.txt</a>'));return
   if path=='/history':
    entries=json.loads((DATA/'history/sources.json').read_text())
    body='<p>Complete historical name-conflict files, kept separate from the release-56 database.</p><ul>'
    for version,source in entries.items():body+='<li><a href="/history/'+version+'/cellosaurus_name_conflicts.txt">Release '+esc(source['release'])+'</a> · '+str(source['raw_bytes'])+' bytes · original: '+esc(source['record_url'])+'</li>'
    self.send(200,page('Historical archives',body+'</ul>'));return
   historical=re.fullmatch(r'/history/(53|54)/cellosaurus_name_conflicts\.txt',path)
   if historical:return self.download_file('history/'+historical[1]+'/cellosaurus_name_conflicts.txt')
   if path=='/description.html':
    body=(STATIC/'description-fragment.html').read_text()
    self.send(200,page('Description of Cellosaurus',body));return
   name=path.rsplit('/',1)[-1]
   if name in FILES and (path=='/'+name or path=='/databases/cellosaurus/'+name):return self.download_file(name)
   if path in ['/coverage','/license','/outside','/api','/description.html','/contact','/sars-cov-2.html','/educational_resources.html','/overview_rii.html','/SAB.html','/references.html']:
    body='<p>Cellosaurus record search, downloads and CLASTR STR matching. Use the search form to find records and the result controls to sort or export a view.</p><p>Data: CALIPHO / SIB, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. CLASTR code: <a href="/CLASTR-LICENSE.txt">GPL-3.0</a>.</p>'
    if q.get('url'):body+='<p>Outside archived scope: '+esc(q['url'][0])+'</p>'
    self.send(200,page('About this environment',body));return
   if path=='/faq':
    with gzip.open(DATA/'cellosaurus_faq.txt.gz','rt') as f:s=f.read()
    self.send(200,page('Cellosaurus FAQ','<pre>'+linkify(s)+'</pre>'));return
   with conn() as db:
    if path in ['/','/index.html']:
     n=db.execute('SELECT count(*) FROM cell').fetchone()[0]
     self.send(200,page('Cellosaurus — the reference resource on cell lines','<p>Release 56 of June 2026 · '+str(n)+' cell lines</p><div class="cards"><section><h2>Browse</h2><p><a href="/browse_by_group">Browse by cell line group</a></p><p><a href="/browse_by_panel">Browse by cell line panel</a></p><p><a href="/search?query=%22problematic%20cell%20line%22">Problematic cell lines</a></p></section><section><h2>Tools</h2><p><a href="/str-search/">CLASTR — STR similarity search</a></p><p><a href="/download">Download complete Cellosaurus data</a></p><p><a href="/faq">Frequently asked questions</a></p></section></div>'));return
    if path in ['/browse_by_group','/browse_by_panel']:
     kind='Group' if path.endswith('group') else 'Part of';selected=q.get('label',[''])[0]
     if selected:
      rows=db.execute('SELECT c.ac,c.name,c.species FROM cell c JOIN membership m ON m.ac=c.ac WHERE m.kind=? AND m.label=? ORDER BY c.name COLLATE NOCASE,c.ac',(kind,selected)).fetchall();body='<p>'+str(len(rows))+' records</p>'+rows_html(rows)
     else:
      rows=db.execute('SELECT label,count(*) FROM membership WHERE kind=? GROUP BY label ORDER BY label COLLATE NOCASE',(kind,));body='<ul>'+''.join('<li><a href="'+path+'?label='+urllib.parse.quote(label)+'">'+esc(label)+'</a> ('+str(n)+')</li>' for label,n in rows)+'</ul>'
     self.send(200,page('Cell line '+('groups' if kind=='Group' else 'panels')+(': '+selected if selected else ''),body));return
    if path in ['/search','/search/export']:
     query=q.get('query',q.get('input',['']))[0];rows=search(db,query)
     if path.endswith('/export'):return self.export(db,rows,q.get('format',['txt'])[0])
     body='<p>'+str(len(rows))+' hits for <strong>'+esc(query)+'</strong></p><p>Export all matching records: <a download href="/search/export?query='+urllib.parse.quote(query)+'&format=txt">TXT</a> · <a download href="/search/export?query='+urllib.parse.quote(query)+'&format=csv">CSV</a></p>'+rows_html(rows)
     self.send(200,page('Cellosaurus search result',body,query));return
    if re.fullmatch('/CVCL_[A-Za-z0-9]+(?:\.txt)?',path):return self.detail(db,path[1:])
   self.send(404,page('Not available','<p>This path is outside the reproduced scope.</p>'))
  except QueryError as e:self.send(400,page('Query not supported','<p>'+esc(e)+'</p>',q.get('query',[''])[0]))
  except Exception as e:
   print(type(e).__name__,str(e),flush=True);self.json(500,{'error':'Local query failed; no partial result is claimed'})
 def download_file(self,name):
  if not (DATA/(name+".gz")).is_file():self.json(503,{"error":"This archive is not yet available; coverage is incomplete"});return
  self.send_response(200);self.send_header('Content-Type','application/xml' if name.endswith(('.xml','.xsd')) else 'text/plain; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="'+name.rsplit('/',1)[-1]+'"');self.send_header('Connection','close');self.end_headers()
  try:
   with gzip.open(DATA/(name+'.gz'),'rb') as f:
    while True:
     b=f.read(65536)
     if not b:break
     self.wfile.write(b)
  except (BrokenPipeError,ConnectionResetError):pass
 def export(self,db,rows,fmt):
  if fmt not in ['csv','txt']:raise QueryError('Invalid export format')
  self.send_response(200);self.send_header('Content-Type','text/csv' if fmt=='csv' else 'text/plain; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="Cellosaurus_results.'+fmt+'"');self.send_header('Connection','close');self.end_headers()
  try:
   if fmt=='csv':self.wfile.write(b'Accession,Name,Species,Record\r\n')
   for ac,name,sp in rows:
    raw=zlib.decompress(db.execute('SELECT raw FROM cell WHERE ac=?',(ac,)).fetchone()[0]).decode()
    if fmt=='txt':b=raw.encode()
    else:
     s=io.StringIO();csv.writer(s).writerow([ac,name,sp,raw]);b=s.getvalue().encode()
    self.wfile.write(b)
  except (BrokenPipeError,ConnectionResetError):pass
 def detail(self,db,ac):
  txt=ac.endswith('.txt');ac=ac.removesuffix('.txt').upper();r=db.execute('SELECT name,raw FROM cell WHERE ac=?',(ac,)).fetchone()
  if not r:
   secondary=db.execute('SELECT ac FROM alias WHERE kind="secondary" AND name=?',(ac,)).fetchone()
   if secondary:self.send(302,'',headers={'Location':'/'+secondary[0]+('.txt' if txt else '')});return
   with gzip.open(DATA/'cellosaurus_deleted_ACs.txt.gz','rt') as archive:
    deleted=next((line.strip().split(None,1)[1] for line in archive if line.startswith(ac+' ')),None)
   if deleted:
    self.send(200,page('Cellosaurus ('+ac+')','<p>'+ac+': This entry was deleted. '+esc(deleted)+'</p>'));return
   self.send(404,page('Record not in this release' ,'<p>'+esc(ac)+' is not a primary or secondary accession in the archived release. <a href="/cellosaurus_deleted_ACs.txt">Deleted accessions</a>.</p>'));return
  raw=zlib.decompress(r[1]).decode()
  if txt:self.send(200,raw,'text/plain; charset=utf-8');return
  d=fields(raw);body='<p><a download href="/'+ac+'.txt">Text version</a> · RRID:'+ac+'</p>'
  labels={'ID':'Cell line name','AC':'Accession','AS':'Secondary accession','SY':'Synonyms','DR':'Cross-references','WW':'Web pages','CC':'Comments','ST':'STR profile','DI':'Diseases','OX':'Species of origin','HI':'Parent cell lines','OI':'Same individual as','SX':'Sex','AG':'Age at sampling','CA':'Category','DT':'Entry history'}
  body+='<table class="record"><tbody>'
  for code,label in labels.items():
   if code not in d:continue
   vals=d[code];content='<br>'.join(linkify(v) for v in vals)
   if code=='CC':
    content=''
    for v in vals:
     rendered=linkify(v)
     if v.startswith(('Group: ','Part of: ')):
      kind,group_label=v.split(': ',1);route='/browse_by_group' if kind=='Group' else '/browse_by_panel'
      rendered=esc(kind)+': <a href="'+route+'?label='+urllib.parse.quote(group_label.rstrip('.'))+'">'+esc(group_label)+'</a>'
     content+='<p>'+rendered+'</p>'
   if code=='ST':content=str_profile(vals,r[0])
   body+='<tr id="'+code+'"><th>'+label+'</th><td>'+content+'</td></tr>'
  children=db.execute('SELECT c.ac,c.name FROM relation r JOIN cell c ON c.ac=r.src WHERE r.dst=? AND r.kind="parent" ORDER BY c.name COLLATE NOCASE',(ac,)).fetchall()
  if children:body+='<tr id="children"><th>Children</th><td><details><summary>'+str(len(children))+' child cell lines</summary>'+''.join('<p><a href="/'+c+'">'+esc(n)+' ('+c+')</a></p>' for c,n in children)+'</details></td></tr>'
  body+='</tbody></table><h2 id="references">References</h2>'
  for ref, in db.execute('SELECT DISTINCT r.raw FROM cellref c JOIN ref_alias a ON a.name=c.ref JOIN reference r ON r.id=a.id WHERE c.ac=? ORDER BY r.id',(ac,)):
   f=fields(ref);authors=f.get('RA',[])+f.get('RG',[]);body+='<article class="reference"><p>'+linkify('; '.join(re.sub(r'PubMed=(\d+)',r'https://pubmed.ncbi.nlm.nih.gov/\1/',x) if x.startswith('PubMed=') else re.sub(r'DOI=(.+)',r'https://doi.org/\1',x) for x in re.split(r';\s+(?=[A-Za-z]+=)',' '.join(f.get('RX',[])).rstrip(';'))))+'</p><p>'+esc('; '.join(authors[:10]))
   if len(authors)>10:body+='</p><details><summary>Show all '+str(len(authors))+' authors</summary>'+esc('; '.join(authors))+'</details><p>'
   body+='</p><p><strong>'+esc(' '.join(f.get('RT',[])))+'</strong></p><p>'+esc(' '.join(f.get('RL',[])))+'</p></article>'
  body+='<details><summary>Complete original record</summary><pre>'+esc(raw)+'</pre></details>'
  self.send(200,page('Cellosaurus '+r[0]+' ('+ac+')',body))
 def proxy(self,path,query,post):
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<0 or length>16*1024**2:self.json(413,{'error':'Request exceeds the explicit 16 MiB upload limit'});return
   body=self.rfile.read(length) if post else None
   req=urllib.request.Request(CLASTR+path+('?' + query if query else ''),data=body,headers={'Content-Type':self.headers.get('Content-Type','application/json')},method='POST' if post else 'GET')
   try:r=urllib.request.urlopen(req,timeout=120)
   except urllib.error.HTTPError as e:r=e
   with r:
    b=r.read();status=r.status
    if status>=400:self.json(status,{'error':'CLASTR rejected the request' if status<500 else 'CLASTR query failed'});return
    self.send(status,b,r.headers.get('Content-Type','application/json'),{k:r.headers[k] for k in ['Content-Disposition'] if r.headers.get(k)})
  except Exception:self.json(503,{'error':'CLASTR is not ready; no partial result is returned'})
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
