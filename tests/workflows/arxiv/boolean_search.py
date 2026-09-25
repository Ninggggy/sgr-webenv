#!/usr/bin/env python3
"""HTTP metamorphic check of official boolean search; not a source relevance oracle."""
import json,re,urllib.parse,urllib.request
base='http://127.0.0.1:8080/search/advanced?'
def query(terms):
 args={'advanced':'1','date-filter_by':'date_range','date-from_date':'2020-01-01','date-to_date':'2020-02-01','date-date_type':'submitted_date_first','abstracts':'hide','size':'200','order':'-announced_date_first'}
 for i,(word,operator) in enumerate(terms):
  args.update({f'terms-{i}-term':word,f'terms-{i}-operator':operator,f'terms-{i}-field':'title'})
 ids=set();start=0
 while True:
  args['start']=str(start)
  html=urllib.request.urlopen(base+urllib.parse.urlencode(args),timeout=90).read().decode()
  if 'produced no results' in html:return ids
  m=re.search(r'Showing\s+[\d,]+(?:\s|&ndash;|–|-)+[\d,]+\s+of\s+([\d,]+)',html)
  if not m:raise AssertionError('Missing result count')
  total=int(m[1].replace(',',''))
  ids.update(re.findall(r'href="/abs/([^"?]+)',html))
  start+=200
  if start>=total:
   assert len(ids)==total,(len(ids),total)
   return ids
sets={}
sets['A']=query([('graph','AND')]);sets['B']=query([('quantum','AND')])
for op in ('AND','OR','NOT'):sets[op]=query([('graph','AND'),('quantum',op)])
expected={'AND':sets['A']&sets['B'],'OR':sets['A']|sets['B'],'NOT':sets['A']-sets['B']}
checks=[{'operator':op,'passed':sets[op]==expected[op],'actual_count':len(sets[op]),'expected_count':len(expected[op])} for op in expected]
assert sets['A'] and sets['B']
print(json.dumps({'scope':'Boolean set identities over independent single-term result sets; not source-data relevance verification','single_term_counts':{k:len(sets[k]) for k in ('A','B')},'checks':checks},indent=2))
assert all(x['passed'] for x in checks)
