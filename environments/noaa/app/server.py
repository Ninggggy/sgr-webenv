from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import json,re,copy,mimetypes,csv,io,html,urllib.parse
import query
ROOT=Path(__file__).resolve().parent; STATIC=ROOT/"static";BASE="/access/monitoring/climate-at-a-glance"
TEMPLATES={}
for s in ("divisional","statewide"):
 for v in ("mapping","time-series"):
  TEMPLATES[s,v]=((ROOT/f"templates/{s}-{v}.html").read_text(),json.loads((ROOT/f"templates/{s}-{v}.json").read_text()))

def validate_series(scope,loc,beg,end):
 if scope=="divisional" and f"{int(loc):04d}" not in query.META["locationsMeta"]:raise ValueError("Unknown climate division")
 if not 1895<=int(beg)<=int(end)<=2026:raise ValueError("Time series years must be ordered within 1895–2026")

def page(scope,view,args,qs):
 text,c=copy.deepcopy(TEMPLATES[scope,view]);const=c["constants"];v=c["variables"]
 const["http"]="";const["cloud"]="/unavailable";const["dataDirs"]={};const["scopes"]={"national":"Home","statewide":"Statewide","divisional":"Divisional"};const["sections"]={"mapping":"Mapping","time-series":"Time Series"}
 const["usStates"]={k:x for k,x in const["usStates"].items() if 1<=int(k)<=48}
 for name in ["usCities","usCounties","usRegions"]:const[name]={}
 const["usClimateDivisions"]={k:x for k,x in const["usClimateDivisions"].items() if 1<=int(k)//100<=48}
 const["locations"]={k:x for k,x in const["locations"].items() if (1<=int(k)<=48 or int(k)==110) if view=="mapping" or scope=="statewide"} if view=="mapping" or scope=="statewide" else {k:x for k,x in const["locations"].items() if 1<=int(k)//100<=48}
 if view=="mapping":
  if args:
   if len(args)!=5:raise ValueError("Invalid mapping URL")
   loc,p,date,ts,mode=args;query.validate(scope,int(loc),p,date,ts)
   if mode not in ("value","anomaly","rank","mean","pctavg"):raise ValueError("Invalid result mode")
   v.update(locationId=int(loc),parameter=p,date=int(date),year=int(date)//100,month=int(date)%100,timescale=ts,returnType=mode)
 else:
  if args:
   if len(args)==5 and re.fullmatch(r"[0-9]{4}-[0-9]{4}",args[-1]):args=args[:4]+args[-1].split("-")
   if len(args) not in (4,6):raise ValueError("Invalid time-series URL")
   loc,p,ts,mo=args[:4];m=int(mo);y=2026;sid=int(loc)//100 if scope=="divisional" else int(loc)
   query.validate(scope,sid,p,f"{y}{max(m,1):02d}",ts)
   if not 0<=m<=12:raise ValueError("Invalid month")
   v.update(locationId=f"{int(loc):04d}" if scope=="divisional" else int(loc),state=sid,parameter=p,timescale=ts,month=m)
   if len(args)==6:v.update(begyear=int(args[4]),endyear=int(args[5]))
  if v["begyear"]>v["endyear"]:raise ValueError("Start year must not exceed end year")
  validate_series(scope,v["locationId"],v["begyear"],v["endyear"])
  if "base_prd" in qs:v["basePeriod"]=qs["base_prd"][0].lower() in ("true","1")
  for source,target in [("begbaseyear","begBaseYear"),("endbaseyear","endBaseYear"),("begtrendyear","begtrendyear"),("endtrendyear","endtrendyear")]:
   if source in qs:v[target]=int(qs[source][0])
  if "filter" in qs:
   if qs["filter"][0] not in const["filters"] and qs["filter"][0]!="none":raise ValueError("Unknown time-series filter")
   v["filter"]=qs["filter"][0]
  if "trend_base" in qs:
   v["trend_base"]=int(qs["trend_base"][0])
   if v["trend_base"] not in (10,100):raise ValueError("Invalid trend unit")
  validate_series(scope,v["locationId"],v["begBaseYear"],v["endBaseYear"])
  validate_series(scope,v["locationId"],v["begtrendyear"],v["endtrendyear"])
  for k in ["basePeriod","plotDepartures","trend"]:
   if k in qs:v[k]=qs[k][0].lower() in ("true","1")
 return text.replace("__CAG_CONFIG__",json.dumps(c))

class Handler(BaseHTTPRequestHandler):
 def send(self,b,code=200,kind="text/html; charset=utf-8",download=None):
  if isinstance(b,str):b=b.encode()
  self.send_response(code);self.send_header("Content-Type",kind);self.send_header("Content-Length",str(len(b)));self.send_header("X-Content-Type-Options","nosniff")
  self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'self'")
  if download:self.send_header("Content-Disposition",f"attachment; filename=\"{download}\"")
  self.end_headers();self.wfile.write(b)
 def do_GET(self):
  try:self.route()
  except NotImplementedError as e:self.error(501,str(e),"Unsupported product")
  except (ValueError,KeyError) as e:self.error(400,str(e),"Invalid query")
  except (BrokenPipeError,ConnectionResetError):pass
  except Exception as e:
   import traceback;traceback.print_exc();self.error(500,"The query could not be completed.","Service error")
 def error(self,status,msg,title):
  if self.path.split("?")[0].endswith(".json"):self.send(json.dumps({"error":title,"message":msg}),status,"application/json");return
  self.send(f"<!doctype html><title>{title}</title><h1>{title}</h1><p>{html.escape(msg)}</p><a href=\"{BASE}/divisional/mapping\">Return to divisional mapping</a>",status)
 def route(self):
  u=urllib.parse.urlsplit(self.path);path=urllib.parse.unquote(u.path);qs=urllib.parse.parse_qs(u.query)
  if path=="/health":self.send(json.dumps({"status":"ok","release":"20260904","implementation":"2-review-repair-20260913"}),kind="application/json");return
  if path.endswith("/data-info"):
   self.send((STATIC/"home.html").read_text());return
  if path in ("/","/help",BASE,BASE+"/national",BASE+"/national/"):
   self.send((STATIC/"home.html").read_text());return
  if path.endswith("/cache/"):self.send("{}",kind="application/json");return
  m=re.fullmatch(BASE+r"/national/mapping/110-(\w+)-(\d{6})-(\w+)/data.json",path)
  if m:
   p,date,ts=m.groups();y,mon,n=query.validate("divisional",110,p,date,ts);v=query.window("national",110,p,y,mon,n);vs,mu=query.stats("national",110,p,mon,n);d=query.PARAMS[p]["precision"]
   obj={"value":query.rounded(v,d),"mean":query.rounded(mu,d),"anomaly":query.rounded(v-mu,d) if v is not None else None,"rank":None if v is None else query.rank_stats(vs,v,d)[0]+max(0,query.rank_stats(vs,v,d)[3]-1)/10000}
   self.send(json.dumps({k:{"110":val} for k,val in obj.items()}),kind="application/json");return
  m=re.fullmatch(BASE+r"/(divisional|statewide)/mapping/(\d+)-(\w+)-(\d{6})-(\w+)/data\.(json|csv|xml)",path)
  if m:
   scope,loc,p,date,ts,fmt=m.groups();obj=query.query(scope,int(loc),p,date,ts)
   if fmt=="json" and qs.get("raw")==["1"]:
    y,mon,n=query.validate(scope,int(loc),p,date,ts)
    for ident,row in obj["data"].items():
     value=query.window(scope,int(ident),p,y,mon,n);_,mean=query.stats(scope,int(ident),p,mon,n)
     row["value"]=query.rounded(value,0 if p in ("hdd","cdd") else 4)
     row["anomaly"]=query.rounded(value-mean,0 if p in ("hdd","cdd") else 4) if value is not None and mean is not None else None
    obj={key:{id:(row.get(key)+row.get("ties",0)/10000 if key=="rank" and row.get(key) is not None else row.get(key)) for id,row in obj["data"].items()} for key in ["value","anomaly","rank","mean","pctavg"]}
   self.export(obj,fmt);return
  m=re.fullmatch(BASE+r"/(divisional|statewide)/time-series/(\d+)/(\w+)/(\w+)/(\d+)(?:/(\d+)[/-](\d+))?/data\.(json|csv|xml)",path)
  if m:
   scope,loc,p,ts,mo,beg,end,fmt=m.groups();loc=int(loc);mo=int(mo);query.validate(scope,loc//100 if scope=="divisional" else loc,p,"2026"+f"{max(mo,1):02d}",ts)
   if not 0<=mo<=12:raise ValueError("Invalid month")
   validate_series(scope,loc,int(beg or 1895),int(end or 2026))
   vals={}
   for y in range(int(beg or 1895),int(end or 2026)+1):
    for mon in ([mo] if mo else range(1,13)):
     value=query.window(scope,loc,p,y,mon,mon if ts=="ytd" else int(ts))
     if value is not None:vals[str(y) if mo else f"{y}{mon:02d}"]=query.rounded(value,query.PARAMS[p]["precision"])
   self.export(vals if qs.get("raw")==["1"] else {"description":{"release":"20260904"},"data":vals},fmt);return
  m=re.fullmatch(BASE+r"/(divisional|statewide)(?:/(mapping|time-series))?(?:/(.*?))?/?",path)
  if m:
   scope,view,args=m.groups();self.send(page(scope,view or "mapping",args.split("/") if args else [],qs));return
  if path.startswith(BASE) and not path.startswith(BASE+"/api/"):raise NotImplementedError("This offline release supports statewide and divisional Mapping and Time Series. County, city, global, regional and ranking products are not available.")
  f=(STATIC/path.lstrip("/")).resolve()
  if STATIC.resolve() not in f.parents or not f.is_file():self.error(404,"Resource not available locally","Not found");return
  self.send(f.read_bytes(),kind=mimetypes.guess_type(str(f))[0] or "application/octet-stream")
 def export(self,obj,fmt):
  if fmt=="json":self.send(json.dumps(obj,allow_nan=False),kind="application/json");return
  data=obj.get("data",obj); keys=list(next(iter(data.values())).keys()) if data and isinstance(next(iter(data.values())),dict) else ["value"]
  if fmt=="csv":
   out=io.StringIO();w=csv.writer(out);w.writerow(["Location / Year"]+keys)
   for k,v in data.items():w.writerow([k]+[v.get(x) for x in keys] if isinstance(v,dict) else [k,v])
   self.send(out.getvalue(),kind="text/csv; charset=utf-8",download="data.csv")
  else:self.send("<?xml version=\"1.0\"?><data>"+"".join(f"<record id=\"{html.escape(k)}\">{html.escape(json.dumps(v))}</record>" for k,v in data.items())+"</data>",kind="application/xml",download="data.xml")

if __name__=="__main__":ThreadingHTTPServer(("0.0.0.0",8080),Handler).serve_forever()
