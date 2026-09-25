"""Split an archive into <=1 GiB Release assets; prints ordered asset sizes."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
parts=[]
with a.archive.open('rb') as src:
 i=0
 while True:
  first=src.read(1024*1024)
  if not first:break
  dest=a.archive.with_name(a.archive.name+f'.part-{i:03d}')
  with dest.open('xb') as out:
   out.write(first)
   for _ in range(1023):
    b=src.read(1024*1024)
    if not b:break
    out.write(b)
  parts.append({'name':dest.name,'bytes':dest.stat().st_size});i+=1
print(json.dumps(parts,indent=2))
