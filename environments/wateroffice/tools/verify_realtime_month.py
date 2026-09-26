"""Validate all station files and report revisions before activating a new snapshot."""
import argparse, csv, datetime as dt, decimal, gzip, json, math, pathlib


def stamp(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def verify(data, original, expected):
    results=[];failures=[];total=0;size=0;began=[];ended=[]
    start='2026-08-26T09:40:00Z';end='2026-09-25T09:40:00Z'
    oldwindow=json.loads((original/'realtime/window.json').read_text())
    for n in expected:
        try:
            metadata=json.loads((data/(n+'.json')).read_text())
            if metadata.get('complete') is not True or metadata['from']!=start or metadata['to']!=end:
                raise ValueError('Incomplete metadata or wrong interval')
            with gzip.open(data/(n+'.csv.gz'),'rt',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
            assert len(rows)==metadata['rows'],'row count'
            seen=set();new={};quality={'approval_nonempty':0,'grade_nonempty':0,'unknown_approval_values':set()}
            for r in rows:
                key=(r['Date'],r['Parameter/Paramètre'])
                assert key not in seen,'duplicate observation';seen.add(key)
                assert r[' ID']==n and r['Parameter/Paramètre'] in metadata['parameters'],'unexpected record'
                assert stamp(start)<=stamp(r['Date'])<=stamp(end),'outside interval'
                if r['Value/Valeur']:assert math.isfinite(float(r['Value/Valeur'])),'nonfinite value'
                quality['approval_nonempty']+=bool(r['Approval/Approbation']);quality['grade_nonempty']+=bool(r['Grade/Classification'])
                if r['Value/Valeur'] and r['Approval/Approbation'].split('/')[0].upper() not in ('PROVISIONAL','FINAL'):
                    quality['unknown_approval_values'].add(r['Approval/Approbation'])
                if r['Parameter/Paramètre'] in ('46','47') and stamp(oldwindow['from'])<=stamp(r['Date'])<=stamp(oldwindow['to']):
                    new[(stamp(r['Date']),r['Parameter/Paramètre'])]=r
            if not metadata['parameters']:
                assert not rows and metadata.get('availability')=='no_published_parameters_in_archived_catalog'
            else:
                intervals=[]
                import urllib.parse
                for part in metadata['segments']:
                    assert part['complete'];q=urllib.parse.parse_qs(urllib.parse.urlsplit(part['url']).query)
                    assert q['stations[]']==[n] and q['parameters[]']==metadata['parameters']
                    intervals.append((stamp(q['start_date'][0]).replace(tzinfo=dt.timezone.utc),stamp(q['end_date'][0]).replace(tzinfo=dt.timezone.utc)))
                    began.append(part['started']);ended.append(part['finished'])
                point=stamp(start)
                for lo,hi in sorted(intervals):
                    assert lo==point and hi>lo,'segment gap or overlap';point=hi
                assert point==stamp(end),'incomplete temporal request coverage'
            old={}
            with gzip.open(original/'realtime'/(n+'.csv.gz'),'rt',encoding='utf-8-sig') as f:
                for r in csv.DictReader(f):
                    for field,code in [('LEVEL','46'),('DISCHARGE','47')]:
                        if r[field]:old[(stamp(r['DATETIME']),code)]=r[field]
            revised=0;equal=0;missing=0
            for key,value in old.items():
                if key not in new or not new[key]['Value/Valeur']:missing+=1;continue
                v=decimal.Decimal(new[key]['Value/Valeur']);quantum=decimal.Decimal(1).scaleb(v.as_tuple().exponent)
                if decimal.Decimal(value).quantize(quantum,rounding=decimal.ROUND_HALF_UP)==v:equal+=1
                else:revised+=1
            added=sum(bool(v['Value/Valeur']) and k not in old for k,v in new.items())
            quality['unknown_approval_values']=sorted(quality['unknown_approval_values'])
            results.append({'station':n,'rows':len(rows),'availability':metadata.get('availability','queried'),
                            'quality':quality,'overlap':{'equal_at_published_csv_precision':equal,'revised_values':revised,'missing_old_values':missing,'additional_values':added},'passed':True})
            total+=len(rows);size+=(data/(n+'.csv.gz')).stat().st_size
        except Exception as e:failures.append({'station':n,'error':str(e)})
    report={'requested_stations':len(expected),'validated_stations':len(results),'failures':failures,'complete':not failures,
            'rows':total,'bytes':size,'stations':results,'comparison_precision':'Official CSV precision; the original graph may retain finer internal precision.',
            'old_unit_status_comparison':'The old GeoMet snapshot has no Approval/Grade; these fields cannot be retrospectively compared or attached to old values.'}
    (data.parent/'month-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    if failures:raise ValueError('Incomplete national acquisition; no runtime window activated')
    catalog_ids={r['number'] for r in json.loads((original/'realtime-stations.json').read_text())['stations']}
    if not set(expected)<=catalog_ids:raise ValueError('Station scope exceeds original catalog')
    window={'format':'wateroffice-csv-v2','from':start,'to':end,'station_count':len(expected),'complete':True,
            'collection_started':min(began),'collection_finished':max(ended),
            'source':'Official Wateroffice CSV service','default_days':7,
            'catalog_station_count':len(catalog_ids),'national_30day_complete':set(expected)==catalog_ids}
    if set(expected)!=catalog_ids:
        window.update(covered_stations=sorted(expected),legacy_window=oldwindow)
        report.update(scope='Partial thirty-day upgrade; all other catalog stations retain the original snapshot',national_30day_complete=False)
        (data.parent/'month-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (data/'window.json').write_text(json.dumps(window,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=pathlib.Path,required=True);p.add_argument('--original',type=pathlib.Path,required=True)
    p.add_argument('--station-list',type=pathlib.Path,required=True)
    a=p.parse_args();r=verify(a.data,a.original,json.loads(a.station_list.read_text()))
    print(json.dumps({k:v for k,v in r.items() if k!='stations'}))
