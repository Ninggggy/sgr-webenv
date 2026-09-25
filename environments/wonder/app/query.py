"""National joint-distribution query engine. No author evidence is accessible here."""
import collections,json,os,pathlib,sqlite3
from decimal import Decimal,ROUND_HALF_UP
ROOT=pathlib.Path(__file__).resolve().parent;DATA=pathlib.Path(os.environ.get('WONDER_DATA','/data'))
DICTIONARY=json.loads((ROOT/'dictionary.json').read_text());CAUSES=json.loads((ROOT/'causes.json').read_text())
APP_VERSION='0.3'
DATA_VERSION='2026.09.18'
SHARED=['year','month','race','origin','place','mother_age','sex','gestation','weight','plurality']
DEATH=['death_age','death_days','cause','leading']
EXPRESSIONS={k:k for k in SHARED+['death_age','death_days']}
EXPRESSIONS['month']='CAST(CAST(month AS INTEGER) AS TEXT)'
EXPRESSIONS['origin_recode']="CASE WHEN origin='7' THEN '5' ELSE origin END"
EXPRESSIONS.update(hispanic="CASE WHEN origin='0' THEN '2186-5' WHEN origin IN ('9','10','100') THEN '9' ELSE '2135-2' END",place6="CASE WHEN place IN ('3','4','5') THEN '4' WHEN place='6' THEN '3' WHEN place='7' THEN '5' ELSE place END",place3="CASE WHEN place='1' THEN '1' WHEN place='9' THEN '3' WHEN place='10' THEN '100' ELSE '2' END")

def catalog():
 out={}
 for product in ['natality','linked']:
  docs=[json.loads(p.read_text()) for p in sorted(DATA.glob(product+'-*.json')) if p.with_suffix('.sqlite').exists()]
  out[product]={'years':[str(x['year']) for x in docs],'records':[{ 'year':x['year'],'origin_resolution':x.get('origin_resolution'),'unsupported_dimensions':x.get('layout',{}).get('unsupported_dimensions',[]),'limitations':x.get('layout',{}).get('limitations',[]),'members':{k:{a:v[a] for a in ['raw_records','us_resident_records','joint_rows']} for k,v in x['members'].items()}} for x in docs]}
 for product,info in out.items():
  for record in info['records']:
   if product=='natality' and record['year']==2021 and record.get('origin_resolution')!='expanded':
    record['limitations']=['MHISPX is unusable in the 2021 public archive. MHISP_R retains Mexican, Puerto Rican, Cuban, Central/South American, Non-Hispanic and Unknown. Dominican and Other/Unknown Hispanic are combined. Use origin_recode for all categories or filter origin to unambiguous categories.']
    record['unsupported_dimensions']=[d for d in record['unsupported_dimensions'] if d!='origin']
    record['partial_dimensions']={'origin':{'group_all':False,'unambiguous_filters':['0','2148-5','2180-8','2182-4','4','9'],'combined_filter':['5','7'],'coarse_dimension':'origin_recode'}}
 return out

def metadata():return {'version':APP_VERSION,'data_version':DATA_VERSION,'datasets':catalog(),'dimensions':DICTIONARY,'scope':'United States residents (50 states and District of Columbia). State, county and maps are not supported.'}
def check_version(q):
 if q.get('version',APP_VERSION)!=APP_VERSION or q.get('data_version',DATA_VERSION)!=DATA_VERSION:
  raise ValueError(f"Saved request/result uses application {q.get('version','unspecified')} and data {q.get('data_version','unspecified')}; this service provides application {APP_VERSION}, data {DATA_VERSION}. The old release is not loaded in this session. It cannot be restored or reinterpreted here. Open a new request to use the current release; an administrator can deploy the archived release separately.")

