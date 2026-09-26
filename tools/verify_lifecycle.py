#!/usr/bin/env python3
"""Author-side lifecycle check against an already isolated installation."""
import argparse,json,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('site',choices=['census','wonder','wateroffice','arxiv','cellosaurus']);p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--release',default='v0.1.1');a=p.parse_args()
root=Path(__file__).resolve().parents[1];base=[sys.executable,str(root/'tools/env.py')];common=[a.site,'--state-dir',str(a.state_dir),'--release',a.release]
project='sgr-'+a.site+'-'+a.release.replace('.','-');browser=project+'_'+a.site+'-browser_1';web=project+'_'+a.site+'-web_1'
def locate(service):
 ids=subprocess.check_output(['docker','ps','--filter','label=com.docker.compose.project='+project,'--filter','label=com.docker.compose.service='+service,'--format','{{.ID}}'],text=True).split();assert len(ids)==1;return ids[0]
def ready():
 global browser,web
 browser=locate('browser' if a.site=='arxiv' else a.site+'-browser');web=locate('web' if a.site=='arxiv' else a.site+'-web')
 for _ in range(45):
  if subprocess.run(['docker','exec',browser,'test','-S','/tmp/'+a.site+'-browser.sock'],capture_output=True).returncode==0:return
  time.sleep(1)
 raise RuntimeError('Browser failed to start')
def call(action,**kw):
 r=subprocess.run(['docker','exec','-i',browser,'python3','/browser/bridge.py','--call'],input=json.dumps({'action':action,**kw})+'\n',text=True,capture_output=True,check=True,timeout=90);return json.loads(r.stdout)
ready();assert 'error' not in call('goto',url='/')
if a.site=='wonder':
 assert 'error' not in call('goto',url='/natality-expanded-current.html')
 assert 'error' not in call('click',selector='#agree')
else:
 x=call('new_tab');assert len(x['tabs'])==2
for c in [browser,web]:subprocess.run(['docker','exec',c,'python3','-c','from pathlib import Path; Path("/tmp/sgr-lifecycle-probe").write_text("temporary author test")'],check=True)
subprocess.run(base+['reset']+common,check=True);ready()
for c in [browser,web]:assert subprocess.run(['docker','exec',c,'test','-e','/tmp/sgr-lifecycle-probe']).returncode!=0
x=call('goto',url='/');assert 'error' not in x and not x.get('downloads')
if a.site=='wonder':
 assert 'error' not in call('goto',url='/request?dataset=natality')
 assert 'error' not in call('click',selector='#agree')
else:assert len(x['tabs'])==1
checks=[{'check':'reset clears prior '+('agreement session' if a.site=='wonder' else 'tabs')+', download registry and transient files','passed':True}]
for url in ['https://example.com/','file:///etc/passwd','http://169.254.169.254/']:
 assert call('goto',url=url).get('error');checks.append({'check':'navigation refused','url':url,'passed':True})
if a.site=='arxiv':
 # Preserve the actual isolated instance configuration, including author-side
 # storage placement. Do not regenerate it or delete its persistent index.
 config=a.state_dir/a.release/'arxiv/compose.json'
 compose=['docker','compose']
 if subprocess.run(compose+['version'],capture_output=True).returncode:compose=['docker-compose']
 dc=compose+['-p',project,'-f',str(config)]
 subprocess.run(dc+['down'],check=True)
 subprocess.run(dc+['up','-d','search'],check=True)
 subprocess.run(dc+['run','--rm','--no-deps','web','python3','/app/wait_search.py','--verify'],check=True)
 subprocess.run(dc+['up','-d'],check=True)
else:
 subprocess.run(base+['stop']+common,check=True)
 subprocess.run(base+['start']+common+['--allow-candidate'],check=True)
ready();assert 'error' not in call('goto',url='/')
subprocess.run(base+['verify']+common,check=True);checks.append({'check':'stop/start preserves usable data','passed':True})
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'site':a.site,'checks':checks},indent=2)+'\n');print(a.output.read_text())
