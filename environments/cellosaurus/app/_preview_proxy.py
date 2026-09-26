"""Loopback-published preview bridge. Website remains on an internal network."""
import http.server,os,urllib.request,urllib.error
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
OPENER=urllib.request.build_opener(NoRedirect)
UPSTREAM=os.environ['UPSTREAM'].rstrip('/')
class Proxy(http.server.BaseHTTPRequestHandler):
 def do_GET(self):self.forward()
 def do_POST(self):self.forward()
 def do_HEAD(self):self.forward()
 def forward(self):
  if not self.path.startswith('/') or self.path.startswith('//'):
   self.send_error(400);return
  body=self.rfile.read(int(self.headers.get('Content-Length',0))) if self.command=='POST' else None
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','transfer-encoding')}
  req=urllib.request.Request(UPSTREAM+self.path,data=body,headers=headers,method=self.command)
  started=False
  try:
   try:r=OPENER.open(req,timeout=120)
   except urllib.error.HTTPError as e:r=e
   with r:
    self.send_response(r.status)
    for k,v in r.headers.items():
     if k.lower() not in ('connection','transfer-encoding'):self.send_header(k,v)
    # HTTP/1.0 close framing also works when the upstream is chunked or has no length.
    self.send_header('Connection','close');self.end_headers();self.close_connection=True;started=True
    if self.command!='HEAD':
     while True:
      chunk=r.read(65536)
      if not chunk:break
      self.wfile.write(chunk)
  except (BrokenPipeError,ConnectionResetError):self.close_connection=True
  except (OSError,ValueError):
   self.close_connection=True
   if not started:self.send_error(502)
http.server.ThreadingHTTPServer(('0.0.0.0',8080),Proxy).serve_forever()