def validate(q):
 if not isinstance(q,dict):raise ValueError('Request must be an object')
 allowed={'dataset','version','data_version','groups','filters','measures','precision','rate_per','show_zeros','show_suppressed','title'}
 if set(q)-allowed:raise ValueError('Unsupported request parameters: '+', '.join(sorted(set(q)-allowed)))
 p=q.get('dataset');cat=catalog()
 if p not in cat:raise ValueError('Unsupported database')
 check_version(q)
 q={**q,'version':APP_VERSION,'data_version':DATA_VERSION};groups=q.get('groups',['year']);filters=q.get('filters',{})
 if not isinstance(groups,list) or not 1<=len(groups)<=5 or len(set(groups))!=len(groups):raise ValueError('Select one to five different Group Results By variables')
 dimensions=set(DICTIONARY)-({'month'} if p=='linked' else set(DEATH))
 if any(k not in dimensions for k in groups):raise ValueError('Unsupported grouping for this database')
 if not isinstance(filters,dict) or set(filters)-dimensions:raise ValueError('Unsupported filter (geographic queries are not supported)')
 if 'leading' in filters:raise ValueError('Use the ICD-10 cause list to filter causes')
 if 'leading' in groups and len(groups)!=1:raise ValueError('15 Leading Causes cannot be cross-tabulated')
 for family in [('place','place6','place3'),('origin','origin_recode','hispanic'),('death_age','death_days')]:
  active=set(groups).union(k for k,v in filters.items() if v and v!=['*All*'])
  if len(active.intersection(family))>1:raise ValueError('Select one classification only: '+', '.join(family))
 for k,v in filters.items():
  if not isinstance(v,list) or not v or any(not isinstance(x,str) for x in v):raise ValueError('Select at least one value or All for '+k)
  if '*All*' in v and len(v)!=1:raise ValueError('All cannot be combined with individual values')
  opts=set(cat[p]['years']) if k=='year' else {x[0] for x in DICTIONARY[k]['options']}
  if v!=['*All*'] and set(v)-opts:raise ValueError('Unsupported '+k+' value: '+', '.join(sorted(set(v)-opts)))
 years=filters.get('year',[cat[p]['years'][-1]] if cat[p]['years'] else [])
 if years==['*All*']:years=cat[p]['years']
 if not years:raise ValueError('No imported years are available for this database')
 if '7' in filters.get('origin',[]) and any(int(y)<(2018 if p=='natality' else 2019) for y in years):raise ValueError('Dominican origin is not separately available in one or more selected years')
 active=set(groups).union(k for k,v in filters.items() if v!=['*All*'])
 for record in cat[p]['records']:
  if str(record['year']) not in years:continue
  unsupported=active.intersection(record['unsupported_dimensions'])
  if p=='natality' and record['year']==2021 and record.get('origin_resolution')!='expanded' and 'origin' in active:
   selected=filters.get('origin',['*All*'])
   ambiguous=set(selected).intersection({'5','7'})
   # MHISP_R retains each unambiguous category, and the union of Dominican + Other.
   if selected!=['*All*'] and (not ambiguous or ambiguous=={'5','7'} and 'origin' not in groups):unsupported.discard('origin')
   else:raise ValueError('Natality 2021 cannot separate Dominican from Other and Unknown Hispanic. Choose Hispanic Origin Recode (Dominican combined), broad Hispanic Origin, or explicitly select Mexican, Puerto Rican, Cuban, Central or South American, Non-Hispanic, or Unknown. Expanded grouping of all categories requires excluding 2021 yourself; All Years includes 2021. A combined Dominican + Other filter is supported without expanded grouping.')
  if unsupported:raise ValueError('Unsupported dimension for '+str(record['year'])+': '+', '.join(sorted(unsupported))+'. '+ ' '.join(record['limitations']))
 q['filters']={**filters,'year':years};q['groups']=groups
 q['measures']=q.get('measures',['births'] if p=='natality' else ['deaths','births','rate'])
 if not isinstance(q['measures'],list) or not q['measures'] or len(set(q['measures']))!=len(q['measures']):raise ValueError('Select different measures')
 if set(q['measures'])-({'births','percent'} if p=='natality' else {'deaths','births','rate'}):raise ValueError('Unsupported measure')
 q['precision']=q.get('precision',2);q['rate_per']=q.get('rate_per',1000)
 if type(q['precision'])!=int or not 0<=q['precision']<=9:raise ValueError('Precision must be between 0 and 9')
 if type(q['rate_per'])!=int or q['rate_per'] not in [1000,100000]:raise ValueError('Unsupported rate multiplier')
 for k in ['show_zeros','show_suppressed']:
  if k in q and type(q[k])!=bool:raise ValueError('Invalid display option')
 if 'leading' in groups:
  if q.get('show_zeros',False) or q.get('show_suppressed',False):raise ValueError('15 Leading Causes does not permit Show Zero Values or Show Suppressed Values. Set both options to false.')
  q['show_zeros']=False;q['show_suppressed']=False
 else:
  q.setdefault('show_zeros',False);q.setdefault('show_suppressed',True)
 if not isinstance(q.get('title',''),str) or len(q.get('title',''))>200:raise ValueError('Title is limited to 200 characters')
 return q

