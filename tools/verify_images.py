#!/usr/bin/env python3
"""Pull declared non-NOAA images and inspect their platform/repository association."""
import json,os,subprocess,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'releases/v0.1.0.json').read_text())
images=['ghcr.io/ninggggy/sgr-webenv-release-runtime:1','ghcr.io/ninggggy/sgr-webenv-release-browser-base:1']
for site,spec in manifest['environments'].items():
 if site!='noaa':images.extend(spec['images'].values())
results=[]
for image in images:
 subprocess.run(['docker','pull','--platform','linux/amd64',image],check=True)
 info=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
 assert (info['Os'],info['Architecture'])==('linux','amd64'),image
 assert info['Config']['Labels']['org.opencontainers.image.source']=='https://github.com/Ninggggy/sgr-webenv',image
 row={'image':image,'pulled':True,'platform':'linux/amd64','source_label':info['Config']['Labels']['org.opencontainers.image.source']}
 token=os.environ.get('GITHUB_TOKEN')
 if token:
  package=image.rsplit('/',1)[1].split(':')[0]
  req=urllib.request.Request('https://api.github.com/users/Ninggggy/packages/container/'+package,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'sgr-webenv-verification'})
  try:
   with urllib.request.urlopen(req,timeout=30) as r:p=json.load(r)
   row['visibility']=p['visibility'];row['package_url']=p['html_url'];row['associated_repository']=(p.get('repository') or {}).get('full_name');row['association_matches']=row['associated_repository']=='Ninggggy/sgr-webenv'
  except urllib.error.HTTPError as e:row['visibility']='unavailable HTTP '+str(e.code)
 results.append(row)
out=root/'image-verification.json';out.write_text(json.dumps({'kind':'authenticated registry pull, not anonymous acceptance','images':results},indent=2)+'\n')
print(out.read_text())
