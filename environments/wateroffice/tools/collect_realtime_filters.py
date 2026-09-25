"""Capture national official result sets for the original real-time filter controls."""
import pathlib,subprocess,urllib.parse,json,re,datetime
from html_tables import Page
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/realtime-filters';O.mkdir(exist_ok=True)
filters={'parameter_type':['3','6','46','47'],'regulation':['R','N'],'operation_schedule':['C','S','M'],'operating_agency':['MANITOBA TRANSPORTATION AND INFRASTRUCTURE','UNITED STATES GEOLOGICAL SURVEY','WATER SURVEY OF CANADA (DOE) (CANADA)']}
result={}
for key,values in filters.items():
 result[key]={}
 for i,value in enumerate(values):
  q={'search_type':'province','province':'all',key:value};url='https://wateroffice.ec.gc.ca/search/real_time_results_e.html?'+urllib.parse.urlencode(q);p=O/f'{key}-{i}.html'
  if not p.exists() or not re.search(r'Found ([\d,]+) stations',p.read_text()):subprocess.run(['curl','-fLsS','--compressed','--retry','3','--retry-all-errors','--retry-delay','3','--max-time','90',url,'-o',str(p)],check=True)
  s=p.read_text();page=Page();page.feed(s);count=int(re.search(r'Found ([\d,]+) stations',s)[1].replace(',',''));rows=page.tables[0]['rows'][1:] if page.tables else [];ids=[r[3] for r in rows]
  assert count==len(ids),(key,value,count,len(ids))
  result[key][value]={'source':url,'declared_count':count,'stations':ids};print(key,value,count,flush=True)
  (O/'progress.json').write_text(json.dumps(result,indent=2))
(R/'data/realtime-filter-membership.json').write_text(json.dumps({'captured':datetime.datetime.now(datetime.timezone.utc).isoformat(),'filters':result},indent=2))
