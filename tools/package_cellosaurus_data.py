#!/usr/bin/env python3
"""Export only the complete Cellosaurus runtime data, using a consistent SQLite backup."""
import argparse,gzip,json,shutil,sqlite3,tarfile,tempfile
from pathlib import Path
FILES=('README','cellosaurus_relnotes.txt','cellosaurus.txt','cellosaurus_refs.txt','cellosaurus.xml','cellosaurus.xsd','cellosaurus_xrefs.txt','cellosaurus_deleted_ACs.txt','cellosaurus_name_conflicts.txt','cellopub.txt','cellosaurus.obo','cellosaurus_faq.txt')
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--temporary-dir',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('Output already exists')
 if shutil.disk_usage('/').free<5*1024**3:raise ValueError('Keep 5 GiB on root filesystem')
 a.temporary_dir.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='cellosaurus-export-',dir=a.temporary_dir) as temp:
  d=Path(temp);source=sqlite3.connect('file:'+str(a.source/'cellosaurus.sqlite')+'?mode=ro',uri=True)
  with sqlite3.connect(d/'cellosaurus.sqlite') as target:
   source.backup(target)
   assert target.execute('pragma integrity_check').fetchone()[0]=='ok'
   assert target.execute('select count(*) from cell').fetchone()[0]==168970
   # Compare every table against the source; never rebuild or filter runtime records here.
   tables=[r[0] for r in source.execute("select name from sqlite_master where type='table'")]
   for t in tables:
    query='select * from "'+t.replace('"','""')+'"'
    one=source.execute(query);two=target.execute(query)
    while True:
     x=one.fetchmany(2048);y=two.fetchmany(2048)
     if x!=y:raise ValueError('Backup differs: '+t)
     if not x:break
  source.close()
  names=[x+'.gz' for x in FILES]+['sources.json','history/sources.json','history/53/cellosaurus_name_conflicts.txt.gz','history/54/cellosaurus_name_conflicts.txt.gz']
  manifest=json.loads((a.source/'sources.json').read_text())
  for n in FILES:
   assert manifest[n]['complete']
   with gzip.open(a.source/(n+'.gz'),'rb') as f:
    total=0
    for block in iter(lambda:f.read(1024*1024),b''):total+=len(block)
   assert total==manifest[n]['raw_bytes'],n
  notice=Path(__file__).resolve().parents[1]/'environments/cellosaurus/licenses/NOTICE.md'
  with tarfile.open(a.output,'w:gz',compresslevel=6) as tar:
   tar.add(d/'cellosaurus.sqlite',arcname='cellosaurus.sqlite')
   for n in names:tar.add(a.source/n,arcname=n)
   tar.add(notice,arcname='NOTICE.md')
 print(json.dumps({'records':168970,'all_tables_equal':True,'source_files':len(names),'archive_bytes':a.output.stat().st_size}))
if __name__=='__main__':main()
