"""Stream the official Kaggle metadata snapshot into a separate author database.

No task labels or answers are read. All primary/cross-listed cs/math/stat
records are retained. The original source stays on the acquisition host.
"""
import argparse
import datetime as dt
import email.utils
import json
from pathlib import Path
import sqlite3
import sys
from harvest import connect,check_space,utc

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'upstream/arxiv-base'),str(Path(__file__).resolve().parents[1]/'runtime')]
from source_scope import groups,equivalent_categories,announcement_month

SOURCE='https://www.kaggle.com/datasets/Cornell-University/arxiv'
CREATED='2026-09-19T23:53:14.078Z'
SIZE=5545506967


def selected(record):
    return bool(groups(record['categories']))


def initialize(path):
    db=connect(path)
    db.executescript('''CREATE TABLE IF NOT EXISTS snapshot_import (
       source TEXT PRIMARY KEY, source_created TEXT, expected_bytes INTEGER,
       lines INTEGER NOT NULL, byte_offset INTEGER NOT NULL, included INTEGER NOT NULL,
       complete INTEGER NOT NULL, updated_at TEXT);
       CREATE TABLE IF NOT EXISTS record_extras (
       paper_id TEXT PRIMARY KEY REFERENCES records(id), authors_parsed TEXT,
       source TEXT NOT NULL, source_created TEXT NOT NULL);
       CREATE TABLE IF NOT EXISTS snapshot_duplicates (paper_id TEXT PRIMARY KEY, duplicate_count INTEGER NOT NULL);
       CREATE TABLE IF NOT EXISTS snapshot_revisions (
       paper_id TEXT, previous_json TEXT NOT NULL, incoming_json TEXT NOT NULL, decision TEXT NOT NULL);
       CREATE TABLE IF NOT EXISTS catalog (
       paper_id TEXT NOT NULL REFERENCES records(id), context TEXT NOT NULL, month TEXT NOT NULL,
       PRIMARY KEY(context,month,paper_id));
    ''')
    db.execute('INSERT OR IGNORE INTO snapshot_import VALUES (?,?,?,0,0,0,0,?)',
               (SOURCE,CREATED,SIZE,utc()));db.commit()
    return db


def insert(db,r):
    pid=r['id'];versions=r['versions']
    numbers=[int(v['version'][1:]) for v in versions]
    if sorted(numbers) != list(range(1,len(numbers)+1)) or not numbers:raise ValueError('Invalid timeline '+pid)
    fields=[r.get(k) for k in ('title','abstract','authors','categories','comments','journal-ref','doi','license','report-no','acm-class','msc-class')]
    existing=db.execute('SELECT oai_modified,title,abstract,authors,categories,comments,journal_ref,doi,license,report_num,acm_class,msc_class FROM records WHERE id=?',(pid,)).fetchone()
    replaced=False
    if existing:
        current=tuple((r.get('update_date'),*fields))
        old_versions=db.execute('SELECT number,submitted_at FROM versions WHERE paper_id=? ORDER BY number',(pid,)).fetchall()
        new_versions=sorted((n,email.utils.parsedate_to_datetime(v['created']).astimezone(dt.timezone.utc).isoformat()) for v,n in zip(versions,numbers))
        db.execute('INSERT INTO snapshot_duplicates VALUES (?,1) ON CONFLICT(paper_id) DO UPDATE SET duplicate_count=duplicate_count+1',(pid,))
        if existing==current and old_versions==new_versions:
            return False
        # The source contains older metadata followed by revised copies. Choose
        # the explicit most recent metadata date, retaining both observations.
        # Equal-date conflicts have no defensible ordering and must stop.
        if not existing[0] or not current[0] or existing[0]==current[0]:
            raise ValueError('Ambiguous duplicate source record '+pid)
        decision='incoming' if current[0]>existing[0] else 'existing'
        db.execute('INSERT INTO snapshot_revisions VALUES (?,?,?,?)',
            (pid,json.dumps({'fields':existing,'versions':old_versions}),json.dumps(r),decision))
        if decision=='existing':return False
        for table in ('versions','membership','catalog','record_extras'):
            db.execute('DELETE FROM '+table+' WHERE paper_id=?',(pid,))
        db.execute('DELETE FROM records WHERE id=?',(pid,))
        replaced=True
    db.execute('INSERT INTO records VALUES ('+','.join('?' for _ in range(16))+')',
               (pid,r.get('update_date'),0,*fields,'',utc()))
    for v,n in zip(versions,numbers):
        date=email.utils.parsedate_to_datetime(v['created'])
        if not date.tzinfo:raise ValueError('Missing timezone '+pid)
        db.execute('INSERT INTO versions(paper_id,number,submitted_at) VALUES (?,?,?)',
                   (pid,n,date.astimezone(dt.timezone.utc).isoformat()))
    for group in groups(r['categories']):
        db.execute('INSERT INTO membership VALUES (?,?)',(pid,group+':'+group))
    contexts=set()
    for cat in r['categories'].split():
        for equivalent in equivalent_categories(cat):
            contexts.add(equivalent);contexts.add(equivalent.split('.')[0])
    month=announcement_month(pid)
    db.executemany('INSERT INTO catalog VALUES (?,?,?)',[(pid,context,month) for context in sorted(contexts)])
    db.execute('INSERT INTO record_extras VALUES (?,?,?,?)',
               (pid,json.dumps(r.get('authors_parsed')),SOURCE,CREATED))
    return not replaced


