"""Bounded-memory offline index build. Publish only after zero-error completion.

Run in the author container on the private index network. No task IDs, answers,
cloud access, or precomputed query results enter the index.
"""
import argparse
import json
from pathlib import Path
import re
import sqlite3
import urllib.request
from arxiv.util.authors import parse_author_affil_utf
from source_scope import primary_category,classification,announcement_month


def document(row,versions,chosen=None):
    latest=versions[-1]
    chosen=chosen or latest
    current=chosen['number']==latest['number']
    doc={k:row[k] for k in ('title','abstract','comments','journal_ref','report_num') if row[k] is not None}
    for key,separator in [('acm_class',';'),('msc_class',',')]:
        if row[key]:doc[key]=[s.strip() for s in row[key].split(separator)]
    parsed=[]
    for author in parse_author_affil_utf(row['authors'] or ''):
        last,first,suffix=author[:3]
        full=' '.join((first+' '+last).split())
        parts=full.split()
        parsed.append({'last_name':last,'first_name':first,'suffix':suffix,
                       'full_name':full,'initials':' '.join(pt[0] for pt in first.split() if pt),'full_name_initialized':' '.join([p[0] for p in parts[:-1]]+parts[-1:])})
    doc.update(announced_date_first=announcement_month(row['id']),id=f'{row["id"]}v{chosen["number"]}',paper_id=row['id'],
               paper_id_v=f'{row["id"]}v{chosen["number"]}',
               authors=parsed,authors_freeform=row['authors'],version=chosen['number'],
               latest_version=latest['number'],latest=f'{row["id"]}v{latest["number"]}',
               is_current=current,submitted_date=chosen['submitted_at'],
               submitted_date_latest=latest['submitted_at'],
               submitted_date_first=versions[0]['submitted_at'],
               submitted_date_all=[v['submitted_at'] for v in versions] if current else None)
    if row['license']:doc['license']={'uri':row['license']}
    if row['doi']:doc['doi']=row['doi'].split()
    cats=(row['categories'] or '').split()
    if cats:
        doc['primary_classification']=classification(primary_category(row['categories']))
        doc['secondary_classification']=[classification(c) for c in cats[1:]]
    # Actual announcement dates are still sourced independently.
    return doc


def documents(db, paper_ids=None, include_historical=False, historical_only=False):
    query='SELECT * FROM records WHERE deleted=0'
    params=()
    if paper_ids is not None:
        query+=' AND id IN ('+','.join('?' for _ in paper_ids)+')';params=tuple(paper_ids)
    for row in db.execute(query+' ORDER BY id',params):
        versions=db.execute('SELECT * FROM versions WHERE paper_id=? ORDER BY number',(row['id'],)).fetchall()
        if not versions:raise ValueError('Missing version timeline: '+row['id'])
        if not historical_only:yield document(row,versions)
        if include_historical or historical_only:
            for version in versions[:-1]:
                if not version['detail_json']:raise ValueError('Unacquired historical fields: '+row['id']+'v'+str(version['number']))
                data=dict(row);fields=json.loads(version['detail_json'])
                # API/HTML fields explicitly belong to this version. Never inherit
                # latest optional fields when the historical source lacks them.
                for key in ('title','abstract','authors','categories','comments','journal_ref','doi','license','report_num','acm_class','msc_class'):
                    data[key]=fields.get(key)
                yield document(data,versions,version)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--database',required=True,type=Path)
    p.add_argument('--index',required=True)
    p.add_argument('--include-historical',action='store_true')
    p.add_argument('--codec',choices=['default','best_compression'],default='best_compression')
    p.add_argument('--server',default='http://search:9200')
    p.add_argument('--mapping',type=Path,default=Path('/opt/search/mappings/DocumentMapping.json'))
    args=p.parse_args()
    if not re.fullmatch(r'arxiv-[a-z0-9-]+',args.index):p.error('Require an arxiv- index name')
    def call(method,path,body,content_type='application/json'):
        req=urllib.request.Request(args.server+path,data=body,method=method,headers={'Content-Type':content_type})
        with urllib.request.urlopen(req,timeout=120) as result:return json.load(result)
    db=sqlite3.connect('file:'+str(args.database)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    if args.include_historical:
        missing=db.execute('SELECT 1 FROM versions v JOIN records r ON r.id=v.paper_id WHERE r.deleted=0 AND v.detail_json IS NULL AND v.number<(SELECT max(v2.number) FROM versions v2 WHERE v2.paper_id=v.paper_id) LIMIT 1').fetchone()
        if missing:raise ValueError('Historical acquisition is incomplete; refusing a partial history index')
    # Existing indices are not deleted or overwritten by this builder.
    mapping=json.loads(args.mapping.read_text())
    mapping.setdefault('settings',{}).update(number_of_shards=1,number_of_replicas=0,codec=args.codec)
    call('PUT','/'+args.index,json.dumps(mapping).encode())
    batch=[];count=0;maximum=0
    def flush():
        nonlocal batch,count,maximum
        if not batch:return
        payload=('\n'.join(batch)+'\n').encode();maximum=max(maximum,len(payload))
        result=call('POST','/_bulk',payload,'application/x-ndjson')
        if result.get('errors'):
            errors=[x for x in result['items'] if x['index'].get('error')]
            raise RuntimeError(json.dumps(errors[:3]))
        count+=len(batch)//2;batch=[]
        if count%10000==0:print(json.dumps({'indexed':count}),flush=True)
    for doc in documents(db,include_historical=args.include_historical):
        batch.extend([json.dumps({'index':{'_index':args.index,'_type':'document','_id':doc['id']}}),json.dumps(doc)])
        if len(batch)>=400:flush()
    flush();call('POST','/'+args.index+'/_refresh',b'{}')
    actual=call('GET','/'+args.index+'/_count',None)['count']
    if actual!=count:raise RuntimeError('Indexed count mismatch')
    print(json.dumps({'index':args.index,'documents':count,'maximum_batch_bytes':maximum,
                      'authors':'official arxiv.util.authors parser','historical_versions_indexed':args.include_historical,
                      'full_scope':bool(db.execute('SELECT min(complete) FROM harvest_state').fetchone()[0])}))


if __name__=='__main__':main()
