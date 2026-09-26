#!/usr/bin/env python3
"""Pull declared non-NOAA images and inspect their platform/repository association."""
import argparse,json,os,subprocess,urllib.request,urllib.error,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--release',default='v0.1.1');args=parser.parse_args()
manifest=json.loads((root/'releases'/f'{args.release}.json').read_text())
images=['ghcr.io/ninggggy/sgr-webenv-release-runtime:1','ghcr.io/ninggggy/sgr-webenv-release-browser-base:1']
for site,spec in manifest['environments'].items():
 if site!='noaa':images.extend(spec['images'].values())
results=[]
# The REST package response can omit repository. Query the repository's actual
# GraphQL package connection instead of treating an absent REST field as proof.
associations={}
token=os.environ.get('GITHUB_TOKEN')
if token:
 query='query { repository(owner:"Ninggggy", name:"sgr-webenv") { packages(first:100) { pageInfo { hasNextPage } nodes { name repository { nameWithOwner } } } } }'
 req=urllib.request.Request('https://api.github.com/graphql',data=json.dumps({'query':query}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'sgr-webenv-verification'})
 with urllib.request.urlopen(req,timeout=30) as r:g=json.load(r)
 if g.get('errors'):raise SystemExit('Package association query failed: '+json.dumps(g['errors']))
 connection=g['data']['repository']['packages']
 if connection['pageInfo']['hasNextPage']:raise SystemExit('Package association pagination needs extending')
 associations={p['name']:(p.get('repository') or {}).get('nameWithOwner') for p in connection['nodes']}
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
   row['visibility']=p['visibility'];row['package_url']=p['html_url'];row['associated_repository']=associations.get(package);row['association_evidence']='GraphQL repository.packages';row['association_matches']=row['associated_repository']=='Ninggggy/sgr-webenv';row['association_status']='verified' if row['association_matches'] else 'unverified; inspect package web page'
  except urllib.error.HTTPError as e:row['visibility']='unavailable HTTP '+str(e.code)
 # Public GHCR pages redirect to a repository-scoped package URL when linked.
 # This is directly observable even when API package listings omit containers.
 package=image.rsplit('/',1)[1].split(':')[0]
 public_url='https://github.com/users/Ninggggy/packages/container/package/'+package
 try:
  with urllib.request.urlopen(public_url,timeout=30) as response:
   resolved=response.geturl()
  expected='/Ninggggy/sgr-webenv/pkgs/container/'+package
  if urllib.parse.urlparse(resolved).netloc=='github.com' and urllib.parse.urlparse(resolved).path==expected:
   row.update(visibility='public',associated_repository='Ninggggy/sgr-webenv',association_matches=True,association_status='verified',association_evidence='Anonymous package page redirects to repository-scoped URL',package_url=resolved)
 except urllib.error.HTTPError:
  pass
 results.append(row)
out=root/'image-verification.json';out.write_text(json.dumps({'kind':'Registry image check','images':results},indent=2)+'\n')
print(out.read_text())

if any(not r.get("association_matches") for r in results):
 raise SystemExit("Package association with the new repository is not verified; inspect image-verification.json")
