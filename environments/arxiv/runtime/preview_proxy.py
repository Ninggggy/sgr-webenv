"""Loopback preview transport. Fixed upstream; no open-proxy functionality."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith('/') or self.path.startswith('//'):
            self.send_error(400);return
        if self.headers.get('Transfer-Encoding'):
            self.send_error(400, 'Chunked request bodies are not supported');return
        try:
            length=int(self.headers.get('Content-Length','0'))
        except ValueError:
            self.send_error(400, 'Invalid Content-Length');return
        if length<0 or length>1024*1024:
            self.send_error(413);return
        body=self.rfile.read(length) if length else None
        headers={'Host':'127.0.0.1:8083'}
        for key in ('Cookie','Accept','Accept-Language','Content-Type','If-None-Match','If-Modified-Since'):
            if key in self.headers:headers[key]=self.headers[key]
        conn=HTTPConnection('preview-web',8080,timeout=60)
        try:
            conn.request(self.command,self.path,body=body,headers=headers)
            response=conn.getresponse()
            self.send_response(response.status)
            for key,value in response.getheaders():
                if key.lower() not in ('connection','transfer-encoding','server','date'):
                    self.send_header(key,value)
            self.end_headers()
            if self.command!='HEAD':
                while True:
                    data=response.read(65536)
                    if not data:break
                    self.wfile.write(data)
        except OSError:
            self.close_connection=True
        finally:conn.close()

    do_HEAD=do_GET
    do_POST=do_GET


ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
