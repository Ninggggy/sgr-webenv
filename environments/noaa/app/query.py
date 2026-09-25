import sqlite3,json,os,calendar
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
DATA=Path(os.environ.get("NOAA_DATA",str(Path(__file__).resolve().parents[1]/"data")))
META=json.loads((DATA/"metadata.json").read_text()); PARAMS=META["parameters"]; MAX=2026*12+7; MIN=1895*12

def rounded(x,d):
 if x is None:return None
 a=x*10**d; sign=-1 if a<0 else 1;a=abs(a);z=(a.numerator*2+a.denominator)//(2*a.denominator)
 return sign*z/10**d if z else 0

@lru_cache(maxsize=4200)
def series(scope,loc,p):
 c=sqlite3.connect(f"file:{DATA}/climate.sqlite?mode=ro",uri=True)
 rows=c.execute("SELECT year,months FROM series WHERE scope=? AND location=? AND parameter=? ORDER BY year",(scope,loc,p)).fetchall();c.close()
 a=[None]*(MAX-MIN+1)
 for y,js in rows:
  for m,v in enumerate(json.loads(js)):
   i=y*12+m-MIN
   if 0<=i<len(a):a[i]=v
 sums=[0];missing=[0]
 for x in a:sums.append(sums[-1]+(x or 0));missing.append(missing[-1]+(x is None))
 return sums,missing

def window(scope,loc,p,y,m,n):
 sums,missing=series(scope,loc,p); end=y*12+m-MIN; beg=end-n
 if beg<0 or end>=len(sums) or missing[end]!=missing[beg]:return None
 return Fraction(sums[end]-sums[beg],100*(1 if p in ("pcp","hdd","cdd") else n))

@lru_cache(maxsize=12000)
def stats(scope,loc,p,m,n):
 vals=[(y,window(scope,loc,p,y,m,n)) for y in range(1895,2027)];vals=[(y,v) for y,v in vals if v is not None]
 ref=[v for y,v in vals if 1901<=y<=2000];mean=sum(ref,Fraction())/len(ref) if ref else None
 return vals,mean

def validate(scope,loc,p,date,ts):
 if scope not in ("divisional","statewide"):raise NotImplementedError("This product is not supported by this offline release.")
 if p not in PARAMS:raise ValueError("Unknown parameter")
 if len(str(date))!=6:raise ValueError("Date must be YYYYMM")
 y,m=divmod(int(date),100);n=m if str(ts)=="ytd" else int(ts)
 if not 1895<=y<=2026 or not 1<=m<=12 or n not in list(range(1,13))+[18,24,36,48,60]:raise ValueError("Invalid year, month or time scale")
 if p in ("pdsi","phdi","pmdi") and n!=1:raise ValueError("This Palmer parameter supports 1-Month only, as on CAG.")
 if loc!=110 and not 1<=loc<=48:raise NotImplementedError("Only the contiguous 48 states are supported.")
 return y,m,n

def rank_stats(vals,v,d):
 # Mapping candidate inferred from independently recorded NOAA queries:
 # float64 scaling + nearest-even rounding, then tie midpoint selects tail.
 # This is not asserted to recover all NOAA mapping ranks; see strict reports.
 rank_value=lambda x:round(float(x)*10**d)/10**d
 target=None if v is None else rank_value(v)
 allv=[rank_value(x) for _,x in vals]
 lo=None if v is None else 1+sum(x<target for x in allv)
 hi=None if v is None else sum(x<=target for x in allv)
 rank=None if v is None else (lo if lo+hi<=len(allv)+1 else hi)
 ties=0 if v is None else hi-lo+1
 return rank,lo,hi,ties

def query(scope,loc,p,date,ts):
 y,m,n=validate(scope,loc,p,date,ts);d=PARAMS[p]["precision"]
 if scope=="divisional":ids=[int(k) for k in META["locationsMeta"] if 1<=int(k)//100<=48 and (loc==110 or int(k)//100==loc)]
 else:ids=list(range(1,49)) if loc==110 else [loc]
 data={}
 for ident in sorted(ids):
  v=window(scope,ident,p,y,m,n); vals,mu=stats(scope,ident,p,m,n)
  displayed=rounded(v,d);rank,lo,hi,ties=rank_stats(vals,v,d)
  sid=ident//100 if scope=="divisional" else ident;state=META["usStates"][str(sid)]
  name=META["locationsMeta"].get(f"{ident:04d}",{}).get("name") if scope=="divisional" else state["name"]
  key=f"{ident:04d}" if scope=="divisional" else str(ident)
  data[key]={"name":name,"stateId":sid,"state":state["name"],"stateAbbr":state["abbr"],"value":displayed,"anomaly":rounded(v-mu,d) if v is not None and mu is not None else None,"mean":rounded(mu,d),"rank":rank,"ties":max(0,ties-1),"rankStart":lo,"rankEnd":hi,"years":len(vals)}
  if scope=="divisional":data[key]["divisionId"]=ident%100
  if p=="pcp":data[key]["pctavg"]=rounded(v/mu*100,0) if mu and v is not None else None
 first=(y*12+m-n); by,bm=divmod(first,12)
 name = META["usStates"].get(str(loc),{}).get("name","Contiguous U.S."); label=PARAMS[p]["title"]
 title=f"{calendar.month_name[bm+1]} {by} - {calendar.month_name[m]} {y} {name} {scope.title()} {label}"
 return {"description":{"title":title,"anomalies":"1901-2000 base period","mean":"1901-2000","release":"20260904","units":"°Df" if p in ("hdd","cdd") else PARAMS[p]["units"]},"data":data}
