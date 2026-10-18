"""Shared validation, snapshots and atomic writes for the portable project."""
import datetime
import hashlib
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parent

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

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
    if not isinstance(value,str) or not value.startswith('assets/') or '\\' in value:
        raise ValueError(f'Expected local assets/ path: {value!r}')
    if any(x in value for x in ['?', '#', '\x00']) or ':' in value:
        raise ValueError(f'Unsupported asset path: {value!r}')
    path=(ROOT/'dist'/value).resolve()
    if not path.is_relative_to((ROOT/'dist/assets').resolve()) or not path.is_file():
        raise ValueError(f'Missing or escaping asset: {value!r}')
    return path

def valid_date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{2}/\d{2}',value):return False
    try: datetime.datetime.strptime('2000/'+value,'%Y/%m/%d');return True
    except ValueError:return False

def text(value, label, maximum=200):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:
        raise ValueError(f'{label} must be a nonempty string of at most {maximum} characters')
    return value

def validate(site, content):
    if not isinstance(site,dict) or not isinstance(content,dict):raise ValueError('Configuration must be objects')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',site.get('id','')):raise ValueError('site.id must be a lowercase slug')
    for key,maximum in [('recipient',32),('title',48),('description',160),('letterLine',48),('letterDescription',100)]:text(site.get(key),key,maximum)
    year=site.get('year')
    if type(year) is not int or not 1900<=year<=2200:raise ValueError('year must be 1900..2200')
    for key in ['memories','collage','quiz']:
        if not isinstance(content.get(key),list):raise ValueError(f'{key} must be a list')
    seen=set()
    for album in content['memories']:
        date=album.get('date')
        if not valid_date(date) or date in seen:raise ValueError(f'Invalid or duplicate album date: {date}')
        seen.add(date);text(album.get('title'), 'album title')
        if not isinstance(album.get('photos'),list) or not album['photos']:raise ValueError('Album must contain photos')
        for photo in album['photos']:
            if photo.get('type') not in ['image','live','video']:raise ValueError('Unknown media type')
            asset(photo.get('src'));asset(photo.get('thumb'))
            if photo.get('type') in ['live','video']:asset(photo.get('poster'))
            if photo.get('type')=='live' and not photo['src'].endswith('.live.mp4'):raise ValueError('Live requires .live.mp4')
            if photo.get('original'):asset(photo['original'])
    welcome=site.get('welcomeDate')
    if welcome is not None and welcome not in seen:raise ValueError('welcomeDate must match an album or be null')
    for piece in content['collage']:
        for key in ['src','preview','thumb']:asset(piece.get(key))
        for key in ['width','height']:
            if type(piece.get(key)) is not int or piece[key]<1:raise ValueError('Collage dimensions must be positive integers')
    for question in content['quiz']:
        text(question.get('question'),'question',1000)
        options=question.get('options')
        if not isinstance(options,list) or len(options)!=4:raise ValueError('Each question requires exactly four options')
        answer=question.get('answer')
        if answer is not None and (type(answer) is not int or answer not in range(4)):raise ValueError('answer must be 0..3 or null')
        for option in options:
            if isinstance(option,str):text(option,'option',500)
            elif isinstance(option,dict):
                text(option.get('label'),'option label',500);asset(option.get('src'));asset(option.get('preview'))
            else:raise ValueError('Invalid quiz option')
        for image in question.get('explanationImages',[]):asset(image.get('src'))

def render(site, content):
    validate(site,content)
    # Content hashes invalidate videos after any byte replacement, not just a date stamp.
    hasher=hashlib.sha256()
    for path in sorted((ROOT/'dist/assets').rglob('*')):
        if path.is_file():hasher.update(path.relative_to(ROOT/'dist').as_posix().encode());hasher.update(bytes.fromhex(digest(path)))
    payload={**content,'siteId':site['id'],'recipient':site['recipient'],'hintYear':site['year'],'welcomeDate':site.get('welcomeDate'),'mediaVersion':hasher.hexdigest()[:16]}
    js='/* Generated from content.json and site.json by build.py. */\nwindow.BIRTHDAY_CONTENT = '+json.dumps(payload,ensure_ascii=False,indent=2)+';\n'
    # Version HTML dependencies whenever code, config or media changes.
    hasher.update(js.encode())
    for path in sorted((ROOT/'dist').iterdir()):
        if path.suffix in ['.css','.js'] and path.name!='content.js':hasher.update(path.read_bytes())
    version=hasher.hexdigest()[:16]
    values={'VERSION':version,'TITLE':site['title'],'RECIPIENT':site['recipient'],'YEAR':str(site['year']),'DESCRIPTION':site['description'],'LETTER_LINE':site['letterLine'],'LETTER_DESCRIPTION':site['letterDescription'],'COLLAGE_COVER':content['collage'][0]['preview'] if content['collage'] else 'assets/demo/sea.png'}
    page=(ROOT/'index.template.html').read_text(encoding='utf-8')
    page=re.sub(r'\{\{([A-Z_]+)\}\}',lambda m:html.escape(values[m[1]],quote=True),page)
    return page.encode('utf-8'),js.encode('utf-8')

def commit_content(content):
    page,js=render(read_json(ROOT/'site.json'),content)
    saved=backup([ROOT/'content.json',ROOT/'dist/index.html',ROOT/'dist/content.js'])
    write_json(ROOT/'content.json',content)
    atomic_write(ROOT/'dist/index.html',page);atomic_write(ROOT/'dist/content.js',js)
    return saved
