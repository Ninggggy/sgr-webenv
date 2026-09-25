import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('harvest',ROOT/'tools'/'harvest.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)


class HarvestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=h.connect(Path(self.tmp.name)/'metadata.sqlite')
        self.body=(ROOT/'tests/fixtures'/'raw-sample.xml').read_bytes()

    def tearDown(self):
        self.db.close();self.tmp.cleanup()

    def test_real_source_fields_and_version_times(self):
        h.import_page(self.db,self.body,'cs:cs')
        row=self.db.execute('SELECT title,categories,comments FROM records').fetchone()
        self.assertIn('Self-Consistency',row[0])
        self.assertEqual(row[1],'cs.CL cs.AI')
        self.assertIn('Published at ICLR 2023',row[2])
        versions=self.db.execute('SELECT number,submitted_at FROM versions ORDER BY number').fetchall()
        self.assertEqual(len(versions),4)
        self.assertEqual(versions[0],(1,'2022-03-21T17:48:52+00:00'))
        self.assertEqual(versions[3],(4,'2023-03-07T17:57:37+00:00'))

    def test_no_fabricated_historical_details_or_announcements(self):
        h.import_page(self.db,self.body,'cs:cs')
        self.assertEqual(self.db.execute('SELECT count(*) FROM versions WHERE detail_json IS NOT NULL').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM announcements').fetchone()[0],0)

    def test_cross_set_dedup_preserves_membership(self):
        h.import_page(self.db,self.body,'cs:cs')
        h.import_page(self.db,self.body,'stat:stat')
        self.assertEqual(self.db.execute('SELECT count(*) FROM records').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM membership').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT count(*) FROM versions').fetchone()[0],4)

    def test_truncated_xml_does_not_advance_checkpoint(self):
        with self.assertRaises(Exception):h.import_page(self.db,self.body[:200],'cs:cs')
        self.assertEqual(self.db.execute('SELECT count(*) FROM harvest_state').fetchone()[0],0)

    def test_oai_error_is_not_empty_complete_corpus(self):
        body=b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="badResumptionToken">expired</error></OAI-PMH>'
        with self.assertRaises(ValueError):h.import_page(self.db,body,'cs:cs')
        self.assertEqual(self.db.execute('SELECT count(*) FROM harvest_state').fetchone()[0],0)

    def test_missing_middle_version_fails(self):
        body=self.body.replace(b'version="v2"',b'version="v9"')
        with self.assertRaises(ValueError):h.import_page(self.db,body,'cs:cs')

    def test_record_identifier_mismatch_fails(self):
        with self.assertRaises(ValueError):
            h.import_page(self.db,self.body.replace(b'<id>2203.11171</id>',b'<id>2101.01097</id>'),'cs:cs')


if __name__=='__main__':unittest.main()
