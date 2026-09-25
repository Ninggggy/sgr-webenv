"""Replay task-relevant UI workflows using only the restricted browser bridge.
Tests information accessibility; an old oracle is not assumed exhaustive.
"""
import argparse,base64,datetime as dt,json,re,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--container',default='sgr-arxiv-v0-1-0_browser_1');p.add_argument('--resume',action='store_true');p.add_argument('--tasks',nargs='+');p.add_argument('--all-candidates',action='store_true');p.add_argument('--pagination-only',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
records=[json.loads(line) for name in ('constraint.jsonl','goal.jsonl') for line in (root/'benchmark'/name).read_text().splitlines() if line.strip() and json.loads(line)['task_id'].startswith('arxiv_')];events=json.loads((out/'events.json').read_text()) if (a.resume or a.tasks) and (out/'events.json').exists() else []
for _ in range(30):
 if subprocess.run(['docker','exec',a.container,'test','-S','/tmp/arxiv-browser.sock'],capture_output=True).returncode==0:break
 time.sleep(1)
else:raise RuntimeError('Restricted browser did not become ready')
action_count=0
def call(action,shot=None,**kw):
 global action_count
 action_count+=1
 if action_count%50==0:
  subprocess.run(['python3',str(Path(__file__).with_name('export_browser_evidence.py')),'--container',a.container,'--output',str(out/'traces')],check=True,timeout=120)
 req={'action':action,**kw}
 p=subprocess.run(['docker','exec','-i',a.container,'python3','/browser/bridge.py','--call'],input=json.dumps(req)+'\n',text=True,capture_output=True,check=True,timeout=60)
 r=json.loads(p.stdout);png=r.pop('screenshot',None)
 if shot and png:(out/(shot+'.png')).write_bytes(base64.b64decode(png))
 record={'request':req,'response':{k:v for k,v in r.items() if k not in ('text',)}}
 if '/abs/' in r.get('url','') and r.get('text'):
  with (out/'detail-observations.jsonl').open('a') as f:f.write(json.dumps({'url':r['url'],'text':r['text']},ensure_ascii=False)+'\n')
 events.append(record)
 with (out/'events.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 if 'error' in r:raise AssertionError(r['error'])
 return r
configs={
 'arxiv_001':(['"dataset distillation"','"dataset condensation"'],'2019-01-01','2021-12-31'),
 'arxiv_002':(['"chain of thought"','"chain-of-thought"','"self-consistency"','CoT'],'2022-01-01','2022-12-31'),
 'arxiv_003':(['transformer','ViT'],'2020-10-01','2020-12-31'),
 'arxiv_004':(['smoothing','smoothed','"partition aggregation"','backdoor','poisoning'],'2020-01-01','2020-06-30')}
results=json.loads((out/'results.json').read_text()) if (a.resume or a.tasks) and (out/'results.json').exists() else []
for task,(terms,start,end) in configs.items():
 if a.tasks and task not in a.tasks:continue
 if a.resume and any(r['task']==task and r['information_replay_passed'] for r in results):continue
 previous_result=next((r for r in results if r['task']==task),{})
 results=[r for r in results if r['task']!=task]
 call('goto',url='https://arxiv.org/search/advanced')
 for i,(term,field) in enumerate((term,field) for term in terms for field in ('title','abstract')):
  if i:call('click',selector='button[data-toggle=fieldset-add-row]')
  call('fill',selector=f'#terms-{i}-term',value=term)
  call('select',selector=f'#terms-{i}-field',value=field)
  if i:call('select',selector=f'#terms-{i}-operator',value='OR')
 call('check',selector='#classification-computer_science',value=True)
 call('check',selector='input[name="classification-include_cross_list"][value="exclude"]',value=True)
 call('check',selector='input[name="date-filter_by"][value="date_range"]',value=True)
 # Official UI uses Eastern midnight and an exclusive upper boundary.
 # Search a conservative superset; adjudicate exact UTC v1 dates from source.
 query_start=(dt.date.fromisoformat(start)-dt.timedelta(days=1)).isoformat()
 query_end=(dt.date.fromisoformat(end)+dt.timedelta(days=1)).isoformat()
 call('fill',selector='#date-from_date',value=query_start);call('fill',selector='#date-to_date',value=query_end)
 call('check',selector='input[name="date-date_type"][value="submitted_date_first"]',value=True)
 call('check',selector='input[name="abstracts"][value="hide"]',value=True)
 call('select',selector='#size',value='25')
 state=call('press',selector='#terms-0-term',key='Enter',shot=task+'-results');result_urls=[];found={}
 while True:
  text=state['text'];m=re.search(r'Showing\s+([\d,]+)[–-]([\d,]+)\s+of\s+([\d,]+)',text)
  if not m:raise AssertionError((task,'No result count',text[:600]))
  current_url=state['url'];result_urls.append(current_url)
  with (out/'result-observations.jsonl').open('a') as f:f.write(json.dumps({'task':task,'url':current_url,'text':text},ensure_ascii=False)+'\n')
  for pid in re.findall(r'(?m)^arXiv:(\d{4}\.\d{4,5})(?:v\d+)?\s+\[pdf,',text):found[pid]=current_url
  finish,total=int(m[2].replace(',','')),int(m[3].replace(',',''))
  if finish>=total:break
  state=call('click',selector='a.pagination-next >> nth=0')
  if len(result_urls)>100:raise AssertionError('Unexpectedly large query; investigate before continuing')
 assert len(found)==total,(task,'Result headings differ from displayed total',len(found),total)
 base=next(r for r in records if r['task_id']==task);required={line.split('|')[0]:line.split('|') for line in base['oracle_answer'].splitlines()[1:]}
 extras=[]
 missing=sorted((set(required)|set(extras))-set(found));details=[]
 if a.pagination_only:details=[d for d in previous_result.get('details',[]) if d['id'] in found]
 opened=[] if a.pagination_only else sorted(found) if a.all_candidates else sorted(set(required)|set(extras))
 for pid in opened:
  if pid not in found:continue
  detail=call('goto',url='https://arxiv.org/abs/'+pid,shot=task+'-'+pid if pid in required else None)
  text=detail['text'];ok='Submission history' in text and pid in text
  expected_dates=re.findall(r'\b20\d{2}-\d{2}-\d{2}\b','|'.join(required.get(pid,[])))
  missing_dates=[]
  for date in expected_dates:
   d=dt.date.fromisoformat(date);needle=f'{d.day} {d.strftime("%b %Y")}'
   if needle not in text:missing_dates.append(date)
  missing_publication=[]
  if pid in required:
   normalized=' '.join(text.split()).lower()
   missing_publication=[clue for clue in required[pid][-1].split('; ') if ' '.join(clue.split()).lower() not in normalized]
  details.append({'id':pid,'history_visible':ok,'missing_expected_dates':missing_dates,'missing_publication_clues':missing_publication,'url':detail['url']})
  if len(details)%150==0:
   # Normal browser actions discard inspected document resources; the query
   # URLs/candidate list and all observations remain in the author report.
   call('new_tab');call('switch_tab',index=0);call('close_tab')
  if len(details)%25==0:print(json.dumps({'task':task,'candidates_opened':len(details),'total':len(opened)}),flush=True)
 result={'task':task,'result_count':total,'query_date_window':[query_start,query_end],'task_utc_date_window':[start,end],'result_pages':len(result_urls),'visible_candidate_ids':sorted(found),'missing_required_ids':missing,'details':details,
         'additional_reference_ids_previously_opened':sorted(set(d['id'] for d in previous_result.get('details',[]))-set(found)),
         'information_replay_passed':not missing and (not (a.all_candidates or a.pagination_only) or len(details)==len(found)) and all(d['history_visible'] and not d['missing_expected_dates'] and not d['missing_publication_clues'] for d in details),
         'oracle_agreement':'information replay only; see independent author review and revision evidence',
         'variants':[r['task_id'] for r in records if r['task_id'] in (task,task+'-g')]}
 results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('details','visible_candidate_ids')}),flush=True)
print('Replayed UI information checks; this is not model solve-rate or formal oracle acceptance.')

if not results or any(not r["information_replay_passed"] for r in results):
 raise SystemExit("One or more browser workflow checks failed; inspect results.json")
