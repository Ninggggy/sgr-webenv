import json,urllib.request,urllib.error,urllib.parse,re
base='http://127.0.0.1:8080'
def fetch(path):
 try:
  with urllib.request.urlopen(base+path,timeout=60) as r:return r.status,r.read().decode()
 except urllib.error.HTTPError as e:return e.code,e.read().decode()
checks=[]
paths=[('/abs/2101.01097',200),('/abs/2101.01097v1',501),('/abs/2101.01097v999',404),('/bibtex/2101.01097',200),('/bibtex/2101.01097v1',501),('/api/query?id_list=2101.01097v1',501),('/api/query?id_list=2101.01097v999',404),('/search/?query=graph&include_older_versions=1',501),('/api/query?search_query=ti:graph&include_older_versions=1',501),('/list/cs/new',501),('/list/cs/recent',501),('/catchup',501),('/pdf/2101.01097',501),('/src/2101.01097',501),('/login',501),('/search/?query=test&searchtype=orcid',501),('/search/?query=test&searchtype=author_id',501),('/search/?query=test&searchtype=msc_class',501),('/api/query?search_query=orcid:123',501),('/api/query?search_query=msc:11A41',501),('/api/query?search_query=cat:astro-ph',503)]
for path,expected in paths:
 status,body=fetch(path);checks.append({'path':path,'expected':expected,'actual':status,'passed':status==expected})
status,body=fetch('/abs/2101.01097');checks.append({'check':'true first submission date remains 30 Dec 2020','passed':'30 Dec 2020' in body})
latest=max(map(int,re.findall(r'2101\.01097v(\d+)',body)));a,b=fetch('/abs/2101.01097v'+str(latest));checks.append({'check':'explicit latest version serves real current page','passed':a==200 and '30 Dec 2020' in b})
print(json.dumps({'checks':checks,'passed':all(x['passed'] for x in checks)},indent=2))
assert all(x['passed'] for x in checks)
