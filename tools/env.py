#!/usr/bin/env python3
"""Manage isolated SGR website instances. Python standard library only."""
import argparse,json,os,platform,shutil,sqlite3,subprocess,sys,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITES=('noaa','census','wonder','arxiv','wateroffice','cellosaurus')
def run(args,**kwargs):
 return subprocess.run(args,check=True,**kwargs)
def load(site,release):
 if '/' in release or '..' in release:raise ValueError('Invalid release')
 m=json.loads((ROOT/'releases'/f'{release}.json').read_text())
 return m,m['environments'][site]
def download(url,dest):
 """Resume only when the server confirms the requested range."""
 dest=Path(dest);partial=dest.with_name(dest.name+'.partial')
 offset=partial.stat().st_size if partial.exists() else 0
 req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
 with urllib.request.urlopen(req,timeout=120) as r:
  resume=offset and r.status==206 and r.headers.get('Content-Range','').startswith(f'bytes {offset}-')
  with partial.open('ab' if resume else 'wb') as f:shutil.copyfileobj(r,f,1024*1024)
 partial.replace(dest)
def extract(archive,dest):
 """Extract only ordinary files/directories under an empty destination."""
 dest=Path(dest)
 if dest.exists() and any(dest.iterdir()):raise ValueError('Data destination is not empty')
 dest.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive,'r:gz') as t:
  for member in t:
   p=Path(member.name)
   if p.is_absolute() or '..' in p.parts or not(member.isfile() or member.isdir()):raise ValueError('Unsafe archive member: '+member.name)
   target=dest/p
   if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
   target.parent.mkdir(parents=True,exist_ok=True)
   with t.extractfile(member) as src,target.open('wb') as out:shutil.copyfileobj(src,out,1024*1024)
   target.chmod(0o644)
def validate_data(site,spec,directory):
 for name in spec.get('required_files',[]):
  if not (directory/name).is_file():raise ValueError('Missing runtime data: '+name)
 for database in directory.rglob('*'):
  if database.suffix not in ('.sqlite','.sqlite3','.db'):continue
  with sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True) as c:
   if c.execute('pragma quick_check').fetchone()[0]!='ok':raise ValueError('Invalid SQLite data: '+database.name)
   if site=='cellosaurus' and database.name=='cellosaurus.sqlite':
    if c.execute('select count(*) from cell').fetchone()[0]!=spec['expected_records']:raise ValueError('Incomplete Cellosaurus database')
   if site=='arxiv' and database.name=='snapshot.sqlite':
    for table,key in [('records','expected_records'),('versions','expected_versions')]:
     count=c.execute('select count(*) from '+table+(' where deleted=0' if table=='records' else '')).fetchone()[0]
     if count!=spec[key]:raise ValueError('Incomplete '+table+': '+str(count))

