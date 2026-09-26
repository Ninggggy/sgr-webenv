"""Offline ChemExpo public-data query service. No outbound network client."""
import csv, gzip, io, json, math, mimetypes, os, re, sqlite3, zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

DATA=Path(os.environ.get('CHEMEXPO_DATA','/data'))
STATIC=Path(__file__).parent/'static'
DOWNLOADS={'dl_pucs':'pucs','dl_puctags':'attributes','dl_lpkeywords':'keywords','dl_functionalusecategories':'functions','dl_lp_chemicals':'presence','dl_functional_uses':'functional','dl_co_chemicals':'composition'}

def connect():
    db=sqlite3.connect(f'file:{DATA}/chemexpo.sqlite?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA query_only=ON');db.execute('PRAGMA cache_size=-16384')
    return db

def integer(q,key,default=0,maximum=100000000):
    try:n=int(q.get(key,default))
    except (ValueError,TypeError):raise ValueError('Invalid '+key)
    if n<0 or n>maximum:raise ValueError('Out-of-range '+key)
    return n

def allrows(db,sql,args=()):return [dict(r) for r in db.execute(sql,args)]

def pucs(db,sid=None):
    ps=allrows(db,'SELECT * FROM puc ORDER BY general,family,type,id')
    if sid:
        counts=dict(db.execute("SELECT puc,count(*) FROM record WHERE source='composition' AND sid=? AND puc IS NOT NULL GROUP BY puc",(sid,)))
        for p in ps:p['direct']=counts.get(p['id'],0);p['cumulative']=p['direct']
        byid={p['id']:p for p in ps}
        for p in sorted(ps,key=lambda x:-x['level']):
            if p['parent']:byid[p['parent']]['cumulative']+=p['cumulative']
        ps=[p for p in ps if p['cumulative']]
    return ps

def puc_view(db,q):
    threshold=float(q.get('min') or 0)
    if not math.isfinite(threshold) or threshold<0:raise ValueError('Invalid minimum count')
    sort=q.get('sort','general');direction=q.get('direction','asc')
    if sort not in ['id','kind','level','general','family','type','direct','cumulative','allowed','assumed'] or direction not in ['asc','desc']:raise ValueError('Invalid PUC sort')
    if q.get('kind') and q['kind'] not in ['FO','AR','OC']:raise ValueError('Invalid PUC kind')
    if q.get('level') and q['level'] not in ['1','2','3']:raise ValueError('Invalid PUC level')
    if q.get('assumed','any') not in ['any','empty','nonempty']:raise ValueError('Invalid attribute filter')
    rows=pucs(db)
    rows=[p for p in rows if p['cumulative']>=threshold and (q.get('filter','').lower() in ' '.join([p['general'],p['family'],p['type']]).lower()) and (not q.get('kind') or p['kind']==q['kind']) and (not q.get('level') or p['level']==int(q['level'])) and (not q.get('allowed') or q['allowed'] in [t.strip() for t in p['allowed'].split(';')]) and (q.get('assumed','any')=='any' or bool(p['assumed'])==(q['assumed']=='nonempty'))]
    rows.sort(key=lambda p:(p['general'],p['family'],p['type'],p['id']))
    rows.sort(key=lambda p:p[sort],reverse=direction=='desc')
    return rows

def keyword_sets(db,sid):
    rows=allrows(db,"SELECT r.doc,r.keyword_set,r.raw_name,r.raw_cas,r.payload,d.keyword_count FROM record r LEFT JOIN document_keyword_total d ON d.doc=r.doc WHERE r.sid=? AND r.source='presence' AND coalesce(r.keyword_set,'')<>''",(sid,))
    headers=json.loads((DATA/'sources.json').read_text())['presence']['columns'];retained=[i for i,c in enumerate(headers) if c not in ['Reported Function','Harmonized Function']]
    seen=set();unique=[]
    for r in rows:
        values=json.loads(zlib.decompress(r['payload']));signature=(r['doc'],r['keyword_set'],r['raw_name'],r['raw_cas'],tuple(values[i] for i in retained if i<len(values)))
        if signature not in seen:seen.add(signature);unique.append(r)
    rows=unique
    exact={r['doc'] for r in rows if len({x.strip() for x in r['keyword_set'].split(';') if x.strip()})==r['keyword_count']}
    groups={}
    for r in rows:
        g=groups.setdefault(r['keyword_set'],{'keyword_set':r['keyword_set'],'documents':0,'document_ids':set()})
        count=len({x.strip() for x in r['keyword_set'].split(';') if x.strip()})
        if count==r['keyword_count'] or r['doc'] not in exact:
            g['documents']+=1;g['document_ids'].add(r['doc'])
    for g in groups.values():g['document_ids']=sorted(g['document_ids']);g['unique_documents']=len(g['document_ids'])
    return sorted((g for g in groups.values() if g['documents']),key=lambda g:g['keyword_set'])

