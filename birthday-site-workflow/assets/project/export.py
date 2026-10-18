"""Validate and package dist only. Never includes source media, backups or credentials."""
import argparse
import pathlib
import zipfile
from project_lib import ROOT,read_json,render

def export(destination):
    destination=destination.resolve()
    if destination.exists() or destination.is_relative_to(ROOT/'dist'):
        raise ValueError('Choose a new output file outside dist')
    page,js=render(read_json(ROOT/'site.json'),read_json(ROOT/'content.json'))
    if page!=(ROOT/'dist/index.html').read_bytes() or js!=(ROOT/'dist/content.js').read_bytes():
        raise ValueError('Run python build.py before exporting')
    files=sorted((ROOT/'dist').rglob('*'))
    if any(p.is_symlink() or not p.resolve().is_relative_to(ROOT/'dist') for p in files):
        raise ValueError('Linked deployment files require review')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.is_file():archive.write(path,path.relative_to(ROOT/'dist').as_posix())
    print(f'Created {destination}')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=pathlib.Path)
    export(parser.parse_args().output)
