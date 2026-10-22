"""Contract compatibility, schema/runtime parity and write prevention."""
import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from data_validation import validate_site, validate_content, validate_import_options
from project_lib import validate, render, read_json
import test_workflow as workflow


class DataContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = {name: read_json(ROOT/(name+'.json')) for name in ('site', 'content', 'import-options')}
        cls.validators = {}
        for name in cls.samples:
            schema = read_json(ROOT/'schemas'/(name+'.schema.json'))
            Draft202012Validator.check_schema(schema)
            cls.validators[name] = Draft202012Validator(schema)

    def check(self, name, value, expected):
        schema_ok = self.validators[name].is_valid(value)
        runtime_ok = True
        try:
            {'site': validate_site, 'content': validate_content,
             'import-options': validate_import_options}[name](value)
        except ValueError:
            runtime_ok = False
        self.assertEqual((schema_ok, runtime_ok), (expected, expected), repr(value)[:500])

    def case(self, name, path, value, expected=False):
        data = copy.deepcopy(self.samples[name]); target = data
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        self.check(name, data, expected)

    def test_schema_and_legacy_examples(self):
        for name, original in self.samples.items():
            with self.subTest(name=name):
                self.check(name, original, True)
                legacy = {k: v for k, v in original.items() if k not in ('$schema', 'schemaVersion')}
                self.check(name, legacy, True)
                legacy['customMetadata'] = {'author': 'fictional', 'tags': []}
                self.check(name, legacy, True)
                for invalid in (None, [], '', False):
                    self.check(name, invalid, False)
                for version in (0, 2, '1', True, None, 1.5):
                    self.case(name, ['schemaVersion'], version)
                self.case(name, ['schemaVersion'], 1.0, True)
                self.case(name, ['$schema'], 17)

    def test_site_boundaries_and_dates(self):
        for field, maximum in [('recipient', 32), ('title', 48), ('description', 160), ('letterLine', 48), ('letterDescription', 100)]:
            for value in (None, False, 2, [], {}, '', ' \t', '夏'*(maximum+1)):
                with self.subTest(field=field, value=value):
                    self.case('site', [field], value)
            self.case('site', [field], '夏'*maximum, True)
        for value in (True, '2026', 1899, 2201, 2026.5):
            self.case('site', ['year'], value)
        for value in (1900, 2200, 2026.0):
            self.case('site', ['year'], value, True)
        for value in ('UPPER', '', 'a'*65, 'a\n', 4, None):
            self.case('site', ['id'], value)
        for date in ('02/30', '04/31', '13/01', '00/01', '01/00', '6/15', '06.15', '06/15\n', False):
            self.case('site', ['welcomeDate'], date)
            self.case('content', ['memories', 0, 'date'], date)
        for date in ('02/29', '12/31', '06/15'):
            self.case('site', ['welcomeDate'], date, True)
            self.case('content', ['memories', 0, 'date'], date, True)

    def test_content_types_and_paths(self):
        for path in [('memories',), ('collage',), ('quiz',), ('memories', 0), ('memories', 0, 'photos'), ('memories', 0, 'photos', 0), ('collage', 0), ('quiz', 0), ('quiz', 0, 'options'), ('quiz', 1, 'options', 0), ('quiz', 1, 'explanationImages'), ('quiz', 1, 'explanationImages', 0)]:
            for value in (None, False, 6):
                with self.subTest(path=path, value=value):
                    self.case('content', path, value)
        photo = ['memories', 0, 'photos', 0]
        for value in ('https://example.com/a.jpg', '/assets/a.jpg', 'assets/../a', 'assets/x/../../a', 'assets/./a', 'assets//a', 'assets/a?x=1', 'assets/a#x', 'assets/%2e%2e/a', 'assets/a\\b', 'assets/a\n', 'assets/'):
            self.case('content', [*photo, 'src'], value)
        self.case('content', [*photo, 'src'], 'assets/中文 name/a.png', True)
        for field in ('caption', 'alt'):
            self.case('content', [*photo, field], 4)
        for field in ('preview', 'original', 'poster'):
            self.case('content', [*photo, field], None)
        for dimension in (0, -1, True, '10', 1.2):
            self.case('content', ['collage', 0, 'width'], dimension)
        self.case('content', ['collage', 0, 'width'], 1.0, True)
        for value in (4, -1, True, '0', 0.1):
            self.case('content', ['quiz', 0, 'answer'], value)
        for value in (0, 3, None, 1.0):
            self.case('content', ['quiz', 0, 'answer'], value, True)
        self.case('content', ['quiz', 0, 'options'], ['a']*3)
        self.case('content', ['quiz', 0, 'options'], ['a']*5)
        self.case('content', ['quiz', 0, 'options', 0], ' ')
        self.case('content', ['quiz', 0, 'explanation'], None)
        self.case('content', ['quiz', 0, 'pendingImages'], 'true')
        self.case('content', ['quiz', 0, 'pendingImages'], True, True)
        self.case('content', ['memories', 0, 'photos', 2, 'src'], 'assets/video.mp4')
        for media in self.samples['content']['memories'][0]['photos']:
            for field in ('type', 'src', 'thumb') + (('poster',) if media['type']=='live' else ()):
                value = copy.deepcopy(media); del value[field]
                self.case('content', ['memories', 0, 'photos', 0], value)

    def test_import_options(self):
        for value in ({}, {'live_dates': [], 'sequence_overrides': {}}, {'live_dates': ['02.29'], 'sequence_overrides': {'collages': {'my file.png': 3.0}}}):
            self.check('import-options', value, True)
        for value in ({'live_dates': ['06/15']}, {'live_dates': ['02.30']}, {'live_dates': ['06.15', '06.15']}, {'sequence_overrides': []}, {'sequence_overrides': {'06.15': []}}, {'sequence_overrides': {'06.15': {'x': False}}}, {'sequence_overrides': {'06.15': {'x': 0}}}, {'sequence_overrides': {'06.15': {'x': '1'}}}, {'sequence_overrides': {'06.15': {'../x': 1}}}, {'sequence_overrides': {'': {'x': 1}}}):
            self.check('import-options', value, False)

    def test_cross_references_and_legacy_render(self):
        site = copy.deepcopy(self.samples['site']); content = copy.deepcopy(self.samples['content'])
        legacy = copy.deepcopy({k:v for k,v in content.items() if k not in ('$schema','schemaVersion')})
        self.assertEqual(render(site, content), render(site, legacy))
        self.assertEqual(render(site, content), ((ROOT/'dist/index.html').read_bytes(), (ROOT/'dist/content.js').read_bytes()))
        content['memories'].append(copy.deepcopy(content['memories'][0]))
        with self.assertRaisesRegex(ValueError, r'content.memories\[2\].date'):
            validate(site, content)
        with self.assertRaisesRegex(ValueError, 'site.welcomeDate'):
            validate({**site, 'welcomeDate': '01/01'}, legacy)
        content = copy.deepcopy(legacy); content['memories'][0]['photos'][0]['preview']='assets/missing.webp'
        with self.assertRaisesRegex(ValueError, r'photos\[0\].preview'):
            validate(site, content)
        validate({**site, 'welcomeDate': None}, {'memories': [], 'collage': [], 'quiz': []})


