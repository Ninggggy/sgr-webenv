import sys,sqlite3,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from query import search,normalize
D=R/'data';db=sqlite3.connect('file:'+str(D/'cellosaurus.sqlite')+'?mode=ro',uri=True);out=[]
for case in json.loads((R/'tests/search-expected.json').read_text()):
 t=time.time()
 try:
  rows=search(db,case['query']);ids=[r[0] for r in rows];expected=case['accessions'];expected_ids=set(expected);names={r[0]:normalize(r[1]) for r in rows}
  ordered_comparable=ids if case['complete'] else [x for x in ids if x in expected_ids]
  tie_equal=len(ordered_comparable)==len(expected) and all(names.get(x)==names.get(y) for x,y in zip(ordered_comparable,expected))
  out.append({'query':case['query'],'local_count':len(ids),'official_count':case['total'],'official_complete':case['complete'],'count_pass':len(ids)==case['total'],'set_pass':set(ids)==set(expected) if case['complete'] else None,'order_pass':ids[:len(expected)]==expected,'order_except_casefold_ties':tie_equal,'official_displayed_count':len(expected),'missing':sorted(set(expected)-set(ids)),'extra':sorted(set(ids)-set(expected)) if case['complete'] else [],'seconds':time.time()-t})
 except Exception as e:out.append({'query':case['query'],'error':str(e),'pass':False})
(R/'validation/search-checks.json').write_text(json.dumps(out,indent=2))
for c in out:print({k:v for k,v in c.items() if k not in ['missing','extra']},flush=True)

assert all(c.get("count_pass") and c.get("set_pass") is not False and c.get("order_except_casefold_ties") for c in out), "Search regression failed"