def consume(db,stream,root):
    state=db.execute('SELECT lines,byte_offset,included FROM snapshot_import WHERE source=?',(SOURCE,)).fetchone()
    lines,offset,included=state;pending=0
    for raw in stream:
        event=json.loads(raw)
        if event.get('complete'):
            if event['byte_offset']!=SIZE or event['lines']!=lines:raise ValueError('Incomplete source stream')
            db.execute('UPDATE snapshot_import SET complete=1,updated_at=?',(utc(),))
            # Coverage completion is about the source file, not inferred from a row count.
            for group in ('cs','math','stat'):
                db.execute('INSERT OR REPLACE INTO harvest_state VALUES (?,NULL,1,0,?,?)',(group+':'+group,CREATED,utc()))
            db.commit();print(json.dumps({'complete':True,'source_lines':lines,'included':included}),flush=True);return
        if event['line']!=lines+1 or event['byte_offset']<=offset:raise ValueError('Non-contiguous source stream')
        if not pending:check_space(root,reserve=256*1024**2)
        record=event.get('record')
        if record is not None:
            if not selected(record):raise ValueError('Unexpected out-of-scope record')
            included+=int(insert(db,record))
        lines=event['line'];offset=event['byte_offset'];pending+=1
        db.execute('UPDATE snapshot_import SET lines=?,byte_offset=?,included=?,updated_at=?',
                   (lines,offset,included,utc()))
        if pending>=1000:
            db.commit();pending=0
            if lines%50000==0:print(json.dumps({'lines':lines,'included':included}),flush=True)
    db.rollback()
    raise ValueError('Stream ended without complete source marker; last committed offset remains resumable')


def produce(path,offset,lines):
    if path.stat().st_size!=SIZE:raise ValueError('Source download size is not complete')
    with path.open('rb') as f:
        f.seek(offset)
        for raw in f:
            r=json.loads(raw);lines+=1
            event={'line':lines,'byte_offset':f.tell()}
            if selected(r):event['record']=r
            print(json.dumps(event,ensure_ascii=False),flush=False)
        print(json.dumps({'complete':True,'lines':lines,'byte_offset':f.tell()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['produce','consume','state'])
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--source-file',type=Path);p.add_argument('--offset',type=int,default=0);p.add_argument('--lines',type=int,default=0)
    a=p.parse_args()
    if a.mode=='produce':produce(a.source_file,a.offset,a.lines)
    else:
        path=a.root/'data/snapshot.sqlite'
        if a.mode=='state' and path.exists():
            db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
        else:db=initialize(path)
        if a.mode=='state':print(json.dumps(db.execute('SELECT lines,byte_offset,included,complete FROM snapshot_import').fetchone()))
        else:consume(db,sys.stdin.buffer,a.root)
