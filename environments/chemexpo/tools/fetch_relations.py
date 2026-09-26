"""Resume public product/document relation pagination without guessing identities."""
import concurrent.futures, gzip, json, shutil, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/relations'
URL = 'https://comptox.epa.gov/chemexpo/chemical_product_json/'

def page(start):
    p = DEST / f'{start:07d}.json.gz'
    if p.exists():
        with gzip.open(p, 'rt') as f: return json.load(f)
    for attempt in range(4):
        try:
            if shutil.disk_usage(DEST).free < 5*1024**3 + 16*1024**2:
                raise RuntimeError('Preserve 5 GiB disk reserve')
            with urllib.request.urlopen(URL+f'?draw=1&start={start}&length=100',timeout=60) as r:
                d=json.load(r)
            if d.get('result') != 'ok' or 'data' not in d: raise ValueError('Bad public response')
            tmp=p.with_suffix('.partial')
            with gzip.open(tmp,'wt') as f: json.dump(d,f)
            tmp.replace(p)
            time.sleep(.5)
            return d
        except Exception:
            if attempt==3: raise
            time.sleep(5 * (attempt+1))

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    first=page(0);total=first['recordsTotal'];n=len(first['data'])
    if n!=min(100,total):raise ValueError('Unexpected page size')
    count=n
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for start,d in zip(range(100,total,100),ex.map(page,range(100,total,100))):
            if d['recordsTotal']!=total or len(d['data'])!=min(100,total-start):
                raise ValueError('Source changed or incomplete page; cannot claim complete snapshot')
            count+=len(d['data'])
            if start%10000==0:print(count,'/',total,flush=True)
    (ROOT/'data/relations.json').write_text(json.dumps({'url':URL,'records':count,'complete':count==total,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
    print('complete',count,flush=True)

if __name__=='__main__':main()
