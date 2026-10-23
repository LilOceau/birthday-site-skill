"""Read-only birthday-site inventory; output must be outside the site."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import pathlib
import re
import subprocess
import urllib.parse


def css_references(text):
    pattern = r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^\s)]*))\s*\)'''
    return [a or b or c for a,b,c in re.findall(pattern,text,re.I)]


def html_references(text):
    class References(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.references=[];self.in_style=False
        def handle_starttag(self,tag,attrs):
            if tag=='style':self.in_style=True
            for key,value in attrs:
                if key in ('src','href') and value:self.references.append(value)
                if key=='style' and value:self.references.extend(css_references(value))
        def handle_endtag(self,tag):
            if tag=='style':self.in_style=False
        def handle_data(self,data):
            if self.in_style:self.references.extend(css_references(data))
    parser=References();parser.feed(text);parser.close()
    return parser.references


def inspect(site):
    site = site.resolve(strict=True)
    dist = site / 'dist'
    if not (site/'import-materials.py').is_file() or not (dist/'content.js').is_file():
        raise ValueError('Expected existing birthday site with import-materials.py and dist/content.js')
    # Existing project content is evaluated in a context without Node APIs.
    js = "const fs=require('fs'),vm=require('vm');const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c,{timeout:1000});console.log(JSON.stringify(c.window.BIRTHDAY_CONTENT));"
    content = json.loads(subprocess.check_output(['node','-e',js,str(dist/'content.js')],text=True,encoding='utf-8'))
    references = set()
    def walk(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ('src','thumb','poster','preview','original') and isinstance(item,str): references.add(item)
                elif key=='explanationImages' and isinstance(item,list):
                    references.update(x for x in item if isinstance(x,str))
                walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    walk(content)
    files = {}
    for p in sorted(dist.rglob('*')):
        if p.is_symlink(): raise ValueError('Symlink in dist requires separate review')
        if p.is_file():
            with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            files[p.relative_to(dist).as_posix()]={'bytes':p.stat().st_size,'sha256':digest}
            if p.suffix.lower() in ('.html','.css'):
                text=p.read_text(encoding='utf-8')
                found=html_references(text) if p.suffix.lower()=='.html' else css_references(text)
                for ref in found:
                    if not ref.startswith(('#','data:')):
                        references.add(urllib.parse.urljoin(p.relative_to(dist).as_posix(),ref))
    missing, external, invalid = [], [], []
    for ref in sorted(references):
        url=urllib.parse.urlsplit(ref)
        if url.scheme or url.netloc: external.append(ref);continue
        path=urllib.parse.unquote(url.path).lstrip('/')
        if not path:continue
        target=(dist/path).resolve()
        if not target.is_relative_to(dist.resolve()):invalid.append(ref)
        elif not target.is_file():missing.append(ref)
    photos=[p for a in content.get('memories',[]) for p in a.get('photos',[])]
    counts={'albums':len(content.get('memories',[])),'media':len(photos),'live':sum(p.get('type')=='live' for p in photos),'videos':sum(p.get('type')=='video' for p in photos),'collages':len(content.get('collage',[])),'quiz':len(content.get('quiz',[]))}
    return {'counts':counts,'distFiles':len(files),'distBytes':sum(x['bytes'] for x in files.values()),'missingReferences':missing,'invalidReferences':invalid,'externalReferences':external,'files':files}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site',type=pathlib.Path,required=True)
    parser.add_argument('--output',type=pathlib.Path)
    args=parser.parse_args()
    if args.output and args.output.resolve().is_relative_to(args.site.resolve()):
        parser.error('--output must be outside the site')
    report=inspect(args.site)
    if args.output:
        if args.output.exists():parser.error('Output exists; choose a new report path')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
    return 1 if report['missingReferences'] or report['invalidReferences'] else 0


if __name__=='__main__':raise SystemExit(main())
