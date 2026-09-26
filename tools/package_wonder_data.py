from pathlib import Path
import sqlite3,json,itertools,shutil
import argparse
p=argparse.ArgumentParser(description="Create consistent WONDER public-use-derived runtime copies without changing records")
p.add_argument('--source-data',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--source-manifest',type=Path,default=Path(__file__).resolve().parents[1]/'environments/wonder/sources/download-manifest.json')
a=p.parse_args();src=a.source_data;out=a.output
out.mkdir(exist_ok=False);data=out/'data';data.mkdir()
manifest=json.loads(a.source_manifest.read_text())
by_name={x['filename'].lower():x for x in manifest}
shared=['year','month','race','origin','place','mother_age','sex','gestation','weight','plurality']
rows=[]
for database in sorted(src.glob('*.sqlite')):
 meta=json.loads(database.with_suffix('.json').read_text())
 archive=meta['archive'].replace('-complete','')
 official=by_name[archive.lower()]
 assert official['bytes']==meta['archive_bytes']
 assert official['url'].startswith('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/')
 a=sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True)
 b=sqlite3.connect(data/database.name);a.backup(b)
 assert b.execute('pragma integrity_check').fetchone()[0]=='ok'
 tables=[x[0] for x in a.execute("select name from sqlite_master where type='table'")]
 assert set(tables)==({'births'} if meta['product']=='natality' else {'births','deaths'})
 result={'file':database.name,'product':meta['product'],'year':meta['year'],'official_source_url':official['url'],'source_archive_bytes':official['bytes'],'source_member_names':{k:v['name'] for k,v in meta['members'].items()},'tables':[],'sqlite_integrity':'ok','consistent_backup':True}
 for table in tables:
  cols=[x[1] for x in a.execute('pragma table_info('+table+')')]
  expected=shared+(['death_age','death_days','cause_leaf','icd'] if table=='deaths' else [])+['n','weight_micro']
  assert cols==expected,(database.name,cols)
  count=0
  for old,new in itertools.zip_longest(a.execute('select * from '+table+' order by rowid'),b.execute('select * from '+table+' order by rowid')):
   assert old==new;count+=1
  result['tables'].append({'name':table,'columns':cols,'rows':count,'all_rows_equal_to_validated_install':True,'contains_small_multiplicities':bool(a.execute('select 1 from '+table+' where n between 1 and 9 limit 1').fetchone())})
 a.close();b.close()
 # Marginal tables and timing are author audit material, not runtime inputs.
 clean=json.loads(json.dumps(meta))
 for member in clean['members'].values():member.pop('marginal_counts',None);member.pop('seconds',None)
 clean['source_url']=official['url'];clean['data_use_notice']='DATA_USE_NOTICE.md'
 serialized=json.dumps(clean,indent=2)+'\n'
 assert '/home/' not in serialized and '/Users/' not in serialized
 (data/database.with_suffix('.json').name).write_text(serialized)
 result['origin_resolution']=meta.get('origin_resolution')
 if meta.get('recovery_source'):result['recovery_source']=meta['recovery_source']
 rows.append(result)
assert len(rows)==16
report={'decision':'Publish audited national public-use-derived computational data with retained source/use conditions; no special CDC authorization claimed.','source_basis':'NCHS national public-use archives, not WONDER query exports or restricted-use files','application_changed':False,'databases':rows,'all_runtime_rows_unchanged':True,'excluded':['raw source ZIPs','web query captures','author marginal audit tables','answers','credentials','logos and media'],'root_free_bytes':shutil.disk_usage('/').free}
(out/'wonder-data-release.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__).resolve().parents[1]/'environments/wonder/licenses/DATA_USE_NOTICE.md',data/'DATA_USE_NOTICE.md')
(data/'PROVENANCE.json').write_text(json.dumps({'source':'CDC/NCHS NVSS','files':[{k:v for k,v in r.items() if k not in ('tables',)} for r in rows]},indent=2)+'\n')
print('Prepared 16 databases with all rows unchanged; '+str(sum(p.stat().st_size for p in data.iterdir()))+' bytes')
