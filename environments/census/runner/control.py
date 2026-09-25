#!/usr/bin/env python3
import json,subprocess,sys,re,time
project=sys.argv[1] if len(sys.argv)>1 else 'censuseval'
if not re.fullmatch(r'census[a-z0-9_-]{1,40}',project):sys.exit('Invalid instance')
req=json.load(sys.stdin)
if req.get('action') not in {'goto','select','click','fill','check','hover','scroll','press','tabs','new_tab','switch_tab','close_tab','back','reload','observe','download','read_download','archive'}:sys.exit('Unknown tool')
ids=subprocess.check_output(['docker','ps','-q','--filter',f'label=com.docker.compose.project={project}','--filter','label=com.docker.compose.service=census-browser'],text=True).split()
if len(ids)!=1:sys.exit('Expected one browser in this project')
for attempt in range(30):
 r=subprocess.run(['docker','exec','-i',ids[0],'python3','/browser/bridge.py','--call'],input=json.dumps(req)+'\n',text=True,capture_output=True)
 if r.returncode==0 or not any(t in r.stderr for t in ['FileNotFoundError','ConnectionRefusedError']):break
 time.sleep(.5)
sys.stdout.write(r.stdout);sys.stderr.write(r.stderr);sys.exit(r.returncode)
