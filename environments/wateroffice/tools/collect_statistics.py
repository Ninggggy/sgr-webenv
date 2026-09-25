import pathlib,subprocess,urllib.parse,json,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/statistics';O.mkdir(exist_ok=True)
def run(case):
 name,change=case;q={'station':'08EE004','data_type':'daily','first_year':'1948','last_year':'1948','start_year':'1946','end_year':'1950','start_month':'01','end_month':'12','results_type':'historical','parameter_type':'flow',**{k:'1' for k in ['maximum','minimum','mean','median','upper','lower']},**change};url='https://wateroffice.ec.gc.ca/services/historical_graph/json/inline?'+urllib.parse.urlencode(q)
 b=subprocess.check_output(['curl','-fLsS','--compressed','--max-time','60',url]);j=json.loads(b);(O/(name+'.json')).write_bytes(b);print(name,[(k,len(v)) for k,v in j.items()],flush=True);return {'case':name,'url':url,'query':q}
cases=[('daily-leap',{}),('daily-normal',{'first_year':'1949','last_year':'1949'}),('monthly',{'data_type':'monthly'}),('level',{'parameter_type':'level','first_year':'2020','last_year':'2020','start_year':'2011','end_year':'2025'})]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:r=list(p.map(run,cases))
(O/'manifest.json').write_text(json.dumps(r,indent=2))
