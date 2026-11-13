import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import discover_html, canonical, unique

class CollectorTests(unittest.TestCase):
    def test_source_count_and_exact_duplicate(self):
        a=json.loads((Path(__file__).resolve().parents[1]/'sources.json').read_text())
        self.assertEqual(len(a),18)
        self.assertEqual(a[2]['url'],a[17]['url'])
    def test_canonical_removes_tracker(self):
        self.assertEqual(canonical('https://example.com/a/?utm_source=site#x'),'https://example.com/a')
    def test_filter_and_external_rejection(self):
        source={'id':'source_03','name':'Dodge','url':'https://www.construction.com/construction-news/'}
        sample='<main><article><h2><a href="/dodge-momentum-index-falls-9-in-october/">Dodge Momentum Index Falls 9% in October</a></h2></article><article><a href="https://unrelated.com/construction">Construction News on other domain</a></article><a href="/privacy">Privacy Policy</a></main>'
        a=discover_html(source['url'],sample,source)
        self.assertEqual(len(a),1)
        self.assertIn('momentum',a[0]['url'])
    def test_no_fake_numeric_data(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'data/latest.json').read_text())
        self.assertEqual(data['source_count'],18)
        self.assertNotIn('metrics',data)

if __name__=='__main__':unittest.main()
