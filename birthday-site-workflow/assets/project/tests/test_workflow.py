"""Integration checks in disposable copies; never mutate the working site."""
import hashlib,json,os,pathlib,shutil,subprocess,sys,tempfile,unittest,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]

class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)/'site'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.work','.backups','.local','node_modules','.venv','__pycache__'))
    def tearDown(self):self.temp.cleanup()
    def run_script(self,*args,ok=True):
        result=subprocess.run([sys.executable,*args],cwd=self.root,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode==0,ok,result.stdout+result.stderr);return result
    def read(self,name):return json.loads((self.root/name).read_text(encoding='utf-8'))
    def write(self,name,value):(self.root/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    def test_build_escapes_text_and_rejects_bad_asset(self):
        site=self.read('site.json');site['recipient']='<script>x</script>';self.write('site.json',site)
        self.run_script('build.py');self.run_script('build.py','--check')
        self.assertIn('&lt;script&gt;x&lt;/script&gt;',(self.root/'dist/index.html').read_text(encoding='utf-8'))
        before=(self.root/'dist/content.js').read_bytes();content=self.read('content.json')
        content['memories'][0]['photos'][0]['src']='assets/../../site.json';self.write('content.json',content)
        self.run_script('build.py',ok=False);self.assertEqual(before,(self.root/'dist/content.js').read_bytes())
    def test_incremental_import_preserves_other_sections_and_sources(self):
        before=self.read('content.json')
        hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'materials').rglob('*') if p.is_file()}
        self.run_script('import-materials.py','--date','06.15');after=self.read('content.json')
        for key in ['quiz','collage']:self.assertEqual(before[key],after[key])
        self.assertEqual(before['memories'][1],after['memories'][1]);self.assertEqual(before['memories'][0]['title'],after['memories'][0]['title'])
        self.assertEqual(hashes,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'materials').rglob('*') if p.is_file()})
        self.assertTrue(list((self.root/'.backups').glob('*/content.json')))
        self.assertTrue(list((self.root/'manifests').glob('*.json')))
        self.run_script('build.py','--check')
    def test_duplicate_sequence_leaves_content_unchanged(self):
        source=self.root/'materials/photos/06.15';shutil.copy2(source/'01-seaside.png',source/'another-1.png')
        before=(self.root/'content.json').read_bytes();self.run_script('import-materials.py','--date','06.15',ok=False)
        self.assertEqual(before,(self.root/'content.json').read_bytes())
    def test_collage_import_preserves_albums_and_quiz(self):
        before=self.read('content.json');self.run_script('import-collages.py');after=self.read('content.json')
        for key in ['memories','quiz']:self.assertEqual(before[key],after[key])
        self.assertEqual([p['src'] for p in before['collage']],[p['src'] for p in after['collage']])
    def test_export_and_range_server(self):
        self.run_script('build.py');self.run_script('export.py',str(self.root/'release.zip'))
        with zipfile.ZipFile(self.root/'release.zip') as archive:
            self.assertIn('index.html',archive.namelist());self.assertNotIn('site.json',archive.namelist())
            self.assertFalse(any(name.startswith(('.backups','materials')) for name in archive.namelist()))
        self.run_script('export.py',str(self.root/'release.zip'),ok=False)
        server=subprocess.Popen([sys.executable,'serve.py','--port','0'],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        try:
            url=server.stdout.readline().strip().split('Preview: ')[1]
            media=self.read('content.json')['memories'][0]['photos'][2]['src']
            request=urllib.request.Request(url+'/'+media,headers={'Range':'bytes=0-31'})
            with urllib.request.urlopen(request,timeout=5) as result:
                self.assertEqual(result.status,206);self.assertEqual(len(result.read()),32)
            with urllib.request.urlopen(url+'/index.html',timeout=5) as result:self.assertIn(b'<!doctype html>',result.read().lower())
        finally:server.terminate();server.wait(timeout=5);server.stdout.close()

if __name__=='__main__':unittest.main()
