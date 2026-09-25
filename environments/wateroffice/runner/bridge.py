"""Browser-only RPC. Async event handling keeps blocked WebSockets from stalling navigation."""
import asyncio,json,sys,os,socket,base64
from pathlib import Path
from urllib.parse import urlsplit
SOCKET='/tmp/wateroffice-browser.sock';ORIGIN='http://wateroffice-web:8080';OUTPUT=Path('/tmp/output')
def allowed(url):
 u=urlsplit(url)
 return u.scheme=='http' and u.hostname=='wateroffice-web' and u.port==8080 and not u.username and not u.password

async def main():
 from playwright.async_api import async_playwright
 OUTPUT.mkdir(exist_ok=True);Path('/tmp/home').mkdir(exist_ok=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/opt/chrome-linux64/chrome',chromium_sandbox=True,args=['--disable-dev-shm-usage'])
  blocked=[];downloads={};download_tasks=[];download_counter=0;counter=0
  async def route(r):
   if allowed(r.request.url):await r.continue_()
   else:blocked.append(r.request.url);await r.abort('blockedbyclient')
  async def block_socket(ws):
   blocked.append(ws.url);await ws.close(code=1008,reason='WebSockets are disabled in the offline environment')
  async def persist_download(d,key):
   path=OUTPUT/key;await d.save_as(path);downloads[key]={'path':str(path),'name':d.suggested_filename}
  def on_download(d):
   nonlocal download_counter
   download_counter+=1;download_tasks.append(asyncio.create_task(persist_download(d,f'download-{download_counter}')))
  async def setup():
   context=await browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True,service_workers='block')
   await context.route('**/*',route);await context.route_web_socket('**/*',block_socket)
   await context.tracing.start(screenshots=True,snapshots=True,sources=False)
   page=await context.new_page();page.set_default_timeout(15000);page.on('download',on_download)
   return context,page
  context,page=await setup();lock=asyncio.Lock()
  async def execute(req):
   nonlocal context,page,counter,download_counter
   action=req.get('action');selector=req.get('selector','')
   if not isinstance(selector,str) or len(selector)>500:raise ValueError('Invalid selector')
   if action=='goto':
    url=req['url'];parsed=urlsplit(url)
    if parsed.scheme in ('http','https') and parsed.hostname=='wateroffice.ec.gc.ca' and not parsed.username and not parsed.password and parsed.port in (None,80,443):url=ORIGIN+(parsed.path or '/')+('?' +parsed.query if parsed.query else '')+('#'+parsed.fragment if parsed.fragment else '')
    elif url.startswith('/') and not url.startswith('//'):url=ORIGIN+url
    if not allowed(url):raise ValueError('Only the local Wateroffice website is allowed')
    await page.goto(url,wait_until='networkidle')
   elif action=='select':await page.locator(selector).select_option(str(req['value']))
   elif action=='click':await page.locator(selector).click();await page.wait_for_timeout(500)
   elif action=='fill':await page.locator(selector).fill(str(req['value'])[:1000])
   elif action=='check':await page.locator(selector).set_checked(bool(req['value']))
   elif action=='press':await page.locator(selector).press(str(req['key'])[:50]);await page.wait_for_timeout(500)
   elif action=='tabs':pass
   elif action=='new_tab':page=await context.new_page();page.set_default_timeout(15000);page.on('download',on_download)
   elif action=='switch_tab':page=context.pages[int(req['index'])]
   elif action=='close_tab':
    if len(context.pages)<2:raise ValueError('Cannot close the last tab')
    await page.close();page=context.pages[-1]
   elif action=='hover':await page.locator(selector).hover()
   elif action=='scroll':await page.mouse.wheel(max(-2000,min(2000,int(req.get('x',0)))),max(-2000,min(2000,int(req.get('y',600)))))
   elif action=='back':await page.go_back(wait_until='networkidle')
   elif action=='reload':await page.reload(wait_until='networkidle')
   elif action=='observe':pass
   elif action=='download':
    async with page.expect_download() as item:await page.locator(selector).click()
    await item.value
   elif action=='read_download':
    item=downloads[req['id']];path=Path(item['path']);offset=int(req.get('offset',0));limit=int(req.get('limit',65536))
    if offset<0 or not 1<=limit<=262144:raise ValueError('Invalid read range')
    with path.open('rb') as src:src.seek(offset);b=src.read(limit)
    result={'name':item['name'],'offset':offset,'next_offset':offset+len(b),'size':path.stat().st_size,'eof':offset+len(b)>=path.stat().st_size,'base64':base64.b64encode(b).decode()}
    try:result['text']=b.decode('utf-8')
    except UnicodeDecodeError:pass
    return result
   elif action=='forward':await page.go_forward(wait_until='networkidle')
   elif action=='reset':
    if download_tasks:await asyncio.gather(*download_tasks);download_tasks.clear()
    await context.close()
    for child in OUTPUT.iterdir():
     if child.is_file():child.unlink()
    downloads.clear();blocked.clear();counter=0;download_counter=0;context,page=await setup()
   elif action=='archive':await context.tracing.stop(path=str(OUTPUT/'trace.zip'));await context.tracing.start(screenshots=True,snapshots=True,sources=False)
   else:raise ValueError('Unknown browser action')
   await asyncio.sleep(0)
   if download_tasks:await asyncio.gather(*download_tasks);download_tasks.clear()
   counter+=1;png=await page.screenshot(path=str(OUTPUT/f'step-{counter:04d}.png'))
   result={'tabs':[p.url for p in context.pages],'url':page.url,'text':(await page.locator('body').inner_text())[:30000],'screenshot':base64.b64encode(png).decode(),'downloads':{k:v['name'] for k,v in downloads.items()},'blocked':blocked[-20:]}
   with (OUTPUT/'operations.jsonl').open('a') as log:log.write(json.dumps({'request':req,'url':page.url,'step':counter})+'\n')
   return result
  async def client(reader,writer):
   try:
    line=await reader.readline()
    if len(line)>65536:raise ValueError('Request too large')
    req=json.loads(line)
    async with lock:result=await execute(req)
   except Exception as e:result={'error':str(e)}
   try:writer.write((json.dumps(result)+'\n').encode());await writer.drain()
   finally:writer.close();await writer.wait_closed()
  server=await asyncio.start_unix_server(client,path=SOCKET,limit=65536,backlog=2);os.chmod(SOCKET,0o600)
  print('Browser ready',flush=True)
  async with server:await server.serve_forever()

if __name__=='__main__':
 if '--call' in sys.argv:
  s=socket.socket(socket.AF_UNIX);s.connect(SOCKET);s.sendall(sys.stdin.buffer.readline(65537));f=s.makefile('r');print(f.readline());s.close()
 else:asyncio.run(main())
