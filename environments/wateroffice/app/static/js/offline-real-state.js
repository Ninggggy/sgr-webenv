/* Local URL persistence for report controls and cross-view consistency. */
(()=>{
 const controls={prm1:'y1-type',prm2:'y2-type',startDate:'start-date',endDate:'end-date',y1Max:'y1-max',y1Min:'y1-min',y2Max:'y2-max',y2Min:'y2-min'};
 function sync(){
  const u=new URL(location.href);
  for(const [key,id] of Object.entries(controls)){const e=document.getElementById(id);if(!e)continue;if(e.value==='')u.searchParams.delete(key);else u.searchParams.set(key,e.value)}
  if(u.href!==location.href)history.pushState(null,'',u);
  document.querySelectorAll('a[href]').forEach(a=>{
   const link=new URL(a.href,location.href);if(link.origin!==location.origin)return;
   if(link.pathname==='/report/real_time_e.html'&&['Graph','Table'].includes(link.searchParams.get('mode'))){const mode=link.searchParams.get('mode');link.search=u.search;link.searchParams.set('mode',mode);a.href=link.href}
   if(link.pathname==='/download/index_e.html')for(const key of ['startDate','endDate']){if(u.searchParams.has(key))link.searchParams.set(key,u.searchParams.get(key));a.href=link.href}
  });
 }
 function init(){for(const id of Object.values(controls)){const e=document.getElementById(id);if(!e)continue;e.addEventListener('change',sync);e.addEventListener('focusout',sync);e.addEventListener('keypress',event=>{if(event.key==='Enter')sync()})}}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
 window.addEventListener('popstate',()=>location.reload());
})();
