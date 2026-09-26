"""Exercise source transport failures and resumable segment validation."""
import csv,io,json,importlib.util,tempfile,unittest,subprocess,urllib.parse
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]/'environments/wateroffice/tools/collect_realtime_month.py'
spec=importlib.util.spec_from_file_location('month_collector',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Collector(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name);m.STOP.clear();self.addCleanup(m.STOP.clear)
 def csv(self,cmd,conflict=False,**kwargs):
  q=urllib.parse.parse_qs(urllib.parse.urlsplit(cmd[-1]).query);lo=q['start_date'][0];hi=q['end_date'][0]
  f=io.StringIO(newline='');w=csv.writer(f);w.writerow(m.FIELDS)
  for time,value in [(lo,'1.0')]+([(hi,'2.0')] if conflict else []):
   w.writerow(['TEST',time.replace(' ','T')+'Z','46',value,'','','Provisional/Provisoire','',''])
  return subprocess.CompletedProcess(cmd,0,f.getvalue().rstrip('\r\n').encode(),b'')
 def test_official_missing_final_newline_and_resume(self):
  with patch.object(m,'space'),patch.object(m.subprocess,'run',side_effect=self.csv) as run:
   result=m.acquire('TEST',['46'],self.out)
   self.assertEqual(result['rows'],5);self.assertEqual(run.call_count,5)
   self.assertEqual(m.acquire('TEST',['46'],self.out),result);self.assertEqual(run.call_count,5)
 def test_conflicting_shared_boundary_is_not_published(self):
  with patch.object(m,'space'),patch.object(m.subprocess,'run',side_effect=lambda cmd,**kwargs:self.csv(cmd,True)):
   with self.assertRaisesRegex(ValueError,'Conflicting segment-boundary'):m.acquire('TEST',['46'],self.out)
  self.assertFalse((self.out/'TEST.json').exists())
 def test_partial_transport_never_published(self):
  with patch.object(m,'space'),patch.object(m.time,'sleep'),patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],28,b'partial',b'timeout')):
   with self.assertRaises(RuntimeError):m.acquire('TEST',['46'],self.out)
  self.assertFalse((self.out/'TEST.json').exists())
 def test_refusal_stops_other_stations_without_more_requests(self):
  with patch.object(m,'space'),patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],22,b'',b'HTTP 429')) as run:
   with self.assertRaises(m.AcquisitionStopped):m.acquire('TEST',['46'],self.out)
   with self.assertRaises(m.AcquisitionStopped):m.acquire('OTHER',['46'],self.out)
   self.assertEqual(run.call_count,1)
if __name__=='__main__':unittest.main()
