#!/usr/bin/env python3
"""Download fixed official Summary releases; validate before replacing caches."""
import subprocess,argparse,concurrent.futures,datetime,json,pathlib,re,urllib.request,zipfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def fetch(year,product,name,kind,transport='https'):
 n=5 if product=='acs5' else 1
 base=f'https://www2.census.gov/programs-surveys/acs/summary_file/{year}/'
 if kind=='data':rel=f'data/{n}_year_by_state/{name}_All_Geographies'+('_Not_Tracts_Block_Groups' if n==5 else '')+'.zip'
 elif kind=='lookup':rel=f'documentation/user_tools/ACS_{n}yr_Seq_Table_Number_Lookup.txt'
 elif kind=='templates':rel=f'data/{year}_{n}yr_Summary_FileTemplates.zip'
 else:raise ValueError(kind)
 url=base+rel
 if transport=='ftp':url=url.replace('https://www2.census.gov/','ftp://ftp2.census.gov/')
 folder=ROOT/f'sources/summary/{year}/{product}';folder.mkdir(parents=True,exist_ok=True);dest=folder/rel.split('/')[-1];side=dest.with_suffix(dest.suffix+'.source.json')
 def validate(path):
  if path.stat().st_size<100:raise ValueError('Empty or truncated file')
  if path.suffix in ['.zip','.part'] and dest.suffix=='.zip':
   with zipfile.ZipFile(path) as z:
    if z.testzip():raise ValueError('Corrupt ZIP')
    names=z.namelist()
    if kind=='data' and not any(re.search(f'e{year}{n}',x) for x in names):raise ValueError('Wrong release ZIP')
    if kind=='templates' and not any(f'{year}_SFGeoFileTemplate' in x for x in names):raise ValueError('Wrong release template ZIP')
    return {'members':len(names),'expanded_bytes':sum(x.file_size for x in z.infolist())}
  head=path.read_text(encoding='cp1252')[:200]
  if not head.startswith('File ID,Table ID,Sequence Number'):raise ValueError('Unexpected layout content')
  return {}
 now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
 if dest.exists():
  m=json.loads(side.read_text());assert m['url'].split('census.gov/',1)[1]==url.split('census.gov/',1)[1];validate(dest);m['checked_utc']=now();side.write_text(json.dumps(m,indent=2));return str(dest)
 tmp=dest.with_suffix(dest.suffix+'.part')
 for attempt in range(3):
  try:
   if kind=='data' and transport=='https':
    progress=tmp.with_suffix('.progress.json');offset=0;total=None
    if progress.exists() and tmp.exists():
     state=json.loads(progress.read_text())
     if state['url']!=url or state['bytes']!=tmp.stat().st_size:raise ValueError('Partial source state mismatch')
     offset=state['bytes'];total=state['total']
    while total is None or offset<total:
     end=offset+1024*1024-1
     headers=tmp.with_suffix('.headers');chunk=tmp.with_suffix('.chunk')
     subprocess.run(['curl','--silent','--show-error','--fail','--max-time','45','--range',f'{offset}-{end}','--dump-header',str(headers),'--output',str(chunk),url],check=True)
     raw_headers=headers.read_text();match=re.search(r'content-range:\s*bytes (\d+)-(\d+)/(\d+)',raw_headers,re.I)
     if not match or int(match[1])!=offset:raise ValueError('Server did not honor exact range')
     next_total=int(match[3]);expected=int(match[2])-offset+1
     if total is not None and next_total!=total:raise ValueError('Source length changed during retrieval')
     b=chunk.read_bytes()
     if len(b)!=expected:raise ValueError('Truncated range')
     with tmp.open('ab' if offset else 'wb') as out:out.write(b)
     offset+=len(b);total=next_total
     progress.write_text(json.dumps({'url':url,'bytes':offset,'total':total,'checked_utc':now()},indent=2))
    size=offset
   else:
    with urllib.request.urlopen(url,timeout=50) as f,tmp.open('wb') as out:
     expected=f.headers.get('Content-Length');size=0
     while True:
      b=f.read(1024*1024)
      if not b:break
      out.write(b);size+=len(b)
      if size>1500000000:raise ValueError('Batch too large')
    if expected and int(expected)!=size:raise ValueError('Truncated transfer')
   details=validate(tmp);tmp.replace(dest);side.write_text(json.dumps({'url':url,'year':year,'product':product,'retrieved_utc':now(),'checked_utc':now(),'bytes':size,**details},indent=2));return str(dest)
  except Exception as e:
   dest.with_suffix(dest.suffix+'.failure.json').write_text(json.dumps({'url':url,'utc':now(),'error':str(e),'attempt':attempt+1},indent=2))
   if attempt==2:raise
   time.sleep(1+attempt)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--transport',choices=['https','ftp'],default='https');p.add_argument('--states',nargs='+',default=['Delaware']);p.add_argument('--years',nargs='+',type=int,default=[2016,2017,2018,2019]);p.add_argument('--products',nargs='+',default=['acs5','acs1']);a=p.parse_args()
 jobs=[(y,p,s,'data') for y in a.years for p in a.products for s in a.states]+[(y,p,'',k) for y in a.years for p in a.products for k in ['lookup','templates']]
 failures=0
 with concurrent.futures.ThreadPoolExecutor(4) as pool:
  fs=[pool.submit(fetch,*j,a.transport) for j in jobs]
  for f in concurrent.futures.as_completed(fs):
   try:print(f.result(),flush=True)
   except Exception as e:failures+=1;print('FAILED',e,flush=True)
 if failures:raise SystemExit(1)
