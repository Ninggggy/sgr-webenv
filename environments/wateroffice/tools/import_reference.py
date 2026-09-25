import csv,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
source=ROOT/'author/reference-index-compressed.csv'
rows=list(csv.reader(source.open(encoding='utf-8-sig')))
assert rows[-1]==['DC = Data Contributed By'],'Official CSV terminator missing; possible truncated download'
header=rows[0];assert len(header)==18
out=[]
for line,row in enumerate(rows[1:],2):
 if len(row) not in (18,19):continue
 if len(row)==19:
  assert row[-1]=='','Unexpected nonempty extra CSV field'
  row=row[:18]
 if row[0] and not re.fullmatch(r'\d{2}[A-Z]{2}\d{3}',row[0]):raise ValueError((line,row[0]))
 entry=dict(zip(header,row));entry['source_line']=line
 if out and entry['Station Number'] and out[-1]['Station Number']==entry['Station Number']:
  out[-1]['records'].append(entry)
 else:
  out.append({'Station Number':entry['Station Number'],'Water Course':entry['Water Course'],'source_line':line,'records':[entry]})
ids={r['Station Number'] for r in out if r['Station Number']}
assert len(ids)==8417
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data/reference.json').write_text(json.dumps({'source':'https://wateroffice.ec.gc.ca/station_metadata/reference_index_download_e.html','captured':'2026-09-25','rows':out},ensure_ascii=False,separators=(',',':'))+'\n')
print('Imported',len(out),'river/station entries;',len(ids),'unique stations')
