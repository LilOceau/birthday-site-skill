"""Shared validation, snapshots and atomic writes for the portable project."""
import datetime
import hashlib
import html
import json
import math
import pathlib
import re
import uuid
from data_validation import (ASSET_PATTERN, PATH_FIELDS, validate_site,
                             validate_content, validate_import_options)

ROOT = pathlib.Path(__file__).resolve().parent

def read_json(path):
    def reject_constant(value):
        raise ValueError(f'{path.name}: non-JSON numeric value {value}')
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f'{path.name}: numeric value exceeds finite range')
        return result
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'{path.name}: duplicate JSON key {key!r}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8-sig'),
                      parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_keys)

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)

def backup(paths):
    saved = ROOT/'.backups'/ (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    for path in paths:
        if path.is_file():
            rel=path.resolve().relative_to(ROOT)
            target=saved/rel; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(path.read_bytes())
    return saved

def asset(value):
    if not isinstance(value, str) or not re.fullmatch(ASSET_PATTERN, value):
        raise ValueError(f'Expected canonical local assets/ path: {value!r}')
    path=(ROOT/'dist'/value).resolve()
    if not path.is_relative_to((ROOT/'dist/assets').resolve()) or not path.is_file():
        raise ValueError(f'Missing or escaping asset: {value!r}')
    return path

def valid_date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{2}/\d{2}',value):return False
    try: datetime.datetime.strptime('2000/'+value,'%Y/%m/%d');return True
    except ValueError:return False

def validate(site, content):
    validate_site(site)
    validate_content(content)
    def references(value, path):
        for key in PATH_FIELDS:
            if key in value:
                try:
                    asset(value[key])
                except ValueError as error:
                    raise ValueError(f'{path}.{key}: {error}') from error
    seen = set()
    for i, album in enumerate(content['memories']):
        path = f'content.memories[{i}]'
        if album['date'] in seen:
            raise ValueError(f"{path}.date: duplicate album date {album['date']}")
        seen.add(album['date'])
        for j, photo in enumerate(album['photos']):
            references(photo, f'{path}.photos[{j}]')
    welcome = site.get('welcomeDate')
    if welcome is not None and welcome not in seen:
        raise ValueError('site.welcomeDate: must match an album or be null/omitted')
    for i, piece in enumerate(content['collage']):
        references(piece, f'content.collage[{i}]')
    for i, question in enumerate(content['quiz']):
        for j, option in enumerate(question['options']):
            if isinstance(option, dict):
                references(option, f'content.quiz[{i}].options[{j}]')
        for j, image in enumerate(question.get('explanationImages', [])):
            references(image, f'content.quiz[{i}].explanationImages[{j}]')


def load_configuration():
    site = read_json(ROOT/'site.json')
    content = read_json(ROOT/'content.json')
    options = read_json(ROOT/'import-options.json')
    validate_import_options(options)
    validate(site, content)
    return site, content, options


def render(site, content):
    validate(site,content)
    # Content hashes invalidate videos after any byte replacement, not just a date stamp.
    hasher=hashlib.sha256()
    for path in sorted((ROOT/'dist/assets').rglob('*')):
        if path.is_file():hasher.update(path.relative_to(ROOT/'dist').as_posix().encode());hasher.update(bytes.fromhex(digest(path)))
    public_content={key:value for key,value in content.items() if key not in ('$schema','schemaVersion')}
    payload={**public_content,'siteId':site['id'],'recipient':site['recipient'],'hintYear':int(site['year']),'welcomeDate':site.get('welcomeDate'),'mediaVersion':hasher.hexdigest()[:16]}
    js='/* Generated from content.json and site.json by build.py. */\nwindow.BIRTHDAY_CONTENT = '+json.dumps(payload,ensure_ascii=False,indent=2)+';\n'
    # Version HTML dependencies whenever code, config or media changes.
    hasher.update(js.encode())
    for path in sorted((ROOT/'dist').iterdir()):
        if path.suffix in ['.css','.js'] and path.name!='content.js':hasher.update(path.read_bytes())
    version=hasher.hexdigest()[:16]
    values={'VERSION':version,'TITLE':site['title'],'RECIPIENT':site['recipient'],'YEAR':str(int(site['year'])),'DESCRIPTION':site['description'],'LETTER_LINE':site['letterLine'],'LETTER_DESCRIPTION':site['letterDescription'],'COLLAGE_COVER':content['collage'][0]['preview'] if content['collage'] else 'assets/demo/sea.png'}
    page=(ROOT/'index.template.html').read_text(encoding='utf-8')
    page=re.sub(r'\{\{([A-Z_]+)\}\}',lambda m:html.escape(values[m[1]],quote=True),page)
    return page.encode('utf-8'),js.encode('utf-8')

def commit_content(content):
    page,js=render(read_json(ROOT/'site.json'),content)
    saved=backup([ROOT/'content.json',ROOT/'dist/index.html',ROOT/'dist/content.js'])
    write_json(ROOT/'content.json',content)
    atomic_write(ROOT/'dist/index.html',page);atomic_write(ROOT/'dist/content.js',js)
    return saved
