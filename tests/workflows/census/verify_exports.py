import csv,json,pathlib,zipfile,xml.etree.ElementTree as ET,re
import argparse
p=argparse.ArgumentParser();p.add_argument('exports',type=pathlib.Path);args=p.parse_args();D=args.exports
def normal(s):
 s=s.strip();t=s.removeprefix('±') if hasattr(s,'removeprefix') else s[1:] if s.startswith('±') else s
 if re.fullmatch(r'-?[0-9][0-9,]*(?:\.[0-9]+)?',t):return t.replace(',','')
 return s
rows=list(csv.reader((D/'custom.csv').open(encoding='utf-8-sig')));dom=json.loads((D/'custom-dom.json').read_text());assert [[normal(x) for x in r] for r in rows]==[[normal(x) for x in r] for r in dom]
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(D/'custom.xlsx') as z:
 root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));matrix=[[''.join(c.itertext()) for c in row] for row in root.findall('.//s:row',ns)];assert matrix==rows;assert 'Coverage' in z.read('xl/workbook.xml').decode()
with zipfile.ZipFile(D/'custom.zip') as z:
 data=list(csv.DictReader(z.read('data.csv').decode('utf-8-sig').splitlines()));assert len(data)==4 and len(data[0])==2+49*4;assert 'B01001_003E' in data[0]
with zipfile.ZipFile(D/'partial.zip') as z:
 cov=json.loads(z.read('coverage.json'));assert cov['archived']==4;data=list(csv.DictReader(z.read('data.csv').decode('utf-8-sig').splitlines()));assert len(data)==4
with zipfile.ZipFile(D/'partial.xlsx') as z:assert '259' in z.read('xl/worksheets/sheet2.xml').decode()
r={'custom_csv_matches_visible_dom':True,'xlsx_matches_csv':True,'zip_ignores_customization_full_4_geographies_49_variables':True,'partial_exports_preserve_coverage':True,'csv_matrix_rows':len(rows),'numeric_annotation_cells_compared':sum(len(r)-1 for r in rows[1:])}
(D.parent/'export-checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
