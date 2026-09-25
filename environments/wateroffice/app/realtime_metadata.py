"""Dated official report metadata; no inference from the older historical release."""
import functools,json,re,html
from decimal import Decimal,InvalidOperation
from html.parser import HTMLParser
@functools.lru_cache(maxsize=2)
def catalog(data):
 folder=data/'realtime-metadata'
 if not (folder/'manifest.json').exists():raise OSError('The national real-time metadata archive is incomplete')
 return {p.stem:json.loads(p.read_text()) for p in folder.glob('*.json') if p.name!='manifest.json'}
class Inline(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='abbr':self.parts.append('<abbr title="'+html.escape(attrs.get('title',''),quote=True)+'">')
  elif tag=='sup':self.parts.append('<sup>')
  elif tag=='a' and attrs.get('href','').startswith('/report/datum_e.html?'):self.parts.append('<a href="'+html.escape(attrs['href'],quote=True)+'">')
 def handle_endtag(self,tag):
  if tag in ('abbr','sup','a'):self.parts.append('</'+tag+'>')
 def handle_data(self,s):self.parts.append(html.escape(s))
def render_field(source):
 p=Inline();p.feed(source);return ''.join(p.parts)
def area_filter(data,rows,q):
 import operator
 predicates={'<':operator.lt,'<=':operator.le,'>':operator.gt,'>=':operator.ge,'=':operator.eq}
 for key,field in [('gross_drainage','gross-drainage'),('effective_drainage','effective-drainage')]:
  raw=q.get(key+'_area','')
  if raw=='':continue
  try:threshold=Decimal(raw)
  except InvalidOperation:raise ValueError('Invalid drainage area')
  if not threshold.is_finite() or not 0<=threshold<=1800000:raise ValueError('Drainage area outside the published input range')
  op=q.get(key+'_operator','>')
  if op not in predicates:raise ValueError('Invalid drainage-area comparison')
  metadata=catalog(data);selected=[]
  for row in rows:
   source=metadata[row['number']]['text'][field];match=re.match(r'^([\d,]+(?:\.\d+)?)\s',source)
   if match and predicates[op](Decimal(match[1].replace(',','')),threshold):selected.append(row)
  rows=selected
 return rows
def coordinate_filter(data,rows,q):
 bounds={}
 for side in ('north','south','east','west'):
  try:deg=int(q[side+'_degrees']);minute=int(q.get(side+'_minutes') or '0');second=int(q.get(side+'_seconds') or '0')
  except (KeyError,ValueError):raise ValueError('Enter valid bounding coordinates')
  lo,hi=(42,83) if side in ('north','south') else (52,141)
  if not lo<=deg<=hi or not 0<=minute<60 or not 0<=second<60:raise ValueError('Bounding coordinates outside the published input range')
  bounds[side]=Decimal(deg)+Decimal(minute)/60+Decimal(second)/3600
 if bounds['north']<bounds['south'] or bounds['west']<bounds['east']:raise ValueError('Reversed bounding coordinates')
 # Both are official current map responses; real-time coordinates take precedence.
 # Displayed degree/minute/second strings are rounded and unsuitable for boundaries.
 points={}
 for kind in ('historical','real_time'):
  points.update({r['station_id']:(Decimal(r['latitude']),abs(Decimal(r['longitude']))) for r in json.loads((data/f'map-stations-{kind}.json').read_text())})
 selected=[]
 for row in rows:
  n=row['number']
  if n not in points:raise OSError('Precise official station coordinates not archived')
  lat,lon=points[n]
  if bounds['south']<=lat<=bounds['north'] and bounds['east']<=lon<=bounds['west']:selected.append(row)
 return selected
