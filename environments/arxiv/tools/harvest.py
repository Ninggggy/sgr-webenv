"""Author-side OAI harvesting. Never imported by the public web application."""
import argparse
import datetime as dt
import email.utils
import json
import shutil
import shlex
import sqlite3
import subprocess
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

OAI = 'http://www.openarchives.org/OAI/2.0/'
RAW = 'http://arxiv.org/OAI/arXivRaw/'
SETS = ('cs:cs', 'math:math', 'stat:stat')
BASE = 'https://oaipmh.arxiv.org/oai'
GIB = 1024**3


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def used_bytes(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


def check_space(root, reserve=2*GIB):
    free = shutil.disk_usage(root).free
    # User accepted the >10 GiB estimate on 2026-09-25. Preserve the absolute
    # free-space floor and headroom for one page/SQLite transaction instead.
    if free < 8*GIB + reserve:
        raise RuntimeError(f'Capacity stop: free={free}, reserved={reserve}')


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript('''
      PRAGMA foreign_keys=ON;
      CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, oai_modified TEXT, deleted INTEGER NOT NULL,
        title TEXT, abstract TEXT, authors TEXT, categories TEXT,
        comments TEXT, journal_ref TEXT, doi TEXT, license TEXT,
        report_num TEXT, acm_class TEXT, msc_class TEXT,
        source_xml TEXT NOT NULL, fetched_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS versions (
        paper_id TEXT NOT NULL REFERENCES records(id), number INTEGER NOT NULL,
        submitted_at TEXT NOT NULL, source_size TEXT, source_type TEXT,
        detail_json TEXT, detail_source TEXT,
        PRIMARY KEY(paper_id, number)
      );
      CREATE TABLE IF NOT EXISTS membership (
        paper_id TEXT NOT NULL REFERENCES records(id), source_set TEXT NOT NULL,
        PRIMARY KEY(paper_id, source_set)
      );
      CREATE TABLE IF NOT EXISTS harvest_state (
        source_set TEXT PRIMARY KEY, token TEXT, complete INTEGER NOT NULL DEFAULT 0,
        pages INTEGER NOT NULL DEFAULT 0, response_date TEXT, updated_at TEXT
      );
      CREATE TABLE IF NOT EXISTS announcements (
        paper_id TEXT NOT NULL REFERENCES records(id), version INTEGER,
        category TEXT NOT NULL, announced_at TEXT NOT NULL, event_type TEXT NOT NULL,
        source TEXT NOT NULL, source_position INTEGER, PRIMARY KEY(paper_id, category, announced_at, event_type)
      );
    ''')
    return db


def parse_page(body):
    root = ET.fromstring(body)
    if root.tag != '{'+OAI+'}OAI-PMH':
        raise ValueError('Response is not OAI-PMH XML')
    errors = root.findall('{'+OAI+'}error')
    if errors:
        raise ValueError('OAI error: ' + '; '.join(str(e.attrib)+' '+(e.text or '') for e in errors))
    output = []
    for record in root.findall('.//{'+OAI+'}record'):
        header = record.find('{'+OAI+'}header')
        identifier = header.findtext('{'+OAI+'}identifier')
        if not identifier or not identifier.startswith('oai:arXiv.org:'):
            raise ValueError('Unexpected OAI identifier')
        paper_id = identifier[len('oai:arXiv.org:'):]
        deleted = header.get('status') == 'deleted'
        raw = record.find('.//{'+RAW+'}arXivRaw')
        if not deleted and raw is None:
            raise ValueError('Missing arXivRaw metadata')
        def field(name):
            if raw is None:
                return None
            return raw.findtext('{'+RAW+'}'+name)
        if not deleted and field('id') != paper_id:
            raise ValueError('Header/metadata identifier mismatch')
        versions = []
        if raw is not None:
            for v in raw.findall('{'+RAW+'}version'):
                label = v.attrib['version']
                if not label.startswith('v'):
                    raise ValueError('Unexpected version label')
                number = int(label[1:])
                date = email.utils.parsedate_to_datetime(v.findtext('{'+RAW+'}date'))
                if date.tzinfo is None:
                    raise ValueError('Version time has no timezone')
                versions.append((number, date.astimezone(dt.timezone.utc).isoformat(),
                                 v.findtext('{'+RAW+'}size'), v.findtext('{'+RAW+'}source_type')))
            numbers = sorted(v[0] for v in versions)
            if not numbers or numbers != list(range(1, max(numbers)+1)):
                raise ValueError('Incomplete or duplicate version sequence')
        fields = [field(k) for k in ('title','abstract','authors','categories','comments',
                  'journal-ref','doi','license','report-no','acm-class','msc-class')]
        output.append((paper_id, header.findtext('{'+OAI+'}datestamp'), int(deleted),
                       fields, versions, ET.tostring(record, encoding='unicode')))
    token = root.find('.//{'+OAI+'}resumptionToken')
    return output, (token.text or '').strip() if token is not None else '', root.findtext('{'+OAI+'}responseDate')


def import_page(db, body, source_set):
    records, token, response_date = parse_page(body)
    if not records:
        raise ValueError('Unexpected empty page; not marking coverage complete')
    now = utc()
    with db:
        for paper_id, modified, deleted, fields, versions, xml in records:
            values = [paper_id, modified, deleted, *fields, xml, now]
            db.execute('INSERT INTO records VALUES ('+','.join('?' for _ in values)+') '
                       'ON CONFLICT(id) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in
                       ('oai_modified','deleted','title','abstract','authors','categories','comments',
                        'journal_ref','doi','license','report_num','acm_class','msc_class','source_xml','fetched_at')),
                       values)
            for number, date, size, source_type in versions:
                # Historical content remains NULL until separately obtained. Never copy latest fields.
                db.execute('INSERT INTO versions(paper_id,number,submitted_at,source_size,source_type) '
                           'VALUES(?,?,?,?,?) ON CONFLICT(paper_id,number) DO UPDATE SET '
                           'submitted_at=excluded.submitted_at,source_size=excluded.source_size,source_type=excluded.source_type',
                           (paper_id, number, date, size, source_type))
            db.execute('INSERT OR IGNORE INTO membership VALUES (?,?)', (paper_id,source_set))
        db.execute('INSERT INTO harvest_state VALUES (?,?,?,1,?,?) ON CONFLICT(source_set) DO UPDATE SET '
                   'token=excluded.token,complete=excluded.complete,pages=pages+1,'
                   'response_date=excluded.response_date,updated_at=excluded.updated_at',
                   (source_set,token,int(not token),response_date,now))
    return len(records), token


