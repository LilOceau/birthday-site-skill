"""Build configured HTML/content without rewriting hand-maintained JS/CSS/assets."""
import argparse
from project_lib import ROOT,load_configuration,render,atomic_write,backup

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Validate and require generated files to be up to date')
    args=parser.parse_args()
    site,content,_=load_configuration()
    page,js=render(site,content)
    outputs={ROOT/'dist/index.html':page,ROOT/'dist/content.js':js}
    changed=[path for path,data in outputs.items() if not path.is_file() or path.read_bytes()!=data]
    if args.check:
        if changed:raise ValueError('Run python build.py; generated files are stale: '+', '.join(p.name for p in changed))
        print('PASS: configuration, local assets and generated files are consistent.');return
    if changed:
        saved=backup(changed)
        for path in changed:atomic_write(path,outputs[path])
        print('Built dist; previous generated files saved in',saved.relative_to(ROOT))
    else:print('Already up to date.')

if __name__=='__main__':main()
