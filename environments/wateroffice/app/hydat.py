"""Read-only HYDAT access. No benchmark identifiers or stored answers."""
import calendar, datetime, math, pathlib, sqlite3, json, collections
PARAMETERS={'Flow':('DLY_FLOWS','FLOW'),'Level':('DLY_LEVELS','LEVEL')}

def month_evidence(row,parameter):
    _,prefix=PARAMETERS[parameter]
    year,month=int(row['YEAR']),int(row['MONTH'])
    days=calendar.monthrange(year,month)[1]
    values=[row[f'{prefix}{d}'] for d in range(1,days+1)]
    valid=sum(v is not None for v in values)
    computed='C' if valid==days else 'P' if valid else '-'
    flag=row['FULL_MONTH']
    # HYDAT uses SQLite integer Boolean fields (Access exports may use -1).
    if flag not in (None,0,1,-1):raise ValueError(f'Unknown FULL_MONTH: {flag!r}')
    published='C' if flag in (1,-1) else 'P' if valid else '-'
    return {'year':year,'month':month,'calendar_days':days,'valid_days':valid,
            'full_month':flag,'published':published,'computed':computed,
            'conflict':published!=computed,'no_days':row['NO_DAYS']}

class Hydat:
    def __init__(self,path):self.path=pathlib.Path(path)
    def connect(self):
        db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        db.row_factory=sqlite3.Row
        return db
    def station(self,number):
        with self.connect() as db:
            row=db.execute('SELECT * FROM STATIONS WHERE STATION_NUMBER=?',(number,)).fetchone()
            if row is None:raise KeyError(number)
            return dict(row)
    def months(self,number,parameter,start=1850,end=9999):
        table,_=PARAMETERS[parameter]
        with self.connect() as db:
            return [dict(r) for r in db.execute(f'SELECT * FROM {table} WHERE STATION_NUMBER=? AND YEAR BETWEEN ? AND ? ORDER BY YEAR,MONTH',(number,start,end))]
    def availability(self,number,parameter):
        return [month_evidence(row,parameter) for row in self.months(number,parameter)]
    def daily(self,number,parameter,start,end):
        start=datetime.date.fromisoformat(start);end=datetime.date.fromisoformat(end)
        if end<start:raise ValueError('End date precedes start date')
        _,prefix=PARAMETERS[parameter]
        result=[]
        for row in self.months(number,parameter,start.year,end.year):
            for day in range(1,calendar.monthrange(row['YEAR'],row['MONTH'])[1]+1):
                date=datetime.date(row['YEAR'],row['MONTH'],day)
                if start<=date<=end:
                    result.append({'station':number,'date':date.isoformat(),'parameter':parameter,'value':row[f'{prefix}{day}'],'symbol':row.get(f'{prefix}_SYMBOL{day}')})
        return result
    def search(self,q):
        where=[];args=[]
        typ=q.get('search_type','station_name')
        if typ in ('station_name','station_number'):
            key={'station_name':'STATION_NAME','station_number':'STATION_NUMBER'}[typ]
            term=q.get(typ,'').strip()
            if ',' in term and typ=='station_number':
                ids=term.upper().split(',');where.append('s.STATION_NUMBER IN ('+','.join('?' for _ in ids)+')');args+=ids
            elif term:
                where.append(f'UPPER(s.{key}) LIKE ? ESCAPE "\\"');args.append('%'+term.upper().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%')
        elif typ=='province':
            if q.get('province','all')!='all':where.append('s.PROV_TERR_STATE_LOC=?');args.append(q['province'])
        elif typ=='basin':where.append('s.STATION_NUMBER LIKE ?');args.append(q.get('basin','')+'%')
        elif typ=='coordinate':
            for side,column,op,sign in [('north','LATITUDE','<=',1),('south','LATITUDE','>=',1),('east','LONGITUDE','<=',-1),('west','LONGITUDE','>=',-1)]:
                val=sum(float(q.get(side+'_'+unit) or 0)/scale for unit,scale in [('degrees',1),('minutes',60),('seconds',3600)])*sign
                if not math.isfinite(val):raise ValueError('Invalid coordinate')
                where.append(f's.{column}{op}?');args.append(val)
        else:raise ValueError('Invalid search type')
        for name,column in [('gross_drainage','DRAINAGE_AREA_GROSS'),('effective_drainage','DRAINAGE_AREA_EFFECT')]:
            if q.get(name+'_area'):
                op=q.get(name+'_operator','>')
                if op not in ('>','<','>=','<=','='):raise ValueError('Invalid area operator')
                val=float(q[name+'_area'])
                if not math.isfinite(val) or val<0:raise ValueError('Invalid area')
                where.append(f's.{column}{op}?');args.append(val)
        if q.get('station_status','all')!='all':
            if q['station_status'] not in ('A','D'):raise ValueError('Invalid station status')
            where.append('s.HYD_STATUS=?');args.append(q['station_status'])
        if q.get('operating_agency','all')!='all':
            where.append('s.OPERATOR_ID IN (SELECT AGENCY_ID FROM AGENCY_LIST WHERE AGENCY_EN=?)');args.append(q['operating_agency'])
        for name,column in [('real_time','REAL_TIME'),('rhbn','RHBN')]:
            value=q.get(name,'---')
            if value not in ('---','Y','N'):raise ValueError('Invalid '+name)
            if value!='---':where.append(f'COALESCE(s.{column},0)=?');args.append(1 if value=='Y' else 0)
        value=q.get('sediment','---')
        if value not in ('---','Y','N'):raise ValueError('Invalid sediment filter')
        if value!='---':
            where.append(('' if value=='Y' else 'NOT ') + "EXISTS(SELECT 1 FROM STN_DATA_RANGE r WHERE r.STATION_NUMBER=s.STATION_NUMBER AND r.DATA_TYPE IN ('I','S','T'))")
        if q.get('contributed','---')!='---':raise ValueError('Contributed-data filter is pending source-equivalence validation')
        regulation=q.get('regulation','all')
        if regulation not in ('all','R','N'):raise ValueError('Invalid regulation')
        if regulation!='all':
            where.append('EXISTS(SELECT 1 FROM STN_REGULATION r WHERE r.STATION_NUMBER=s.STATION_NUMBER AND r.REGULATED=?)')
            args.append(1 if regulation=='R' else 0)
        # Preserve the official nationwide search snapshot, including duplicate rows.
        # Program history is not equivalent to this published predicate.
        operation=q.get('operation_schedule','all')
        if operation not in ('all','C','S','M'):raise ValueError('Invalid operation schedule')
        multiplicity=None
        if operation!='all':
            if q.get('parameter_type','all')!='all':raise ValueError('The official operation-schedule search returned server errors when combined with a specific parameter during capture; this combination is unavailable in the offline archive')
            catalog=json.loads((self.path.parent/'operation-membership.json').read_text())['operations'][operation]
            multiplicity=collections.Counter(catalog['stations'])
        parameter=q.get('parameter_type','all')
        if parameter not in ('all','flows','levels'):raise ValueError('Invalid parameter')
        start=int(q.get('start_year') or 1850);end=int(q.get('end_year') or 9999)
        if end<start:raise ValueError('Invalid year range')
        tables=['DLY_FLOWS','DLY_LEVELS'] if parameter=='all' else ['DLY_FLOWS' if parameter=='flows' else 'DLY_LEVELS']
        clauses=[]
        for table in tables:
            clauses.append(f'EXISTS(SELECT 1 FROM {table} d WHERE d.STATION_NUMBER=s.STATION_NUMBER GROUP BY d.STATION_NUMBER HAVING MIN(d.YEAR)<=? AND MAX(d.YEAR)>=?)');args.extend((end,start))
        where.append('('+' OR '.join(clauses)+')')
        minimum=int(q['minimum_years']) if q.get('minimum_years') else None
        if minimum is not None:
            if minimum<1 or minimum>end-start:raise ValueError('Minimum number of years must be positive and cannot exceed the difference between the selected end and start years')
            union=' UNION '.join(f'SELECT YEAR FROM {table} WHERE STATION_NUMBER=s.STATION_NUMBER AND YEAR BETWEEN ? AND ?' for table in tables)
            where.append('(SELECT COUNT(*) FROM ('+union+'))>=?')
            for table in tables:args.extend((start,end))
            args.append(minimum)
        latest=q.get('latest_year','')
        if latest not in ('','Y'):raise ValueError('Invalid latest-year flag')
        if latest=='Y':
            where.append('('+' OR '.join(f'EXISTS(SELECT 1 FROM {table} d WHERE d.STATION_NUMBER=s.STATION_NUMBER AND d.YEAR=2026)' for table in tables)+')')

        with self.connect() as db:
            rows=[dict(r) for r in db.execute('SELECT s.* FROM STATIONS s WHERE '+' AND '.join(where)+' ORDER BY s.STATION_NAME,s.STATION_NUMBER',args)]
            return rows if multiplicity is None else [r for r in rows for _ in range(multiplicity[r['STATION_NUMBER']])]
