import json,sys,time,urllib.request,sqlite3,os
for attempt in range(90):
 try:
  with urllib.request.urlopen('http://search:9200',timeout=5) as r:json.load(r)
  break
 except OSError:
  if attempt==89:raise
  time.sleep(2)
if '--verify' in sys.argv:
 with sqlite3.connect('file:/data/metadata.sqlite?mode=ro',uri=True) as c:expected=c.execute('select count(*) from records where deleted=0').fetchone()[0]
 with urllib.request.urlopen('http://search:9200/'+os.environ['ELASTICSEARCH_INDEX']+'/_count',timeout=60) as r:actual=json.load(r)['count']
 if actual!=expected:raise RuntimeError(f'Incomplete index: {actual}/{expected}; refusing startup')
