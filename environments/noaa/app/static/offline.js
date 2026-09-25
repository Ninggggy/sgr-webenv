// Additional offline feedback; source form submission and chart/map controls are retained.
addEventListener("DOMContentLoaded",()=>{
 const form=document.querySelector("#select-form");
 if(form){const status=document.createElement("p");status.id="offline-status";status.hidden=true;form.after(status);form.addEventListener("change",()=>{status.hidden=false;status.textContent="Selections changed. Plot or a result-mode selection applies the current controls."});document.querySelector("#submit")?.addEventListener("click",()=>{status.hidden=true});document.querySelector("#return")?.addEventListener("change",()=>{status.hidden=true});}
 document.querySelectorAll("a").forEach(a=>{if(/\/(county|city|global|regional)(\/|$)|\/rankings|\/haywood/.test(a.getAttribute("href")||"")){a.classList.add("unsupported");a.title="Not supported in this offline release";}});
});

addEventListener("DOMContentLoaded",()=>{const r=document.getElementById("return");if(r){const n=document.createElement("p");n.className="rank-note";n.textContent="Rank uses a two-tailed rule inferred from NOAA observations. Exact mapping-rank compatibility is not yet complete; see data help. * marks ties.";r.after(n);}document.querySelectorAll("input[placeholder]").forEach(e=>{if(e.placeholder.includes("Search Monitoring")){e.disabled=true;e.placeholder="Offline climate explorer";}});});
