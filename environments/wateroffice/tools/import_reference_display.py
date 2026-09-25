import pathlib,json,re,html
ROOT=pathlib.Path(__file__).resolve().parents[1];source=json.loads((ROOT/'data/reference-pages.json').read_text());rows=[];last=None
for page in source['pages']:
 for row in page['rows']:
  key=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',row))).strip()
  if key==last:continue
  last=key;number=re.search(r'\b\d{2}[A-Z]{2}\d{3}\b',key)
  rows.append({'number':number[0] if number else '', 'html':row})
raw=json.loads((ROOT/'data/reference.json').read_text())['rows'];assert len(rows)==len(raw)==9329
assert [x['number'] for x in rows]==[x['Station Number'] for x in raw]
(ROOT/'data/reference-display.json').write_text(json.dumps({'source':'Complete official HTML index pagination; 86 pages, shared boundary rows removed','captured':'2026-09-25','rows':rows},ensure_ascii=False,separators=(',',':')))
print(len(rows),'rows, station ordering exactly matches complete official CSV')
