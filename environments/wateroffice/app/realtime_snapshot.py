"""Read dated Wateroffice observations without inferring quality status."""
import csv
import datetime as dt
import functools
import gzip
import json
from pathlib import Path


UTC = dt.timezone.utc
# Published Wateroffice FAQ grade names, not inferred approval or grade values.
GRADE_NAMES = {'10': 'ICE', '20': 'ESTIMATED', '30': 'PARTIAL DAY', '40': 'DRY', '50': 'REVISED'}
TIMEZONE_NAMES = {'AST': 'Atlantic Standard Time', 'CST': 'Central Standard Time',
                  'EST': 'Eastern Standard Time', 'MST': 'Mountain Standard Time',
                  'NST': 'Newfoundland Standard Time', 'PST': 'Pacific Standard Time'}


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def window(data, station=None):
    value=json.loads((Path(data) / 'realtime/window.json').read_text())
    if station is not None and 'covered_stations' in value and station not in value['covered_stations']:
        return value['legacy_window']
    return value


def is_official_csv(data, station=None):
    return window(data,station).get('format') == 'wateroffice-csv-v2'


@functools.lru_cache(maxsize=4)
def station_timezones(data):
    rows = json.loads((Path(data) / 'map-stations-real_time.json').read_text())
    return {r['station_id']: dt.timezone(dt.timedelta(hours=float(r['timezone_offset']))) for r in rows}


def timezone(data, station):
    try:
        return station_timezones(str(data))[station]
    except KeyError:
        raise ValueError('Official station time zone is unavailable')


def bounds(data, station):
    w = window(data,station)
    tz = timezone(data, station)
    return timestamp(w['from']).astimezone(tz), timestamp(w['to']).astimezone(tz)


def dates(data, station, start=None, end=None, days=7):
    lo, hi = bounds(data, station)
    end_date = dt.date.fromisoformat(end) if end else hi.date()
    start_date = dt.date.fromisoformat(start) if start else max(lo.date(), end_date - dt.timedelta(days=days))
    if not lo.date() <= start_date <= end_date <= hi.date():
        raise ValueError('Dates outside the archived real-time snapshot')
    return start_date, end_date


def approval_code(value):
    name = value.split('/')[0].strip().upper()
    return {'PROVISIONAL': '1', 'FINAL': '4'}.get(name)


def approval_label(value):
    return {'1': 'Provisional', '4': 'Final'}.get(value, value or '')


@functools.lru_cache(maxsize=4)
def station_ids(data):
    return frozenset(r['number'] for r in json.loads((Path(data)/'realtime-stations.json').read_text())['stations'])


