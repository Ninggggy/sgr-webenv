"""Normalize evidenced median bounds in a staging database; do not invent exact values."""
import sqlite3,pathlib,sys,json
R=pathlib.Path(__file__).resolve().parents[1];path=pathlib.Path(sys.argv[1]);assert path.resolve()!=(R/'data/census.sqlite').resolve()
c=sqlite3.connect(path);c.row_factory=sqlite3.Row;report=[]
for row in c.execute("SELECT c.*,t.title,v.label FROM cells c JOIN tables t ON t.year=c.year AND t.product=c.product AND t.id=c.table_id JOIN variables v ON v.year=c.year AND v.product=c.product AND v.id=c.variable WHERE c.moe IS NULL AND upper(t.title) LIKE '%MEDIAN%' AND c.estimate IS NOT NULL").fetchall():
 title=row['title'].upper();note=None;reason=None
 if row['estimate']==2499 and any(s in title for s in ['INCOME','EARNINGS']):note='2,500-';reason='Official Summary median income/earnings lower interval; not an exact estimate.'
 if row['table_id']=='B25092' and row['variable']=='B25092_003E' and row['estimate']==9:
  bins=dict(c.execute("SELECT variable,estimate FROM cells WHERE year=? AND product=? AND geo=? AND variable IN ('B25091_013E','B25091_014E','B25091_023E')",(row['year'],row['product'],row['geo'])))
  if len(bins)==3 and all(v is not None for v in bins.values()) and bins['B25091_014E']*2>bins['B25091_013E']-bins['B25091_023E']:
   note='Less than 10%';reason='Lower median interval corroborated by same-release B25091: more than half of computed no-mortgage owner costs lie below 10%. Raw Summary code remains 9; no exact median inferred.'
  else:note='9 (median bound unresolved)';reason='Raw value 9 with missing MOE differs from documented jam code; exact percentage not certified.'
 if not note and row['ma']=='Not available (Summary File .)':
  note=f"{row['estimate']:g} (median precision unresolved)";reason='Missing median MOE may denote a boundary code; no exact-value interpretation is certified for this cell.'
 if note:
  c.execute('UPDATE cells SET ea=? WHERE year=? AND product=? AND geo=? AND variable=?',(note,row['year'],row['product'],row['geo'],row['variable']));report.append({'year':row['year'],'product':row['product'],'geo':row['geo'],'variable':row['variable'],'raw_estimate':row['estimate'],'annotation':note,'reason':reason})
c.commit();c.close();(R/'validation/repair-20260917/median-normalization.json').write_text(json.dumps(report,indent=2));print('Flagged median cells:',len(report))
