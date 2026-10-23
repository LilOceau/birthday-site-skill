"""Optional configuration: compatibility, validation, rendering and no writes on failure."""
import copy
import json
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from jsonschema import Draft202012Validator
from configuration import DEFAULTS,resolve_options,schema_properties
from data_validation import validate_site
from project_lib import read_json,render,validate
import test_workflow as workflow


class Configuration(unittest.TestCase):
    def setUp(self):
        self.site=read_json(ROOT/'site.json');self.content=read_json(ROOT/'content.json')
        self.schema=Draft202012Validator(read_json(ROOT/'schemas/site.schema.json'))

    def test_old_configuration_defaults_and_schema_sync(self):
        legacy={k:v for k,v in self.site.items() if k not in DEFAULTS}
        self.assertEqual(resolve_options(legacy),DEFAULTS)
        self.assertEqual(render(legacy,self.content),render(self.site,self.content))
        for key,value in schema_properties().items():
            self.assertEqual(self.schema.schema['properties'][key],value)
        sample=read_json(ROOT/'site.custom.example.json')
        self.schema.validate(sample);validate(sample,self.content)

    def test_valid_partial_configuration_and_types(self):
        cases=[('theme',{'ink':'#123ABC'}),('assets',{'motifAlt':''}),('sections',{'quiz':False}),
               ('behavior',{'hintAfterAttempts':0,'persistProgress':False}),
               ('behavior',{'hintAfterAttempts':3.0,'openingMotion':'reduced'}),
               ('labels',{'quizThanks':'Thank you, {recipient}!','datesTitle':'Line 1\nLine 2'}),
               ('labels',{'quizCorrect':'','quizScore':'{score}/{total}'})]
        for group,value in cases:
            with self.subTest(group=group,value=value):
                site={**self.site,group:value};self.schema.validate(site);validate_site(site)
                resolved=resolve_options(site)
                for key,item in value.items():self.assertEqual(resolved[group][key],item)
                self.assertEqual(resolved['assets']['background'],DEFAULTS['assets']['background'])

    def test_invalid_configuration_parity(self):
        cases=[('theme',None),('theme',{'ink':'red'}),('theme',{'ink':'#fff'}),
               ('theme',{'paper':'#123456;display:none'}),('theme',{'colour':'#123456'}),
               ('assets',{'background':'https://example.com/a.png'}),('assets',{'motif':None}),
               ('assets',{'texture':'assets/../private.png'}),('sections',{'quiz':'false'}),
               ('sections',{'unknown':True}),('behavior',{'persistProgress':0}),
               ('behavior',{'hintAfterAttempts':True}),('behavior',{'hintAfterAttempts':11}),
               ('behavior',{'hintAfterAttempts':-1}),('behavior',{'hintAfterAttempts':1.5}),
               ('behavior',{'openingMotion':'always'}),('labels',{'quizScore':'{wrong}'}),
               ('labels',{'quizThanks':'{recipient'}),('labels',{'quizThanks':'{{recipient}}'}),
               ('labels',{'footerMessage':'a'*501}),('labels',{'typo':'value'})]
        for group,value in cases:
            with self.subTest(group=group,value=value):
                site={**self.site,group:value}
                self.assertFalse(self.schema.is_valid(site))
                with self.assertRaises(ValueError):validate_site(site)

    def test_render_escaping_assets_and_visibility(self):
        site=copy.deepcopy(self.site)
        site['labels'].update(quizWelcome='<script>alert(1)</script> {recipient}',datesTitle='A < B\nC & D')
        site['sections'].update(dates=False,collage=False)
        page,js=render(site,self.content);html=page.decode()
        self.assertNotIn('<script>alert(1)</script>',html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',html)
        self.assertIn('A &lt; B<br>C &amp; D',html)
        self.assertIn('href="#dates" hidden',html);self.assertIn('<section hidden id="collage"',html)
        self.assertNotIn('{{',html)
        payload=json.loads(js.decode().split(' = ',1)[1].removesuffix(';\n'))
        self.assertEqual(payload['config']['sections']['quiz'],True)
        self.assertEqual(payload['memories'],self.content['memories'])
        site['assets']['background']='assets/missing-background.png'
        with self.assertRaisesRegex(ValueError,'site.assets.background'):render(site,self.content)


class ConfigurationWorkflow(unittest.TestCase):
    setUp=workflow.Workflow.setUp
    tearDown=workflow.Workflow.tearDown
    read=workflow.Workflow.read
    write=workflow.Workflow.write
    run_script=workflow.Workflow.run_script

    def test_bad_configuration_prevents_build_and_import(self):
        before={name:(self.root/name).read_bytes() for name in ('content.json','dist/index.html','dist/content.js')}
        site=self.read('site.json');site['behavior']={'liveAutoplay':'false'};self.write('site.json',site)
        for args in [('build.py',),('import-materials.py','--date','06.15'),('import-collages.py',)]:
            self.assertIn('site.behavior.liveAutoplay',self.run_script(*args,ok=False).stderr)
        for name,data in before.items():self.assertEqual((self.root/name).read_bytes(),data)
        self.assertFalse((self.root/'.work').exists());self.assertFalse((self.root/'.backups').exists())


if __name__=='__main__':unittest.main()
