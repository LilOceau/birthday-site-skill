"""Build the repository's fictional public demo in a new directory; see 操作说明.txt."""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'birthday-site-workflow/assets/project'


def build_demo(output, url):
    output=output.resolve()
    if output.exists() or output.is_relative_to(TEMPLATE.resolve()):
        raise ValueError('Choose a new output directory outside the template; nothing was overwritten')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='demo-build-',dir=output.parent) as temporary:
        project=pathlib.Path(temporary)/'project'
        shutil.copytree(TEMPLATE,project,ignore=shutil.ignore_patterns('.local','.work','.backups','__pycache__','.venv','node_modules','release','manifests'))
        site=json.loads((project/'site.json').read_text(encoding='utf-8'))
        site['id']='birthday-skill-public-demo'
        site.setdefault('sharing',{}).update(url=url,title='Birthday Site · 可交互的虚构演示',
            description='体验信封开场、日期相册、Live、拼贴与问答。人物和素材均为虚构，附 Windows 替换教程。')
        site.setdefault('labels',{}).update(headerRight='FICTIONAL DEMO · 示例素材',footerMessage='Happy birthday. · 虚构示例')
        (project/'site.json').write_text(json.dumps(site,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        subprocess.run([sys.executable,'build.py'],cwd=project,check=True)
        subprocess.run([sys.executable,'build.py','--check'],cwd=project,check=True)
        page=project/'dist/index.html'
        text=page.read_text(encoding='utf-8')
        notice='''<p id="demoNotice" style="font:14px/1.8 sans-serif;margin:24px auto 0;max-width:620px;padding:0 16px">这是公开的虚构演示，不含私人照片。点击“带我看一段回忆”或输入 0822 体验相册。<br><a href="https://github.com/LilOceau/birthday-site-skill">获取源码与 Skill</a> · <a href="https://github.com/LilOceau/birthday-site-skill/blob/main/birthday-site-workflow/assets/project/docs/replacement-guide.md">Windows 替换教程</a></p>'''
        if text.count('</footer>')!=1:raise ValueError('Demo footer structure changed')
        page.write_text(text.replace('</footer>',notice+'</footer>'),encoding='utf-8',newline='\n')
        shutil.copytree(project/'dist',output)
    (output/'.nojekyll').write_bytes(b'')
    print(json.dumps({'output':str(output),'url':url,'files':len([p for p in output.rglob('*') if p.is_file()]),
                      'indexSha256':hashlib.sha256((output/'index.html').read_bytes()).hexdigest()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=pathlib.Path)
    parser.add_argument('--url',required=True,help='Actual HTTPS directory URL, ending with /')
    args=parser.parse_args();build_demo(args.output,args.url)