def keyword_documents(db,q):
    return next((g['document_ids'] for g in keyword_sets(db,q['sid']) if g['keyword_set']==q['keyword_set']),[])

def scope(q,db):
    where=[];args=[]
    for key,col in [('sid','r.sid'),('doc','r.doc'),('puc','r.puc'),('source','r.source'),('keyword_set','r.keyword_set'),('function','r.function_name'),('method','r.method')]:
        if q.get(key):
            if key in ['doc','puc']:integer(q,key)
            if key=='source' and q[key] not in ['composition','presence','functional']:raise ValueError('Invalid source')
            where.append(col+'=?');args.append(q[key])
    if q.get('keyword'):
        where.append("instr(';'||replace(r.keyword_set,'; ',';')||';',';'||?||';')>0");args.append(q['keyword'])
    if q.get('product'):
        integer(q,'product');where.append('EXISTS(SELECT 1 FROM product_document pd JOIN product p ON p.id=pd.product WHERE pd.document=r.doc AND p.id=? AND (r.product_title IS NULL OR r.product_title=p.title))');args.append(q['product'])
    if q.get('q'):
        where.append('(instr(lower(r.raw_name),lower(?))>0 OR instr(lower(r.raw_cas),lower(?))>0 OR instr(lower(coalesce(r.product_title,\'\')),lower(?))>0)');args.extend([q['q']]*3)
    if q.get('sid') and q.get('keyword_set'):
        ids=keyword_documents(db,q);where.append('r.doc IN('+','.join('?' for _ in ids)+')' if ids else '0');args.extend(ids)
    return ' AND '.join(where) or '1',args

def record_query(q,db):
    where,args=scope(q,db)
    sort=q.get('sort','id');allowed={'id':'r.id','chemical':'r.raw_name','document':'r.doc','puc':'r.puc','product':'r.product_title'}
    if sort not in allowed:raise ValueError('Invalid sort')
    direction=q.get('direction','asc')
    if direction not in ['asc','desc']:raise ValueError('Invalid direction')
    return where,args,allowed[sort]+' '+direction+',r.id ASC'

