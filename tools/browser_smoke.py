#!/usr/bin/env python3
"""Browser protocol/isolation smoke. Does not measure task correctness."""
import argparse,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('site',choices=['noaa','census','wonder','arxiv','wateroffice']);p.add_argument('--release',default='v0.1.1');a=p.parse_args()
project='sgr-'+a.site+'-'+a.release.replace('.','-')
service='browser' if a.site=='arxiv' else a.site+'-browser'
ids=subprocess.check_output(['docker','ps','--filter','label=com.docker.compose.project='+project,'--filter','label=com.docker.compose.service='+service,'--format','{{.ID}}'],text=True).split()
if len(ids)!=1:raise RuntimeError('Expected one running browser service')
for attempt in range(45):
 r=subprocess.run(['docker','exec',ids[0],'test','-S','/tmp/'+a.site+'-browser.sock'],capture_output=True)
 if r.returncode==0:break
 time.sleep(1)
else:raise RuntimeError('Browser RPC did not become ready within 45 seconds')
def call(req):
 r=subprocess.run(['docker','exec','-i',ids[0],'python3','/browser/bridge.py','--call'],input=json.dumps(req)+'\n',capture_output=True,text=True,check=True,timeout=90)
 return json.loads(r.stdout)
records=[]
for url,blocked in [('/',False),('https://example.com/',True),('file:///etc/passwd',True),('http://169.254.169.254/',True)]:
 d=call({'action':'goto','url':url})
 if bool(d.get('error'))!=blocked:raise RuntimeError('Unexpected navigation response: '+url)
 records.append({'url':url,'blocked':blocked,'error':d.get('error')})
print(json.dumps({'site':a.site,'kind':'browser-isolation-smoke','checks':records,'passed':True},indent=2))
