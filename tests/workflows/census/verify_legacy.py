#!/usr/bin/env python3
"""Author-only exact-rational reconstruction; never copied into a web/browser image."""
import sqlite3,json,csv
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,ROUND_HALF_UP
import argparse
p=argparse.ArgumentParser();p.add_argument('exports',type=Path);args=p.parse_args()
D=args.exports
ROOT=Path(__file__).resolve().parents[3]
import zipfile,io
c=sqlite3.connect(':memory:')
c.execute('create table geographies(year int,id text,name text,state text,primary key(year,id))')
c.execute('create table cells(year int,product text,geo text,variable text,estimate real,primary key(year,product,geo,variable))')
for p in sorted(D.glob('????-*.zip')):
 year=int(p.name[:4]);st={2016:'42',2017:'06',2018:'37',2019:'35'}[year]
 z=zipfile.ZipFile(p)
 for row in csv.DictReader(io.StringIO(z.read('data.csv').decode('utf-8-sig'))):
  g=row['GEO_ID'].split('US')[1];c.execute('insert or ignore into geographies values(?,?,?,?)',(year,g,row['NAME'],st))
  for k,v in row.items():
   if k.endswith('E') and k[0] in 'BC' and '_' in k:c.execute('insert into cells values(?,?,?,?,?)',(year,'acs5',g,k,float(v) if v else None))
assert c.execute('select count(*) from cells').fetchone()[0]==25647
tasks=[json.loads(line) for name in ('constraint','goal') for line in (ROOT/'benchmark'/f'{name}.jsonl').read_text().splitlines() if line.strip()]
tasks=[t for t in tasks if t['task_id'].startswith('census_')]
def calculate(n):
 y,st={1:(2018,'37'),2:(2019,'35'),3:(2017,'06'),4:(2016,'42')}[n];out={}
 for g,name in c.execute('SELECT id,name FROM geographies WHERE year=? AND state=? ORDER BY name',(y,st)):
  cells=dict(c.execute('SELECT variable,estimate FROM cells WHERE year=? AND product="acs5" AND geo=?',(y,g)))
  def v(t,i):
   x=cells.get(f'{t}_{i:03d}E')
   if x is None or x<0:raise ValueError('Missing/special estimate')
   return int(x)
  def s(t,ids):return sum(v(t,i) for i in ids)
  def rate(a,b):return F(a*100,b)
  income=v('B19013',1)
  if n==1:
   hh=v('B28002',1);row=[v('B28002',13),rate(v('B28002',13),hh),rate(s('B11010',[5,12]),hh),rate(v('B08201',2),hh),income]
  elif n==2:
   hh=v('C16002',1);lep=s('C16002',[4,7,10,13]);row=[v('B25003',3),lep,rate(lep,hh),rate(v('B28002',13),v('B28002',1)),rate(v('B08201',2),v('B08201',1)),rate(s('B25070',[8,9,10]),v('B25070',1)-v('B25070',11)),rate(s('B25014',[11,12,13]),v('B25014',8)),income]
  elif n==3:
   age=v('B16004',2);lep=s('B16004',[7,8,12,13,17,18,22,23]);row=[age,lep,rate(lep,age),rate(v('B28011',8),v('B28011',1)),rate(v('B08201',2),v('B08201',1)),rate(v('B09010',2),v('B09010',1)),rate(s('B25014',[11,12,13]),v('B25014',8)),income]
  else:
   age=s('B18105',[12,15,28,31]);amb=s('B18105',[13,16,29,32]);row=[age,amb,rate(amb,age),rate(s('B11010',[5,12]),v('B25003',1)),rate(v('B08201',2),v('B08201',1)),rate(v('B25044',10),v('B25044',9)),rate(v('B25024',10),v('B25024',1)),income]
  out[g]={'name':name.split(',')[0],'fields':row,'source_estimates':cells}
  if n==2:out[g]['raw_ratios']={'LEPSharePct':[lep,hh],'NoInternetPct':[v('B28002',13),v('B28002',1)],'NoVehiclePct':[v('B08201',2),v('B08201',1)],'SevereRentBurdenPct':[s('B25070',[8,9,10]),v('B25070',1)-v('B25070',11)],'CrowdedRenterPct':[s('B25014',[11,12,13]),v('B25014',8)]}
  if n==4:out[g]['raw_ratios']={'AmbDiffPct':[amb,age],'SeniorLivingAloneSharePct':[s('B11010',[5,12]),v('B25003',1)],'NoVehiclePct':[v('B08201',2),v('B08201',1)],'RenterNoVehiclePct':[v('B25044',10),v('B25044',9)],'MobileHomePct':[v('B25024',10),v('B25024',1)]}
 state=out[st]['fields'];selected=[]
 for g,r in out.items():
  if g==st:continue
  x=r['fields'];path=''
  if n==1:keep=x[0]>=4000 and all(x[i]>state[i] for i in [1,2,3]) and x[4]<state[4]
  elif n==2:
   flags=[x[5]>state[5],x[6]>state[6]];path='BOTH' if all(flags) else 'RENT' if flags[0] else 'CROWD';keep=x[0]>=2500 and x[1]>=500 and all(x[i]>state[i] for i in [2,3,4]) and x[7]<state[7] and any(flags)
  elif n==3:
   flags=[x[5]>state[5],x[6]>state[6],x[4]>state[4]];path='+'.join(label for flag,label in zip(flags,['BENEFITS','CROWD','MOBILITY']) if flag);keep=x[0]>=75000 and x[1]>=2000 and x[2]>state[2] and x[3]>state[3] and x[7]<state[7] and sum(flags)>=2
  else:
   flags=[x[3]>state[3],x[6]>state[6],x[4]>state[4],x[5]>state[5]];path='+'.join(label for flag,label in zip(flags,['ALONE','MOBILE_HOME','NO_VEHICLE','RENTER_NO_VEHICLE']) if flag);keep=x[0]>=15000 and x[1]>=4000 and x[2]>state[2] and x[7]<state[7] and sum(flags)>=2
  r['selected']=keep;r['path']=path
  if n in [2,4]:
   conditions=({'renters_at_least_2500':x[0]>=2500,'LEP_at_least_500':x[1]>=500,'LEP_above_state':x[2]>state[2],'internet_above_state':x[3]>state[3],'vehicle_above_state':x[4]>state[4],'income_below_state':x[7]<state[7],'at_least_one_stress':any(flags)} if n==2 else {'senior_at_least_15000':x[0]>=15000,'difficulty_at_least_4000':x[1]>=4000,'difficulty_above_state':x[2]>state[2],'income_below_state':x[7]<state[7],'at_least_two_barriers':sum(flags)>=2})
   r['conditions']=conditions;r['excluded_reasons']=[k for k,v in conditions.items() if not v];r['branch_flags']=flags
  if keep:selected.append([r['name']]+[format((Decimal(v.numerator)/Decimal(v.denominator)).quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'f') if isinstance(v,F) else str(v) for v in x]+([path] if n>1 else []))
 selected.sort(key=lambda r:r[0]);return out,selected
