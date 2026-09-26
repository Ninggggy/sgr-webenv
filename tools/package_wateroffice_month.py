#!/usr/bin/env python3
"""Reuse an immutable released archive and replace its realtime snapshot.

The HYDAT member is streamed from the existing archive; no unpacked database
copy or database rewrite is made. Run the independent month verifier first.
"""
import argparse,io,json,shutil,tarfile
from pathlib import Path
FILES={'Hydat.sqlite3','operation-membership.json','map-stations-real_time.json',
       'reference.json','realtime-stations.json','map-stations-historical.json',
       'realtime-filter-membership.json','reference-display.json'}
DIRECTORIES={'watch-snapshot','datums','realtime-metadata','map','realtime-daily','realtime'}


def space(output):
    if shutil.disk_usage('/').free<5*1024**3 or shutil.disk_usage(output.parent).free<5*1024**3:
        raise RuntimeError('Preserve at least 5 GiB free space')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-archive',type=Path,required=True)
    p.add_argument('--realtime',type=Path,required=True)
    p.add_argument('--verification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();space(a.output)
    if a.output.exists():raise ValueError('Output already exists')
    window=json.loads((a.realtime/'window.json').read_text());report=json.loads(a.verification.read_text())
    if window.get('format')!='wateroffice-csv-v2' or not window.get('complete') or window.get('catalog_station_count')!=2248:
        raise ValueError('Verified snapshot and complete original catalog required')
    if not report.get('complete') or report.get('validated_stations')!=window['station_count'] or report.get('failures'):
        raise ValueError('Independent verification of every upgraded station required')
    ids={r['station'] for r in report['stations']}
    if len(ids)!=window['station_count']:raise ValueError('Duplicate or missing station verification')
    if len(ids)<2248 and (set(window.get('covered_stations',[]))!=ids or not window.get('legacy_window')):
        raise ValueError('Partial upgrade must explicitly retain the earlier snapshot')
    names={n+suffix for n in ids for suffix in ('.json','.csv.gz')}|{'window.json'}
    if any(not (a.realtime/n).is_file() or (a.realtime/n).is_symlink() for n in names):raise ValueError('Missing station file')
    temporary=a.output.with_suffix(a.output.suffix+'.partial');seen=set();copied=0
    def clean(info):
        info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644;info.pax_headers={};return info
    def text_member(out,name,text):
        raw=text.encode();info=tarfile.TarInfo(name);info.size=len(raw);out.addfile(clean(info),io.BytesIO(raw))
    try:
        with tarfile.open(a.base_archive,'r|gz') as source,tarfile.open(temporary,'w|gz',compresslevel=3) as out:
            for member in source:
                path=Path(member.name)
                if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe base archive path')
                if not member.isfile():continue
                if member.name not in FILES and path.parts[0] not in DIRECTORIES:continue
                if path.parts[0]=='realtime' and (path.name=='window.json' or path.name in names):continue
                if member.name in seen:raise ValueError('Duplicate base member')
                seen.add(member.name)
                content=source.extractfile(member)
                if member.name=='realtime-stations.json':
                    raw=content.read();catalog=json.loads(raw)
                    catalog_ids={r['number'] for r in catalog['stations']}
                    if len(catalog_ids)!=2248 or not ids<=catalog_ids:raise ValueError('Station scope differs from the released catalog')
                    content=io.BytesIO(raw)
                out.addfile(clean(member),content);copied+=1
                if copied%100==0:space(a.output)
            if not FILES<=seen:raise ValueError('Incomplete base archive')
            for name in sorted(names):
                out.add(a.realtime/name,arcname='realtime/'+name,filter=clean,recursive=False)
            text_member(out,'DATA_VERSION.json',json.dumps({'base_release':'v0.1.0','realtime':window,
                'base_archive_url':'https://github.com/Ninggggy/sgr-webenv/releases/download/v0.1.0/wateroffice-data-v0.1.0.tar.gz',
                'method':'Immutable base members streamed unchanged; selected stations upgraded to complete thirty-day official CSV products; other stations retain original observations and daily means.'},indent=2)+'\n')
            text_member(out,'NOTICE.md','# Wateroffice data attribution\n\nHydrometric observations and station information: Environment and Climate Change Canada, Water Survey of Canada. Data are subject to revision. Preserve the source disclaimer and attribution; do not resell the bundled raw data.\n\nSource terms: https://wateroffice.ec.gc.ca/disclaimer_info_e.html\n\nBasemap: Natural Resources Canada, Toporama, under the Open Government Licence – Canada.\n\nThe application code license does not replace the separate source-data terms.\n')
        space(a.output);temporary.replace(a.output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    print(json.dumps({'base_members_reused':copied,'realtime_files':len(names),'bytes':a.output.stat().st_size,'hydat_copied_to_disk':False}))

if __name__=='__main__':main()
