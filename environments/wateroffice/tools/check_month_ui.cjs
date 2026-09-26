const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),assert=require('assert');
const out=process.env.WATEROFFICE_OUTPUT || '/tmp/wateroffice-month-ui';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/opt/chrome-linux64/chrome',headless:true,chromiumSandbox:true});
 const results=[];
 for(const [width,height] of [[1440,1000],[1280,800],[390,844]]){
  const context=await browser.newContext({viewport:{width,height},acceptDownloads:true});const page=await context.newPage();
  const errors=[],external=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(process.env.WATEROFFICE_ORIGIN || 'http://wateroffice-web:8080').origin)external.push(r.url())});
  const base=process.env.WATEROFFICE_ORIGIN || 'http://wateroffice-web:8080';
  async function go(url){await page.goto(base+url,{waitUntil:'domcontentloaded'});await page.waitForTimeout(1500);const agree=page.locator('input[value="I Agree"]');if(await agree.count()){await agree.click();await page.waitForLoadState('domcontentloaded');await page.waitForTimeout(1500)}}
  async function test(name,fn){if(process.env.TESTS&&!process.env.TESTS.split(',').includes(name))return;try{const prev=errors.length;await fn();assert.equal(errors.length,prev,errors.slice(prev).join(';'));results.push({name,width,height,pass:true})}catch(e){results.push({name,width,height,pass:false,error:String(e)})}await page.screenshot({path:`${out}/${width}-${name}.png`,fullPage:false});fs.writeFileSync(out+'/results.json',JSON.stringify({results,external},null,2));console.log(results.at(-1))}
  await test('month-table',async()=>{await go('/report/real_time_e.html?stn=05AB047&mode=Table&prm1=46&prm2=-1&startDate=2026-08-26&endDate=2026-09-25');assert.equal(await page.locator('#start-date').inputValue(),'2026-08-26');assert.equal(await page.locator('table.wb-tables thead th').first().innerText(),'Date (MST)');const table=page.locator('table.wb-tables').first();assert.equal(await table.locator('thead th').count(),5);assert((await table.innerText()).includes('Provisional'));assert(await page.locator('.dataTables_wrapper').count());const info=await page.locator('.dataTables_info').first().innerText();assert(!info.includes('of 0'));});
  await test('month-graph',async()=>{await go('/report/real_time_e.html?stn=05AB047&mode=Graph&prm1=46&prm2=47&startDate=2026-08-26&endDate=2026-09-25');await page.locator('canvas#graph').waitFor();await page.waitForTimeout(1000);assert(await page.locator('canvas#graph').evaluate(c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)));});
  await test('delayed-old-response',async()=>{
   await go('/report/real_time_e.html?stn=05AB047&mode=Graph&prm1=46&prm2=-1&startDate=2026-08-27&endDate=2026-08-27');await page.locator('canvas#graph').waitFor();
   let release,entered;const delay=new Promise(r=>release=r),arrival=new Promise(r=>entered=r);
   const pattern='**/services/real_time_graph/json/inline?**';
   await page.route(pattern,async route=>{if(new URL(route.request().url()).searchParams.get('param1')==='3'){entered();await delay;await route.fulfill({status:400,contentType:'text/plain',body:'Delayed obsolete error'})}else await route.continue()});
   try{await page.locator('#y1-type').selectOption('3');await Promise.race([arrival,new Promise((_,reject)=>setTimeout(()=>reject(Error('Old request did not start')),5000))]);
    const latest=page.waitForResponse(r=>r.url().includes('/services/real_time_graph/json/inline')&&new URL(r.url()).searchParams.get('param1')==='47');await page.locator('#y1-type').selectOption('47');assert.equal((await latest).status(),200);release();await page.waitForTimeout(1200);
    assert.equal(await page.locator('#offline-query-error').count(),0);assert.equal(await page.locator('#y1-type').inputValue(),'47');assert.equal(new URL(page.url()).searchParams.get('prm1'),'47');assert(await page.locator('canvas#graph').evaluate(c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)));
   }finally{release();await page.unroute(pattern)}
  });
  await test('daily-grade',async()=>{await go('/report/real_time_e.html?stn=05PE031&mode=Table&prm1=3&prm2=-1&startDate=2026-09-25&endDate=2026-09-25');assert.equal(await page.locator('table.wb-tables thead th').count(),2);const res=await context.request.get(base+'/services/real_time_graph/json/inline?station=05PE031&param1=3&param2=-1&start_date=2026-09-25&end_date=2026-09-25');assert.equal(res.status(),200);const d=await res.json();assert(d['3'].provisional.some(r=>r[4]==='PARTIAL DAY'));});
  await test('empty-table',async()=>{await go('/report/real_time_e.html?stn=01BL003&mode=Table&prm1=46&prm2=-1&startDate=2026-08-26&endDate=2026-09-25');assert((await page.locator('main').innerText()).includes('No data available for the selected time period.'));assert.equal(await page.locator('table.wb-tables').count(),0);});
  await test('download-month',async()=>{await go('/report/real_time_e.html?stn=05AB047&mode=Table&prm1=46&prm2=-1&startDate=2026-08-26&endDate=2026-09-25');await page.locator('a[href^="/download/index_e.html"]').first().click();await page.waitForLoadState('domcontentloaded');const links=await page.locator('a[href^="/download/report_e.html"]').evaluateAll(es=>es.map(e=>e.href));assert(links.length);for(const href of links){const u=new URL(href);assert.equal(u.searchParams.get('startDate'),'2026-08-26');assert.equal(u.searchParams.get('endDate'),'2026-09-25');}});
  await test('quick-graph-intervals',async()=>{
   await go('/my_station_list/quick_graph_list/new_e.html');await page.locator('#list-name').fill('Monthly graph check');await page.locator('input[value=Save]').click();await page.waitForLoadState('domcontentloaded');
   await go('/my_station_list/quick_graph_list/parameters_e.html?id=first&station_number%5B%5D=08GA043');await page.locator('input[value="46"]').check();await page.locator('input[value=Save]').click();await page.waitForLoadState('domcontentloaded');
   await go('/my_station_list/index_e.html');await page.locator('.quick-graph canvas').first().waitFor();
   for(const [days,start] of [['14','2026-09-11'],['28','2026-08-28']]){
    await page.locator('#days').selectOption(days);const response=page.waitForResponse(r=>r.url().includes('/services/real_time_graph/json/inline')&&new URL(r.url()).searchParams.get('start_date')===start);await page.locator('input[value=Go]').click();assert.equal((await response).status(),200);await page.waitForLoadState('domcontentloaded');await page.locator('.quick-graph canvas').first().waitFor();assert.equal(new URL(page.url()).searchParams.get('days'),days);assert.equal(await page.locator('section[data-start-date]').first().getAttribute('data-start-date'),start);
    const link=await page.locator('section[data-start-date] a').first().getAttribute('href');assert.equal(new URL(link,base).searchParams.get('startDate'),start);
   }
   await page.reload({waitUntil:'domcontentloaded'});assert.equal(await page.locator('#days').inputValue(),'28');
  });
  await test('responsive-controls',async()=>{await go('/search/real_time_e.html');assert(await page.locator('main input').count());const bad=await page.locator('main input, main select, main button').evaluateAll(es=>es.filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&(r.left<0||r.right>innerWidth+2)}).map(e=>e.id||e.name));assert.deepEqual(bad,[]);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));});
  assert.equal(external.length,0,JSON.stringify(external));await context.close();
 }
 await browser.close();process.exitCode=results.some(x=>!x.pass)?1:0;
})();
