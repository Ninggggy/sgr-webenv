import sqlite3,json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/"data";d.mkdir(exist_ok=True)
con=sqlite3.connect(d/"climate.sqlite");con.execute("CREATE TABLE IF NOT EXISTS series(scope TEXT,location INTEGER,parameter TEXT,year INTEGER,months TEXT,PRIMARY KEY(scope,location,parameter,year))")
params={"tavg":"tmpc","tmax":"tmax","tmin":"tmin","pcp":"pcpn","hdd":"hddc","cdd":"cddc","zndx":"zndx","pdsi":"pdsi","phdi":"phdi","pmdi":"pmdi"};coverage=[]
for scope,suffix in [("divisional","dv"),("statewide","st")]:
 for p,code in params.items():
  f=r/"sources/release-20260904"/f"climdiv-{code}{suffix}-v1.0.0-20260904";rows=[];valid=0
  for l in f.read_text().splitlines():
   loc=int(l[:4]); year=int(l[6:10]);state=loc//100 if scope=="divisional" else int(l[:3])
   if not (1<=state<=48 or (scope=="statewide" and state==110)):continue
   if scope=="statewide":loc=state
   a=[None if float(v)<=-99 else int(round(float(v)*100)) for v in l[10:].split()];assert len(a)==12
   valid+=sum(v is not None for v in a);rows.append((scope,loc,p,year,json.dumps(a,separators=(",",":"))))
  con.execute("DELETE FROM series WHERE scope=? AND parameter=?",(scope,p))
  con.executemany("INSERT OR REPLACE INTO series VALUES (?,?,?,?,?)",rows)
  if scope=="statewide":con.executemany("INSERT OR REPLACE INTO series VALUES (?,?,?,?,?)",[("national",loc,p,y,a) for _,loc,p,y,a in rows if loc==110])
  con.commit();coverage.append({"scope":scope,"parameter":p,"locations":len(set(x[1] for x in rows if x[1]!=110)),"years":[min(x[3] for x in rows),max(x[3] for x in rows)],"valid_months":valid,"file":f.name});print(coverage[-1],flush=True)
(d/"coverage.json").write_text(json.dumps(coverage,indent=2));con.close()
c=json.load(open(r/"sources/cag-config.json"));(d/"metadata.json").write_text(json.dumps({k:c["constants"][k] for k in ["usStates","locationsMeta","parameters"]}))
