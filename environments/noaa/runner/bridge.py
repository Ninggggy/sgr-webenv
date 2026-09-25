"""Structured browser-only RPC over a container-local Unix socket. No model code execution."""
import json,sys,os,socket,base64
from pathlib import Path
from urllib.parse import urlsplit
SOCKET="/tmp/noaa-browser.sock";ORIGIN="http://noaa-web:8080";OUTPUT=Path("/tmp/output")
def allowed(url):
 u=urlsplit(url)
 return u.scheme=="http" and u.hostname=="noaa-web" and u.port==8080 and not u.username and not u.password

def main():
 from playwright.sync_api import sync_playwright
 OUTPUT.mkdir(exist_ok=True);Path("/tmp/home").mkdir(exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path="/opt/chrome-linux64/chrome",chromium_sandbox=True,args=["--disable-dev-shm-usage"])
  context=browser.new_context(viewport={"width":1440,"height":1000},accept_downloads=True,service_workers="block")
  blocked=[];downloads={};counter=0
  def route(r):
   if allowed(r.request.url):r.continue_()
   else:blocked.append(r.request.url);r.abort("blockedbyclient")
  context.route("**/*",route);context.route_web_socket("**/*",lambda ws:ws.close())
  context.tracing.start(screenshots=True,snapshots=True,sources=False)
  page=context.new_page();page.set_default_timeout(15000)
  def on_download(d):
   key=f"download-{len(downloads)+1}";path=OUTPUT/key;d.save_as(path);downloads[key]={"path":str(path),"name":d.suggested_filename}
  page.on("download",on_download)
  server=socket.socket(socket.AF_UNIX);server.bind(SOCKET);os.chmod(SOCKET,0o600);server.listen(2)
  print("Browser ready",flush=True)
  while True:
   conn,_=server.accept()
   with conn:
    f=conn.makefile("r");line=f.readline(65537)
    try:
     if len(line)>65536:raise ValueError("Request too large")
     req=json.loads(line);action=req.get("action");selector=req.get("selector","")
     if not isinstance(selector,str) or len(selector)>500:raise ValueError("Invalid selector")
     if action=="goto":
      url=req["url"]
      if url.startswith("/"):url=ORIGIN+url
      if not allowed(url):raise ValueError("Only the local NOAA website is allowed")
      page.goto(url,wait_until="networkidle")
     elif action=="select":page.locator(selector).select_option(str(req["value"]))
     elif action=="click":page.locator(selector).click();page.wait_for_timeout(500)
     elif action=="fill":page.locator(selector).fill(str(req["value"])[:1000])
     elif action=="check":page.locator(selector).set_checked(bool(req["value"]))
     elif action=="hover":page.locator(selector).hover()
     elif action=="scroll":page.mouse.wheel(0,max(-2000,min(2000,int(req.get("y",600)))))
     elif action=="back":page.go_back(wait_until="networkidle")
     elif action=="reload":page.reload(wait_until="networkidle")
     elif action=="observe":pass
     elif action=="download":
      with page.expect_download() as item:page.locator(selector).click()
      d=item.value;key=f"download-{len(downloads)+1}";path=OUTPUT/key;d.save_as(path);downloads[key]={"path":str(path),"name":d.suggested_filename}
     elif action=="read_download":
      item=downloads[req["id"]];b=Path(item["path"]).read_bytes()
      if len(b)>1000000:raise ValueError("Download exceeds tool read limit")
      conn.sendall((json.dumps({"name":item["name"],"text":b.decode("utf-8")})+"\n").encode());continue
     elif action=="archive":context.tracing.stop(path=str(OUTPUT/"trace.zip"));context.tracing.start(screenshots=True,snapshots=True)
     else:raise ValueError("Unknown browser action")
     counter+=1;png=page.screenshot(path=str(OUTPUT/f"step-{counter:04d}.png"))
     result={"url":page.url,"text":page.locator("body").inner_text()[:30000],"screenshot":base64.b64encode(png).decode(),"downloads":{k:v["name"] for k,v in downloads.items()},"blocked":blocked[-20:]}
     with (OUTPUT/"operations.jsonl").open("a") as log:log.write(json.dumps({"request":req,"url":page.url,"step":counter})+"\n")
     conn.sendall((json.dumps(result)+"\n").encode())
    except Exception as e:conn.sendall((json.dumps({"error":str(e)})+"\n").encode())

if __name__=="__main__":
 if "--call" in sys.argv:
  s=socket.socket(socket.AF_UNIX);s.connect(SOCKET);s.sendall(sys.stdin.buffer.readline(65537));f=s.makefile("r");print(f.readline());s.close()
 else:main()
