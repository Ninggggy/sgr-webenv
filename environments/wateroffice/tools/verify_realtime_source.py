"""Independently compare a full local day with the official graph response.

Source JSON and its URL/acquisition time are kept on the author side. This program
never obtains expected values from the application being tested.
"""
import argparse,csv,datetime as dt,decimal,gzip,json,pathlib,subprocess,time,urllib.parse
GRADES={'10':'ICE','20':'ESTIMATED','30':'PARTIAL DAY','40':'DRY','50':'REVISED'}


def run(a):
    maps={r['station_id']:r for r in json.loads((a.original/'map-stations-real_time.json').read_text())}
    filters=json.loads((a.original/'realtime-filter-membership.json').read_text())['filters']['parameter_type']
    a.reference.mkdir(parents=True,exist_ok=True)
    checks=[];failures=[]
    for station in json.loads(a.station_list.read_text()):
        codes=[c for c in ('46','47','3','6') if station in filters[c]['stations']]
        for code in codes:
            try:
                cache=a.reference/f'{station}-{code}-{a.day}.json'
                url='https://wateroffice.ec.gc.ca/services/real_time_graph/json/inline?'+urllib.parse.urlencode({'station':station,'start_date':a.day,'end_date':a.day,'param1':code,'param2':'-1'})
                if not cache.exists():
                    started=dt.datetime.now(dt.timezone.utc).isoformat()
                    p=subprocess.run(['curl','-fLsS','--connect-timeout','15','--max-time','120',url],capture_output=True)
                    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[:240])
                    source=json.loads(p.stdout)
                    if code not in source:raise ValueError('Source parameter absent')
                    cache.write_bytes(p.stdout)
                    cache.with_suffix('.source.json').write_text(json.dumps({'url':url,'started':started,'finished':dt.datetime.now(dt.timezone.utc).isoformat()},indent=2))
                    time.sleep(0.25)
                else:source=json.loads(cache.read_text())
                if a.fetch_only:
                    checks.append({'station':station,'parameter':code,'source_saved':True});continue
                tz=dt.timezone(dt.timedelta(hours=float(maps[station]['timezone_offset'])))
                with gzip.open(a.data/f'{station}.csv.gz','rt',encoding='utf-8-sig') as f:
                    expected={}
                    for row in csv.DictReader(f):
                        local=dt.datetime.fromisoformat(row['Date'].replace('Z','+00:00')).astimezone(tz)
                        if row['Parameter/Paramètre']==code and local.date().isoformat()==a.day and row['Value/Valeur']:
                            expected[local.strftime('%Y-%m-%d %H:%M:%S')]=row
                actual={r[0]:(group,r) for group in ('final','provisional') for r in source[code][group] if r[1] is not None}
                if set(actual)!=set(expected):raise ValueError(f'Timestamp sets differ: {len(actual)} source, {len(expected)} snapshot')
                for t,row in expected.items():
                    group,r=actual[t];value=decimal.Decimal(row['Value/Valeur']);q=decimal.Decimal(1).scaleb(value.as_tuple().exponent)
                    if decimal.Decimal(str(r[1])).quantize(q,rounding=decimal.ROUND_HALF_UP)!=value:raise ValueError('Value differs at published CSV precision: '+t)
                    if row['Approval/Approbation'].split('/')[0].strip().lower()!=group:raise ValueError('Approval differs: '+t)
                    grade=row['Grade/Classification'].split('/')[0]
                    if GRADES.get(grade,grade)!=(r[4] or ''):raise ValueError('Grade differs: '+t)
                    if row['Qualifiers/Qualificatifs']!=(r[6] or ''):raise ValueError('Qualifiers differ: '+t)
                checks.append({'station':station,'parameter':code,'day':a.day,'rows':len(expected),'passed':True})
            except Exception as e:failures.append({'station':station,'parameter':code,'error':str(e)})
        print(station,'checked',flush=True)
    result={'checks':checks,'failures':failures,'passed':not failures,'fetch_only':a.fetch_only,'comparison':'Full local day; values at official CSV precision; published Approval, Grade and Qualifiers'}
    a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'failures':failures,'passed':result['passed']}))
    return 1 if failures else 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('data','original','station-list','reference','report'):p.add_argument('--'+name,type=pathlib.Path,required=True)
    p.add_argument('--day',default='2026-08-27');p.add_argument('--fetch-only',action='store_true')
    raise SystemExit(run(p.parse_args()))
