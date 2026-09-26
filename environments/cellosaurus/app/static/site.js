// Native navigation owns requests/history. No stale asynchronous results are rendered.
document.querySelectorAll('form').forEach(f=>f.addEventListener('reset',()=>{setTimeout(()=>{const q=f.querySelector('[name=query]');if(q)q.value='';},0);}));

// Fixed original-site paths only; external destinations display a scope notice.
document.addEventListener('click',event=>{
 const a=event.target.closest('a[href]');if(!a)return;const u=new URL(a.href,location.href);
 if(!['http:','https:'].includes(u.protocol)||u.origin===location.origin)return;
 event.preventDefault();let target='/outside?url='+encodeURIComponent(u.href);
 if(u.hostname==='www.cellosaurus.org')target=u.pathname+u.search;
 else if(u.hostname==='ftp.expasy.org'&&u.pathname.startsWith('/databases/cellosaurus/'))target=u.pathname;
 else if(u.hostname==='zenodo.org'&&/^\/records\/(16878225|18418061)(\/files\/cellosaurus_name_conflicts\.txt)?$/.test(u.pathname))target=u.pathname;
 if(a.target==='_blank')window.open(target,'_blank','noopener');else location.assign(target);
},true);
