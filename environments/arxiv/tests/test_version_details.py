import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('version_details',ROOT/'tools/version_details.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class VersionDetailsTests(unittest.TestCase):
    def setUp(self):
        self.body=(ROOT/'tests/fixtures/historical-abstract.html').read_text()

    def test_real_v1_december_not_identifier_january(self):
        result=v.parse(self.body,'2101.01097v1')
        self.assertEqual(result['citation_date'],'2020/12/30')
        self.assertEqual(result['primary_category'],'cs.CV')
        self.assertIn('cs.LG',result['categories'])
        self.assertEqual(result['authors_list'],['You, Junyong','Korhonen, Jari'])
        self.assertEqual(result['authors'],'Junyong You, Jari Korhonen')

    def test_displayed_history_license_and_source_entrances(self):
        result=v.parse(self.body,'2101.01097v1')
        self.assertEqual(result['submitted_at'],'2020-12-30T18:43:11+00:00')
        self.assertEqual(result['submitter_name'],'Junyong You')
        self.assertEqual(result['history_display'][0]['size_display'],'362 KB')
        self.assertEqual(result['history_display'][1]['size_display'],'376 KB')
        self.assertEqual(result['license'],'http://arxiv.org/licenses/nonexclusive-distrib/1.0/')
        self.assertEqual(result['download_entrances'],[{'label':'View PDF','href':'/pdf/2101.01097v1'}])

    def test_preprint_doi_is_not_publication_doi(self):
        self.assertIsNone(v.parse(self.body,'2101.01097v1')['doi'])

    def test_latest_or_other_version_must_not_masquerade_as_v1(self):
        with self.assertRaises(ValueError): v.parse(self.body,'2101.01097v2')

    def test_error_page_must_not_be_imported(self):
        with self.assertRaises(ValueError):v.parse('<title>503</title>','2101.01097v1')

    def test_report_number_is_not_journal_reference(self):
        row='<tr><td class="label">Report&nbsp;number:</td><td class="jref">TR-2020-12</td></tr>'
        body=self.body.replace('<table summary="Additional metadata">','<table summary="Additional metadata">'+row)
        result=v.parse(body,'2101.01097v1')
        self.assertEqual(result['report_num'],'TR-2020-12')
        self.assertIsNone(result['journal_ref'])


if __name__=='__main__': unittest.main()
