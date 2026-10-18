"""Create a self-contained birthday site from the bundled template. Never overwrite."""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import uuid

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=pathlib.Path)
    parser.add_argument('--recipient',default='小夏')
    parser.add_argument('--title',default='A day for you')
    args=parser.parse_args()
    destination=args.destination.resolve()
    template=pathlib.Path(__file__).resolve().parents[1]/'assets/project'
    if destination.exists():parser.error('Destination exists; choose a new directory. Nothing was overwritten.')
    if destination.is_relative_to(template):parser.error('Choose a destination outside the bundled template')
    if not args.recipient.strip() or len(args.recipient)>32 or not args.title.strip() or len(args.title)>48:parser.error('Recipient must be 1..32 chars, title 1..48 chars')
    shutil.copytree(template,destination,ignore=shutil.ignore_patterns('__pycache__','.venv','node_modules','.work','.backups','.local','manifests','release'))
    config=json.loads((destination/'site.json').read_text(encoding='utf-8'))
    config.update(id='birthday-'+uuid.uuid4().hex[:12],recipient=args.recipient,title=args.title)
    (destination/'site.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(destination/'build.py')],check=True,cwd=destination)
    print('Created:',destination)
    print('Preview: cd to that directory, then run python serve.py')

if __name__=='__main__':main()
