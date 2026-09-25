import pathlib,subprocess,urllib.parse,json,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/statistics-boundaries';O.mkdir(exist_ok=True)
def run(case):
 name,change=case;q={'station':'08EE004','data_type':'daily','first_year':'1948','last_year':'1948','start_year':'1946','end_year':'1950','start_month':'01','end_month':'12','results_type':'historical','parameter_type':'flow',**{k:'1' for k in ['maximum','minimum','mean','median','upper','lower']},**change};url='https://wateroffice.ec.gc.ca/services/historical_graph/json/inline?'+urllib.parse.urlencode(q)
 b=subprocess.check_output(['curl','-fLsS','--compressed','--max-time','60',url]);j=json.loads(b);(O/(name+'.json')).write_bytes(b);print(name,[(k,len(v)) for k,v in j.items()],flush=True);return {'case':name,'url':url,'query':q}
cases=[('nine-years',{'end_year':'1954'}),('ten-years',{'end_year':'1955'}),('monthly-other-period',{'data_type':'monthly','start_year':'1990','end_year':'1995'}),('two-display-years',{'last_year':'1949','end_year':'1955'})]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:r=list(p.map(run,cases))
(O/'manifest.json').write_text(json.dumps(r,indent=2))
