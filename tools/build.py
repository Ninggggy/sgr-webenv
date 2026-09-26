#!/usr/bin/env python3
"""Build the complete public dependency chain on Linux amd64."""
import argparse,json,subprocess,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREFIX='ghcr.io/ninggggy/sgr-webenv-release-'
def build(tag,file,context,args=()):
 if shutil.disk_usage('/').free<5*1024**3:raise RuntimeError('Root free space below 5 GiB; build stopped')
 subprocess.run(['docker','build','--platform','linux/amd64','--label','org.opencontainers.image.source=https://github.com/Ninggggy/sgr-webenv','-t',PREFIX+tag,'-f',str(file),*args,str(context)],check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('site',choices=['base','noaa','census','wonder','arxiv','wateroffice','cellosaurus']);p.add_argument('--push',action='store_true');a=p.parse_args()
 if a.site=="noaa":raise RuntimeError("NOAA distribution is withheld: ZingChart OEM redistribution permission is not established; see docs/THIRD_PARTY.md")
 tags=[]
 if a.site=='base':
  for name,file in [('runtime:1','runtime.Dockerfile'),('browser-base:1','browser-base.Dockerfile')]:build(name,ROOT/'docker'/file,ROOT/'docker');tags.append(name)
 else:
  s=json.loads((ROOT/'releases/v0.1.2.json').read_text())['environments'][a.site]
  for role,image in s['images'].items():
   tag=image[len(PREFIX):];build(tag,ROOT/'environments'/a.site/('Dockerfile.'+role),ROOT/'environments'/a.site);tags.append(tag)
 if a.push:
  for t in tags:subprocess.run(['docker','push',PREFIX+t],check=True)
if __name__=='__main__':main()
