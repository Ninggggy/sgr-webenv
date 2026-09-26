"""Author-side acquisition. Runtime never contacts the source website."""
import csv, gzip, io, json, os, shutil, time, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
RESERVE = 5 * 1024**3
SOURCES = {
    'pucs': 'dl_pucs', 'attributes': 'dl_puctags',
    'keywords': 'dl_lpkeywords', 'functions': 'dl_functionalusecategories',
    'composition': 'dl_co_chemicals', 'presence': 'dl_lp_chemicals',
    'functional': 'dl_functional_uses',
}

def space(extra=0):
    if shutil.disk_usage(RAW).free < RESERVE + extra:
        raise RuntimeError('Insufficient disk space: preserve 5 GiB; no automatic deletion')

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'data/sources.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, route in SOURCES.items():
        if manifest.get(name, {}).get('complete'):
            print(name, 'already complete', flush=True)
            continue
        url = 'https://comptox.epa.gov/chemexpo/' + route + '/'
        start = time.time()
        space(64 * 1024**2)
        with urllib.request.urlopen(url, timeout=90) as r:
            is_zip = 'zip' in r.headers.get('Content-Type', '')
            suffix = '.zip' if is_zip else '.csv.gz'
            path = RAW / (name + suffix)
            temp = path.with_suffix(path.suffix + '.partial')
            source_bytes = 0
            with temp.open('wb') as raw:
                out = raw if is_zip else gzip.GzipFile(fileobj=raw, mode='wb')
                try:
                    while True:
                        space(8 * 1024**2)
                        chunk = r.read(1024 * 1024)
                        if not chunk: break
                        out.write(chunk)
                        source_bytes += len(chunk)
                finally:
                    if out is not raw: out.close()
            if is_zip:
                with zipfile.ZipFile(temp) as z:
                    if z.testzip(): raise ValueError('Corrupt ZIP')
                    csv_members = [i for i in z.infolist() if i.filename.endswith('.csv')]
                    if len(csv_members) != 1: raise ValueError('Expected one CSV member')
                    with z.open(csv_members[0]) as f:
                        header = next(csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig')))
                    uncompressed = csv_members[0].file_size
            else:
                with gzip.open(temp, 'rt', encoding='utf-8-sig', newline='') as f:
                    header = next(csv.reader(f))
                uncompressed = source_bytes
            if len(header) < 2 or any('<html' in x.lower() for x in header):
                raise ValueError('Download is not the expected CSV')
            os.replace(temp, path)
            manifest[name] = dict(url=url, complete=True, file=str(path.relative_to(ROOT)),
                retrieved_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                content_disposition=r.headers.get('Content-Disposition'),
                source_bytes=source_bytes, stored_bytes=path.stat().st_size,
                uncompressed_bytes=uncompressed, columns=header, seconds=time.time()-start)
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print(name, json.dumps(manifest[name]), flush=True)

if __name__ == '__main__': main()
