#!/usr/bin/env python3
from prepare import fetch,ROOT
import concurrent.futures,json
# Census Bureau maintained CitySDK archive, matching each source year.
def work(item):
 y,level=item
 url=f'https://raw.githubusercontent.com/uscensusbureau/citysdk/master/v2/GeoJSON/20m/{y}/{level}.json'
 path=ROOT/f'sources/geography/{y}-{level}.json'
 d=fetch(url,path,'geo');print(y,level,len(d['features']),d['features'][0]['properties'],flush=True)
 return y,level,d
results=list(concurrent.futures.ThreadPoolExecutor(3).map(work,[(y,l) for y in range(2016,2020) for l in ['state','county']]))
out=ROOT/'data/boundaries';out.mkdir(parents=True,exist_ok=True)
for y in range(2016,2020):
 fs=[f for yr,l,d in results if yr==y for f in d['features']]
 (out/f'{y}.json').write_text(json.dumps({'type':'FeatureCollection','features':fs},separators=(',',':')))
