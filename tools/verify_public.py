#!/usr/bin/env python3
"""Anonymous source, Release and GHCR checks. Does not use a GitHub credential."""
import argparse,json,os,subprocess,tempfile,urllib.request,urllib.error
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pull-images',action='store_true');p.add_argument('--release',default='v0.1.1');a=p.parse_args()
root=Path(__file__).resolve().parents[1];m=json.loads((root/'releases'/f'{a.release}.json').read_text());checks=[]
def http(url,method='GET'):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,method=method,headers={'User-Agent':'sgr-webenv-anonymous-check'}),timeout=60) as r:return r.status,r.headers, r.read() if method=='GET' else b''
 except urllib.error.HTTPError as e:return e.code,e.headers,b''
status,_,body=http('https://api.github.com/repos/Ninggggy/sgr-webenv')
checks.append({'kind':'anonymous_repository','passed':status==200 and not json.loads(body or b'{}').get('private',True),'status':status})
for site,spec in m['environments'].items():
 for asset in spec['data_assets']:
  status,headers,_=http(asset['url'],'HEAD')
  length=headers.get('Content-Length')
  checks.append({'kind':'anonymous_asset','name':asset['name'],'status':status,'expected_bytes':asset['bytes'],'content_length':length,'passed':status==200 and length==str(asset['bytes'])})
if a.pull_images:
 images=['ghcr.io/ninggggy/sgr-webenv-release-runtime:1','ghcr.io/ninggggy/sgr-webenv-release-browser-base:1']
 for site,spec in m['environments'].items():
  if site!='noaa':images.extend(spec['images'].values())
 # Capture only the selected daemon address. Do not copy registry credentials
 # or credential helpers into this temporary Docker configuration.
 context=json.loads(subprocess.check_output(['docker','context','inspect'],text=True))[0]
 endpoint=os.environ.get('DOCKER_HOST') or context['Endpoints']['docker']['Host']
 with tempfile.TemporaryDirectory(prefix='sgr-anonymous-docker-') as directory:
  env={**os.environ,'DOCKER_CONFIG':directory,'DOCKER_HOST':endpoint}
  env.pop('DOCKER_CONTEXT',None);env.pop('DOCKER_AUTH_CONFIG',None)
  for image in images:
   result=subprocess.run(['docker','pull','--platform','linux/amd64',image],env=env,capture_output=True,text=True)
   checks.append({'kind':'anonymous_image_pull','image':image,'passed':result.returncode==0,'exit_code':result.returncode})
report={'scope':'No Authorization header or GitHub credential. Docker pulls use an empty credential directory; daemon layers may already be cached. Not an independent-machine installation.','checks':checks,'passed':all(x['passed'] for x in checks)}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if not report['passed']:raise SystemExit(1)
