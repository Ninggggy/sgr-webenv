"""Independent XML/TXT reconciliation, not the application's parser."""
import sqlite3,gzip,xml.etree.ElementTree as ET,json,re,zlib,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data';db=sqlite3.connect('file:'+str(D/'cellosaurus.sqlite')+'?mode=ro',uri=True)
checks=[];differences=[];counts={};seen=0;start=time.time()
sample=set();snapshots={}
with gzip.open(D/'cellosaurus.xml.gz','rb') as f:
 root=None;stack=[]
 for event,e in ET.iterparse(f,events=['start','end']):
  if event=='start':stack.append(e);continue
  if e.tag=='release':checks.append({'name':'XML version/count','pass':e.attrib['version']=='56.0' and e.attrib['nb-cell-lines']=='168970','actual':e.attrib})
  if e.tag=='cell-line':
   seen+=1;ac=e.findtext('accession-list/accession[@type="primary"]');name=e.findtext('name-list/name[@type="identifier"]');r=db.execute('SELECT name,category,raw FROM cell WHERE ac=?',(ac,)).fetchone()
   if not r:differences.append({'ac':ac,'kind':'missing_record'})
   else:
    txt=zlib.decompress(r[2]).decode();fields={}
    for l in txt.splitlines():
     if re.match(r'^[A-Z]{2}   ',l):fields.setdefault(l[:2],[]).append(l[5:])
    expected={'name':name,'category':e.attrib['category'],'parents':sorted(x.attrib['accession'] for x in e.findall('derived-from/xref[@database="Cellosaurus"]')),'same_individual':sorted(x.attrib['accession'] for x in e.findall('same-origin-as/xref[@database="Cellosaurus"]')),'taxa':sorted(x.attrib['accession'] for x in e.findall('species-list/xref')),'aliases':sorted((x.text or '') for x in e.findall('name-list/name[@type="synonym"]'))}
    actual={'name':r[0],'category':r[1],'parents':sorted(v.split()[0] for v in fields.get('HI',[])),'same_individual':sorted(v.split()[0] for v in fields.get('OI',[])),'taxa':sorted(re.findall(r'NCBI_TaxID=(\d+)',' '.join(fields.get('OX',[])))),'aliases':sorted(v[0] for v in db.execute("SELECT name FROM alias WHERE ac=? AND kind='synonym'",(ac,)))}
    if actual!=expected:differences.append({'ac':ac,'expected':expected,'actual':actual})
    if ac in sample:snapshots[ac]={'fields':fields,'xml':expected}
   cat=e.attrib['category'];counts[cat]=counts.get(cat,0)+1
   e.clear()
   if len(stack)>1:stack[-2].remove(e)
  elif e.tag=='reference' and len(stack)>1 and stack[-2].tag=='publication-list':e.clear();stack[-2].remove(e)
  stack.pop()
checks.extend([{'name':'Full XML record count','pass':seen==168970,'actual':seen},{'name':'All identity/category/parent/donor/species/alias comparisons','pass':not differences,'differences':len(differences)},{'name':'SQLite structural check','pass':db.execute('PRAGMA quick_check').fetchone()[0]=='ok'}])
report={'checks':checks,'differences':differences,'categories':counts,'samples':snapshots,'seconds':time.time()-start}
(R/'validation/data-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(checks,indent=2))

assert all(c["pass"] for c in checks), "Source reconciliation failed"