def cause_leaves(code):return [k for k,v in CAUSES.items() if code in v['ancestors']]
def aggregate(con,table,groups,filters):
 # Birth denominator deliberately omits every death-only dimension and predicate.
 g=[k for k in groups if table=='deaths' or k not in DEATH];clauses=[];params=[]
 for k,values in filters.items():
  if values==['*All*'] or table=='births' and k in DEATH:continue
  if k=='cause':
   values=sorted({x for v in values for x in cause_leaves(v)});expr='cause_leaf'
  else:
   expr=EXPRESSIONS[k]
   if k=='origin' and '5' in values and '7' in values and con.execute('PRAGMA database_list').fetchone()[2].endswith('natality-2021.sqlite') and json.loads((DATA/'natality-2021.json').read_text()).get('origin_resolution')!='expanded':values=[v for v in values if v!='7']
  clauses.append(expr+' IN ('+','.join('?' for _ in values)+')');params+=values
 where=' WHERE '+' AND '.join(clauses) if clauses else ''
 # Cause hierarchy may overlap, so total is queried independently of grouped rows.
 raw_groups=[k if k not in ['cause','leading'] else 'cause_leaf' for k in g]
 expressions=[EXPRESSIONS.get(k,k) for k in raw_groups]
 prefix=','.join(expressions)+',' if expressions else ''
 sql=f'SELECT {prefix} SUM(n),SUM(weight_micro) FROM {table}{where}'+(' GROUP BY '+','.join(expressions) if expressions else '')
 out=collections.defaultdict(lambda:[0,0])
 for row in con.execute(sql,params):
  if row[-2] is None:continue
  key=tuple(row[:-2]);keys=[key]
  if 'cause' in g or 'leading' in g:
   pos=g.index('cause' if 'cause' in g else 'leading');leaf=key[pos]
   if leaf not in CAUSES:raise ValueError('Unmapped cause code in imported data')
   ancestors=CAUSES[leaf]['ancestors']
   if 'leading' in g:ancestors=[k for k in ancestors if CAUSES[k]['rankable']]
   if 'leading' in g and len(ancestors)>1:raise ValueError('Ambiguous rankable cause mapping')
   keys=[key[:pos]+(v,)+key[pos+1:] for v in ancestors]
  for key in keys:out[key][0]+=row[-2];out[key][1]+=row[-1]
 return out

