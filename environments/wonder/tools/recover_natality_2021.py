"""Reconstruct the 2021 Natality joint distribution from the documented same-year birth denominator. Reverse only flagged not-stated birthweight imputations and require exact original coarse-origin joint equality before writing a database. Author-side preparation only."""
import pathlib,json,zipfile,collections,sqlite3,argparse,copy
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-project',type=pathlib.Path,required=True,help='Author project containing sources archive and linked-2021 metadata')
parser.add_argument('--reference-db',type=pathlib.Path,required=True,help='Preserved original Natality2021 database with coarse origin')
parser.add_argument('--reference-metadata',type=pathlib.Path,required=True,help='Metadata for the preserved original Natality2021 database')
parser.add_argument('--output-dir',type=pathlib.Path,required=True,help='New directory, must not exist')
a=parser.parse_args();R=a.source_project;D=a.output_dir
if not a.reference_db.is_file():parser.error('Reference database missing')
original_info=json.loads(a.reference_metadata.read_text())
if original_info['product']!='natality' or original_info['year']!=2021:parser.error('Expected original Natality2021 metadata')
D.mkdir(parents=True,exist_ok=False)
info=json.loads((R/'data/linked-2021.json').read_text());counts=collections.Counter();raw=resident=flagged=0
races={'1':'2106-3','2':'2054-5','3':'1002-5','4':'A','5':'NHOPI','6':'M'};origins={'0':'0','1':'2148-5','2':'2180-8','3':'2182-4','4':'4','5':'7','6':'5','9':'9'};ages=['15','15-19','20-24','25-29','30-34','35-39','40-44','45-49','50+']
with zipfile.ZipFile(R/'sources'/info['archive']) as z:
 with z.open(info['members']['births']['name']) as f:
  for row in f:
   raw+=1
   if row[103:104]==b'4':continue
   resident+=1;flag=row[515:516];assert flag in [b' ',b'1'];flagged+=flag==b'1'
   grams=9999 if flag==b'1' else int(row[511:515]);weight='%02d'%(12 if grams==9999 else min(grams//500+1,11))
   weeks=int(row[498:500]);gest='%02d'%(10 if weeks==99 else 1 if weeks<20 else 2 if weeks<28 else 3 if weeks<32 else 4 if weeks<36 else 5 if weeks==36 else 6 if weeks<40 else 7 if weeks==40 else 8 if weeks==41 else 9)
   origin=origins[row[111:112].decode()] if row[115:116]==b'1' else '100';place=row[31:32].decode().strip() or ('10' if row[32:33]!=b'1' else '9')
   key=('2021',row[12:14].decode(),races[row[106:107].decode()],origin,place,ages[int(row[78:79])-1],row[474:475].decode(),gest,weight,str(min(int(row[453:454]),3)))
   counts[key]+=1
cols=['year','month','race','origin','place','mother_age','sex','gestation','weight','plurality'];coarse=collections.Counter()
for key,n in counts.items():coarse[key[:3]+('5' if key[3]=='7' else key[3],)+key[4:]]+=n
c=sqlite3.connect('file:'+str(a.reference_db)+'?mode=ro',uri=True);s=','.join(cols);old={tuple(r[:-1]):r[-1] for r in c.execute('select '+s+',sum(n) from births group by '+s)};c.close();diff=[{'key':k,'original':old.get(k,0),'candidate':coarse.get(k,0)} for k in old.keys()|coarse.keys() if old.get(k,0)!=coarse.get(k,0)]
report={'source_archive':info['archive'],'source_member':info['members']['births']['name'],'raw_records':raw,'resident_records':resident,'imputed_resident_weights_reverted_to_not_stated':flagged,'full_joint_columns':cols,'comparison_collapses_only_Dominican_and_Other':True,'different_cells':len(diff),'differences':diff,'detailed_origin_counts':dict(collections.Counter({o:sum(n for k,n in counts.items() if k[3]==o) for o in {k[3] for k in counts}}))}
(D/'origin-recovery-comparison.json').write_text(json.dumps(report,indent=2))
assert not diff,'Candidate fails complete joint equivalence'
f=D/'natality-2021.sqlite';assert not f.exists();c=sqlite3.connect(f);c.execute('create table births ('+','.join(k+' TEXT NOT NULL' for k in cols)+',n INTEGER NOT NULL,weight_micro INTEGER NOT NULL)');c.executemany('insert into births values ('+','.join('?' for _ in range(12))+')',(k+(n,n*1000000) for k,n in counts.items()));c.execute('create index births_population on births(race,origin)');c.commit();c.close()
meta={k:copy.deepcopy(info[k]) for k in ['year','archive','archive_bytes','retrieved_at']}
meta.update(product='natality',import_version='0.3',runtime_bytes=f.stat().st_size,origin_resolution='expanded',unsupported_dimensions=[],limitations=[])
meta['layout']={'reviewed':True,'guide':'linked2021.pdf','record_length':{'births':1346},'origin_position':112,'weight_position':[512,515],'weight_imputation_flag_position':516,'restore_flagged_weight_to':'9999'}
births={k:copy.deepcopy(v) for k,v in info['members']['births'].items() if k not in ['seconds','marginal_counts','joint_rows']}
births.update(raw_records=raw,us_resident_records=resident,joint_rows=len(counts))
births['marginal_counts']={col:dict(sorted(collections.Counter({v:sum(n for key,n in counts.items() if key[i]==v) for v in {key[i] for key in counts}}).items())) for i,col in enumerate(cols)}
meta['members']={'births':births}
meta['recovery_source']={'archive':info['archive'],'member':info['members']['births']['name'],'population':'All 2021 births to US residents; birth denominator, not infant deaths','origin_position':112,'birthweight_rule':'Use positions 512-515 unless BWTIMP at position 516 is 1; restore flagged values to original Not Stated 9999','basis':'Official linked2021 guide: period birth denominator population and Birthweight section','original_natality_archive':original_info['archive'],'joint_comparison':'Exact equality on all ten supported joint dimensions after collapsing Dominican and Other for comparison only','restored_missing_weights':flagged}
meta['original_natality_source']={k:copy.deepcopy(original_info[k]) for k in ['archive','archive_bytes','layout','retrieved_at']}
meta['origin_recovery_status']='full_joint_equivalence_verified'
(D/'natality-2021.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='differences'},indent=2))
