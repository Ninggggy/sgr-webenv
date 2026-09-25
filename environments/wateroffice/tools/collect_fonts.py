import pathlib,re,subprocess,urllib.parse,json,concurrent.futures
root=pathlib.Path(__file__).resolve().parents[1];p=root/'app/static/vendor/wet/v13.4.0/GCWeb/css/theme.min.css';s=p.read_text();urls=sorted(set(re.findall(r'https://fonts\.gstatic\.com/[^\s)\'\"]+',s)));records=[]
def get(url):
 name=urllib.parse.urlsplit(url).path.lstrip('/').replace('/','_');dest=root/'app/static/vendor/fonts'/name;dest.parent.mkdir(exist_ok=True);r=subprocess.run(['curl','-fLsS','--max-time','45',url,'-o',str(dest)],capture_output=True);return {'url':url,'local':'/vendor/fonts/'+name,'ok':r.returncode==0}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:records=list(ex.map(get,urls))
for r in records:
 if r['ok']:s=s.replace(r['url'],r['local'])
p.write_text(s);(root/'author/font-manifest.json').write_text(json.dumps(records,indent=2));print(len(records),sum(r['ok'] for r in records))
