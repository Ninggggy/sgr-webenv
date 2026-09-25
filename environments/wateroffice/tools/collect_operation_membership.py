import pathlib,subprocess,urllib.parse,concurrent.futures,json,re,datetime
from html_tables import Page
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/operation-membership';O.mkdir(exist_ok=True)
def run(op):
 q={'search_type':'province','province':'all','operation_schedule':op,'start_year':'1850','end_year':'2026','parameter_type':'all'};url='https://wateroffice.ec.gc.ca/search/historical_results_e.html?'+urllib.parse.urlencode(q);p=O/(op+'.html')
 if not p.exists():subprocess.run(['curl','-fLsS','--compressed','--max-time','90',url,'-o',str(p)],check=True)
 s=p.read_text();v=Page();v.feed(s);rows=v.tables[0]['rows'][1:] if v.tables else [];ids=[x[4] for x in rows];count=int(re.search(r'Found ([\d,]+) stations',s)[1].replace(',',''))
 assert count==len(ids),(count,len(ids))
 print(op,count,flush=True);return op,{'source':url,'declared_count':count,'stations':ids,'unique_stations':len(set(ids))}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:values=dict(p.map(run,['C','S','M']))
(R/'data/operation-membership.json').write_text(json.dumps({'captured':'2026-09-25','scope':'Official nationwide historical search operation predicates; independent combinations still require validation','operations':values},indent=2))