def records(data, station, parameter, start=None, end=None):
    if station not in station_ids(str(data)):
        raise ValueError('Station not in real-time snapshot')
    if parameter not in ('3', '6', '46', '47'):
        raise ValueError('Invalid real-time parameter')
    folder = Path(data) / 'realtime'
    metadata = json.loads((folder / (station + '.json')).read_text())
    w = window(data)
    if not metadata.get('complete') or metadata.get('from') != w['from'] or metadata.get('to') != w['to']:
        raise OSError('This station snapshot is incomplete')
    if parameter not in metadata['parameters']:
        raise ValueError('This parameter is not published for the selected station in the archived station list')
    first, last = dates(data, station, start, end)
    lower, upper = timestamp(w['from']), timestamp(w['to'])
    tz = timezone(data, station)
    result = []
    with gzip.open(folder / (station + '.csv.gz'), 'rt', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['Parameter/Paramètre'] != parameter:
                continue
            instant = timestamp(row['Date'])
            local = instant.astimezone(tz)
            if lower <= instant <= upper and first <= local.date() <= last:
                result.append({'utc': row['Date'], 'time': local.strftime('%Y-%m-%d %H:%M:%S'),
                               'value': row['Value/Valeur'], 'approval': row['Approval/Approbation'],
                               'grade': row['Grade/Classification'], 'qualifiers': row['Qualifiers/Qualificatifs'],
                               'symbol': row['Symbol/Symbole'], 'qualifier': row['Qualifier/Qualificatif']})
    return result


def table_series(data, station, parameter, start=None, end=None):
    result = []
    for row in records(data, station, parameter, start, end):
        # Keep the seven-field graph shape. CSV publishes approval names,
        # not the graph's finer internal approval codes; never invent those codes.
        grade = row['grade'].split('/', 1)
        result.append([row['time'], float(row['value']) if row['value'] else None,
                       row['approval'].split('/')[0], row['grade'],
                       GRADE_NAMES.get(grade[0], grade[0]), grade[-1], row['qualifiers']])
    return result


def graph_series(data, station, parameter, start=None, end=None):
    out = {key: [] for key in ('final', 'provisional', 'measurements', 'maximum', 'minimum',
                               'mean', 'median', 'upper_quartile', 'lower_quartile')}
    for row in table_series(data, station, parameter, start, end):
        kind = {'1': 'provisional', '4': 'final'}.get(approval_code(row[2]))
        if kind is None:
            if row[1] is not None:
                raise ValueError('Approval unavailable for selected observations; use the table or download for unclassified data')
            continue
        out[kind].append(row)
    return out


def description(data, station=None):
    w = window(data,station)
    if station is None and 'covered_stations' in w:
        return (str(len(w['covered_stations']))+' stations have official CSV observations for the thirty-day window '+w['from']+' through '+w['to']+'. Other catalog stations retain the original seven-day GeoMet observations and separately dated daily means. Unit-value Approval and Grade are unavailable in that older source. Each station uses its own complete source snapshot; new quality fields are never attached to old values.')
    if w.get('format')!='wateroffice-csv-v2':
        return 'Seven-day GeoMet observation snapshot: '+w['from']+' through '+w['to']+'. Unit-value Approval and Grade are unavailable from this source. Daily means retain their separately archived source metadata.'
    return ('Fixed UTC observation window: ' + w['from'] + ' through ' + w['to'] +
            '. Local boundary dates may be partial. Official values and quality fields were collected ' +
            w.get('collection_started', 'at the documented per-request times') + ' through ' +
            w.get('collection_finished', 'the documented end of collection') +
            '; this is a dated acquisition, not a simultaneous historical website snapshot.')


def export_zip(data, numbers, parameter, fmt, start=None, end=None):
    import io
    import zipfile
    import xml.etree.ElementTree as ET
    from downloads import value_text
    if fmt not in ('csv', 'txt', 'xml'):
        raise ValueError('Invalid real-time download format')
    stations = {r['number']: r for r in json.loads((Path(data) / 'realtime-stations.json').read_text())['stations']}
    maps = {r['station_id']: r for r in json.loads((Path(data) / 'map-stations-real_time.json').read_text())}
    params = {'46': ('HG', 'Water level (unit values)', 'm', 'Level'),
              '47': ('QR', 'Discharge (unit values)', 'm3/s', 'Flow'),
              '3': ('HGD', 'Water level (daily mean values)', 'm', 'Level'),
              '6': ('QRD', 'Discharge (daily mean values)', 'm3/s', 'Flow')}
    if parameter not in params:
        raise ValueError('Invalid real-time parameter')
    abbr, label, unit, kind = params[parameter]
    with_quality = parameter in ('46', '47')
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for number in numbers:
            if number not in stations:
                raise ValueError('Station not in real-time snapshot')
            rows = records(data, number, parameter, start, end)
            tz = maps[number]['timezone_abbr_en']
            def fields(row):
                return [value_text(float(row['value']), kind) if row['value'] else '',
                        row['approval'].split('/')[0], row['grade'].split('/')[0], row['qualifiers']]
            if fmt == 'xml':
                root = ET.Element('realTimeData')
                for key, value in [('stationid', number), ('fromdate', rows[0]['time'] if rows else ''),
                                   ('todate', rows[-1]['time'] if rows else ''), ('timezone', tz)]:
                    ET.SubElement(root, key).text = value
                body = ET.SubElement(root, 'data')
                for row in rows:
                    record = ET.SubElement(body, 'record')
                    pairs = [('datestamp', row['time'] + '.000'), ('code', abbr), ('value', fields(row)[0])]
                    if with_quality:
                        pairs += list(zip(('approval', 'grade', 'qualifiers'), fields(row)[1:]))
                    for key, value in pairs:
                        ET.SubElement(record, key).text = value
                payload = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            else:
                text = io.StringIO(newline='')
                text.write('\ufeffReal-time data - subject to revision\r\nCopyright Environment Canada(2026)\r\n\r\n')
                writer = csv.writer(text, delimiter=',' if fmt == 'csv' else '\t')
                station = stations[number]
                writer.writerow([f'Real-Time Hydrometric Data for {station["name"]} ({number}) [{station["province"]}]'])
                writer.writerow([])
                writer.writerow([number, station['name']])
                writer.writerow(['Description of parameters:'])
                writer.writerow([parameter, label, unit])
                writer.writerow([])
                writer.writerow([f'Date ({tz})', 'Parameter ', f'Value ({unit})'] + (['Approval', 'Grade', 'Qualifiers'] if with_quality else []))
                for row in rows:
                    writer.writerow([row['time'], parameter] + (fields(row) if with_quality else fields(row)[:1]))
                payload = text.getvalue().encode('utf-8')
            stamp = timestamp(window(data)['to']).strftime('%Y%m%dT%H%M')
            z.writestr(f'{number}_{abbr}_{stamp}.{fmt}', payload)
        z.writestr('OFFLINE_SNAPSHOT.txt', description(data) + '\nOfficial blank quality fields remain blank. Daily-mean download columns follow the original daily format; their quality metadata is retained in graph data.\n')
    return out.getvalue()
