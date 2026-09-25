"""Author-side export of browser-generated evidence without resetting web state.
Only exported trace/screenshot files are removed from the browser's bounded tmpfs.
No task data or host path is exposed to the evaluation browser.
"""
import argparse,datetime as dt,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--container',default='sgr-arxiv-v0-1-0_browser_1');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=a.output.resolve();r.mkdir(parents=True,exist_ok=True)
if shutil.disk_usage(r).free<6*1024**3:raise SystemExit('Evidence export would threaten the 5 GiB floor')
# Capture names before stopping. The next tracing.start creates fresh names;
# old trace/network files are immutable once archive succeeds.
list_closed="import json;from pathlib import Path;print(json.dumps([str(p) for p in Path('/tmp').glob('playwright-artifacts-*/*') if p.is_file() and p.suffix in ('.trace','.network')]))"
closed_names=json.loads(subprocess.check_output(['docker','exec',a.container,'python3','-c',list_closed],text=True))
proc=subprocess.run(['docker','exec','-i',a.container,'python3','/browser/bridge.py','--call'],input=json.dumps({'action':'archive'})+'\n',text=True,capture_output=True,check=True,timeout=120)
reply=json.loads(proc.stdout)
if reply.get('error'):raise RuntimeError(reply['error'])
get="import json,re;from pathlib import Path;print(json.dumps([p.name for p in Path('/tmp/output').iterdir() if p.is_file() and (re.fullmatch(r'step-\\d+\\.png',p.name) or p.name in ('trace.zip','operations.jsonl'))]))"
names=json.loads(subprocess.check_output(['docker','exec',a.container,'python3','-c',get],text=True))
assert 'trace.zip' in names
folder=r
target=folder/(a.container+'-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%f')+'.tar')
with target.open('xb') as f:subprocess.run(['docker','exec',a.container,'tar','-C','/tmp/output','-cf','-',*names],stdout=f,check=True,timeout=120)
# Verify the archive is readable before deleting only these exact exported files.
import tarfile
with tarfile.open(target) as f:
 assert set(f.getnames())==set(names)
 for member in f:
  stream=f.extractfile(member)
  if stream:
   while stream.read(1024**2):pass
remove=[n for n in names if n!='operations.jsonl']
code="import json,sys;from pathlib import Path\nfor name in json.load(sys.stdin):\n Path('/tmp/output',name).unlink()"
subprocess.run(['docker','exec','-i',a.container,'python3','-c',code],input=json.dumps(remove),text=True,check=True)
print(json.dumps({'exported':str(target.relative_to(r)),'files':len(names),'bytes':target.stat().st_size,'web_state_preserved':True}))
# Playwright retains raw screencast frames after tracing.stop(). Their names
# contain page ID + monotonic timestamp, so future chunks cannot reuse them.
# Keep all content-addressed DOM/network resources: Playwright caches those.
import io,zipfile,re
frames=set()
for archived in [target]:
 with tarfile.open(archived) as archive:
  try: trace=archive.extractfile('trace.zip')
  except KeyError: continue
  with zipfile.ZipFile(io.BytesIO(trace.read())) as z:
   assert z.testzip() is None, 'Invalid trace ZIP; keeping all raw evidence'
   for name in z.namelist():
    leaf=Path(name).name
    if name.startswith('resources/') and re.fullmatch(r'page@[^/]+-\d+(?:\.\d+)?\.jpeg',leaf):
     z.read(name)  # Check CRC before removing the raw duplicate.
     frames.add(leaf)
cleanup="""import json,sys
from pathlib import Path
names=set(json.load(sys.stdin));count=0
for directory in Path('/tmp').glob('playwright-artifacts-*/resources'):
 for name in names:
  path=directory/name
  if path.is_file():path.unlink();count+=1
print(count)
"""
proc=subprocess.run(['docker','exec','-i',a.container,'python3','-c',cleanup],input=json.dumps(sorted(frames)),text=True,capture_output=True,check=True)
print(json.dumps({'exported_screencast_duplicates_removed':int(proc.stdout)}))

# The exported ZIP contains the completed trace/network data. Older completed
# chunks were exported by earlier invocations; never touch the fresh chunk.
closed_cleanup="import json,sys;from pathlib import Path\nfor name in json.load(sys.stdin):\n p=Path(name)\n if p.parent.name.startswith('playwright-artifacts-') and p.suffix in ('.trace','.network') and p.is_file():p.unlink()"
subprocess.run(['docker','exec','-i',a.container,'python3','-c',closed_cleanup],input=json.dumps(closed_names),text=True,check=True)
print(json.dumps({'completed_raw_trace_network_files_removed':len(closed_names)}))
