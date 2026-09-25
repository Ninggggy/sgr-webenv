import pathlib,subprocess,urllib.parse,json
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/extreme-reports';O.mkdir(exist_ok=True);manifest=[]
jar=O/'cookies.txt'
subprocess.run(['curl','-fLsS','--compressed','--max-time','60','-c',str(jar),'https://wateroffice.ec.gc.ca/report/historical_e.html?stn=08EE004','-o',str(O/'disclaimer.html')],check=True)
subprocess.run(['curl','-fLsS','--compressed','--max-time','60','-b',str(jar),'-c',str(jar),'--data-urlencode','disclaimer_action=I Agree','https://wateroffice.ec.gc.ca/disclaimer_e.html','-o',str(O/'accepted.html')],check=True)
for typ in ['Annual Extremes','Peak']:
 for mode in ['Graph','Table']:
  name=typ.replace(' ','-').lower()+'-'+mode.lower();q={'stn':'08EE004','mode':mode,'dataType':typ,'parameterType':'Flow','first_year':'1948','last_year':'1948'};url='https://wateroffice.ec.gc.ca/report/historical_e.html?'+urllib.parse.urlencode(q);p=O/(name+'.html');subprocess.run(['curl','-fLsS','--compressed','--max-time','60','-b',str(jar),url,'-o',str(p)],check=True);assert 'id="data-type"' in p.read_text(),name;manifest.append({'name':name,'url':url});print(name,flush=True)
 q={'station':'08EE004','data_type':typ.lower().replace(' ','_'),'first_year':'1948','last_year':'1948','start_year':'1850','end_year':'2026','parameter_type':'flow','results_type':'historical'};url='https://wateroffice.ec.gc.ca/services/historical_graph/json/inline?'+urllib.parse.urlencode(q);p=O/(typ.replace(' ','-').lower()+'.json');subprocess.run(['curl','-fLsS','--compressed','--max-time','60',url,'-o',str(p)],check=True);manifest.append({'name':p.name,'url':url})
(O/'manifest.json').write_text(json.dumps(manifest,indent=2))
