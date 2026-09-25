#!/usr/bin/env python3
"""Stream historical sequence releases into an independently staged SQLite database."""
import argparse,csv,io,json,re,sqlite3,zipfile,collections,pathlib,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
CORE=set('B01001 B28002 B11010 B08201 B19013 B25003 C16002 B25070 B25014 B16004 B28011 B09010 B18105 B25044 B25024'.split())
SPECIAL={'-999999999':'N','-888888888':'(X)','-666666666':'-','-555555555':'*****','-333333333':'***','-222222222':'**'}
# Summary File numeric special encodings, not API negative sentinels.
def number(raw,kind='estimate'):
 raw=raw.strip()
 if kind=='moe' and raw=='-1':return None,'Not available (no MOE for this measure)'
 if kind=='moe' and raw=='0':return 0,'*****'
 if raw=='.':return None,'Not available (Summary File .)'
 if raw in ['', '..','...','N','(X)','-','**','***','*****']:return None,raw or None
 if raw in SPECIAL:return None,SPECIAL[raw]
 x=float(raw)
 if x==-999999999:return None,'N'
 return int(x) if x.is_integer() else x,None

def layout(year,product):
 n=product[-1];folder=ROOT/f'sources/summary/{year}/{product}'
 rows=list(csv.DictReader((folder/f'ACS_{n}yr_Seq_Table_Number_Lookup.txt').open(encoding='cp1252')))
 seqs=collections.defaultdict(dict);universes={};titles={};pos=None
 for r in rows:
  t=r['Table ID'];seq=r['Sequence Number'];line=r['Line Number']
  if r['Start Position']:pos=int(r['Start Position'])-1;titles[t]=r['Table Title']
  if r['Table Title'].startswith('Universe:'):universes[t]=r['Table Title'].split(':',1)[1].strip()
  if line and re.fullmatch(r'\d+',line):
   if pos is None:raise ValueError('Missing table sequence start')
   v=f'{t}_{int(line):03d}E';assert pos not in seqs[seq];seqs[seq][pos]=(t,v);pos+=1
 return seqs,universes,titles

def install_metadata(c,year,product,universes,titles):
 folder=ROOT/f'sources/api/{year}/{product}';full=folder/'variables.json'
 if product=='acs5':d=json.loads(full.read_text())['variables']
 else:
  d={}
  for t in CORE:
   f=folder/(t+'.json')
   if f.exists():d.update(json.loads(f.read_text())['variables'])
 for t,title in titles.items():
  c.execute('INSERT INTO tables VALUES (?,?,?,?,?) ON CONFLICT(year,product,id) DO UPDATE SET universe=excluded.universe',(year,product,t,title,universes[t]))
 for v,a in d.items():
  if not re.fullmatch(r'[BC]\d+[A-Z]{0,3}_\d+E',v):continue
  t=v.split('_')[0]
  if t not in titles:continue
  title=titles[t].upper()
  unit='Count'
  if 'DOLLARS' in title:unit='US dollars'
  if 'MEDIAN AGE' in title:unit='Years'
  if 'MEDIAN YEAR' in title:unit='Calendar year'
  if 'MEDIAN NUMBER OF ROOMS' in title:unit='Rooms'
  if 'AVERAGE HOUSEHOLD SIZE' in title:unit='Persons per household'
  if 'AVERAGE FAMILY SIZE' in title:unit='Persons per family'
  if 'GINI INDEX' in title:unit='Index (0–1)'
  if 'TRAVEL TIME' in title and ('MEAN' in title or 'AGGREGATE' in title):unit='Minutes'
  if 'HOURS' in title and ('MEAN' in title or 'AGGREGATE' in title):unit='Hours'
  if ('PERCENT' in title and ('MEDIAN' in title or title.startswith('PERCENT'))) or title.startswith('SHARES OF AGGREGATE'):unit='Percent'
  # Existing verified full labels take precedence for legacy columns.
  c.execute('INSERT INTO variables VALUES (?,?,?,?,?,?) ON CONFLICT(year,product,id) DO UPDATE SET unit=excluded.unit',(year,product,t,v,a['label'],unit))
 return d

