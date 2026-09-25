"""Station metadata from the published HYDAT release, without task-specific rules."""
import collections
PROVINCES={'AB':'Alberta','BC':'British Columbia','MB':'Manitoba','NB':'New Brunswick','NL':'Newfoundland and Labrador','NS':'Nova Scotia','NT':'Northwest Territories','NU':'Nunavut','ON':'Ontario','PE':'Prince Edward Island','QC':'Quebec','SK':'Saskatchewan','YT':'Yukon'}
def station_metadata(db,station):
 n=station['STATION_NUMBER']
 with db.connect() as c:
  def rows(t):return [dict(r) for r in c.execute('SELECT * FROM '+t+' WHERE STATION_NUMBER=?',(n,))]
  ranges=rows('STN_DATA_RANGE');collection=rows('STN_DATA_COLLECTION');regulations=rows('STN_REGULATION');schedules=rows('STN_OPERATION_SCHEDULE')
  def lookup(table,column,key,value):
   r=c.execute('SELECT '+column+' FROM '+table+' WHERE '+key+'=?',(value,)).fetchone();return r[0] if r else 'N/A'
  office=lookup('REGIONAL_OFFICE_LIST','REGIONAL_OFFICE_NAME_EN','REGIONAL_OFFICE_ID',station['REGIONAL_OFFICE_ID'])
  datum=lookup('DATUM_LIST','DATUM_EN','DATUM_ID',station['DATUM_ID'])
  contributor=lookup('AGENCY_LIST','AGENCY_EN','AGENCY_ID',station['CONTRIBUTOR_ID'])
  types=dict(c.execute('SELECT DATA_TYPE,DATA_TYPE_EN FROM DATA_TYPES'))
  operations=dict(c.execute('SELECT OPERATION_CODE,OPERATION_EN FROM OPERATION_CODES'))
  measurements=dict(c.execute('SELECT MEASUREMENT_CODE,MEASUREMENT_EN FROM MEASUREMENT_CODES'))
 hydro=[r for r in ranges if r['DATA_TYPE'] in ('H','Q')]
 latest=max((r['YEAR_TO'] for r in hydro),default=None)
 relevant=[r for r in collection if r['DATA_TYPE'] in ('H','Q')]
 recent=max(relevant,key=lambda r:r['YEAR_TO'] or 0,default={})
 schedule=max((r for r in schedules if r['DATA_TYPE'] in ('H','Q')),key=lambda r:r['YEAR'],default={})
 regulated=[r for r in regulations if r['REGULATED']]
 vals={'active':{'A':'Active','D':'Discontinued'}.get(station['HYD_STATUS'],'N/A'),
 'province':PROVINCES.get(station['PROV_TERR_STATE_LOC'],station['PROV_TERR_STATE_LOC']),
 'latitude':station['LATITUDE'],'longitude':station['LONGITUDE'],
 'gross-drainage':str(station['DRAINAGE_AREA_GROSS'])+' km²' if station['DRAINAGE_AREA_GROSS'] is not None else 'N/A',
 'effective-drainage':str(station['DRAINAGE_AREA_EFFECT'])+' km²' if station['DRAINAGE_AREA_EFFECT'] is not None else 'N/A',
 'record-length':str(max((r['RECORD_LENGTH'] for r in hydro),default=0))+' Years',
 'record-period':f"{min((r['YEAR_FROM'] for r in hydro),default='N/A')}-{latest or 'N/A'}",
 'regulation-type':'Regulated' if regulated else 'Natural',
 'regulation-length':', '.join(f"{r['YEAR_FROM'] or 'Unknown'} - {r['YEAR_TO'] or 'present'}" for r in regulated) or 'N/A',
 'realtime-data':'Yes' if station['REAL_TIME'] else 'No',
 'sediment-data':'Yes' if any(r['DATA_TYPE'] not in ('H','Q') for r in ranges) else 'No',
 'water-body':'Not provided in this HYDAT release',
 'rhbn':'Yes' if station['RHBN'] else 'No','regional-office':office,
 'operation-schedule':operations.get(recent.get('OPERATION_CODE'),'N/A'),
 'contributed-by':contributor,'operation-period':f"{schedule.get('MONTH_FROM') or 'N/A'} - {schedule.get('MONTH_TO') or 'N/A'}",
 'published-data':datum,'datum-data':datum}
 grouped=collections.defaultdict(list)
 for r in relevant:grouped[(r['YEAR_FROM'],r['YEAR_TO'],r['OPERATION_CODE'],r['MEASUREMENT_CODE'])].append(r['DATA_TYPE'])
 history=[]
 for (start,end,op,measurement),params in sorted(grouped.items(),key=lambda kv:(kv[0][0] or 0,kv[0][1] or 9999)):
  history.append([f'{start} - {end}',' & '.join('Flow' if p=='Q' else 'Level' for p in sorted(params,reverse=True)),operations.get(op,'N/A'),measurements.get(measurement,'N/A')])
 return vals,history
