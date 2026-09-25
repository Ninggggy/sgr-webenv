"""Crawl the public index's own Next links, retaining exact river hierarchy/link targets."""
import pathlib,subprocess,re,json,urllib.parse,time
from html_tables import Page
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/'author/reference-pages';out.mkdir(exist_ok=True);url='https://wateroffice.ec.gc.ca/station_metadata/reference_index_e.html';records=[];seen=set()
for i in range(150):
 if url in seen:raise RuntimeError('Reference pagination loop')
 seen.add(url);p=out/f'{i:03d}.html'
 if not p.exists():
  for attempt in range(3):
   r=subprocess.run(['curl','-fLsS','--compressed','--max-time','45',url,'-o',str(p)],capture_output=True)
   if r.returncode==0 and '</html>' in p.read_text(errors='replace'):break
  else:raise RuntimeError(r.stderr.decode())
 s=p.read_text();table=re.search(r'<table\b.*?</table>',s,re.S)[0];parsed=Page();parsed.feed(s)
 following=re.search(r'<a href="([^"]+)" rel="next"',s)
 previous=re.search(r'<a href="([^"]+)" rel="prev"',s)
 rows=re.findall(r'<tr\b[^>]*>.*?</tr>',re.search(r'<tbody\b[^>]*>.*?</tbody>',table,re.S)[0],re.S)
 records.append({'url':url,'rows':rows,'table':table,'next':following[1] if following else None,'previous':previous[1] if previous else None})
 (out/'progress.json').write_text(json.dumps({'pages':len(records),'last':url}));print(i,len(rows),url,flush=True)
 if not following:break
 url=urllib.parse.urljoin(url,following[1].replace('&amp;','&'))
else:raise RuntimeError('Pagination did not terminate within limit')
flat=[row for p in records for row in p['rows']]
ids=set(re.findall(r'\b\d{2}[A-Z]{2}\d{3}\b',''.join(flat)))
(ROOT/'data/reference-pages.json').write_text(json.dumps({'source':'Official Station Reference Index page chain','captured':'2026-09-25','pages':records,'unique_stations':len(ids)},ensure_ascii=False,separators=(',',':')))
print('COMPLETE',len(records),len(flat),len(ids))
