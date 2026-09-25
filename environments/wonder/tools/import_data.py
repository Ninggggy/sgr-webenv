#!/usr/bin/env python3
"""Stream complete official annual ZIP members to joint distributions.
No task IDs, oracle values or expected rows are used. Numerator and denominator stay separate.
"""
import argparse,collections,datetime,json,pathlib,re,sqlite3,time,zipfile,subprocess
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1]
SHARED=['year','month','race','origin','place','mother_age','sex','gestation','weight','plurality']
RACES={'1':'2106-3','2':'2054-5','3':'1002-5','4':'A','5':'NHOPI','6':'M'}
ORIGINS={'0':'0','1':'2148-5','2':'2180-8','3':'2182-4','4':'4','5':'7','6':'5','9':'9'}
AGES=['15','15-19','20-24','25-29','30-34','35-39','40-44','45-49','50+']
def common(line,year,linked,origin_position):
 s=lambda a,b=None:line[a-1:b or a].decode('ascii').strip()
 race=RACES[s(107)]
 origins=ORIGINS if origin_position==112 else {**ORIGINS,'5':'5'}
 origin_code=s(origin_position)
 if s(116)=='1' and origin_code not in origins:raise ValueError('Unexpected Hispanic origin code')
 if origin_position==112 and s(116)=='1' and ('5' if origin_code in ['5','6'] else origin_code)!=s(115):raise ValueError('Inconsistent detailed and broad Hispanic origin fields; review the annual source before import')
 origin=origins[origin_code] if s(116)=='1' else '100'
 # Preserve valid place codes even when intended-home detail is not reported.
 place=s(32) or ('10' if s(33)!='1' else '9')
 age=AGES[int(s(79))-1];weeks=int(s(499,500) or 99)
 gest='10' if weeks==99 else f'{1 if weeks<20 else 2 if weeks<28 else 3 if weeks<32 else 4 if weeks<36 else 5 if weeks==36 else 6 if weeks<40 else 7 if weeks==40 else 8 if weeks==41 else 9:02d}'
 grams=int(s(512,515) if linked else s(504,507))
 weight=f'{12 if grams==9999 else min(grams//500+1,11):02d}'
 return (str(year),s(13,14),race,origin,place,age,s(475),gest,weight,str(min(int(s(454)),3)))
def main():
 p=argparse.ArgumentParser();p.add_argument('product',choices=['natality','linked']);p.add_argument('year',type=int);p.add_argument('archive');p.add_argument('--member');p.add_argument('--numerator');p.add_argument('--denominator');a=p.parse_args()
 # Each selected year's layout must first be reviewed and explicitly recorded.
 layouts=json.loads((ROOT/'sources/layouts.json').read_text());layout=layouts.get(f'{a.product}-{a.year}')
 if not layout or not layout.get('reviewed'):raise ValueError('Annual layout has not been reviewed')
 out=ROOT/'data'/f'{a.product}-{a.year}.sqlite'
 if out.exists():raise FileExistsError(f'Preserving existing import: {out}')
 tmp=out.with_suffix('.importing')
 if tmp.exists():raise FileExistsError('Inspect unfinished import before retry: '+str(tmp))
 con=sqlite3.connect(tmp);con.execute('pragma journal_mode=OFF');con.execute('pragma synchronous=OFF')
 spec=[('births',a.member)] if a.product=='natality' else [('births',a.denominator),('deaths',a.numerator)]
 report={'product':a.product,'year':a.year,'archive':pathlib.Path(a.archive).name,'archive_bytes':pathlib.Path(a.archive).stat().st_size,'import_version':'0.3','layout':layout,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'members':{}}
 with zipfile.ZipFile(a.archive) as z:
  for table,member in spec:
   if not member:
    pattern=('usnum' if table=='deaths' else 'usden') if a.product=='linked' else 'nat'
    candidates=[n for n in z.namelist() if not n.endswith('/') and (re.match(r'^VS(?:'+str(a.year)+'|'+str(a.year)[-2:]+r')LINK\.',pathlib.PurePosixPath(n).name,re.I) and pattern in n.lower())]
    if a.product=='natality':candidates=[n for n in z.namelist() if not n.endswith('/') and z.getinfo(n).file_size>100000000]
    if len(candidates)!=1:raise ValueError('Explicit member names required: '+str(z.namelist()))
    member=candidates[0]
   fields=SHARED+(['death_age','death_days','cause_leaf','icd'] if table=='deaths' else [])
   con.execute(f'CREATE TABLE {table} ({",".join(k+" TEXT NOT NULL" for k in fields)}, n INTEGER NOT NULL, weight_micro INTEGER NOT NULL)')
   counts=collections.defaultdict(lambda:[0,0]);raw=kept=0;statuses=collections.Counter();marginals={k:collections.Counter() for k in fields};t=time.time()
   observed_length=None
   with subprocess.Popen(['unzip','-p',a.archive,member],stdout=subprocess.PIPE) as process:
    for line in process.stdout:
     raw+=1
     length=len(line.rstrip(b'\r\n'));declared=layout['record_length'][table]
     if observed_length is None:observed_length=length
     if length!=observed_length or length<declared or line[declared:length].strip():raise ValueError(f'Unexpected non-blank record extension or length at {member}:{raw}: {length} vs {declared}')
     status=line[103:104].decode();statuses[status]+=1
     if status=='4':continue
     if status not in ['1','2','3']:raise ValueError('Unexpected residence status '+status)
     row=common(line,a.year,a.product=='linked',layout['origin_position']);w=1000000
     if table=='deaths':
      w=int(Decimal(line[1376:1384].decode().strip())*1000000)
      row+=(line[1358:1359].decode().zfill(2),str(int(line[1355:1358])), 'GR130-'+line[1372:1375].decode(),line[1367:1371].decode().strip())
     if w<1000000:raise ValueError('Unexpected record weight')
     counts[row][0]+=1;counts[row][1]+=w;kept+=1
     for key,value in zip(fields,row):marginals[key][value]+=1
     if raw%1000000==0:print(table,raw,'rows',round(time.time()-t,1),'seconds',flush=True)
    if process.wait()!=0:raise RuntimeError('Archive decompression failed')
   con.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in range(len(fields)+2))})',(k+tuple(v) for k,v in counts.items()))
   con.execute(f'CREATE INDEX {table}_population ON {table}(race,origin)')
   report['members'][table]={'name':member,'uncompressed_bytes':z.getinfo(member).file_size,'raw_records':raw,'us_resident_records':kept,'joint_rows':len(counts),'residence_status':dict(statuses),'marginal_counts':{k:dict(v) for k,v in marginals.items()},'seconds':round(time.time()-t,1),'observed_record_length':observed_length,'declared_record_length':layout['record_length'][table]}
   del counts
 con.commit();check=con.execute('pragma integrity_check').fetchone()[0];con.close()
 if check!='ok':raise RuntimeError(check)
 tmp.rename(out);report['runtime_bytes']=out.stat().st_size
 (ROOT/'data'/f'{a.product}-{a.year}.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!='members'}),flush=True)
if __name__=='__main__':main()
