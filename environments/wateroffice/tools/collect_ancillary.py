import pathlib,subprocess,urllib.parse,json,concurrent.futures,re
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/ancillary';O.mkdir(exist_ok=True)
def run(case):
 name,route,q=case;url='https://wateroffice.ec.gc.ca/report/'+route+'_e.html?'+urllib.parse.urlencode(q);s=subprocess.check_output(['curl','-fLsS','--compressed','--max-time','60','-b',str(R/'author/extra-downloads/cookies.txt'),url]).decode();(O/(name+'.html')).write_text(s);print(name,re.findall(r'<h1[^>]*>(.*?)</h1>',s,re.S),flush=True);return {'name':name,'url':url}
cases=[]
for n in ['08EE004','01AD003']:
 for route in ['datum','remarks']:
  cases.append((route+'-'+n,route,{'stn':n,'mode':'Graph','type':'h2oArc','page':'historical','dataType':'Daily','parameterType':'Flow','first_year':'1948','last_year':'1948'}))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:result=list(p.map(run,cases))
(O/'manifest.json').write_text(json.dumps(result,indent=2))