def compose(site,spec,state,mode):
 envdir=ROOT/'environments'/site
 web='web' if site=='arxiv' else site+'-web'
 browser='browser' if site=='arxiv' else site+'-browser'
 common={'user':'1000:1000','read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'pids_limit':256,'networks':['browsing']}
 services={web:{**common,'image':spec['images']['web'],'volumes':[str(state/'data')+':/data:ro'],'tmpfs':['/tmp:rw,nosuid,nodev,size=128m,mode=1777'],'mem_limit':'1536m'},browser:{**common,'image':spec['images']['browser'],'security_opt':['no-new-privileges:true','seccomp:'+str(envdir/('runner' if site=='arxiv' else 'docker')/'seccomp_profile.json')],'tmpfs':['/tmp:rw,nosuid,nodev,size=768m,mode=1777'],'shm_size':'256m','mem_limit':'1536m','stdin_open':True,'depends_on':[web]}}
 networks={'browsing':{'internal':True,'driver_opts':{'com.docker.network.bridge.gateway_mode_ipv4':'isolated'}}}
 volumes={}
 if site=='arxiv':
  networks['index']={'internal':True}
  services[web]['networks']=['browsing','index']
  services[web]['volumes']=[str(state/'data/snapshot.sqlite')+':/data/metadata.sqlite:ro']
  services[web]['environment']={'ELASTICSEARCH_SERVICE_HOST':'search','ELASTICSEARCH_INDEX':'arxiv-release-0-1-0','ARXIV_RELEASE_STATUS':('accepted-current-eight' if spec['distribution_status']=='ready' else 'candidate')}
  services['search']={'image':spec['images']['search'],'user':'1000:0','read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'networks':['index'],'volumes':['search-data:/usr/share/elasticsearch/data',str(envdir/'config/elasticsearch.yml')+':/usr/share/elasticsearch/config/elasticsearch.yml:ro'],'environment':{'discovery.type':'single-node','ES_JAVA_OPTS':'-Xms2g -Xmx2g -XX:ParallelGCThreads=4 -XX:ConcGCThreads=2 -Djna.boot.library.path=/usr/share/elasticsearch/native','xpack.security.enabled':'false','xpack.monitoring.enabled':'false','xpack.watcher.enabled':'false','xpack.ml.enabled':'false'},'tmpfs':['/tmp:rw,noexec,nosuid,size=256m','/usr/share/elasticsearch/logs:rw,nosuid,size=32m,uid=1000,gid=0'],'mem_limit':'24g','pids_limit':256}
  volumes['search-data']={}
 if site=='cellosaurus':
  networks['clastr']={'internal':True}
  services[web]['networks']=['browsing','clastr']
  services[browser]['mem_limit']='2g'
  services['cellosaurus-clastr']={**common,'image':spec['images']['clastr'],'networks':['clastr'],'mem_limit':'1536m','tmpfs':['/tmp:rw,nosuid,nodev,size=384m,mode=1777'],'volumes':[str(state/'data/cellosaurus.xml.gz')+':/data/cellosaurus.xml.gz:ro'],'environment':{'JAVA_OPTS':'-Xms128m -Xmx1024m -Djava.io.tmpdir=/tmp','CELLOSAURUS_XML':'/data/cellosaurus.xml.gz'}}
  services['cellosaurus-clastr']['healthcheck']={'test':['CMD','python3','-c','import urllib.request,json; d=json.load(urllib.request.urlopen("http://127.0.0.1:8080/str-search/api/database")); assert d["version"]=="56.0"'],'interval':'5s','timeout':'3s','retries':36}
  services[web]['healthcheck']={'test':['CMD','python3','-c','import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/health")'],'interval':'5s','timeout':'3s','retries':12}
  services[web]['depends_on']={'cellosaurus-clastr':{'condition':'service_healthy'}}
  services[browser]['depends_on']={web:{'condition':'service_healthy'}}
 if mode=='preview':
  networks['preview']={}
  services['preview']={**common,'image':spec['images']['web'],'command':['python3','/app/_preview_proxy.py'],'environment':{'UPSTREAM':f'http://{web}:8080'},'networks':['browsing','preview'],'ports':[f'127.0.0.1:{spec["port"]}:8080'],'mem_limit':'128m','depends_on':[web]}
 return {'version':'2.4','services':services,'networks':networks,**({'volumes':volumes} if volumes else {})}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=['prepare','start','verify','reset','stop'])
 p.add_argument('site',choices=SITES);p.add_argument('--release',default='v0.1.1')
 p.add_argument('--mode',choices=['preview','eval'],default='eval')
 p.add_argument('--port',type=int,help='Override the preview loopback port for an additional instance')
 p.add_argument('--state-dir',type=Path,default=ROOT/'.state')
 p.add_argument('--data-archive',type=Path,help='Install a locally staged archive')
 p.add_argument('--local-images',action='store_true',help='Use already built Linux amd64 images instead of pulling; prepare only')
 p.add_argument('--allow-candidate',action='store_true',help='Author validation of an unpublished candidate')
 args=p.parse_args();m,spec=load(args.site,args.release)
 if args.port is not None:
  if not 1<=args.port<=65535:raise ValueError('Preview port must be 1..65535')
  spec={**spec,'port':args.port}
 state=(args.state_dir/args.release/args.site).resolve();state.mkdir(parents=True,exist_ok=True)
 config=state/'compose.json'
 compose_cmd=['docker','compose']
 if subprocess.run(compose_cmd+['version'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  if not shutil.which('docker-compose'):raise ValueError('Docker Compose v2+ is required')
  compose_cmd=['docker-compose']
 def dc(*cmd):return run([*compose_cmd,'-p','sgr-'+args.site+'-'+args.release.replace('.','-'),'-f',str(config),*cmd])
 if args.action in ('stop','reset','verify'):
  if not config.exists():raise ValueError('No installed instance')
 else:
  if spec['distribution_status']!='ready' and not args.allow_candidate:raise ValueError('This environment is not released: see docs/STATUS.md. Author testing requires --allow-candidate.')
  config.write_text(json.dumps(compose(args.site,spec,state,args.mode),indent=2)+'\n')
 if args.action=='prepare':
  if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):raise ValueError('Installation is currently supported on Linux amd64 only')
  archive=args.data_archive
  if archive is None:
   assets=spec['data_assets']
   if not assets:raise ValueError('No redistributable data assets have been published')
   cache=state/'downloads';cache.mkdir(exist_ok=True)
   parts=[]
   for asset in assets:
    f=cache/asset['name'];download(asset['url'],f)
    if f.stat().st_size!=asset['bytes']:raise ValueError('Incomplete download: '+f.name)
    parts.append(f)
   archive=cache/'assembled.tar.gz'
   with archive.open('wb') as out:
    for f in parts:
     with f.open('rb') as src:shutil.copyfileobj(src,out,1024*1024)
  if (state/'data').exists():validate_data(args.site,spec,state/'data')
  else:
   staging=state/'data.incomplete'
   if staging.exists():shutil.rmtree(staging)
   extract(archive,staging);validate_data(args.site,spec,staging);staging.rename(state/'data')
  if args.local_images:
   for image in spec['images'].values():
    info=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
    if info.get('Os')!='linux' or info.get('Architecture')!='amd64':raise ValueError('Expected Linux amd64 image: '+image)
  else:dc('pull')
  if args.site=='arxiv':
   dc('up','-d','search')
   dc('run','--rm','--no-deps', 'web','python3','/app/wait_search.py')
   dc('run','--rm','--no-deps','web','python3','/app/build_index.py','--database','/data/metadata.sqlite','--index','arxiv-release-0-1-0')
 elif args.action=='start':
  if not (state/'data').is_dir():raise ValueError('Run prepare first')
  if args.site=='arxiv':
   dc('up','-d','search')
   dc('run','--rm','--no-deps','web','python3','/app/wait_search.py','--verify')
  dc('up','-d')
 elif args.action=='stop':dc('down')
 elif args.action=='reset':
  c=json.loads(config.read_text());services=[n for n in c['services'] if n!='search']
  dc('up','-d','--force-recreate',*services)
 elif args.action=='verify':
  web='web' if args.site=='arxiv' else args.site+'-web'
  path='/' if args.site=='arxiv' else '/health'
  dc('exec','-T',web,'python3','-c',f'import urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8080{path}",timeout=30); assert r.status==200; print("HTTP smoke passed; this is not task acceptance")')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError,subprocess.CalledProcessError) as e:sys.exit(str(e))
