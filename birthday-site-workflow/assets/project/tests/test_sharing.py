"""Verify metadata without JavaScript, portable paths, asset types and replacement safety."""
import copy
import io
import pathlib
import sys
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PIL import Image
from jsonschema import Draft202012Validator
from configuration import DEFAULTS
from data_validation import validate_site
from project_lib import read_json,render
from make_branding import branding_files
import test_workflow as workflow


class Head(HTMLParser):
    def __init__(self,text):
        super().__init__();self.meta={};self.links={};self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta':self.meta[attrs.get('property',attrs.get('name'))]=attrs.get('content')
        if tag=='link':self.links.setdefault(attrs.get('rel'),[]).append(attrs)


class Sharing(unittest.TestCase):
    def setUp(self):
        self.site=read_json(ROOT/'site.json');self.content=read_json(ROOT/'content.json')
        self.schema=Draft202012Validator(read_json(ROOT/'schemas/site.schema.json'))

    def test_unpublished_has_local_icons_but_no_wrong_canonical(self):
        head=Head(render(self.site,self.content)[0].decode())
        self.assertNotIn('canonical',head.links);self.assertNotIn('og:image',head.meta)
        self.assertNotIn('twitter:card',head.meta)
        self.assertEqual(len(head.links['icon']),2)
        for link in head.links['icon']+head.links['apple-touch-icon']:
            url=urlsplit(link['href']);self.assertFalse(url.scheme)
            self.assertTrue((ROOT/'dist'/unquote(url.path)).is_file());self.assertIn('v=',url.query)

    def test_subdirectory_absolute_metadata_and_text_escaping(self):
        site=copy.deepcopy(self.site);site['sharing']={'url':'https://example.com/birthday-site/',
            'title':'<title> & "quoted"','description':'Description <safe> & clear'}
        page=render(site,self.content)[0].decode();head=Head(page)
        self.assertNotIn('<title> & "quoted"',page)
        self.assertEqual(head.meta['og:title'],site['sharing']['title'])
        self.assertEqual(head.meta['twitter:description'],site['sharing']['description'])
        self.assertEqual(head.meta['og:url'],'https://example.com/birthday-site/')
        self.assertEqual(head.links['canonical'][0]['href'],head.meta['og:url'])
        self.assertTrue(head.meta['og:image'].startswith(head.meta['og:url']+'assets/branding/social-card.png?v='))
        self.assertEqual(head.meta['twitter:image'],head.meta['og:image'])
        self.assertEqual((head.meta['og:image:width'],head.meta['og:image:height']),('1200','630'))
        self.assertEqual(head.meta['og:image:type'],'image/png')
        self.assertEqual(head.meta['twitter:card'],'summary_large_image')

    def test_url_and_field_schema_parity(self):
        for url,valid in [('',True),('https://example.com/',True),('https://name.github.io/my-site/',True),
                          ('https://example.com/nested/site/',True),('http://example.com/',False),
                          ('https://example.com',False),('https://example.com/index.html',False),
                          ('https://example.com/?x=1',False),('https://example.com/#home',False),
                          ('https://user:secret@example.com/',False),('javascript:alert(1)',False),
                          ('https://example.com/../',False),('https://example.com/ space/',False),
                          ('https://example.com/\n',False),(None,False)]:
            with self.subTest(url=url):
                site={**self.site,'sharing':{'url':url}}
                self.assertEqual(self.schema.is_valid(site),valid)
                if valid:validate_site(site)
                else:
                    with self.assertRaises(ValueError):validate_site(site)
        for group,value in [('icons',{'fallback':'https://example.com/icon.png'}),
                            ('sharing',{'image':'assets/../site.json'}),('sharing',{'title':False}),
                            ('sharing',{'unknown':'value'})]:
            site={**self.site,group:value};self.assertFalse(self.schema.is_valid(site))
            with self.assertRaises(ValueError):validate_site(site)

    def test_generated_assets_are_real_images_and_ascii_font_guard(self):
        files=branding_files(self.site,'A little collection of days worth keeping.')
        self.assertIn(b'<svg',files['favicon.svg'])
        for name,size in [('favicon-32.png',(32,32)),('apple-touch-icon.png',(180,180)),('social-card.png',(1200,630))]:
            with Image.open(io.BytesIO(files[name])) as im:self.assertEqual(im.size,size);im.verify()
        site={**self.site,'sharing':{'title':'生日快乐'}}
        with self.assertRaisesRegex(ValueError,'--font'):branding_files(site,'A birthday letter')


class SharingWorkflow(unittest.TestCase):
    setUp=workflow.Workflow.setUp
    tearDown=workflow.Workflow.tearDown
    read=workflow.Workflow.read
    write=workflow.Workflow.write
    run_script=workflow.Workflow.run_script

    def test_asset_missing_or_wrong_size_rejects_before_write(self):
        before=(self.root/'dist/index.html').read_bytes()
        site=self.read('site.json');site['icons']={'fallback':'assets/missing.png'};self.write('site.json',site)
        self.assertIn('site.icons.fallback',self.run_script('build.py',ok=False).stderr)
        site['icons']={'fallback':'assets/demo/choice-1.png'};self.write('site.json',site)
        self.assertIn('32 x 32',self.run_script('build.py',ok=False).stderr)
        self.assertEqual((self.root/'dist/index.html').read_bytes(),before)

    def test_regenerate_requires_opt_in_backups_and_cache_version_changes(self):
        site=self.read('site.json');site['sharing']={'url':'https://example.com/site/'};self.write('site.json',site)
        self.run_script('build.py');before=Head((self.root/'dist/index.html').read_text(encoding='utf-8'))
        card=self.root/'dist/assets/branding/social-card.png';old=card.read_bytes()
        self.run_script('make_branding.py',ok=False);self.assertEqual(card.read_bytes(),old)
        self.run_script('make_branding.py','--replace','--subtitle','Updated birthday moments')
        self.assertTrue(any(p.read_bytes()==old for p in (self.root/'.backups').glob('*/dist/assets/branding/social-card.png')))
        self.run_script('build.py');after=Head((self.root/'dist/index.html').read_text(encoding='utf-8'))
        self.assertNotEqual(before.meta['og:image'],after.meta['og:image'])
        self.run_script('build.py','--check')


if __name__=='__main__':unittest.main()
