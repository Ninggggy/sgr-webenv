import importlib.util,io,json,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('env',P/'tools/env.py');env=importlib.util.module_from_spec(spec);spec.loader.exec_module(env)
class Distribution(unittest.TestCase):
 def test_all_sites_isolated(self):
  for site in env.SITES:
   _,s=env.load(site,'v0.1.4');c=env.compose(site,s,Path('/tmp/example'), 'eval')
   self.assertTrue(all(n.get('internal') for n in c['networks'].values()))
   for role,v in c['services'].items():
    self.assertNotIn('ports',v);self.assertTrue(v['read_only']);self.assertIn('ALL',v['cap_drop']);self.assertNotEqual(v['user'].split(':')[0],'0')
    self.assertFalse(any('author' in x or 'answers' in x for x in v.get('volumes',[])))
 def test_preview_only_proxy_published(self):
  for site in env.SITES:
   _,s=env.load(site,'v0.1.4');c=env.compose(site,s,Path('/tmp/example'),'preview')
   self.assertEqual([k for k,v in c['services'].items() if v.get('ports')],['preview'])
   self.assertTrue(c['services']['preview']['ports'][0].startswith('127.0.0.1:'))
 def test_browser_cannot_reach_index_network(self):
  _,s=env.load('arxiv','v0.1.0');c=env.compose('arxiv',s,Path('/tmp/example'),'eval')
  self.assertEqual(c['services']['browser']['networks'],['browsing'])
  self.assertEqual(c['services']['search']['networks'],['index'])
 def test_noaa_prepare_requires_local_images(self):
  with tempfile.TemporaryDirectory() as tmp, patch.object(env.sys,'argv',['env.py','prepare','noaa','--release','v0.1.2','--state-dir',tmp]), patch.object(env.subprocess,'run',return_value=Mock(returncode=0)), patch.object(env,'download') as download:
   with self.assertRaisesRegex(ValueError,'--local-images'):env.main()
   download.assert_not_called()
 def test_noaa_local_prepare_inspects_images_without_pull(self):
  with tempfile.TemporaryDirectory() as tmp:
   state=Path(tmp)/'v0.1.2/noaa';(state/'data').mkdir(parents=True)
   argv=['env.py','prepare','noaa','--release','v0.1.2','--state-dir',tmp,'--local-images','--data-archive',str(Path(tmp)/'data.gz')]
   with patch.object(env.sys,'argv',argv), patch.object(env.platform,'system',return_value='Linux'), patch.object(env.platform,'machine',return_value='x86_64'), patch.object(env.subprocess,'run',return_value=Mock(returncode=0)) as run, patch.object(env.subprocess,'check_output',return_value='[{"Os":"linux","Architecture":"amd64"}]') as inspect, patch.object(env,'validate_data'):
    env.main()
    self.assertEqual(inspect.call_count,2)
    self.assertFalse(any('pull' in c.args[0] for c in run.call_args_list))
 def test_noaa_start_without_candidate_flag(self):
  with tempfile.TemporaryDirectory() as tmp:
   (Path(tmp)/'v0.1.2/noaa/data').mkdir(parents=True)
   with patch.object(env.sys,'argv',['env.py','start','noaa','--release','v0.1.2','--state-dir',tmp]), patch.object(env.subprocess,'run',return_value=Mock(returncode=0)) as run:
    env.main()
    self.assertEqual(run.call_args.args[0][-2:],['up','-d'])
 def archive(self,path,name,link=False):
  with tarfile.open(path,'w:gz') as t:
   m=tarfile.TarInfo(name);m.size=2
   if link:m.type=tarfile.SYMTYPE;m.linkname='/etc/passwd'
   t.addfile(m,io.BytesIO(b'{}'))
 def test_safe_extract(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);self.archive(p/'data.gz','metadata.json');env.extract(p/'data.gz',p/'data');self.assertEqual((p/'data/metadata.json').read_text(),'{}')
 def test_reject_escape_and_symlink(self):
  for name,link in [('../outside',False),('/etc/file',False),('link',True)]:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);self.archive(p/'data.gz',name,link)
    with self.assertRaises(ValueError):env.extract(p/'data.gz',p/'data')
 def test_not_overwrite_existing_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);self.archive(p/'data.gz','metadata.json');env.extract(p/'data.gz',p/'data')
   with self.assertRaises(ValueError):env.extract(p/'data.gz',p/'data')
if __name__=='__main__':unittest.main()