def geo_columns(year,product):
 with zipfile.ZipFile(ROOT/f'sources/summary/{year}/{product}/{year}_{product[-1]}yr_Summary_FileTemplates.zip') as z:
  name=next(n for n in z.namelist() if 'GeoFileTemplate' in n);b=z.read(name)
 if name.endswith('.xls'):
  import xlrd
  return xlrd.open_workbook(file_contents=b).sheet_by_index(0).row_values(0)
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
  strings=[''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  row=ET.fromstring(z.read('xl/worksheets/sheet1.xml')).find('.//m:row',ns)
  return [strings[int(c.find('m:v',ns).text)] for c in row]

def batch(c,archive,year,product,core_only=False):
 seqs,universes,titles=layout(year,product);definitions=install_metadata(c,year,product,universes,titles)
 active={t for t in titles if not core_only or t in CORE};wanted={v for seq in seqs.values() for t,v in seq.values() if t in active}
 if wanted-set(definitions):raise ValueError('API definitions missing: '+str(sorted(wanted-set(definitions))[:20]))
 with zipfile.ZipFile(archive) as z:
  n=product[-1];gname=next(k for k in z.namelist() if re.fullmatch(f'g{year}{n}[a-z]{{2}}.csv',k));gs={}
  names=geo_columns(year,product);assert names.index('GEOID')==48 and names.index('NAME')==49
  for g in csv.reader(io.TextIOWrapper(z.open(gname),encoding='cp1252')):
   if g[2] not in ['040','050'] or g[3]!='00':continue
   assert len(g)==len(names),(gname,len(g),len(names))
   if g[2]=='040' and re.sub('[^a-z]','',g[49].lower())!=re.sub('[^a-z]','',archive.name.split('_')[0].lower()):raise ValueError('Archive state does not match requested state')
   gid=g[9]+(g[10] if g[2]=='050' else '');assert g[48]=='05000US'+gid if g[2]=='050' else g[48]=='04000US'+gid
   gs[g[4]]=(gid,g[49]);c.execute('INSERT OR REPLACE INTO published_geographies VALUES (?,?,?,?,?)',(year,product,gid,g[49],str(archive.relative_to(ROOT))))
   c.execute('INSERT OR IGNORE INTO geographies VALUES (?,?,?,?,?)',(year,gid,gid[:2],g[49],'state' if len(gid)==2 else 'county'))
  if not gs:raise ValueError('No whole-state/county geography records')
  states={g[0][:2] for g in gs.values()};assert len(states)==1
  state=next(iter(states));stusab=gname[6:8];c.execute('INSERT OR REPLACE INTO publication_scopes VALUES (?,?,?,?)',(year,product,state,str(archive.relative_to(ROOT))))
  counts=collections.Counter();special=collections.Counter();overlap=0;differences=[]
  legacy_tables={r[0] for r in c.execute("SELECT table_id FROM sources WHERE year=? AND product=? AND file NOT LIKE '%#%'",(year,product))} if (year,state) in [(2016,'42'),(2017,'06'),(2018,'37'),(2019,'35')] else set()
  for seq,mapping in seqs.items():
   cols={p:tv for p,tv in mapping.items() if tv[0] in active}
   if not cols:continue
   es=next((k for k in z.namelist() if re.fullmatch(f'e{year}{n}[a-z]{{2}}{seq}000.txt',k)),None)
   if not es:raise ValueError('Missing sequence '+seq)
   ms='m'+es[1:]
   def read(name):
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(name),encoding='cp1252')):
     if row[5] not in gs:continue
     assert row[0]=='ACSSF' and row[1]==f'{year}{name[0]}{n}' and row[4]==seq and row[2].lower()==stusab
     if row[5] in out:raise ValueError('Duplicate LOGRECNO')
     out[row[5]]=row
    if set(out)!=set(gs):raise ValueError('Sequence has incomplete geography rows')
    return out
   e,m=read(es),read(ms)
   for rec,(gid,name) in gs.items():
    values=[]
    for pos,(t,v) in cols.items():
     ev,ea=number(e[rec][pos]);mv,ma=number(m[rec][pos],'moe');counts[t]+=1
     if ea:special['E '+ea]+=1
     if ma:special['M '+ma]+=1
     old=c.execute('SELECT estimate,moe,ea,ma FROM cells WHERE year=? AND product=? AND geo=? AND variable=?',(year,product,gid,v)).fetchone()
     if old is not None:
      overlap+=1
      if tuple(old)!=(ev,mv,ea,ma):differences.append({'geo':gid,'variable':v,'old':tuple(old),'summary':(ev,mv,ea,ma)})
      # Legacy formatted annotations may differ by channel. Preserve verified existing values.
      if t in legacy_tables:continue
      c.execute('DELETE FROM cells WHERE year=? AND product=? AND geo=? AND variable=?',(year,product,gid,v))
     values.append((year,product,t,gid,v,ev,mv,ea,ma))
    c.executemany('INSERT INTO cells VALUES (?,?,?,?,?,?,?,?,?)',values)
  for t,count in counts.items():
   expected=sum(1 for v in wanted if v.startswith(t+'_'))
   if count!=len(gs)*expected:raise ValueError('Incomplete table '+t)
   c.execute('INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?)',(str(archive.relative_to(ROOT))+'#'+t,year,product,t,len(gs),expected))
  return {'archive':str(archive.relative_to(ROOT)),'year':year,'product':product,'state':state,'geographies':dict(gs),'tables':len(counts),'cells':sum(counts.values()),'special':dict(special),'overlap_cells':overlap,'channel_differences':differences,'expanded_bytes':sum(i.file_size for i in z.infolist()),'compressed_bytes':archive.stat().st_size}

