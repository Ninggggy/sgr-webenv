"""General statistical series, verified against captured original graph responses."""
import calendar,datetime,statistics,collections
from decimal import Decimal,ROUND_HALF_UP
from downloads import value_text
UTC=datetime.timezone.utc
def stamp(year,month,day=1):return int(datetime.datetime(year,month,1,tzinfo=UTC).timestamp()*1000)+(day-1)*86400000
def calculate(db,number,parameter,kind,year,start,end,requested):
 groups=collections.defaultdict(list);all_daily=collections.defaultdict(list);precision=8
 for r in db.months(number,parameter,1850 if kind=='monthly' else start,9999 if kind=='monthly' else end):
  precision=r.get('PRECISION_CODE',8)
  if kind=='monthly':
   if r['MONTHLY_MEAN'] is not None:
    # The official monthly statistics use means before monthly display rounding.
    daily=[r[parameter.upper()+str(day)] for day in range(1,calendar.monthrange(r['YEAR'],r['MONTH'])[1]+1)]
    daily=[Decimal(value_text(v,parameter,precision)) for v in daily if v is not None]
    if daily:groups[r['MONTH']].append(sum(daily)/len(daily));all_daily[r['MONTH']].extend(daily)
  else:
   for day in range(1,calendar.monthrange(r['YEAR'],r['MONTH'])[1]+1):
    value=r[parameter.upper()+str(day)]
    if value is not None:groups[(r['MONTH'],day)].append(float(value_text(value,parameter,precision)))
 quantile_available=kind=='monthly' or any(len(v)>=10 for v in groups.values())
 output={key:[] for key in requested}
 if kind!='monthly' and not any(len(v)>=2 for v in groups.values()):return output
 for month in range(1,13):
  for day in ([1] if kind=='monthly' else range(1,calendar.monthrange(year,month)[1]+1)):
   values=sorted(groups.get(month if kind=='monthly' else (month,day),[]));qs=statistics.quantiles(values,n=4,method='exclusive') if len(values)>1 else [values[0]]*3 if values else [None]*3
   computed={'maximum':max(values) if values else None,'minimum':min(values) if values else None,'mean':sum(values)/len(values) if values else None,'median':statistics.median(values) if values else None,'upper_quartile':qs[2],'lower_quartile':qs[0]}
   if kind=='monthly' and all_daily[month]:computed['mean']=sum(all_daily[month])/len(all_daily[month])
   for key in requested:
    quantile=key in ('median','upper_quartile','lower_quartile')
    if quantile and not quantile_available:continue
    v=computed[key] if (kind=='monthly' or len(values)>=2) and (not quantile or kind=='monthly' or len(values)>=10) else None
    if kind=='monthly' and v is not None:
     v=str(v.quantize(Decimal('0.01' if precision==9 else '0.001'),rounding=ROUND_HALF_UP)) if parameter=='Level' else value_text(float(v),parameter,precision)
     v=v.rstrip('0').rstrip('.') if '.' in v else v
     if v.startswith('0.'):v=v[1:]
     elif v.startswith('-0.'):v='-'+v[2:]
    output[key].append([stamp(year,month,day),v])
 return output
