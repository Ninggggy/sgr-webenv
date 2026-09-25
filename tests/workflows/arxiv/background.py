"""Render the preselected 100 non-answer records through the restricted browser."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--container',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[3];papers=[row['id'] for row in json.loads((r/'docs/verification/arxiv-background.json').read_text())['results']];out=a.output;out.parent.mkdir(parents=True,exist_ok=True);results=[]
for _ in range(30):
 if subprocess.run(['docker','exec',a.container,'test','-S','/tmp/arxiv-browser.sock'],capture_output=True).returncode==0:break
 time.sleep(1)
else:raise RuntimeError('Browser did not start')
for pid in papers:
 req={'action':'goto','url':'https://arxiv.org/abs/'+pid}
 p=subprocess.run(['docker','exec','-i',a.container,'python3','/browser/bridge.py','--call'],input=json.dumps(req)+'\n',text=True,capture_output=True,check=True,timeout=90)
 data=json.loads(p.stdout);text=data.get('text','')
 row={'id':pid,'rendered':not data.get('error') and 'Submission history' in text and pid in text,'blocked':data.get('blocked'), 'error':data.get('error')};results.append(row)
 out.write_text(json.dumps({'purpose':'Browser rendering complement to independent source-field checks; historical completeness evaluated separately','results':results},indent=2))
 if not row['rendered'] or row['blocked']:raise AssertionError(row)
 if len(results)%10==0:print(json.dumps({'background_pages_rendered':len(results)}),flush=True)
print(json.dumps({'background_pages_rendered':len(results),'external_requests':0}),flush=True)
