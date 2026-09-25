"""Published vertical-datum descriptions; never infer conversion precision from HYDAT."""
import json,re,html
from urllib.parse import urlencode

def render(data,q,load,faq=False):
 n='faq' if faq else q.get('stn','')
 if not faq and not re.fullmatch(r'[0-9A-Z]{7}',n):raise ValueError('Invalid station number')
 folder=data/'datums'
 if not (folder/'manifest.json').is_file():raise OSError('National datum archive is incomplete')
 p=folder/(n+'.json')
 if not p.is_file():raise ValueError('Station is outside the archived national station list')
 row=json.loads(p.read_text());s=load('datum')
 s=re.sub(r'<title>.*?</title>',lambda _:'<title>'+row['title']+' - Water Level and Flow - Environment Canada</title>',s,count=1,flags=re.S)
 s=re.sub(r'(<h1\b[^>]*>).*?(</h1></div>).*?(<section id="water-topics")',lambda m:m[1]+row['title']+m[2]+'\n'+row['body']+m[3],s,count=1,flags=re.S)
 # Original datum pages link back to realtime reports, including historical entry.
 params={k:q[k] for k in ('stn','mode') if k in q}
 if faq:
  s=re.sub(r'<li><a href="/report/real_time_e.html\?[^"]*">Report</a></li>','',s)
  s=re.sub(r'//eau.ec.gc.ca/report/datum_f.html\?[^"]*','//eau.ec.gc.ca/report/datum_faq_f.html',s)
 else:
  s=s.replace('08EE004',n)
  link='/report/real_time_e.html?'+urlencode(params)
  s=re.sub(r'(<li><a href=")[^"]*(">Report</a></li>)',lambda m:m[1]+html.escape(link,quote=True)+m[2],s)
 return s
