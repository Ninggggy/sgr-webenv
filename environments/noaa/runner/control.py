#!/usr/bin/env python3
"""Trusted controller. Accepts one structured browser request, never a host command."""
import json,subprocess,sys,re
project=sys.argv[1] if len(sys.argv)>1 else "noaaeval"
if not re.fullmatch(r"noaa[a-z0-9_-]{1,40}",project):sys.exit("Invalid instance")
req=json.load(sys.stdin)
if req.get("action") not in {"goto","select","click","fill","check","hover","scroll","back","reload","observe","download","read_download","archive"}:sys.exit("Unknown tool")
ids=subprocess.check_output(["docker","ps","-q","--filter",f"label=com.docker.compose.project={project}","--filter","label=com.docker.compose.service=noaa-browser"],text=True).split()
if len(ids)!=1:sys.exit("Expected one browser in this project")
r=subprocess.run(["docker","exec","-i",ids[0],"python3","/browser/bridge.py","--call"],input=json.dumps(req)+"\n",text=True,capture_output=True)
sys.stdout.write(r.stdout);sys.stderr.write(r.stderr);sys.exit(r.returncode)
