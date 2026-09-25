#!/usr/bin/env python3
"""One-time package migration using already validated local images.
Does not rebuild, download private old images or modify their tags/permissions.
Run only on the release author's trusted runner with GITHUB_TOKEN registry login.
"""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
old='ghcr.io/ninggggy/sgr-webenv-';new='ghcr.io/ninggggy/sgr-webenv-release-'
m=json.loads((root/'releases/v0.1.0.json').read_text())
images=[new+'runtime:1',new+'browser-base:1']
for site,spec in m['environments'].items():
 if site!='noaa':images.extend(spec['images'].values())
for image in images:
 source=old+image[len(new):]
 info=json.loads(subprocess.check_output(['docker','image','inspect',source],text=True))[0]
 assert (info['Os'],info['Architecture'])==('linux','amd64')
 assert info['Config']['Labels']['org.opencontainers.image.source']=='https://github.com/Ninggggy/sgr-webenv'
 subprocess.run(['docker','tag',source,image],check=True)
 tagged=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
 assert tagged['Id']==info['Id'],'Tagging must not change validated image content'
 subprocess.run(['docker','push',image],check=True)
 print('Migrated validated image:',image,flush=True)