class DataWorkflow(unittest.TestCase):
    setUp = workflow.Workflow.setUp
    tearDown = workflow.Workflow.tearDown
    run_script = workflow.Workflow.run_script
    read = workflow.Workflow.read
    write = workflow.Workflow.write

    def test_read_only_validation_and_preflight(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.run_script('validate_data.py')
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        options = self.read('import-options.json'); options['live_dates'] = ['02.30']; self.write('import-options.json', options)
        for args in [('validate_data.py',), ('build.py',), ('import-materials.py', '--date', '06.15'), ('import-collages.py',)]:
            result=self.run_script(*args, ok=False)
            self.assertIn('import-options.live_dates[0]', result.stderr)
        for name in ('content.json', 'dist/content.js', 'dist/index.html'):
            self.assertEqual(before[name], (self.root/name).read_bytes())
        self.assertFalse((self.root/'.work').exists()); self.assertFalse((self.root/'.backups').exists())

    def test_metadata_survives_import(self):
        content=self.read('content.json'); content['customMetadata']={'author':'fictional'}
        content['memories'][0]['customAlbum']={'theme':'sea'}; self.write('content.json',content)
        self.run_script('import-materials.py','--date','06.15'); after=self.read('content.json')
        for key in ('$schema','schemaVersion','customMetadata'):
            self.assertEqual(content[key], after[key])
        self.assertEqual(content['memories'][0]['customAlbum'], after['memories'][0]['customAlbum'])

    def test_strict_json(self):
        for raw in ('{"live_dates":[],"live_dates":[]}', '{"custom":NaN}', '{"custom":Infinity}', '{"custom":1e999}'):
            (self.root/'import-options.json').write_text(raw, encoding='utf-8')
            self.run_script('validate_data.py', ok=False)


if __name__ == '__main__':
    unittest.main()
