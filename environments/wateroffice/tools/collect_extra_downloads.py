import urllib.request,urllib.parse,http.cookiejar,pathlib,json
R=pathlib.Path(__file__).resolve().parents[1];O=R/'author/extra-downloads';O.mkdir(exist_ok=True)
import subprocess
base='https://wateroffice.ec.gc.ca'
def get(path,params=None):
 args=['curl','-fLsS','--compressed','--max-time','60','-b',str(O/'cookies.txt'),'-c',str(O/'cookies.txt'),'-D',str(O/'headers.txt')]
 if params:args+=['--data',urllib.parse.urlencode(params)]
 b=subprocess.check_output(args+[base+path]);return b,{'raw':(O/'headers.txt').read_text()}

q=urllib.parse.urlencode({'check[]':'08EE004,1,1930,2025,Flow and Level','results_type':'historical','download':'Download'})
b,h=get('/search/relay_e.html?'+q)
(O/'selection.html').write_bytes(b)
if b'I Agree' in b:get('/disclaimer_e.html',{'disclaimer_action':'I Agree'})
records=[]
for product,fmt in [('md','csv'),('md','ddf'),('ae','csv'),('pd','csv'),('rmk','csv')]:
 path='/download/report_e.html?'+urllib.parse.urlencode({'dt':product,'df':fmt,'md':'1','ext':'csv'})
 try:
  b,h=get(path);file=product+'-'+fmt+'.csv';(O/file).write_bytes(b);records.append({'source':base+path,'file':file,'headers':h,'bytes':len(b)});print(file,len(b),repr(b[:160]),flush=True)
 except Exception as e:records.append({'source':base+path,'error':str(e)});print(e,flush=True)
(O/'manifest.json').write_text(json.dumps(records,indent=2))
