"""Resumable official CSV acquisition; no changes to the existing runtime snapshot."""
import argparse, concurrent.futures, csv, datetime as dt, gzip, io, json, math
import os, pathlib, shutil, subprocess, threading, time, urllib.parse

START = '2026-08-26T09:40:00Z'
END = '2026-09-25T09:40:00Z'
SOURCE = 'https://wateroffice.ec.gc.ca/services/real_time_data/csv/inline'
FIELDS = [' ID', 'Date', 'Parameter/Paramètre', 'Value/Valeur', 'Qualifier/Qualificatif',
          'Symbol/Symbole', 'Approval/Approbation', 'Grade/Classification', 'Qualifiers/Qualificatifs']
STOP = threading.Event()


class AcquisitionStopped(RuntimeError):
    pass


def check_stop():
    if STOP.is_set():
        raise AcquisitionStopped('Acquisition stopped after an official access refusal')


def utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))


def space(path):
    if shutil.disk_usage(path).free < 5 * 1024**3 + 32 * 1024**2:
        raise RuntimeError('Capacity floor: preserve 5 GiB plus request buffer')


def write_json(path, value):
    temp = path.with_suffix('.partial')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def acquire(station, codes, out):
    began = time.monotonic()
    target = out / (station + '.csv.gz')
    meta = out / (station + '.json')
    if target.exists() and meta.exists():
        old = json.loads(meta.read_text())
        if old.get('complete') and old.get('from') == START and old.get('to') == END and old.get('parameters') == codes:
            return old
    scratch = out / ('segments-' + station)
    scratch.mkdir(exist_ok=True)
    segments = []

    def fetch(lo, hi, level=0):
        stem = lo.strftime('%Y%m%dT%H%M%S') + '-' + hi.strftime('%Y%m%dT%H%M%S')
        dest, info = scratch / (stem + '.csv.gz'), scratch / (stem + '.json')
        if dest.exists() and info.exists():
            record = json.loads(info.read_text())
            if record.get('complete'):
                segments.append((dest, record))
                return
        query = [('stations[]', station)] + [('parameters[]', c) for c in codes] + [
            ('start_date', lo.strftime('%Y-%m-%d %H:%M:%S')),
            ('end_date', hi.strftime('%Y-%m-%d %H:%M:%S'))]
        url = SOURCE + '?' + urllib.parse.urlencode(query)
        failure = None
        for attempt in range(3):
            check_stop()
            space(out)
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            p = subprocess.run(['curl', '-fLsS', '--compressed', '--connect-timeout', '15',
                                '--max-time', '120', url], capture_output=True)
            try:
                if p.returncode:
                    raise RuntimeError(p.stderr.decode(errors='replace')[:300])
                # Official responses omit the final newline. Successful HTTP transport
                # and a complete CSV field set are required; newline is not required.
                reader = csv.DictReader(io.StringIO(p.stdout.decode('utf-8-sig')))
                if reader.fieldnames != FIELDS:
                    raise ValueError('Unexpected official CSV columns')
                count = 0
                for row in reader:
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError('Incomplete CSV row')
                    if row[' ID'] != station or row['Parameter/Paramètre'] not in codes:
                        raise ValueError('Unexpected station or parameter')
                    if not lo <= utc(row['Date']) <= hi:
                        raise ValueError('Timestamp outside request interval')
                    if row['Value/Valeur'] and not math.isfinite(float(row['Value/Valeur'])):
                        raise ValueError('Nonfinite observation')
                    count += 1
                space(out)
                tmp = dest.with_suffix('.partial')
                with gzip.open(tmp, 'wb') as f:
                    f.write(p.stdout)
                tmp.replace(dest)
                record = {'url': url, 'started': started, 'finished': dt.datetime.now(dt.timezone.utc).isoformat(),
                          'rows': count, 'complete': True, 'bytes': dest.stat().st_size}
                write_json(info, record)
                segments.append((dest, record))
                return
            except (ValueError, RuntimeError, UnicodeError) as e:
                failure = str(e)
                # Respect refusal; do not subdivide a rate-limited request to evade it.
                if p.returncode == 22 and any(code in failure for code in ('403', '429')):
                    STOP.set()
                    raise AcquisitionStopped('Access refused; stop this acquisition: ' + failure)
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
        days = (hi - lo).total_seconds() / 86400
        if days > 1:
            width = 3 if days > 3 else 1
            point = lo
            while point < hi:
                end = min(hi, point + dt.timedelta(days=width))
                fetch(point, end, level + 1)
                point = end
            return
        raise RuntimeError(f'{station} {stem}: {failure}')

    for i in range(0, 30, 7):
        fetch(utc(START) + dt.timedelta(days=i), min(utc(END), utc(START) + dt.timedelta(days=i + 7)))
    records = {}
    for path, info in segments:
        with gzip.open(path, 'rt', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                key = (row['Date'], row['Parameter/Paramètre'])
                if key in records and records[key] != row:
                    raise ValueError('Conflicting segment-boundary observations; keep source segments for review')
                records[key] = row
    space(out)
    temp = target.with_suffix('.partial')
    with gzip.open(temp, 'wt', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for key in sorted(records):
            writer.writerow(records[key])
    temp.replace(target)
    values = list(records.values())
    result = {'station': station, 'parameters': codes, 'from': START, 'to': END, 'complete': True,
              'rows': len(values), 'bytes': target.stat().st_size, 'seconds': time.monotonic() - began,
              'approval_values': sorted({r['Approval/Approbation'] for r in values}),
              'grade_values': sorted({r['Grade/Classification'] for r in values}),
              'empty_parameters': [c for c in codes if not any(r['Parameter/Paramètre'] == c for r in values)],
              'segments': [info for _, info in segments]}
    write_json(meta, result)
    # Only this program's completed, reproducible request shards are removed.
    shutil.rmtree(scratch)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--station-list', type=pathlib.Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    stations = json.loads(args.station_list.read_text())
    all_ids = {r['number'] for r in json.loads((args.data / 'realtime-stations.json').read_text())['stations']}
    if len(stations) != len(set(stations)) or not set(stations) <= all_ids:
        raise ValueError('Invalid station list')
    membership = json.loads((args.data / 'realtime-filter-membership.json').read_text())['filters']['parameter_type']
    def work(station):
        check_stop()
        codes = [c for c in ['46', '47', '3', '6'] if station in membership[c]['stations']]
        if not codes:
            # Retain catalog entries that have no published parameter; this is
            # not a successful empty observation query and must remain distinct.
            target=args.output/(station+'.csv.gz')
            with gzip.open(target,'wt',newline='',encoding='utf-8') as f:
                csv.writer(f).writerow(FIELDS)
            result={'station':station,'parameters':[],'from':START,'to':END,'complete':True,
                    'rows':0,'bytes':target.stat().st_size,'seconds':0,'segments':[],
                    'availability':'no_published_parameters_in_archived_catalog',
                    'availability_source':'realtime-filter-membership.json',
                    'approval_values':[],'grade_values':[],'empty_parameters':[]}
            write_json(args.output/(station+'.json'),result)
            return result
        return acquire(station, codes, args.output)
    results, failures = [], []
    began = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(work, n): n for n in stations}
        for future in concurrent.futures.as_completed(futures):
            n = futures[future]
            try:
                r = future.result(); results.append(r)
                message = {'station': n, 'rows': r['rows'], 'bytes': r['bytes'], 'complete': True}
            except Exception as e:
                message = {'station': n, 'error': str(e), 'complete': False}; failures.append(message)
            with (args.output / 'progress.jsonl').open('a') as f:
                f.write(json.dumps(message) + '\n')
            print(json.dumps(message), flush=True)
            if STOP.is_set():
                for pending in futures:
                    pending.cancel()
                break
    report = {'from': START, 'to': END, 'requested_stations': len(stations), 'completed': len(results),
              'failures': failures, 'bytes': sum(r['bytes'] for r in results), 'seconds': time.monotonic() - began,
              'rows': sum(r['rows'] for r in results), 'source': SOURCE, 'complete': not failures}
    write_json(args.output / 'collection-report.json', report)
    print(json.dumps(report), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