def request(url, body_path, headers_path, post_data=None):
    # curl's total deadline also bounds DNS resolution, unlike urllib's socket timeout.
    post_args=['--data-binary','@-','-H','Content-Type: application/x-www-form-urlencoded'] if post_data is not None else []
    p = subprocess.run(['curl','--compressed','--connect-timeout','8','--max-time','600','--speed-time','60','--speed-limit','100','--max-filesize','25000000',
                        '-sS','-D',str(headers_path),'-o',str(body_path),'-w','%{http_code}',url]+post_args,
                       input=post_data,capture_output=True, text=True, timeout=610)
    status = int(p.stdout[-3:]) if p.stdout[-3:].isdigit() else 0
    if p.returncode or status != 200:
        raise RuntimeError(f'HTTP {status}, curl={p.returncode}: {p.stderr.strip()}')
    return body_path.read_bytes()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--pages-per-set',type=int,default=1,help='0 = resume to exhaustion; default is capacity sample')
    p.add_argument('--sets',nargs='+',choices=SETS,default=list(SETS))
    p.add_argument('--delay',type=float,default=3.1)
    p.add_argument('--from-date', help='Inclusive OAI metadata modification date')
    p.add_argument('--until-date', help='Inclusive OAI metadata modification date')
    p.add_argument('--database-name', default='metadata.sqlite')
    p.add_argument('--mirror-host', help='Author SSH host; imports each complete page before local commit')
    p.add_argument('--mirror-root', default=str(Path(__file__).resolve().parents[1]))
    args = p.parse_args()
    if args.delay < 3 or args.pages_per_set < 0:
        p.error('Delay must be at least three seconds and page limit nonnegative')
    root=args.root.resolve(); root.mkdir(parents=True,exist_ok=True)
    reports=root/'reports';reports.mkdir(exist_ok=True)
    if '/' in args.database_name or not args.database_name.endswith('.sqlite'):p.error('Require a SQLite filename')
    if args.mirror_host and args.database_name!='metadata.sqlite':p.error('Named author database must be transferred explicitly')
    for date_value in (args.from_date,args.until_date):
        if date_value:dt.date.fromisoformat(date_value)
    db=connect(root/'data'/args.database_name)
    log=reports/'harvest-events.jsonl'
    previous=0.0
    for source_set in args.sets:
        count=0
        while args.pages_per_set == 0 or count < args.pages_per_set:
            check_space(root)
            row=db.execute('SELECT token,complete FROM harvest_state WHERE source_set=?',(source_set,)).fetchone()
            if row and row[1]:break
            query={'verb':'ListRecords'}
            if row and row[0]: query['resumptionToken']=row[0]
            else:
                query.update(metadataPrefix='arXivRaw',set=source_set)
                if args.from_date:query['from']=args.from_date
                if args.until_date:query['until']=args.until_date
            url=BASE+'?'+urllib.parse.urlencode(query)
            time.sleep(max(0,args.delay-(time.monotonic()-previous)))
            previous=time.monotonic()
            body_path=reports/'last-oai-response.xml';headers_path=reports/'last-oai-response.headers'
            event={'time':utc(),'set':source_set,'url':url}
            try:
                body=request(url,body_path,headers_path)
                parse_page(body)  # Validate before sending author data.
                if args.mirror_host:
                    remote_code = ('import sys; from pathlib import Path; sys.path.insert(0,"tools"); '
                                   'from harvest import connect,check_space,import_page; '
                                   'r=Path.cwd(); check_space(r); '
                                   'd=connect(r/"data/metadata.sqlite"); '
                                   'print(import_page(d,sys.stdin.buffer.read(),'+repr(source_set)+'))')
                    command = 'cd '+shlex.quote(args.mirror_root)+' && python3 -c '+shlex.quote(remote_code)
                    subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',args.mirror_host,command],
                                   input=body,check=True,timeout=180,stdout=subprocess.DEVNULL)
                n,token=import_page(db,body,source_set)
                event.update(records=n,complete=not bool(token),response_bytes=len(body))
            except Exception as exc:
                event['error']=str(exc)
                with log.open('a') as f:f.write(json.dumps(event)+'\n')
                print(json.dumps(event),flush=True)
                raise SystemExit(2)
            with log.open('a') as f:f.write(json.dumps(event)+'\n')
            print(json.dumps(event),flush=True)
            count+=1
            if not token:break
    summary={'captured_at':utc(),'records':db.execute('SELECT count(*) FROM records').fetchone()[0],
             'versions':db.execute('SELECT count(*) FROM versions').fetchone()[0],
             'version_details':db.execute('SELECT count(*) FROM versions WHERE detail_json IS NOT NULL').fetchone()[0],
             'sets':db.execute('SELECT source_set,complete,pages FROM harvest_state').fetchall(),
             'database_bytes':(root/'data'/'metadata.sqlite').stat().st_size}
    (reports/'harvest-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
