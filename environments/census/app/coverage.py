"""One geography/coverage definition for search, tables, maps and exports."""
import re

def geographies(c,year,selection):
 result={}
 for token in dict.fromkeys(selection.split(',')):
  if not token:continue
  if not re.fullmatch(r'\d{2}(?:\d{3}|\*)?',token):raise ValueError('Invalid geography')
  rows=c.execute('SELECT * FROM geographies WHERE year=? AND '+("state=? AND level='county'" if token.endswith('*') else 'id=?')+' ORDER BY name',(year,token.rstrip('*'))).fetchall()
  if not rows:raise ValueError('Geography not in the archived historical geography list: '+token)
  for row in rows:result[row['id']]=dict(row)
 return list(result.values())

def publication_rule(c,year,product,table):
 if not c.execute("SELECT 1 FROM sqlite_master WHERE name='table_publication'").fetchone():return None
 row=c.execute('SELECT * FROM table_publication WHERE year=? AND product=? AND table_id=?',(year,product,table)).fetchone()
 return dict(row) if row else None

def excluded(rule,geo):
 if not rule:return False
 restriction=rule['restriction'].lower();universe=rule.get('title','').lower()
 if 'puerto rico' in universe and not geo.startswith('72'):return True
 if ('pr only' in restriction) and not geo.startswith('72'):return True
 if ('us only' in restriction or 'excluding pr' in restriction) and geo.startswith('72'):return True
 if restriction=='nation only':return True
 if len(geo)==5 and (restriction in ['nation and state only','nation and states only','nation and states only (excluding pr)'] or (restriction.startswith('nation, states,') and 'count' not in restriction)):return True
 return False

def index(c,year,product):
 # Materialized counts are ordinary import metadata, verified against cells before deployment.
 if c.execute("SELECT 1 FROM sqlite_master WHERE name='table_coverage'").fetchone():
  rows=c.execute('SELECT table_id,geo,variables FROM table_coverage WHERE year=? AND product=?',(year,product))
 else:rows=c.execute('SELECT table_id,geo,count(*) variables FROM cells WHERE year=? AND product=? GROUP BY table_id,geo',(year,product))
 counts={}
 for r in rows:counts.setdefault(r['table_id'],{})[r['geo']]=r['variables']
 expected=dict(c.execute('SELECT table_id,count(*) FROM variables WHERE year=? AND product=? GROUP BY table_id',(year,product)))
 out={}
 for t,gs in counts.items():
  rule=publication_rule(c,year,product,t);out[t]={g for g,n in gs.items() if n==expected.get(t) and n>0 and not excluded(rule,g)}
 return out

def describe(c,year,product,table,selected,archived):
 rule=publication_rule(c,year,product,table);ids={g['id'] for g in selected};have=ids&archived
 status=('full' if have==ids else 'partial' if have else 'none') if ids else 'unselected'
 scope=[]
 for state in sorted({g[:2] for g in archived}):
  row=c.execute('SELECT name FROM geographies WHERE year=? AND id=?',(year,state)).fetchone()
  scope.append({'state':state,'name':row[0] if row else state,'state_row':state in archived,'counties':sum(g.startswith(state) and len(g)==5 for g in archived)})
 absent=[];unknown=[];published=[];source_empty=[]
 has=c.execute("SELECT 1 FROM sqlite_master WHERE name='publication_scopes'").fetchone()
 for g in sorted(ids-have):
  if excluded(rule,g):absent.append(g);continue
  raw=c.execute('SELECT count(*),sum(estimate IS NOT NULL OR moe IS NOT NULL OR ea IS NOT NULL OR ma IS NOT NULL) FROM cells WHERE year=? AND product=? AND table_id=? AND geo=?',(year,product,table,g)).fetchone()
  if raw[0]>0 and not raw[1]:source_empty.append(g);continue
  if has and c.execute('SELECT 1 FROM publication_scopes WHERE year=? AND product=? AND state=?',(year,product,g[:2])).fetchone():
   if c.execute('SELECT 1 FROM published_geographies WHERE year=? AND product=? AND geo=?',(year,product,g)).fetchone():published.append(g)
   else:absent.append(g)
  else:unknown.append(g)
 if ids:
  message={'full':f'All {len(ids)} selected geographies archived.','partial':f'Partial archive: {len(have)} of {len(ids)} selected geographies archived.','none':f'No numerical data available for the {len(ids)} selected geographies.'}[status]
  if absent:message+=f' {len(absent)} excluded by the official product geography list or table restrictions.'
  if source_empty:message+=f' {len(source_empty)} have archived source rows containing no published values (blank or suppressed); these source files are present.'
  if unknown or published:message+=f' {len(unknown)+len(published)} locally unarchived; this does not mean Census did not publish them.'
 else:
  labels=[f"{s['name']}: "+('state + ' if s['state_row'] else '')+f"{s['counties']} counties" for s in scope]
  message=('Archive scope (no geography selected): '+'; '.join(labels)+'. Select geographies to view data.') if labels else 'No queryable numerical values in this archive for this table/product/year. Select geographies to distinguish local archive gaps, blank source rows and official publication restrictions.'
 return {'publication_evidence':rule,'status':status,'selected':len(ids),'archived':len(have),'missing_ids':sorted(ids-have),'source_empty_ids':source_empty,'not_published_ids':absent,'publication_unknown_ids':unknown,'locally_missing_ids':published,'scope':scope,'message':message}
