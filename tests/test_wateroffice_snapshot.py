"""Dated, synthetic observations: no network or full HYDAT dependency."""
import csv
import gzip
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / 'environments/wateroffice/app'
spec = importlib.util.spec_from_file_location('snapshot', APP / 'realtime_snapshot.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
HEADER = [' ID','Date','Parameter/Paramètre','Value/Valeur','Qualifier/Qualificatif','Symbol/Symbole','Approval/Approbation','Grade/Classification','Qualifiers/Qualificatifs']


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name); (self.data/'realtime').mkdir()
        (self.data/'realtime/window.json').write_text(json.dumps({'format':'wateroffice-csv-v2','from':'2026-08-26T09:40:00Z','to':'2026-09-25T09:40:00Z'}))
        (self.data/'map-stations-real_time.json').write_text(json.dumps([{'station_id':'TEST','timezone_offset':'-3.5','timezone_abbr_en':'NST'}]))
        (self.data/'realtime-stations.json').write_text(json.dumps({'stations':[{'number':'TEST','name':'Synthetic station','province':'NL'}]}))
        (self.data/'realtime/TEST.json').write_text(json.dumps({'complete':True,'from':'2026-08-26T09:40:00Z','to':'2026-09-25T09:40:00Z','parameters':['46','47','3']}))
        self.rows = [
            ['TEST','2026-08-26T09:40:00Z','46','1.234','','','Provisional/Provisoire','',''],
            ['TEST','2026-09-24T03:25:00Z','46','1.235','','','Final/Finales','50','Q'],
            ['TEST','2026-09-24T03:30:00Z','46','0','','','Final/Finales','',''],
            ['TEST','2026-09-24T03:30:00Z','47','12.3','','','Provisional/Provisoire','20',''],
            ['TEST','2026-09-24T03:30:00Z','3','1.232','','','Provisional/Provisoire','30',''],
            ['TEST','2026-09-25T09:40:00Z','46','1.237','','','Provisional/Provisoire','','']]
        self.write()

    def write(self):
        with gzip.open(self.data/'realtime/TEST.csv.gz','wt',newline='') as f:
            w=csv.writer(f);w.writerow(HEADER);w.writerows(self.rows)

    def test_default_last_week_and_full_month(self):
        self.assertEqual(tuple(map(str,s.dates(self.data,'TEST'))),('2026-09-18','2026-09-25'))
        self.assertEqual(len(s.records(self.data,'TEST','46')),3)
        self.assertEqual(len(s.records(self.data,'TEST','46','2026-08-26','2026-09-25')),4)
        with self.assertRaises(ValueError):s.records(self.data,'TEST','46','2026-08-25','2026-09-25')

    def test_local_midnight_fractional_offset(self):
        a=s.records(self.data,'TEST','46','2026-09-23','2026-09-23')
        self.assertEqual([r['time'] for r in a],['2026-09-23 23:55:00'])
        a=s.records(self.data,'TEST','46','2026-09-24','2026-09-24')
        self.assertEqual(a[0]['time'],'2026-09-24 00:00:00')
        self.assertEqual(a[0]['value'],'0')

    def test_status_buckets_and_grade(self):
        a=s.graph_series(self.data,'TEST','46','2026-09-23','2026-09-25')
        self.assertEqual(len(a['final']),2);self.assertEqual(len(a['provisional']),1)
        self.assertEqual(a['final'][0][2:7],['Final','50','REVISED','50','Q'])
        self.assertEqual(s.table_series(self.data,'TEST','3')[0][4],'PARTIAL DAY')

    def test_unknown_approval_never_assigned_provisional(self):
        self.rows[-1][6]='';self.write()
        self.assertEqual(s.table_series(self.data,'TEST','46')[-1][2],'')
        with self.assertRaisesRegex(ValueError,'Approval unavailable'):s.graph_series(self.data,'TEST','46')

    def test_no_published_parameter_differs_from_empty(self):
        self.assertEqual(s.records(self.data,'TEST','47','2026-09-25','2026-09-25'),[])
        with self.assertRaisesRegex(ValueError,'not published'):s.records(self.data,'TEST','6')

    def test_partial_upgrade_keeps_legacy_window_and_values_separate(self):
        w=json.loads((self.data/'realtime/window.json').read_text())
        w.update(covered_stations=['TEST'],legacy_window={'from':'2026-09-18T09:40:00Z','to':'2026-09-25T09:40:00Z','source':'GeoMet'})
        (self.data/'realtime/window.json').write_text(json.dumps(w))
        (self.data/'realtime-stations.json').write_text(json.dumps({'stations':[{'number':n,'name':n,'province':'NL'} for n in ('TEST','LEGACY')]}))
        (self.data/'map-stations-real_time.json').write_text(json.dumps([{'station_id':n,'timezone_offset':'-3.5','timezone_abbr_en':'NST'} for n in ('TEST','LEGACY')]))
        (self.data/'realtime/LEGACY.json').write_text(json.dumps({'complete':True,'station':'LEGACY'}))
        with gzip.open(self.data/'realtime/LEGACY.csv.gz','wt',newline='') as f:
            writer=csv.writer(f);writer.writerow(['STATION_NUMBER','DATETIME','DATETIME_LST','LEVEL','DISCHARGE','LEVEL_SYMBOL_EN','DISCHARGE_SYMBOL_EN'])
            writer.writerow(['LEGACY','2026-09-24T12:00:00Z','2026-09-24T08:30:00-03:30','8.765','','',''])
        self.assertFalse(s.is_official_csv(self.data,'LEGACY'));self.assertTrue(s.is_official_csv(self.data,'TEST'))
        with self.assertRaises(ValueError):s.dates(self.data,'LEGACY','2026-08-27','2026-09-25')
        with patch.object(sys,'path',[str(APP),*sys.path]):
            import downloads,realtime
            rows=realtime.graph(self.data,{'station':'LEGACY','param1':'46','start_date':'2026-09-24','end_date':'2026-09-24'})['46']['provisional']
            self.assertEqual(rows[0][1],8.765);self.assertIsNone(rows[0][2])
            data=downloads.realtime_zip(self.data,['TEST','LEGACY'],'46','csv','2026-09-23','2026-09-25')
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                old=z.read(next(n for n in z.namelist() if n.startswith('LEGACY_') and n.endswith('.csv'))).decode('utf-8-sig')
                new=z.read(next(n for n in z.namelist() if n.startswith('TEST_') and n.endswith('.csv'))).decode('utf-8-sig')
                self.assertIn('8.765',old);self.assertNotIn('Final',old);self.assertNotIn('Provisional',old)
                self.assertIn('Final',new);self.assertIn('Provisional',new)

    def test_unlisted_station_and_private_paths_refused(self):
        for station in ('UNKNOWN', '../window', '/etc/passwd', '../../author/answers'):
            with self.assertRaisesRegex(ValueError,'Station not in'):
                s.records(self.data,station,'46')

    def test_incomplete_station_refused(self):
        p=self.data/'realtime/TEST.json';m=json.loads(p.read_text());m['complete']=False;p.write_text(json.dumps(m))
        with self.assertRaises(OSError):s.records(self.data,'TEST','46')

    def test_csv_xml_keep_quality_blanks_and_zero(self):
        # Import the real formatter; source precision/rounding is exercised here.
        with patch.object(sys,'path',[str(APP),*sys.path]):
            for fmt in ('csv','txt','xml'):
                content=s.export_zip(self.data,['TEST'],'46',fmt,'2026-09-23','2026-09-25')
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    text=z.read(next(n for n in z.namelist() if n.endswith('.'+fmt))).decode('utf-8-sig')
                    self.assertIn('Final',text);self.assertIn('Provisional',text)
                    self.assertIn('0.000',text)
                    self.assertIn('50',text)
                    self.assertNotIn('None',text)
                    if fmt=='xml':self.assertIn('<grade />',text)


if __name__=='__main__':unittest.main()
