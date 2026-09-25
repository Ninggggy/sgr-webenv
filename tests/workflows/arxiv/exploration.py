"""Forty non-answer-selected browser queries; tests availability, not relevance."""
import argparse,json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

terms=['graph','algebra','probability','topology','logic','network','optimization','geometry',
       'statistics','algorithm','quantum','entropy','matrix','manifold','regression','classification',
       'combinatorics','differential','integral','spectral','random','discrete','continuous','coding',
       'information','computation','automata','language','stochastic','bayesian','convex','nonlinear',
       'time-series','"neural network"','"finite group"','"random walk"','signal-processing',
       'zzzzunmatched827364','"an impossible exact phrase 62849"','absolutelyunmatchedscope92345']
p=argparse.ArgumentParser();p.add_argument('--container',default='sgr-arxiv-v0-1-0_browser_1');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output;out.parent.mkdir(parents=True,exist_ok=True)
rows=[]
for term in terms:
    url='https://arxiv.org/search/?'+urlencode({'query':term,'searchtype':'title','size':25,'order':'-submitted_date','abstracts':'hide'})
    p=subprocess.run(['docker','exec','-i',a.container,'python3','/browser/bridge.py','--call'],
        input=json.dumps({'action':'goto','url':url})+'\n',text=True,capture_output=True,check=True,timeout=45)
    result=json.loads(p.stdout);body=result.get('text','')
    passed='error' not in result and not result.get('blocked') and ('Showing ' in body or 'produced no results' in body)
    rows.append({'term':term,'page_rendered':passed,'url':result.get('url'),
                 'empty':'produced no results' in body,'error':result.get('error'),'blocked':result.get('blocked')})
    out.write_text(json.dumps({'purpose':'candidate browser exploration only; no independent relevance or full-scope acceptance',
                              'results':rows},indent=2))
    if not passed:raise AssertionError(rows[-1])
print(json.dumps({'queries_rendered':len(rows),'empty_results':sum(x['empty'] for x in rows)}))