def dictLabel(k,c):return dict(DICTIONARY[k]['options']).get(c,c)
def rounded_count(w):return int((Decimal(w)/1000000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def format_decimal(v,p):return str(v.quantize(Decimal(1).scaleb(-p),rounding=ROUND_HALF_UP))
def suppressed(n):return 0<n<10

def query(request):
 q=validate(request);p=q['dataset'];groups=q['groups'];filters=q['filters'];births=collections.defaultdict(lambda:[0,0]);deaths=collections.defaultdict(lambda:[0,0]);total_b=total_d=total_raw=0;prefix_b={i:collections.defaultdict(lambda:[0,0]) for i in range(1,len(groups))};prefix_d={i:collections.defaultdict(lambda:[0,0]) for i in range(1,len(groups))}
 for y in filters['year']:
  con=sqlite3.connect(f'file:{DATA}/{p}-{y}.sqlite?mode=ro',uri=True)
  try:
   for key,v in aggregate(con,'births',groups,filters).items():births[key][0]+=v[0];births[key][1]+=v[1]
   total_b+=aggregate(con,'births',[],filters).get((),[0,0])[0]
   if p=='linked':
    for key,v in aggregate(con,'deaths',groups,filters).items():deaths[key][0]+=v[0];deaths[key][1]+=v[1]
    t=aggregate(con,'deaths',[],filters).get((),[0,0]);total_raw+=t[0];total_d+=t[1]
   if 'cause' in groups:
    for level in prefix_b:
     for key,v in aggregate(con,'births',groups[:level],filters).items():prefix_b[level][key][0]+=v[0];prefix_b[level][key][1]+=v[1]
     for key,v in aggregate(con,'deaths',groups[:level],filters).items():prefix_d[level][key][0]+=v[0];prefix_d[level][key][1]+=v[1]
  finally:con.close()
 if 'cause' not in groups:
  bg=[k for k in groups if k not in DEATH]
  for level in prefix_b:
   for key,v in births.items():
    short=tuple(key[bg.index(k)] for k in groups[:level] if k not in DEATH);prefix_b[level][short][0]+=v[0];prefix_b[level][short][1]+=v[1]
   for key,v in deaths.items():
    short=key[:level];prefix_d[level][short][0]+=v[0];prefix_d[level][short][1]+=v[1]
 keys=set(births) if p=='natality' else set(deaths)
 death_only=[k for k in groups if k in DEATH]
 # Explicit zero rows: only declared requested dimensions, bounded to avoid accidental huge grids.
 if p=='linked' and (q.get('show_zeros',False) or not death_only):
  if not death_only:keys.update(births)
  elif set(death_only)<=set(['death_age','death_days','cause']):
   import itertools
   choices=[filters.get(k,[v[0] for v in DICTIONARY[k]['options']]) for k in death_only]
   choices=[[v[0] for v in DICTIONARY[k]['options']] if vs==['*All*'] else vs for k,vs in zip(death_only,choices)]
   for bk in births:
    for dk in itertools.product(*choices):
     bi=iter(bk);di=iter(dk);keys.add(tuple(next(di) if k in DEATH else next(bi) for k in groups))
 def cell(key):
  bk=tuple(v for k,v in zip(groups,key) if k not in DEATH);b=births.get(bk,[0,0])[0];raw,w=deaths.get(key,[0,0]);d=rounded_count(w)
  return b,raw,d
 order={k:{v[0]:i for i,v in enumerate(DICTIONARY[k]['options'])} for k in groups}
 if 'cause' in groups and filters.get('cause',['*All*'])!=['*All*']:
  pos=groups.index('cause');keys={k for k in keys if k[pos] in filters['cause']}
 keys=sorted(keys,key=lambda t:tuple(order[k].get(v,10000) for k,v in zip(groups,t)))
 ranks={}
 all_keys=list(keys)
 if 'leading' in groups:
  keys=sorted((k for k in keys if cell(k)[2]>=10),key=lambda k:(-cell(k)[2],k))
  prev=None;rank=0
  for i,k in enumerate(keys,1):
   d=cell(k)[2]
   if d!=prev:rank=i
   prev=d;ranks[k]=rank
  keys=[k for k in keys if ranks[k]<=15]
 suppressed_birth_cells=sum(suppressed(cell(k)[0]) for k in all_keys);suppressed_death_cells=sum(suppressed(cell(k)[2]) for k in all_keys) if p=='linked' else 0
 # Repeated denominators for death-only groups do not create separate birth cells.
 if death_only:suppressed_birth_cells=sum(suppressed(v[0]) for v in births.values())
 single_child=False
 for level in range(1,len(groups)):
  buckets=collections.defaultdict(list)
  for key in all_keys:buckets[key[:level]].append(suppressed(cell(key)[2] if p=='linked' else cell(key)[0]))
  if any(sum(v)==1 for v in buckets.values()):single_child=True
 hide_total_b=suppressed(total_b) or suppressed_birth_cells==1 or single_child
 hide_total_d=suppressed(rounded_count(total_d)) or suppressed_death_cells==1 or single_child
 # The original disables totals for overlapping 130-cause grouping. A cause filter
 # selects list entries, rather than adding ancestors/descendants to the output.
 # Keep extra protection only on displayed ancestors of a protected displayed row.
 # Unrelated branches never contain that row. This is deliberately stricter than
 # current original-site parent visibility; exact parent equivalence remains open.
 cause_protected=set()
 if 'cause' in groups:
  pos=groups.index('cause');available=set(keys)
  for key in keys:
   if suppressed(cell(key)[2]):
    for ancestor in CAUSES[key[pos]]['ancestors'][:-1]:
     parent=key[:pos]+(ancestor,)+key[pos+1:]
     if parent in available:cause_protected.add(parent)
 cause_suppression=bool(cause_protected)
 def measures(b,d,raw,total=False,protected=False):
  sb=suppressed(b) or total and hide_total_b;sd=suppressed(d) or total and hide_total_d or protected
  result={};state={}
  for m in q['measures']:
   status='Available';value=None
   if m=='births':value=str(b);status='Suppressed' if sb or p=='linked' and sd else 'Available'
   elif m=='deaths':value=str(d);status='Suppressed' if sd else 'Available'
   elif m=='percent':
    if sb or hide_total_b:status='Suppressed'
    elif not total_b:status='Undefined'
    else:value=format_decimal(Decimal(b)*100/total_b,q['precision'])
   elif m=='rate':
    if sd or sb:status='Suppressed'
    elif not b:status='Undefined'
    else:
     value=format_decimal(Decimal(d)*q['rate_per']/b,q['precision'])
     if d<20:status='Unreliable'
   if status=='Suppressed':value=None
   result[m]=value;state[m]=status
  return result,state
 rows=[]
 for key in keys:
  b,raw,d=cell(key);v,s=measures(b,d,raw,protected=key in cause_protected)
  if not q.get('show_suppressed',True) and all(x=='Suppressed' for x in s.values()):continue
  if p=='linked' and d==0 and not q.get('show_zeros',False):continue
  row={'codes':dict(zip(groups,key)),'labels':{k:dict(DICTIONARY[k]['options']).get(code,code) for k,code in zip(groups,key)},'values':v,'status':s}
  if key in ranks:row['rank']=ranks[key]
  rows.append(row)
 subtotals=[]
 for level in ([] if 'cause' in groups else prefix_b):
  prefkeys=set(prefix_b[level]) if p=='natality' else set(prefix_d[level])
  for key in sorted(prefkeys):
   bk=tuple(v for k,v in zip(groups[:level],key) if k not in DEATH);b=prefix_b[level].get(bk,[0,0])[0];raw,w=prefix_d[level].get(key,[0,0]);values,status=measures(b,rounded_count(w),raw,True)
   subtotals.append({'codes':dict(zip(groups[:level],key)),'labels':{**{k:dictLabel(k,c) for k,c in zip(groups[:level],key)},groups[level]:'Total'},'values':values,'status':status,'subtotal_level':level})
 display_rows=[]
 subtotal_lookup={(r['subtotal_level'],tuple(r['codes'].values())):r for r in subtotals}
 for i,row in enumerate(rows):
  display_rows.append(row);key=tuple(row['codes'][k] for k in groups);nextkey=tuple(rows[i+1]['codes'][k] for k in groups) if i+1<len(rows) else None
  for level in range(len(groups)-1,0,-1):
   if nextkey is None or key[:level]!=nextkey[:level]:
    subtotal=subtotal_lookup.get((level,key[:level]))
    if subtotal:display_rows.append(subtotal)
 tv,ts=measures(total_b,rounded_count(total_d),total_raw,True)
 if 'cause' in groups or 'leading' in groups:tv={m:None for m in q['measures']};ts={m:'Not Applicable' for m in q['measures']}
 return {'query':q,'totals_enabled':not set(groups).intersection({'cause','leading'}),'rows':rows,'display_rows':display_rows,'subtotals':subtotals,'total':{'values':tv,'status':ts},'units':{'births':'Live births','deaths':'Weighted infant deaths (rounded)','rate':f'Deaths per {q["rate_per"]:,} live births','percent':'Percent of selected births'},'notes':['National U.S. residents only; state, county and maps are unsupported.','Counts 1–9 are suppressed; a total with exactly one suppressed component is suppressed.','Birth denominators do not change with death-age or cause filters. Weighted deaths are rounded at each aggregation level before rates are calculated. Rates below 20 deaths are marked Unreliable.']+(['15 Leading Causes excludes totals, zero and suppressed rows; ranking uses rounded weighted deaths and includes ties at rank 15.'] if 'leading' in groups else [])+(['Totals and subtotals are disabled for the overlapping ICD-10 130 Cause List. Parent and child categories must not be added.'] if 'cause' in groups else [])+(['Displayed ancestors of suppressed cause rows receive additional protection. This is more conservative than observed WONDER parent visibility; exact parent-level equivalence remains unverified.'] if cause_suppression else [])}
