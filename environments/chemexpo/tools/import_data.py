"""Bounded, resumable ingestion of complete public exports, never oracle data."""
import csv, gzip, html, io, json, re, resource, shutil, sqlite3, sys, time, zipfile, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

def check_space():
    if shutil.disk_usage(DATA).free < 5*1024**3+128*1024**2:
        raise RuntimeError('Disk reserve reached; preserving partial import for inspection')

def rows(info):
    p=ROOT/info['file']
    if p.suffix=='.zip':
        with zipfile.ZipFile(p) as z:
            with z.open(next(n for n in z.namelist() if n.endswith('.csv'))) as f:
                yield from csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
    else:
        with gzip.open(p,'rt',encoding='utf-8-sig',newline='') as f:yield from csv.DictReader(f)

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS imports(source TEXT PRIMARY KEY,rows INTEGER NOT NULL,complete INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS puc(id INTEGER PRIMARY KEY,kind TEXT,level INTEGER,general TEXT,family TEXT,type TEXT,allowed TEXT,assumed TEXT,definition TEXT,direct INTEGER,cumulative INTEGER,parent INTEGER REFERENCES puc(id));
CREATE TABLE IF NOT EXISTS chemical(sid TEXT PRIMARY KEY,name TEXT,cas TEXT);
CREATE TABLE IF NOT EXISTS document(id INTEGER PRIMARY KEY,title TEXT,subtitle TEXT,date TEXT,source TEXT);
CREATE TABLE IF NOT EXISTS dictionary(kind TEXT,name TEXT,definition TEXT,category TEXT,PRIMARY KEY(kind,name));
CREATE TABLE IF NOT EXISTS record(id INTEGER PRIMARY KEY,source TEXT NOT NULL,ordinal INTEGER NOT NULL,doc INTEGER REFERENCES document(id),sid TEXT REFERENCES chemical(sid),puc INTEGER REFERENCES puc(id),product_title TEXT,method TEXT,keyword_set TEXT,function_name TEXT,raw_name TEXT,raw_cas TEXT,payload BLOB NOT NULL,UNIQUE(source,ordinal));
CREATE TABLE IF NOT EXISTS product(id INTEGER PRIMARY KEY,title TEXT,manufacturer TEXT,brand TEXT,puc INTEGER REFERENCES puc(id),method TEXT);
CREATE TABLE IF NOT EXISTS product_document(product INTEGER REFERENCES product(id),document INTEGER REFERENCES document(id),PRIMARY KEY(product,document));
CREATE TABLE IF NOT EXISTS document_keyword_total(doc INTEGER PRIMARY KEY REFERENCES document(id),keyword_count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS entity_id(kind TEXT,name TEXT,id INTEGER,PRIMARY KEY(kind,name),UNIQUE(kind,id));
CREATE TABLE IF NOT EXISTS relation_pages(name TEXT PRIMARY KEY,rows INTEGER);
'''

def main():
    started=time.time();manifest=json.loads((DATA/'sources.json').read_text())
    db=sqlite3.connect(DATA/'chemexpo.sqlite');db.executescript(SCHEMA)
    db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE')
    if not db.execute('SELECT COUNT(*) FROM puc').fetchone()[0]:
        ps=list(rows(manifest['pucs']))
        for r in ps:
            db.execute('INSERT INTO puc VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)',(int(r['PUC ID']),r['PUC kind'],int(r['PUC level']),r['General category'],r['Product family'],r['Product type'],r['Allowed attributes'],r['Assumed attributes'],r['Definition'],int(r['Product count']),int(r['Cumulative product count'])))
        # Parent identity includes kind; names alone are insufficient.
        for p in db.execute('SELECT id,kind,level,general,family FROM puc').fetchall():
            if p[2]>1:
                parent=db.execute('SELECT id FROM puc WHERE kind=? AND level=? AND general=? AND family=?',(p[1],p[2]-1,p[3],p[4] if p[2]==3 else '')).fetchall()
                if len(parent)!=1:raise ValueError(('Ambiguous parent',p,parent))
                db.execute('UPDATE puc SET parent=? WHERE id=?',(parent[0][0],p[0]))
        for source,key,desc,cat in [('attributes','PUC Attribute','Definition',None),('keywords','Keyword','Definition','Keyword Kind'),('functions','Function Category','Description',None)]:
            for r in rows(manifest[source]):db.execute('INSERT INTO dictionary VALUES(?,?,?,?)',(source,r[key],r[desc],r.get(cat,'') if cat else ''))
        db.commit()
    id_source=ROOT/'tools/dictionary-ids.json'
    if id_source.exists():
        for kind,entries in json.loads(id_source.read_text())['data'].items():
            for e in entries:
                name=e.get('name',e.get('title'))
                if not db.execute('SELECT 1 FROM dictionary WHERE kind=? AND name=?',(kind,name)).fetchone():raise ValueError(('Dictionary source mismatch',kind,name))
                db.execute('INSERT OR REPLACE INTO entity_id VALUES(?,?,?)',(kind,name,e['id']))
        db.commit()
    pmap={(k,g,f,t):i for i,k,g,f,t in db.execute('SELECT id,kind,general,family,type FROM puc')}
    kindmap={'Formulation':'FO','Article':'AR','Occupation':'OC','Industrial/Occupational':'OC'}
    for source in ['composition','presence','functional']:
        if not manifest.get(source,{}).get('complete'):print(source,'source unavailable',flush=True);continue
        status=db.execute('SELECT rows,complete FROM imports WHERE source=?',(source,)).fetchone()
        if status and status[1]:continue
        offset=status[0] if status else 0
        n=0
        for n,r in enumerate(rows(manifest[source]),1):
            if n<=offset:continue
            doc=int(r['Data Document ID']) if r.get('Data Document ID') else None
            sid=r.get('DTXSID') or None
            if doc is not None:db.execute('INSERT INTO document VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=CASE WHEN document.source IS NULL THEN excluded.title ELSE document.title END,subtitle=coalesce(document.subtitle,excluded.subtitle),date=CASE WHEN document.source IS NULL THEN excluded.date ELSE document.date END,source=coalesce(document.source,excluded.source)',(doc,r.get('Data Document Title',''),r.get('Data Document Subtitle'),r.get('Document Date',''),r.get('Data Source','')))
            if sid:db.execute('INSERT OR IGNORE INTO chemical VALUES(?,?,?)',(sid,r.get('Curated Chemical Name',''),r.get('Curated CAS','')))
            kind=kindmap.get(r.get('PUC Kind'),r.get('PUC Kind'))
            pk=(kind,r.get('PUC General Category',''),r.get('PUC Product Family',''),r.get('PUC Product Type',''))
            puc=pmap.get(pk)
            if pk[1] and puc is None and kind!='Unknown':raise ValueError(('Unresolved PUC path',pk,n))
            payload=zlib.compress(json.dumps(list(r.values()),ensure_ascii=False,separators=(',',':')).encode(),level=3)
            db.execute('INSERT INTO record(source,ordinal,doc,sid,puc,product_title,method,keyword_set,function_name,raw_name,raw_cas,payload) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(source,n,doc,sid,puc,r.get('Product Name'),r.get('PUC Classification Method'),r.get('Keyword Set'),r.get('Harmonized Functional Use') or r.get('Harmonized Function'),r.get('Raw Chemical Name'),r.get('Raw CAS'),payload))
            if n%10000==0:
                db.execute('INSERT OR REPLACE INTO imports VALUES(?,?,0)',(source,n));db.commit();check_space()
                if n%100000==0:print(source,n,'db_bytes',(DATA/'chemexpo.sqlite').stat().st_size,flush=True)
        db.execute('INSERT OR REPLACE INTO imports VALUES(?,?,1)',(source,n));db.commit();print(source,'complete',n,flush=True)
    if '--refresh-relations' in sys.argv:
        db.execute('DELETE FROM relation_pages');db.commit()
    for path in sorted((DATA/'relations').glob('*.json.gz')):
        if db.execute('SELECT 1 FROM relation_pages WHERE name=?',(path.name,)).fetchone():continue
        with gzip.open(path,'rt') as f:rs=json.load(f)['data']
        for r in rs:
            def ident(s,entity):
                m=re.search('/'+entity+r'/(\d+)/',s or '');return int(m[1]) if m else None
            def text(s):return html.unescape(re.sub('<[^>]*>','',s or ''))
            pid,doc,puc=ident(r[0],'product'),ident(r[3],'datadocument'),ident(r[4],'puc')
            if pid is None or doc is None:raise ValueError('Missing public relationship identity')
            db.execute('INSERT OR IGNORE INTO document VALUES(?,?,NULL,NULL,NULL)',(doc,text(r[3])))
            db.execute('INSERT OR REPLACE INTO product VALUES(?,?,?,?,?,?)',(pid,text(r[0]),text(r[1]) if r[1] is not None else None,text(r[2]) if r[2] is not None else None,puc,text(r[6]) if r[6] is not None else None))
            db.execute('INSERT OR IGNORE INTO product_document VALUES(?,?)',(pid,doc))
        db.execute('INSERT INTO relation_pages VALUES(?,?)',(path.name,len(rs)));db.commit();check_space()
    for name,cols in [('record_sid','sid,source,puc'),('record_doc','doc,source'),('record_puc','puc,sid'),('record_function','function_name'),('product_puc','puc'),('product_document_doc','document')]:
        table='product_document' if name=='product_document_doc' else ('product' if name=='product_puc' else 'record')
        check_space();db.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table}({cols})');db.commit()
    # The official chemical keyword widget compares record tags with the union of document tags.
    doc_tags={}
    for doc,tags in db.execute("SELECT doc,keyword_set FROM record WHERE source='presence' AND coalesce(keyword_set,'')<>''"):
        if doc is not None:doc_tags.setdefault(doc,set()).update(t.strip() for t in tags.split(';') if t.strip())
    db.execute('DELETE FROM document_keyword_total')
    db.executemany('INSERT INTO document_keyword_total VALUES(?,?)',((doc,len(tags)) for doc,tags in doc_tags.items()));db.commit()
    # Only derived index content is rebuilt, never source records.
    db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(kind UNINDEXED,entity_id UNINDEXED,title,body,tokenize="unicode61")')
    db.execute('DELETE FROM search')
    for sql in ["SELECT 'chemical',c.sid,c.name,c.cas||' '||coalesce((SELECT group_concat(alias,' ') FROM (SELECT DISTINCT raw_name||' '||raw_cas alias FROM record WHERE sid=c.sid)), '') FROM chemical c","SELECT 'document',id,title,coalesce(subtitle,'')||' '||coalesce(source,'') FROM document","SELECT 'product',id,title,coalesce(brand,'')||' '||coalesce(manufacturer,'') FROM product","SELECT 'puc',id,general||' - '||family||' - '||type,definition FROM puc","SELECT d.kind,coalesce(e.id,d.name),d.name,d.definition FROM dictionary d LEFT JOIN entity_id e ON e.kind=d.kind AND e.name=d.name"]:
        db.execute('INSERT INTO search(kind,entity_id,title,body) '+sql)
    db.commit()
    report={'counts':{t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['puc','chemical','document','record','product','product_document']},'imports':db.execute('SELECT * FROM imports').fetchall(),'foreign_key_errors':db.execute('PRAGMA foreign_key_check').fetchmany(20),'db_bytes':(DATA/'chemexpo.sqlite').stat().st_size,'seconds':time.time()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    for name in ['/sys/fs/cgroup/memory/memory.max_usage_in_bytes','/sys/fs/cgroup/memory.peak']:
        if Path(name).exists():report['cgroup_peak_bytes']=int(Path(name).read_text())
    (ROOT/'validation').mkdir(exist_ok=True)
    (ROOT/'validation/import.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':main()
