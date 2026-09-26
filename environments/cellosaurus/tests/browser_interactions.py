"""Author-only async browser acceptance. Never mounted in the evaluation browser."""
import asyncio,json,time,resource,os,traceback
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.async_api import async_playwright
O=Path(os.getenv('RESULTS_DIR','/results'));O.mkdir(exist_ok=True);out=[];start=time.monotonic();report=os.getenv('REPORT_NAME','browser-release')
def check(name,ok,**kw):
 out.append(dict(name=name,passed=bool(ok),**kw));(O/(report+'-checks.json')).write_text(json.dumps(out,indent=2));print(name,ok,kw,flush=True)
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/opt/chrome-linux64/chrome',headless=True,chromium_sandbox=True,args=['--disable-dev-shm-usage'])
  ctx=await browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True,service_workers='block')
  async def protect(route):
   if urlsplit(route.request.url).netloc=='cellosaurus-web:8080':await route.continue_()
   else:await route.abort()
  await ctx.route('**/*',protect);await ctx.route_web_socket('**/*',lambda ws:ws.close())
  page=await ctx.new_page();page.set_default_timeout(12000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base='http://cellosaurus-web:8080'
  async def goto(path='/str-search/'):
   await page.goto(base+path,wait_until='networkidle')
  async def example(species='human'):
   if not await page.locator('#input-'+species).evaluate("e=>e.classList.contains('active')"):await page.locator('#input-'+species).click()
   await page.locator('#example').click()
  async def results():
   await page.locator('#table-results tr[data-result]').first.wait_for(state='visible');await page.wait_for_timeout(450)
  async def upload(name,b):
   await page.locator('#load').click();await page.locator('#input-file').set_input_files({'name':name,'mimeType':'application/octet-stream','buffer':b});await page.wait_for_timeout(400)
  async def block(endpoint,delay=1.8):
   event=asyncio.Event();counter=[0]
   async def intercept(route):
    counter[0]+=1;response=await route.fetch()
    if counter[0]==1:event.set();await asyncio.sleep(delay)
    try:await route.fulfill(response=response)
    except Exception:pass
   pattern='**/str-search/api/'+endpoint;await page.route(pattern,intercept);return event,pattern
  async def group(name,fn):
   try:await fn()
   except Exception as e:check(name+' exception',False,error=str(e),trace=traceback.format_exc()[-1600:])
  async def uploads():
   for species,marker,value in [('human','CSF1P0','11,12'),('mouse','M1-1','10'),('dog','PEZ1','119,123')]:
    for ext,sep in [('csv',','),('tsv','\t'),('txt','\t')]:
     await goto();
     if species!='human':await page.locator('#input-'+species).click()
     data=('Sample'+sep+marker+'\n'+'sample<&='+sep+'"'+value+'"\n').encode()
     await upload('sample.'+ext,data)
     target={'human':'CSF1PO','mouse':'Mouse_STR_1-1','dog':'Dog_PEZ1'}[species]
     check(f'{species} {ext} named sample and marker',await page.locator('#description').input_value()=='sample<&=' and await page.locator('#input-'+target).input_value()==value)
     state=json.loads(parse_qs(urlsplit(page.url).query)['_state'][0]);check(f'{species} {ext} upload excluded from URL','input-'+target not in state['controls'] and 'description' not in state['controls'])
   for ext in ['xls','xlsx']:
    await goto()
    # Generate a standards-compliant workbook, with fixed independent expected cells.
    b=await page.evaluate("""ext=>{const w=XLSX.utils.book_new();XLSX.utils.book_append_sheet(w,XLSX.utils.aoa_to_sheet([['Name','THO1'],['workbook',9.3]]),'Profiles');return Array.from(new Uint8Array(XLSX.write(w,{bookType:ext==='xls'?'biff8':'xlsx',type:'array'})));}""",ext)
    await upload('profile.'+ext,bytes(b));check(ext+' workbook upload',await page.locator('#description').input_value()=='workbook' and await page.locator('#input-TH01').input_value()=='9.3')
   for name,b in [('bad.exe',b'a'),('empty.csv',b'Name,TH01\n'),('unnamed.csv',b'Name,TH01\n,9\n'),('unrecognized.csv',b'Other,TH01\ns,9\n'),('alleles.csv',b'Name,TH01\ns,not-an-allele\n'),('ragged.csv',b'Name,TH01\ns,9,extra\n'),('bad.xlsx',b'not an Excel workbook'),('no-markers.csv',b'Name,Unknown\ns,9\n')]:
    await goto();await upload(name,b);text=await page.locator('#dialog-import').inner_text();check('invalid upload '+name,await page.locator('#batch').is_disabled() and any(t in text.lower() for t in ['error','empty','invalid','compatible','supported','sample','malformed']))
   await goto();await upload('profiles.csv',b'Name,TH01\nfirst,9\nsecond,9.3\n');check('batch sample list',await page.locator('#samples a.sample').count()==2 and not await page.locator('#batch').is_disabled())
   await page.locator('#import-extension').select_option('json')
   async with page.expect_download() as d:await page.locator('#batch').click()
   download=await d.value;await download.save_as(O/'batch.json');j=json.loads((O/'batch.json').read_text());check('batch browser download two samples',len(j)==2)
  async def races():
   await goto();await example();event,pattern=await block('query');await page.locator('#search').click();await event.wait();await example('dog');await page.locator('#search').click();await results();await page.wait_for_timeout(2100)
   check('late human response cannot replace dog',await page.evaluate("jsonResponse.parameters.species === SPECIES_DOG"));await page.unroute(pattern)
   await goto();await example();event,pattern=await block('query');await page.locator('#search').click();await event.wait();await page.locator('#reset').click();await page.wait_for_timeout(2100);check('Reset rejects late query',await page.locator('#table-results tr[data-result]').count()==0 and not await page.locator('#results').is_visible());await page.unroute(pattern)
   await goto();await example();event,pattern=await block('query');await page.locator('#search').click();await event.wait();await page.goto(base+'/');await page.wait_for_timeout(2000);check('navigation rejects late query',await page.locator('h1').inner_text()=='Cellosaurus — the reference resource on cell lines');await page.unroute(pattern)
   await goto();await upload('profiles.csv',b'Name,TH01\nfirst,9\nsecond,9.3\n');event,pattern=await block('batch');downloads=[];page.on('download',lambda d:downloads.append(d));await page.locator('#batch').click();await event.wait();await page.locator('[aria-describedby="dialog-import"] .ui-dialog-titlebar-close').click();await page.locator('#reset').click();await page.wait_for_timeout(2200);check('Reset rejects late batch download',len(downloads)==0 and not await page.locator('#import-progressbar').evaluate("e=>e.classList.contains('animate')"));await page.unroute(pattern)
   await goto();await example();await page.locator('#search').click();await results();event,pattern=await block('conversion');await page.locator('#export').click();await page.locator('#export-extension').select_option('csv');before=len(downloads);await page.get_by_role('button',name='Save',exact=True).click();await event.wait();await page.locator('#reset').click();await page.wait_for_timeout(2200);check('Reset rejects late conversion download',len(downloads)==before);await page.unroute(pattern)
   for mode in ['readAsText','readAsBinaryString']:
    await goto();await page.evaluate("""mode=>{const old=FileReader.prototype[mode];FileReader.prototype[mode]=function(...args){setTimeout(()=>old.apply(this,args),1600);};}""",mode)
    if mode=='readAsText':name='slow.csv';b=b'Name,TH01\nlate,9\n'
    else:
     name='slow.xlsx';b=bytes(await page.evaluate("""()=>{const w=XLSX.utils.book_new();XLSX.utils.book_append_sheet(w,XLSX.utils.aoa_to_sheet([['Name','TH01'],['late','9']]),'P');return Array.from(new Uint8Array(XLSX.write(w,{bookType:'xlsx',type:'array'})));}"""))
    await upload(name,b);await page.locator('[aria-describedby="dialog-import"] .ui-dialog-titlebar-close').click();await page.locator('#reset').click();await page.wait_for_timeout(2000);check(mode+' callback after Reset ignored',await page.locator('#description').input_value()=='' and await page.locator('#input-TH01').input_value()=='' and await page.locator('#samples').inner_text()=='')
  async def history():
   await goto();await example();await page.locator('#search').click();await results();url=page.url;first=await page.locator('#table-results').inner_text();await page.locator('#input-dog').click();dogurl=page.url;await page.go_back();await results();check('back restores human query',await page.locator('#table-results').inner_text()==first and page.url==url);await page.go_forward();check('forward restores dog form',await page.locator('#markers-dog').is_visible() and not await page.locator('#results').is_visible() and page.url==dogurl)
   await page.go_back();await results();tab=await ctx.new_page();await tab.goto(url,wait_until='networkidle');await tab.locator('#table-results tr[data-result]').first.wait_for(state='visible');check('copied URL restores complete query',await tab.locator('#table-results').inner_text()==first);await tab.locator('#reset').click();check('other tab reset isolated',await page.locator('#table-results').inner_text()==first);await tab.close()
   await page.locator('#reset').click();await page.locator('#input-TH01').fill('99');await page.locator('#filter-markers').select_option('0');await page.locator('#filter-score').select_option('100');await page.locator('#search').click();await page.wait_for_timeout(1200);check('empty result clears old rows',await page.locator('#table-results tr[data-result]').count()==0 and not await page.locator('#results').is_visible())
  async def details():
   for ac,sp,marker,val in [('CVCL_2257','human','CSF1PO','10,12'),('CVCL_3984','mouse','Mouse_STR_1-1','10'),('CVCL_WS63','dog','Dog_PEZ1','119,123')]:
    await goto('/'+ac);await page.locator('.clastr-prefill').click();await page.wait_for_load_state('networkidle');check(ac+' STR navigation',await page.locator('#markers-'+sp).is_visible() and await page.locator('#input-'+marker).input_value()==val)
   await goto('/str-search/?name=A%26B%3DC%2BD&TH01=9.3');check('encoded name preserved',await page.locator('#description').input_value()=='A&B=C+D' and await page.locator('#input-TH01').input_value()=='9.3')
   for ac in ['CVCL_0222','CVCL_0048']:
    await goto('/'+ac);check('deleted record '+ac,'This entry was deleted' in await page.locator('main').inner_text())
   await goto('/CVCL_0030');await page.screenshot(path=O/'detail.png',full_page=True);authors=page.locator('.reference details');check('reference authors expandable',await authors.count()>0)
   if await authors.count():await authors.first.locator('summary').click();check('author expansion functional',await authors.first.get_attribute('open') is not None)
   await page.locator('#ST summary').click();check('STR collapses',await page.locator('#ST details').get_attribute('open') is None)
   await goto('/browse_by_group');await page.locator('main li a').first.click();check('group navigation',await page.locator('.results tbody tr').count()>0);await page.go_back();check('group history',urlsplit(page.url).path=='/browse_by_group')
   await goto('/browse_by_panel');await page.locator('main li a').first.click();check('panel navigation',await page.locator('.results tbody tr').count()>0)
   await goto('/description.html');check('description archived content','Detailed content description' in await page.locator('main').inner_text())
   for record,version in [('16878225','53'),('18418061','54')]:
    await goto('/records/'+record)
    async with page.expect_download() as d:await page.locator('main a[download]').click()
    download=await d.value;await download.save_as(O/('r'+version+'_name_conflicts.txt'));check('historical archive '+version,('Version: '+version+'.0') in (O/('r'+version+'_name_conflicts.txt')).read_text())
   await goto('/');await page.screenshot(path=O/'home.png',full_page=True);await goto();await example();await page.locator('#search').click();await results();await page.screenshot(path=O/'clastr.png',full_page=True)
  async def links():
   await goto();await example();await page.locator('#search').click();await results()
   for prefix in ['https://web.expasy.org/cellosaurus/','https://www.cellosaurus.org/']:
    link=page.locator('#table-results a[href^="'+prefix+'"]').first;ac=await link.inner_text()
    async with ctx.expect_page() as opened:await link.click()
    tab=await opened.value;await tab.wait_for_load_state('networkidle');check('CLASTR result detail popup '+prefix,urlsplit(tab.url).netloc=='cellosaurus-web:8080' and urlsplit(tab.url).path=='/'+ac and ac in await tab.locator('main').inner_text());await tab.close()
   await page.screenshot(path=O/'clastr-viewport.png')
  for name,fn in [('uploads',uploads),('race',races),('history',history),('detail',details),('links',links)]:
   if not os.getenv('CASE_GROUPS') or name in os.environ['CASE_GROUPS'].split(','):await group(name,fn)
  check('no browser JS exceptions',not errors,errors=errors)
  await ctx.close();await browser.close()
asyncio.run(main())
metrics={'elapsed_seconds':time.monotonic()-start,'self_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
for path in ['/sys/fs/cgroup/memory.peak','/sys/fs/cgroup/memory/memory.max_usage_in_bytes']:
 if Path(path).exists():metrics['cgroup_peak_bytes']=int(Path(path).read_text())
(O/(report+'-resources.json')).write_text(json.dumps(metrics,indent=2))
assert all(x['passed'] for x in out),[x for x in out if not x['passed']]