def main():
 p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--states',nargs='+',default=['Delaware']);p.add_argument('--years',nargs='+',type=int,default=[2016,2017,2018,2019]);p.add_argument('--products',nargs='+',default=['acs5','acs1']);p.add_argument('--report',required=True);a=p.parse_args()
 dest=pathlib.Path(a.database)
 if dest.resolve()==(ROOT/'data/census.sqlite').resolve():raise ValueError('Use an independent staging database')
 if not dest.exists():
  with sqlite3.connect(ROOT/'data/census.sqlite') as src,sqlite3.connect(dest) as out:src.backup(out)
 c=sqlite3.connect(dest);c.executescript('CREATE TABLE IF NOT EXISTS published_geographies(year INTEGER,product TEXT,geo TEXT,name TEXT,source TEXT,PRIMARY KEY(year,product,geo)); CREATE TABLE IF NOT EXISTS publication_scopes(year INTEGER,product TEXT,state TEXT,source TEXT,PRIMARY KEY(year,product,state));CREATE TABLE IF NOT EXISTS table_coverage(year INTEGER,product TEXT,table_id TEXT,geo TEXT,variables INTEGER,PRIMARY KEY(year,product,table_id,geo));')
 reports=[]
 for y in a.years:
  for product in a.products:
   for state in a.states:
    name=state+'_All_Geographies'+('_Not_Tracts_Block_Groups' if product=='acs5' else '')+'.zip';archive=ROOT/f'sources/summary/{y}/{product}/{name}'
    with c:r=batch(c,archive,y,product,product=='acs1');reports.append(r)
    pathlib.Path(a.report).write_text(json.dumps(reports,indent=2));print(y,product,state,r['tables'],r['cells'],flush=True)
 with c:
  c.execute('DELETE FROM table_coverage');c.execute('INSERT INTO table_coverage SELECT year,product,table_id,geo,count(*) FROM cells GROUP BY year,product,table_id,geo HAVING sum(estimate IS NOT NULL OR moe IS NOT NULL OR ea IS NOT NULL OR ma IS NOT NULL)>0')
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 c.close()
if __name__=='__main__':main()
