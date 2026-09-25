import csv,io,json,mimetypes,pathlib,secrets,sqlite3,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlsplit
from query import query,metadata,check_version,APP_VERSION,DATA_VERSION
ROOT=pathlib.Path(__file__).resolve().parent;PUBLIC=ROOT/'public';STATE=pathlib.Path('/tmp/wonder-state.sqlite');LOCK=threading.Lock()
with sqlite3.connect(STATE) as c:c.execute('CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY, session TEXT, kind TEXT, body TEXT, created REAL)')
def put(session,kind,body):
 key=secrets.token_urlsafe(18)
 with LOCK,sqlite3.connect(STATE) as c:c.execute('INSERT INTO objects VALUES (?,?,?,?,?)',(key,session,kind,json.dumps(body),time.time()))
 return key
def get(session,key,kind):
 with sqlite3.connect(STATE) as c:r=c.execute('SELECT body FROM objects WHERE id=? AND session=? AND kind=?',(key,session,kind)).fetchone()
 if not r:raise LookupError('This saved item is unavailable in the current session. A reset clears all saved state.')
 body=json.loads(r[0]);check_version(body['query']);return body
class Handler(BaseHTTPRequestHandler):
 def session(self):
  cookie=SimpleCookie()
  try:cookie.load(self.headers.get('Cookie',''))
  except Exception:pass
  s=cookie.get('wonder_session');value=s.value if s else ''
  if not value or len(value)>80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in value):value=secrets.token_urlsafe(24);self.new_session=value
  return value
 def send(self,body,status=200,content_type='application/json',filename=None):
  if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode()
  elif isinstance(body,str):body=body.encode()
  self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
  if getattr(self,'new_session',None):self.send_header('Set-Cookie',f'wonder_session={self.new_session}; HttpOnly; SameSite=Strict; Path=/')
  if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
  self.end_headers();self.wfile.write(body)
 def do_GET(self):
  self.new_session=None;s=self.session();path=urlsplit(self.path).path
  try:
   if path=='/health':return self.send({'ok':True,'version':APP_VERSION,'data_version':DATA_VERSION,'datasets':metadata()['datasets']})
   if path=='/api/metadata':return self.send(metadata())
   if path.startswith('/api/results/'):return self.send(get(s,path.rsplit('/',1)[-1],'result'))
   if path.startswith('/api/saves/'):return self.send(get(s,path.rsplit('/',1)[-1],'save'))
   if path.startswith('/export/'):
    r=get(s,path.rsplit('/',1)[-1],'result');buf=io.StringIO();w=csv.writer(buf);g=r['query']['groups'];m=r['query']['measures']
    w.writerow([x for k in g for x in [k+' code',k]]+m+[x+' status' for x in m]+(['Rank'] if 'leading' in g else []))
    for row in r.get('display_rows',r['rows']):
     w.writerow([x for k in g for x in [row['codes'].get(k,''),row['labels'].get(k,'')]]+[row['values'][k] if row['values'][k] is not None else row['status'][k] for k in m]+[row['status'][k] for k in m]+([row['rank']] if 'leading' in g else []))
    if r.get('totals_enabled',True):w.writerow(['Total']+['']*(2*len(g)-1)+[r['total']['values'][k] if r['total']['values'][k] is not None else r['total']['status'][k] for k in m]+[r['total']['status'][k] for k in m])
    w.writerow([]);w.writerow(['Query Criteria',json.dumps(r['query'],sort_keys=True)]);w.writerow(['Units',json.dumps(r['units'])])
    for note in r['notes']:w.writerow(['Note',note])
    return self.send(buf.getvalue(),content_type='text/csv; charset=utf-8',filename='wonder-results.csv')
   if path in ['/','/natality-expanded-current.html','/lbd-current-expanded.html','/request','/help'] or path.startswith('/results/') or path.startswith('/saved/'):
    return self.send((PUBLIC/'index.html').read_bytes(),content_type='text/html; charset=utf-8')
   assets={'/app.js','/style.css','/docs/natality-help.txt','/docs/lbd-help.txt','/docs/home-births-2020.pdf','/docs/infant-mortality-2021.pdf'}
   if path in assets:
    f=PUBLIC/path.lstrip('/');return self.send(f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   self.send({'error':'Not found'},404)
  except ValueError as e:self.send({'error':str(e)},409)
  except LookupError as e:self.send({'error':str(e)},404)
  except FileNotFoundError:self.send({'error':'Resource is unavailable'},404)
 def do_POST(self):
  self.new_session=None;s=self.session();path=urlsplit(self.path).path
  try:
   origin=self.headers.get('Origin')
   if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.send({'error':'Cross-origin request denied'},403)
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=65536:return self.send({'error':'Invalid request length'},413)
   body=json.loads(self.rfile.read(n))
   if path=='/api/query':
    r=query(body);key=put(s,'result',r);return self.send({'id':key,'result':r})
   if path=='/api/save':
    from query import validate
    if set(body)-{'query','view','display'}:raise ValueError('Unsupported save parameters')
    q=validate(body['query']);view=body.get('view','request')
    if view not in ['request','results','chart']:raise ValueError('Invalid saved view')
    display=body.get('display',{})
    if not isinstance(display,dict) or set(display)-{'chart_type','chart_measure'}:raise ValueError('Invalid display settings')
    if display.get('chart_type','Bar') not in ['Bar','Line'] or display.get('chart_measure',q['measures'][0]) not in q['measures']:raise ValueError('Unsupported chart display setting')
    key=put(s,'save',{'query':q,'view':view,'display':display});return self.send({'url':'/saved/'+key})
   if path=='/api/reset':
    with LOCK,sqlite3.connect(STATE) as c:c.execute('DELETE FROM objects WHERE session=?',(s,))
    self.new_session=secrets.token_urlsafe(24);return self.send({'reset':True})
   self.send({'error':'Not found'},404)
  except (ValueError,KeyError,TypeError) as e:self.send({'error':str(e)},400)
  except Exception as e:
   self.log_error('Query failed: %r',e);self.send({'error':'The local query could not be completed. Check the imported data and server log.'},500)
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