report=[]
for n in range(1,5):
 candidates,rows=calculate(n)
 (D/f'census_{n:03d}-candidates.json').write_text(json.dumps(candidates,default=lambda x:{'numerator':x.numerator,'denominator':x.denominator},ensure_ascii=False,indent=2))
 for task in [t for t in tasks if t['task_id'].startswith(f'census_{n:03d}')]:
  expected=[[f.strip() for f in row.strip().split('|')] for row in task['oracle_answer'].split(',')];diff=[]
  for i in range(max(len(rows),len(expected))):
   a=rows[i] if i<len(rows) else [];b=expected[i] if i<len(expected) else []
   for j in range(max(len(a),len(b))):
    if (a[j] if j<len(a) else None)!=(b[j] if j<len(b) else None):diff.append({'row':i,'column':j,'actual':a[j] if j<len(a) else None,'expected':b[j] if j<len(b) else None})
  report.append({'task':task['task_id'],'candidates':len(candidates)-1,'computed_rows':len(rows),'expected_rows':len(expected),'numeric_match':not diff,'differences':diff,'semantic_status':'consistent with revised population definitions' if n in [2,4] else 'consistent with verified formula','computed_answer':','.join('|'.join(row) for row in rows)})
(D/'legacy-revised-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps([{k:v for k,v in r.items() if k!='computed_answer'} for r in report],indent=2))

assert len(report)==8 and all(r['numeric_match'] for r in report)

for task in tasks:
 if task['task_id'].startswith('census_002'):assert 'any tenure' in task['instruction'] and 'renter-household cells' not in task['rubric']['normalization']['LEPHH']
 if task['task_id'].startswith('census_004'):assert 'civilian noninstitutionalized' in task['instruction'] and 'B01001 and B18105' not in json.dumps(task['metadata'])
