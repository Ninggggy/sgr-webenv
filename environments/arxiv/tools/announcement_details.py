"""Extract real dated announcement events from official catchup HTML.
Never infer an event date, type, or revision number from submission time.
"""
import datetime as dt,re
from version_details import Page,Node

def parse(body,context,day,allow_partial=False):
 nodes=list(Page(body).root.walk());heading=next((n.text() for n in nodes if n.tag=='h1'),'')
 expected=dt.date.fromisoformat(day).strftime('%a, %d %b %Y')
 if expected not in heading:raise ValueError('Catchup date does not match requested date')
 alltext=' '.join(Page(body).root.text().split())
 total=re.search(r'Total of (\d+) entries for',alltext)
 if not total:raise ValueError('Missing announcement total')
 output=[];section_totals={}
 for dl in (n for n in nodes if n.tag=='dl'):
  headings=[n.text().strip() for n in dl.walk() if n.tag=='h3']
  if len(headings)!=1:raise ValueError('Missing announcement section')
  h=headings[0];m=re.search(r'\((?:continued, )?showing (?:(?:first|last) )?(\d+) of (\d+) entries\)',h)
  if not m or (not allow_partial and m[1]!=m[2]):raise ValueError('Partial announcement section')
  kind=next((v for k,v in [('New submissions','new'),('Cross submissions','cross'),('Replacement submissions','replace')] if h.startswith(k)),None)
  if not kind:raise ValueError('Unknown announcement section')
  section_totals[kind]=int(m[2])
  section=[]
  for node in dl.children:
   if not isinstance(node,Node) or node.tag!='dt':continue
   links=[n.attrs.get('href','') for n in node.walk() if n.tag=='a']
   ids=[x[5:] for x in links if x.startswith('/abs/')]
   if len(ids)!=1:raise ValueError('Unexpected article identifier')
   ident=ids[0];version=None
   for link in links:
    match=re.search(r'/html/'+re.escape(ident)+r'v(\d+)(?:$|[?#])',link)
    if match:version=int(match[1])
   # A missing version is unknown, including cross-list events. No v1 guess.
   section.append({'paper_id':ident,'version':version,'category':context,'announced_at':day,'event_type':kind})
  if len(section)!=int(m[1]):raise ValueError('Section count mismatch')
  output.extend(section)
 if not allow_partial and len(output)!=int(total[1]):raise ValueError('Page total mismatch')
 if len({(r['paper_id'],r['event_type']) for r in output})!=len(output):raise ValueError('Duplicate event')
 return {'events':output,'total':int(total[1]),'section_totals':section_totals} if allow_partial else output
