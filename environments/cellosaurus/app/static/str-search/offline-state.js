/* Local URL state, explicit offline adaptation. Uploaded file content is never serialized. */
(function(){
 if(typeof search!=='function')return;
 let restoring=false,ready=false,uploaded=false;
 const oldReset=reset,oldSwitch=switchSpecies,oldParse=parseURLVariables,oldSearch=search,oldExample=example;
 function invalidate(){cancelPending();jsonResponse=undefined;$('#results').hide();$('#table-results').empty();$('html').removeClass('waiting');}
 function snapshot(searched=false){const controls={};document.querySelectorAll('input[id],select[id]').forEach(e=>{if(e.type==='file'||e.id.startsWith('import-')||e.id.startsWith('export-')||(uploaded&&(e.id.startsWith('input-')||e.id==='description')))return;controls[e.id]={v:e.value,c:e.checked,d:e.disabled};});return {species:speciesNames[species],controls,sort:table.sortState,searched:searched&&!uploaded};}
 function persist(searched=false){if(restoring||!ready)return;const u=new URL(location);u.search='';u.searchParams.set('_state',JSON.stringify(snapshot(searched)));if(u.href!==location.href)history.pushState(null,'',u);}
 function apply(){const raw=new URL(location).searchParams.get('_state');if(!raw)return false;let state;try{state=JSON.parse(raw);}catch(e){return false;}if(!['human','mouse','dog'].includes(state.species))return false;restoring=true;uploaded=false;oldReset();oldSwitch(state.species);table.sortState=state.sort||null;for(const [id,v] of Object.entries(state.controls||{})){const e=document.getElementById(id);if(v&&typeof v==='object'&&e&&['INPUT','SELECT'].includes(e.tagName)&&e.type!=='file'){e.value=String(v.v);e.checked=!!v.c;e.disabled=!!v.d;}}restoring=false;if(state.searched)oldSearch();return true;}
 parseURLVariables=function(){if(!apply()){restoring=true;oldParse();restoring=false;}ready=true;};
 reset=function(){table.sortState=null;uploaded=false;invalidate();jsonInput=undefined;oldReset();if(ready&&!restoring)history.pushState(null,'',location.pathname);};
 switchSpecies=function(name){invalidate();if(species!==speciesNames[name]){jsonInput=undefined;uploaded=false;$('#batch').prop('disabled',true);$('#samples,#import-help').empty();}oldSwitch(name);if(ready)persist(false);};
 example=function(){uploaded=false;invalidate();oldExample();persist(false);};
 const oldRead=importFile.read;importFile.read=function(files){invalidate();jsonInput=[];uploaded=true;persist(false);oldRead.call(importFile,files);};
 const oldLoad=importFile.load;importFile.load=function(value){invalidate();oldLoad.call(importFile,value);persist(false);};
 search=function(){persist(true);oldSearch();};
 $(function(){document.addEventListener('clastr-sort',()=>persist(!!jsonResponse));document.addEventListener('change',e=>{if(e.target.matches('input,select')&&e.target.type!=='file'&&!/^(import-|export-)/.test(e.target.id)){invalidate();persist(false);}});window.addEventListener('popstate',()=>{invalidate();if(!apply()){restoring=true;oldReset();oldParse();restoring=false;}});window.addEventListener('pagehide',invalidate);window.addEventListener('pageshow',e=>{if(e.persisted)apply();});});
})();

document.addEventListener('click',event=>{
 const a=event.target.closest('a[href]');if(!a)return;
 const u=new URL(a.href,location.href);if(!['http:','https:'].includes(u.protocol)||u.origin===location.origin)return;
 event.preventDefault();
 const target=u.hostname==='www.cellosaurus.org'?u.pathname+u.search:(u.hostname==='web.expasy.org'&&u.pathname.startsWith('/cellosaurus/')?'/'+u.pathname.slice('/cellosaurus/'.length)+u.search:'/outside?url='+encodeURIComponent(u.href));
 if(a.target==='_blank')window.open(target,'_blank','noopener');else location.assign(target);
},true);
