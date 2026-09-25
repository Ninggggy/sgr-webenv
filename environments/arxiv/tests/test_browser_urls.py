import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).resolve().parents[1]/'runner/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class URLTests(unittest.TestCase):
    def test_exact_domains_and_parameters(self):
        self.assertEqual(b.map_url('https://arxiv.org/search/advanced?a=1&b=2'),b.ORIGIN+'/search/advanced?a=1&b=2')
        self.assertEqual(b.map_url('https://export.arxiv.org/api/query?id_list=2101.01097'),b.ORIGIN+'/api/query?id_list=2101.01097')
        self.assertEqual(b.map_url('https://info.arxiv.org/help/api'),b.ORIGIN+'/help/api')

    def test_browse_entrypoints(self):
        for path in ('/catchup/cs/2026-09-18','/prevnext?id=2101.01097&context=cs.CV&function=next','/multi?group=grp_cs'):
            self.assertEqual(b.map_url('https://arxiv.org'+path),b.ORIGIN+path)

    def test_lookalikes_credentials_private_paths_and_schemes(self):
        for url in ('https://arxiv.org.evil.example/abs/1', 'https://arxiv.org@evil.example/',
                    'https://user:pass@arxiv.org/', 'https://arxiv.org:9000/',
                    'file:///etc/passwd', 'http://127.0.0.1/', '//evil.example/',
                    'https://arxiv.org/author/legacy-records.json', '/abs/%2e%2e/author',
                    'https://arxiv.org\\@evil.example/', 'javascript:alert(1)'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError): b.map_url(url)

if __name__=='__main__':unittest.main()