class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,ctype='application/json; charset=utf-8',extra=None):
        if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        try:self.get()
        except (ValueError,KeyError) as e:self.send(400,{'error':str(e)})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:
            self.log_error('%s',e);self.send(500,{'error':'Query failed; no partial result is reported'})

    def get(self):
        u=urlsplit(self.path);path=unquote(u.path);q={k:v[-1] for k,v in parse_qs(u.query,keep_blank_values=True).items()}
        if len(u.query)>5000:raise ValueError('Query too long')
        if any(x in path for x in ['..','\\','\x00']):self.send(404,{'error':'Not found'});return
        if path=='/health':
            with connect() as db:db.execute('SELECT 1 FROM puc LIMIT 1').fetchone()
            self.send(200,{'status':'ok','version':'0.1.0-dev'});return
        if path.startswith('/chemexpo/static/'):
            f=STATIC/path.removeprefix('/chemexpo/static/')
            if not f.is_file() or not f.resolve().is_relative_to(STATIC.resolve()):self.send(404,{});return
            self.send(200,f.read_bytes(),mimetypes.guess_type(str(f))[0] or 'application/octet-stream');return
        route=path.removeprefix('/chemexpo/').strip('/')
        if route in DOWNLOADS:
            sources=json.loads((DATA/'sources.json').read_text());info=sources.get(DOWNLOADS[route])
            if not info or not info['complete']:self.send(503,{'error':'Source download not archived'});return
            f=DATA/'raw'/Path(info['file']).name
            zipfile=f.suffix=='.zip'
            self.send_response(200);self.send_header('Content-Type','application/zip' if zipfile else 'text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="ChemExpo_'+DOWNLOADS[route]+('.zip' if zipfile else '.csv')+'"');self.end_headers()
            with (f.open('rb') if zipfile else gzip.open(f,'rb')) as stream:
                while chunk:=stream.read(65536):self.wfile.write(chunk)
            return
        if path.startswith('/chemexpo/api/'):
            with connect() as db:self.api(db,path.removeprefix('/chemexpo/api/'),q)
            return
        if path=='/' or path.startswith('/chemexpo/'):
            valid=path in ['/','/chemexpo/','/chemexpo/get_data/','/chemexpo/visualizations/','/chemexpo/pucs/','/chemexpo/coverage/','/chemexpo/functional_use_categories/','/chemexpo/list_presence_tags/'] or re.fullmatch(r'/chemexpo/(chemical|puc|product|datadocument|functional_use_category|list_presence_tag|search)/[^/]+/',path)
            if valid:self.send(200,(STATIC/'index.html').read_bytes(),'text/html; charset=utf-8');return
        self.send(404,{'error':'Not available in this offline environment'})

    def api(self,db,endpoint,q):
        if endpoint in ['pucs','associated','associated_export','records','export']:
            for key,table,column in [('sid','chemical','sid'),('doc','document','id'),('product','product','id'),('puc','puc','id')]:
                if q.get(key):
                    if key!='sid':integer(q,key)
                    if not db.execute(f'SELECT 1 FROM {table} WHERE {column}=?',(q[key],)).fetchone():
                        self.send(404,{'error':'Requested '+key+' is outside the archived scope; no empty-result claim is made'});return
        if endpoint=='status':
            imports=allrows(db,'SELECT * FROM imports');r=DATA/'relations.json';relations=json.loads(r.read_text()) if r.exists() else {'complete':False}
            complete=relations.get('complete',False) and db.execute('SELECT count(*) FROM product_document').fetchone()[0]==relations.get('records') and len(imports)==3 and all(r['complete'] for r in imports)
            limits=['Search uses a local FTS index, not the original Elasticsearch index or relevance order.', 'Supplementary product/document fields and original document attachments are not included in the seven public exports.', 'Original raw list-presence IDs are absent. Functional-use expansion rows are deduplicated using their other public fields; distinct original records with identical public fields cannot be proven distinct.', 'The original site may contain catalogue entries without records or product links in this archived public-data scope. No matching archived result does not prove absence from the original site.']
            self.send(200,{'version':'0.1.0-dev','revision':'20260926-codefix1','release':'CPDat 4.1','imports':imports,'relations':relations,'dictionary_ids':allrows(db,'SELECT * FROM entity_id'),'complete':False,'public_data_complete':complete,'counts':{t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['chemical','product','document','product_document']},'coverage_limits':limits,'notice':'CPDat 4.1 — chemical and product data.' if complete else 'Product relationships: archived subset.'});return
        if endpoint=='sources':
            sources=json.loads((DATA/'sources.json').read_text())
            self.send(200,{k:{key:v.get(key) for key in ['url','retrieved_utc','complete','uncompressed_bytes','stored_bytes']} for k,v in sources.items()});return
        if endpoint in ['puc_view','puc_export']:
            rows=puc_view(db,q);page=integer(q,'page')
            if endpoint=='puc_export':
                output=io.StringIO();columns=['id','kind','level','general','family','type','direct','cumulative','allowed','assumed','definition']
                writer=csv.DictWriter(output,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
                self.send(200,output.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',{'Content-Disposition':'attachment; filename="ChemExpo_PUC_view.csv"'});return
            self.send(200,{'total':len(rows),'page':page,'rows':rows[page*50:(page+1)*50]});return
        if endpoint=='pucs':self.send(200,pucs(db,q.get('sid')));return
        if endpoint in ['search','search_export']:
            kind=q.get('kind','chemical')
            if kind not in ['chemical','product','document','puc','functions','keywords']:raise ValueError('Invalid search category')
            page=integer(q,'page',0);query=q.get('q','').strip()
            if re.fullmatch(r'DTXSID\d+',query,re.I):
                args=[kind,query.upper()];where='kind=? AND entity_id=?';order='title,entity_id'
            elif query:
                if query.count('"')%2:raise ValueError('Unclosed quoted search phrase')
                terms=[]
                for phrase,word in re.findall(r'"([^"]+)"|([^\s"]+)',query):
                    if phrase:terms.append('"'+phrase.replace('"','""')+'"')
                    elif re.fullmatch(r'\d{2,7}-\d{2}-\d',word):terms.append('"'+word+'"')
                    else:terms.extend('"'+t+'"' for t in re.findall(r'[^\W_]+',word,flags=re.UNICODE))
                if not terms:
                    if endpoint=='search_export':self.send(200,b'kind,id,name,information\r\n','text/csv; charset=utf-8',{'Content-Disposition':'attachment; filename="ChemExpo_search.csv"'})
                    else:self.send(200,{'rows':[],'total':0,'page':page})
                    return
                match=' AND '.join(terms)
                args=[kind,match];where='kind=? AND search MATCH ?';order='rank,title,entity_id'
            else:args=[kind];where='kind=?';order='title,entity_id'
            total=db.execute('SELECT count(*) FROM search WHERE '+where,args).fetchone()[0]
            if endpoint=='search_export':
                cursor=db.execute('SELECT kind,entity_id,title,body FROM search WHERE '+where+' ORDER BY '+order,args)
                self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="ChemExpo_search.csv"');self.end_headers()
                buf=io.StringIO();writer=csv.writer(buf);writer.writerow(['kind','id','name','information']);self.wfile.write(buf.getvalue().encode('utf-8-sig'))
                for row in cursor:
                    buf.seek(0);buf.truncate();writer.writerow(tuple(row));self.wfile.write(buf.getvalue().encode())
                return
            rs=allrows(db,'SELECT kind,entity_id,title,body FROM search WHERE '+where+' ORDER BY '+order+' LIMIT 40 OFFSET ?',args+[page*40])
            self.send(200,{'rows':rs,'total':total,'page':page,'search_rule':'Search supports exact DTXSIDs, CAS numbers, quoted phrases and token conjunction.'});return
        if endpoint=='entity':
            kind=q.get('kind');ident=q.get('id')
            mapping={'chemical':('chemical','sid'),'puc':('puc','id'),'product':('product','id'),'document':('document','id')}
            if kind in mapping:
                table,key=mapping[kind];row=db.execute(f'SELECT * FROM {table} WHERE {key}=?',(ident,)).fetchone()
            elif kind in ['functions','keywords']:
                row=db.execute('SELECT d.*,e.id FROM dictionary d LEFT JOIN entity_id e ON e.kind=d.kind AND e.name=d.name WHERE d.kind=? AND (e.id=? OR d.name=?)',(kind,ident,ident)).fetchone()
            else:raise ValueError('Invalid entity kind')
            if row is None:self.send(404,{'error':'Entity not in the archived data'});return
            d=dict(row)
            if kind=='chemical':
                d['keyword_sets']=keyword_sets(db,ident)
            if kind=='puc':
                # Official PUC detail property differs from the tree/export roll-up:
                # general name at level 1, family name alone at level 2, direct at level 3.
                tree_count=d['cumulative']
                if d['level']==1:d['cumulative']=db.execute('SELECT sum(direct) FROM puc WHERE general=?',(d['general'],)).fetchone()[0]
                elif d['level']==2:d['cumulative']=db.execute('SELECT sum(direct) FROM puc WHERE family=?',(d['family'],)).fetchone()[0]
                else:d['cumulative']=d['direct']
                if tree_count!=d['cumulative']:
                    d['tree_cumulative']=tree_count;d['count_note']='Official detail-page aggregation groups identical category/family names; the Explore tree and source CSV retain the hierarchy roll-up.'
                d['curated_chemicals']=db.execute('SELECT count(DISTINCT sid) FROM record WHERE puc=?',(ident,)).fetchone()[0]
                rel=DATA/'relations.json'
                complete=rel.exists() and json.loads(rel.read_text()).get('complete') and db.execute('SELECT count(*) FROM product_document').fetchone()[0]==json.loads(rel.read_text())['records']
                if complete:d['curated_chemicals']=db.execute('SELECT count(DISTINCT r.sid) FROM record r JOIN product_document pd ON pd.document=r.doc JOIN product p ON p.id=pd.product WHERE p.puc=?',(ident,)).fetchone()[0]
                d['documents']=db.execute('SELECT count(DISTINCT pd.document) FROM product_document pd JOIN product p ON p.id=pd.product WHERE p.puc=?',(ident,)).fetchone()[0] if complete else None
                d['document_relation_coverage']='complete' if complete else 'pending: bulk chemical exports omit some product documents'
            self.send(200,d);return
        if endpoint in ['associated','associated_export']:
            view=q.get('view','products')
            if view not in ['products','documents','chemicals','functions']:raise ValueError('Invalid associated view')
            clauses=[];args=[]
            if q.get('puc'):
                integer(q,'puc');clauses.append('p.puc=?');args.append(q['puc'])
            if q.get('product'):
                integer(q,'product');clauses.append('p.id=?');args.append(q['product'])
            if q.get('doc'):
                integer(q,'doc');clauses.append('pd.document=?');args.append(q['doc'])
            record_clauses=[]
            for key in ['sid','keyword_set','function']:
                if q.get(key):
                    col={'sid':'sid','keyword_set':'keyword_set','function':'function_name'}[key]
                    record_clauses.append(f'rr.{col}=?');args.append(q[key])
            if q.get('keyword'):
                record_clauses.append("rr.source='presence' AND instr(';'||replace(rr.keyword_set,'; ',';')||';',';'||?||';')>0");args.append(q['keyword'])
            if record_clauses:clauses.append('d.id IN(SELECT rr.doc FROM record rr WHERE '+' AND '.join(record_clauses)+')')
            if q.get('kind'):
                if q['kind'] not in ['FO','AR','OC','UN']:raise ValueError('Invalid PUC kind')
                if q['kind']=='UN':clauses.append('p.puc IS NULL')
                else:clauses.append('p.puc IN(SELECT id FROM puc WHERE kind=?)');args.append(q['kind'])
            if q.get('method'):clauses.append('p.method=?');args.append(q['method'])
            if view=='products':
                base=' FROM product p JOIN product_document pd ON pd.product=p.id JOIN document d ON d.id=pd.document '
                fields='p.id,p.title,p.brand,p.manufacturer,p.puc,p.method'
                orders={k:k for k in ['id','title','brand','manufacturer','puc','method']}
                if q.get('sid'):
                    fields+=',pd.document,d.title document_title';orders['document']='document'
            elif view=='documents':
                base=' FROM document d LEFT JOIN product_document pd ON pd.document=d.id LEFT JOIN product p ON p.id=pd.product '
                fields='d.id,d.title,d.subtitle,d.date,d.source';orders={k:k for k in ['id','title','date','source']}
            elif view=='chemicals':
                base=' FROM record r JOIN chemical c ON c.sid=r.sid JOIN document d ON d.id=r.doc LEFT JOIN product_document pd ON pd.document=d.id LEFT JOIN product p ON p.id=pd.product '
                fields='c.sid,c.name,c.cas';orders={k:k for k in ['sid','name','cas']}
            else:
                base=' FROM record r JOIN document d ON d.id=r.doc LEFT JOIN product_document pd ON pd.document=d.id LEFT JOIN product p ON p.id=pd.product '
                clauses.append("coalesce(r.function_name,'')<>''");fields='r.function_name';orders={'function_name':'function_name'}
                if q.get('sid'):clauses.append('r.sid=?');args.append(q['sid'])
            if view in ['chemicals','functions']:
                for key,col in [('function','function_name'),('keyword_set','keyword_set')]:
                    if q.get(key):clauses.append('r.'+col+'=?');args.append(q[key])
                if q.get('keyword'):
                    clauses.append("r.source='presence' AND instr(';'||replace(r.keyword_set,'; ',';')||';',';'||?||';')>0");args.append(q['keyword'])
            filter_columns={'products':{'title':'p.title','brand':'p.brand','manufacturer':'p.manufacturer','method':'p.method'},'documents':{'title':'d.title','subtitle':'d.subtitle','date':'d.date','source':'d.source'},'chemicals':{'sid':'c.sid','name':'c.name','cas':'c.cas'},'functions':{'function_name':'r.function_name'}}[view]
            qfield=q.get('q_field','all')
            if qfield!='all' and qfield not in filter_columns:raise ValueError('Invalid filter column')
            if q.get('q'):
                columns=list(filter_columns.values()) if qfield=='all' else [filter_columns[qfield]]
                clauses.append('('+' OR '.join('instr(lower('+c+'),lower(?))>0' for c in columns)+')');args.extend([q['q']]*len(columns))
            # Document-only records (e.g. list presence) must not disappear through an inner product join.
            clauses=[c.replace('rr.doc=pd.document','rr.doc=d.id') for c in clauses]
            if q.get('sid') and q.get('keyword_set'):
                ids=keyword_documents(db,q);clauses.append('d.id IN('+','.join('?' for _ in ids)+')' if ids else '0');args.extend(ids)
            where=' WHERE '+(' AND '.join(clauses) or '1')
            sql='SELECT * FROM (SELECT '+('' if view=='products' and q.get('sid') else 'DISTINCT ')+fields+base+where+')'
            sort=q.get('sort',next(iter(orders)));direction=q.get('direction','asc')
            if sort not in orders or direction not in ['asc','desc']:raise ValueError('Invalid sort or direction')
            order=orders[sort]+' '+direction+','+','.join(orders)
            page=integer(q,'page',0)
            total=db.execute('SELECT count(*) FROM ('+sql+')',args).fetchone()[0]
            rel=DATA/'relations.json';complete=rel.exists() and json.loads(rel.read_text()).get('complete') and db.execute('SELECT count(*) FROM product_document').fetchone()[0]==json.loads(rel.read_text())['records']
            if endpoint=='associated_export':
                if view=='products' and not complete:self.send(503,{'error':'Product relationship collection is incomplete; export would omit candidates'});return
                cursor=db.execute(sql+' ORDER BY '+order,args)
                self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="ChemExpo_associated.csv"');self.end_headers();buf=io.StringIO();w=csv.writer(buf);w.writerow([c[0] for c in cursor.description]);self.wfile.write(buf.getvalue().encode('utf-8-sig'))
                for r in cursor:
                    buf.seek(0);buf.truncate();w.writerow(tuple(r));self.wfile.write(buf.getvalue().encode())
                return
            self.send(200,{'rows':allrows(db,sql+' ORDER BY '+order+' LIMIT 40 OFFSET ?',args+[page*40]),'total':total,'page':page,'complete':complete,'row_unit':'product_document' if view=='products' and q.get('sid') else view});return
        if endpoint=='record':
            ident=integer(q,'id')
            row=db.execute('SELECT source,payload FROM record WHERE id=?',(ident,)).fetchone()
            if row is None:self.send(404,{'error':'Source record not archived'});return
            headers=json.loads((DATA/'sources.json').read_text())[row['source']]['columns']
            self.send(200,{'id':ident,'source':row['source'],'fields':dict(zip(headers,json.loads(zlib.decompress(row['payload']))))});return
        if endpoint in ['records','export']:
            where,args,order=record_query(q,db)
            page=integer(q,'page',0);size=integer(q,'size',40,100)
            if size==0:raise ValueError('Page size must be positive')
            if endpoint=='export':
                source=q.get('source')
                if not source:raise ValueError('Choose one source for CSV export')
                sources=json.loads((DATA/'sources.json').read_text());header=sources[source]['columns']
                cursor=db.execute('SELECT r.payload FROM record r WHERE '+where+' ORDER BY '+order,args)
                self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="ChemExpo_view.csv"');self.end_headers()
                buf=io.StringIO();writer=csv.writer(buf);writer.writerow(header);self.wfile.write(buf.getvalue().encode('utf-8-sig'))
                for r in cursor:
                    buf.seek(0);buf.truncate();writer.writerow(json.loads(zlib.decompress(r[0])));self.wfile.write(buf.getvalue().encode())
                return
            total=db.execute('SELECT count(*) FROM record r WHERE '+where,args).fetchone()[0]
            rs=allrows(db,'SELECT r.id,r.source,r.doc,d.title document,r.sid,c.name chemical,r.puc,r.product_title,r.method,r.keyword_set,r.function_name,r.raw_name,r.raw_cas FROM record r LEFT JOIN document d ON d.id=r.doc LEFT JOIN chemical c ON c.sid=r.sid WHERE '+where+' ORDER BY '+order+' LIMIT ? OFFSET ?',args+[size,page*size])
            self.send(200,{'rows':rs,'total':total,'page':page,'size':size});return
        self.send(404,{'error':'Unknown API endpoint'})

if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
