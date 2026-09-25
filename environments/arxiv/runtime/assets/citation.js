// Local arXiv citation modal. Crossref is outside the configured offline scope.
document.addEventListener('DOMContentLoaded', () => {
 const trigger=document.getElementById('bib-cite-trigger');
 if (!trigger) return;
 const modal=document.getElementById('bib-cite-modal'),close=modal.querySelector('.bib-modal-close');
 const target=document.getElementById('bib-cite-target'),loading=document.getElementById('bib-cite-loading');
 let previous=null;
 function dismiss(){modal.hidden=true;modal.removeAttribute('aria-modal');if(previous)previous.focus();}
 close.addEventListener('click',dismiss);
 modal.addEventListener('keydown', e=>{
  if(e.key==='Escape'){e.preventDefault();dismiss();}
  if(e.key==='Tab'){
   const nodes=[...modal.querySelectorAll('button,textarea,a[href]')];
   if(e.shiftKey && document.activeElement===nodes[0]){e.preventDefault();nodes.at(-1).focus();}
   if(!e.shiftKey && document.activeElement===nodes.at(-1)){e.preventDefault();nodes[0].focus();}
  }
 });
 trigger.addEventListener('click',async()=>{
  previous=document.activeElement;loading.hidden=false;trigger.disabled=true;
  try{
   const id=document.querySelector('meta[name=citation_arxiv_id]').content;
   const result=await fetch('/bibtex/'+id);
   target.value=await result.text();
   target.setAttribute('aria-label',result.ok?'BibTeX citation':'Citation unavailable');
   const source=document.getElementById('bib-cite-source-api');source.textContent='arXiv metadata (offline)';source.href='/offline';
   modal.hidden=false;modal.setAttribute('aria-modal','true');modal.setAttribute('role','dialog');close.focus();
  }catch(e){target.value='Citation unavailable';modal.hidden=false;close.focus();}
  finally{loading.hidden=true;trigger.disabled=false;}
 });
});
