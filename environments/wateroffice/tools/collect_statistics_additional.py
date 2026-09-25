import pathlib,subprocess,urllib.parse,json,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/statistics-additional';O.mkdir(exist_ok=True)
def run(case):
 name,change=case;q={'station':'08EE004','data_type':'daily','first_year':'1948','last_year':'1948','start_year':'1946','end_year':'1950','start_month':'01','end_month':'12','results_type':'historical','parameter_type':'flow',**{k:'1' for k in ['maximum','minimum','mean','median','upper','lower']},**change};url='https://wateroffice.ec.gc.ca/services/historical_graph/json/inline?'+urllib.parse.urlencode(q)
 b=subprocess.check_output(['curl','-fLsS','--compressed','--retry','3','--retry-all-errors','--retry-delay','3','--max-time','90',url]);j=json.loads(b);(O/(name+'.json')).write_bytes(b);print(name,[(k,len(v)) for k,v in j.items()],flush=True);return {'case':name,'url':url,'query':q}
cases=[('monthly-level',{'parameter_type':'level','data_type':'monthly','first_year':'2020','last_year':'2020'}),('monthly-other-flow',{'station':'01AD003','data_type':'monthly','first_year':'2020','last_year':'2020'}),('monthly-other-level',{'station':'01AD003','parameter_type':'level','data_type':'monthly','first_year':'2020','last_year':'2020'}),('daily-two-years',{'start_year':'1948','end_year':'1949'}),('daily-one-year',{'start_year':'1948','end_year':'1948'})]

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as p:r=list(p.map(run,cases))
(O/'manifest.json').write_text(json.dumps(r,indent=2))
