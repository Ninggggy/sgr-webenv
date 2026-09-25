"""Original remarks layout, populated from nationwide HYDAT remarks."""
import html,re
from urllib.parse import urlencode

def render(db,q,load):
 number=q.get('stn','');station=db.station(number);s=load('remarks')
 s=s.replace('BULKLEY RIVER AT QUICK',html.escape(station['STATION_NAME'])).replace('08EE004',html.escape(number))
 sections=[]
 with db.connect() as c:
  for code,label,annual in [(2,'annual hydrometric',True),(4,'historical discharge',False),(5,'historical water levels',False),(11,'annual water levels',True)]:
   rows=c.execute('SELECT YEAR,REMARK_EN FROM STN_REMARKS WHERE STATION_NUMBER=? AND REMARK_TYPE_CODE=? ORDER BY YEAR',(number,code)).fetchall()
   if not rows:continue
   caption='This table provides a summary of '+label+' remarks'+(' for specific years.' if annual else '.')
   body=''.join('<tr>'+('<td class="align-center">'+str(r['YEAR'])+'</td>' if annual else '')+'<td class="align-center">'+html.escape(r['REMARK_EN'] or '')+'</td></tr>' for r in rows)
   sections.append('<table class="table table-striped table-hover"><caption>'+caption+'</caption><thead><tr>'+('<th>Year</th>' if annual else '')+'<th class="text-center">Remark</th></tr></thead><tbody>'+body+'</tbody></table>')
 body=''.join(sections) if sections else '<p>No remarks are available for this station.</p>'
 s=re.sub(r'(</h1></div>).*?(<section id="water-topics")',lambda m:m[1]+'<div class="container">'+body+'<div class="clearfix"></div></div>'+m[2],s,flags=re.S)
 link='/report/historical_e.html?'+urlencode({k:v for k,v in q.items() if k in ('stn','mode','dataType','parameterType','first_year','last_year','stations')})
 s=re.sub(r'(<li><a href=")[^"]*(">Report</a></li>)',lambda m:m[1]+html.escape(link,quote=True)+m[2],s)
 return s
