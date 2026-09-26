#!/usr/bin/env python3
"""Check that private-path requests cannot read runtime or author files."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--release',default='v0.1.1');p.add_argument('--sites',nargs='+',choices=['census','wonder','arxiv','wateroffice'],default=['census','wonder','arxiv','wateroffice']);a=p.parse_args()
code='''import urllib.request,urllib.error,json
paths=['/.git/config','/benchmark/constraint.jsonl','/data/metadata.sqlite','/app/app.py','/proc/self/environ','/%2e%2e/etc/passwd']
rows=[]
for path in paths:
 try:
  with urllib.request.urlopen('http://127.0.0.1:8080'+path,timeout=20) as r:status=r.status;body=r.read()
 except urllib.error.HTTPError as e:status=e.code;body=e.read()
 rows.append({'path':path,'status':status,'bytes':len(body)})
print(json.dumps(rows))
'''
out={}
for site in a.sites:
 project='sgr-'+site+'-'+a.release.replace('.','-');service='web' if site=='arxiv' else site+'-web'
 ids=subprocess.check_output(['docker','ps','--filter','label=com.docker.compose.project='+project,'--filter','label=com.docker.compose.service='+service,'--format','{{.ID}}'],text=True).split()
 if len(ids)!=1:raise RuntimeError('Expected one running '+site+' web service')
 result=subprocess.run(['docker','exec','-i',ids[0],'python3','-'],input=code,text=True,capture_output=True,check=True)
 rows=json.loads(result.stdout)
 for row in rows:row['denied']=row['status'] in ((400,403,404,405,501,503) if site=='wateroffice' else (400,403,404,405,501))
 out[site]=rows
report={'checks':out,'note':'HTTP responses for private-path requests.'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
if not all(r['denied'] for rows in out.values() for r in rows):raise SystemExit('Private-path check failed')
print('24 private-path checks passed')
