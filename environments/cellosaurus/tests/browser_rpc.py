"""Real browser interaction checks via the restricted agent-facing RPC."""
import os,shlex,json,subprocess,base64,urllib.parse
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'validation/browser';O.mkdir(parents=True,exist_ok=True);out=[];step=0
container=os.environ['CELLOSAURUS_BROWSER_CONTAINER']
cmd=['docker','exec','-i',container,'python3','/browser/bridge.py','--call']
def call(action,**kw):
 global step
 step+=1;r=subprocess.run(cmd,input=json.dumps(dict(action=action,**kw))+'\n',text=True,capture_output=True);d=json.loads(r.stdout);png=d.pop('screenshot',None)
 (O/f'run-{step:02d}.json').write_text(json.dumps(d,indent=2))
 if png and action in ['goto','reload','download','upload']:(O/f'run-{step:02d}.png').write_bytes(base64.b64decode(png))
 if 'error' in d:raise RuntimeError(d['error'])
 return d
def check(name,ok):out.append({'name':name,'passed':bool(ok)});(R/'validation/browser-checks.json').write_text(json.dumps(out,indent=2));print(name,ok,flush=True)
call('reset');call('goto',url='/');call('fill',selector='input[name=query]',value='CCL-2');d=call('press',selector='input[name=query]',key='Enter');check('main search form', '4 hits' in d['text']);url=d['url']
call('new_tab');call('goto',url='/CVCL_0022');d=call('switch_tab',index=0);check('independent tabs',d['url']==url);d=call('reload');check('main reload',d['url']==url and '4 hits' in d['text'])
call('goto',url='/str-search/');call('click',selector='button:has-text("Example")');call('select',selector='#filter-score',value='100');d=call('click',selector='#search');d=call('wait',selector='#export');check('STR Example/search', 'CVCL_0320' in d['text']);queryurl=d['url']
d=call('reload');d=call('wait',selector='#export');check('STR URL restore',d['url']==queryurl and 'CVCL_0320' in d['text'])
for fmt in ['json','csv','xlsx']:
 call('click',selector='#export');call('select',selector='#export-extension',value=fmt);d=call('download',selector='button:has-text("Save")');check('browser export '+fmt,any(x.endswith('.'+fmt) for x in d['downloads'].values()))
call('click',selector='#reset');d=call('observe');check('STR Reset clears results','CVCL_0320' not in d['text'] and '?' not in d['url'])
call('click',selector='#input-mouse');call('click',selector='button:has-text("Example")');d=call('click',selector='#search');d=call('wait',selector='#export');check('Mouse example','mouse cell lines' in d['text'])
call('click',selector='#input-dog');call('click',selector='button:has-text("Example")');d=call('click',selector='#search');d=call('wait',selector='#export');check('Dog example','dog cell lines' in d['text'])
call('click',selector='#reset');call('click',selector='#load');d=call('upload',selector='#input-file',name='public-profile.csv',text='Name,CSF1PO,D13S317\nPublicUpload,12,11\n');check('upload contents absent from URL','PublicUpload' not in urllib.parse.unquote(d['url']));d=call('click',selector='#search');check('uploaded query absent from URL','PublicUpload' not in urllib.parse.unquote(d['url']))
d=call('reset');check('session reset clears downloads',d['downloads']=={} and d['tabs']==['about:blank'])
r=subprocess.run(cmd,input=json.dumps({'action':'goto','url':'https://example.com/'})+'\n',text=True,capture_output=True);d=json.loads(r.stdout);check('outside URL rejected','error' in d)
print('finished',len(out))

assert all(x['passed'] for x in out),out
