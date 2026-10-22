"""Version 1 data contract. Standard-library checks; schemas also support editors.

Keep structural checks in sync with schemas/ via tests/test_data_contract.py.
File existence and relationships between records are checked by project_lib.
"""
import math
import re

DATE_PATTERN = r'^(?:(?:01|03|05|07|08|10|12)/(?:0[1-9]|[12][0-9]|3[01])|(?:04|06|09|11)/(?:0[1-9]|[12][0-9]|30)|02/(?:0[1-9]|1[0-9]|2[0-9]))$'
ASSET_PATTERN = r'^assets/(?!\.{1,2}(?:/|$))[^/\\:?#%\x00-\x1f]+(?:/(?!\.{1,2}(?:/|$))[^/\\:?#%\x00-\x1f]+)*$'
NAME_PATTERN = r'^(?!\.{1,2}$)[^/\\\x00-\x1f]+$'
PATH_FIELDS = ('src', 'thumb', 'preview', 'poster', 'original')


def fail(path, message):
    raise ValueError(f'{path}: {message}')


def object_value(value, path):
    if not isinstance(value, dict):
        fail(path, 'expected an object')


def required(value, keys, path):
    object_value(value, path)
    for key in keys:
        if key not in value:
            fail(f'{path}.{key}', 'required field is missing')


def string(value, path, maximum=None, nonempty=False, pattern=None):
    if not isinstance(value, str):
        fail(path, 'expected a string')
    if nonempty and not re.search(r'\S', value):
        fail(path, 'must contain non-whitespace text')
    if maximum is not None and len(value) > maximum:
        fail(path, f'maximum length is {maximum} characters')
    if pattern and not re.fullmatch(pattern, value):
        fail(path, 'invalid format')


def integer(value, path, minimum=None, maximum=None):
    # JSON Schema defines 1 and 1.0 as the same integral number; bool is not one.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(path, 'expected an integer')
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        fail(path, 'expected a finite integer')
    if minimum is not None and value < minimum:
        fail(path, f'minimum is {minimum}')
    if maximum is not None and value > maximum:
        fail(path, f'maximum is {maximum}')


def array(value, path, minimum=0, maximum=None):
    if not isinstance(value, list):
        fail(path, 'expected an array')
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        fail(path, f'invalid number of items (minimum {minimum}, maximum {maximum})')


def metadata(value, path):
    object_value(value, path)
    if '$schema' in value:
        string(value['$schema'], f'{path}.$schema', nonempty=True)
    if 'schemaVersion' in value:
        integer(value['schemaVersion'], f'{path}.schemaVersion', 1, 1)


def paths(value, path):
    for key in PATH_FIELDS:
        if key in value:
            string(value[key], f'{path}.{key}', pattern=ASSET_PATTERN)
    for key in ('caption', 'alt'):
        if key in value:
            string(value[key], f'{path}.{key}')


def validate_site(site):
    metadata(site, 'site')
    required(site, ('id', 'recipient', 'title', 'year', 'description', 'letterLine', 'letterDescription'), 'site')
    string(site['id'], 'site.id', pattern=r'[a-z0-9][a-z0-9-]{0,63}')
    for key, maximum in [('recipient', 32), ('title', 48), ('description', 160), ('letterLine', 48), ('letterDescription', 100)]:
        string(site[key], f'site.{key}', maximum, nonempty=True)
    integer(site['year'], 'site.year', 1900, 2200)
    if site.get('welcomeDate') is not None:
        string(site['welcomeDate'], 'site.welcomeDate', pattern=DATE_PATTERN)


def validate_content(content):
    metadata(content, 'content')
    required(content, ('memories', 'collage', 'quiz'), 'content')
    for key in ('memories', 'collage', 'quiz'):
        array(content[key], f'content.{key}')
    for i, album in enumerate(content['memories']):
        path = f'content.memories[{i}]'
        required(album, ('date', 'title', 'photos'), path)
        string(album['date'], path+'.date', pattern=DATE_PATTERN)
        string(album['title'], path+'.title', 200, nonempty=True)
        array(album['photos'], path+'.photos', 1)
        for j, photo in enumerate(album['photos']):
            media = f'{path}.photos[{j}]'
            required(photo, ('type', 'src', 'thumb'), media)
            if photo['type'] not in ('image', 'live', 'video'):
                fail(media+'.type', 'expected image, live or video')
            if photo['type'] in ('live', 'video'):
                required(photo, ('poster',), media)
            paths(photo, media)
            if photo['type'] == 'live' and not photo['src'].endswith('.live.mp4'):
                fail(media+'.src', 'Live requires a .live.mp4 path')
    for i, piece in enumerate(content['collage']):
        path = f'content.collage[{i}]'
        required(piece, ('src', 'preview', 'thumb', 'width', 'height'), path)
        paths(piece, path)
        for key in ('width', 'height'):
            integer(piece[key], path+'.'+key, 1)
    for i, question in enumerate(content['quiz']):
        path = f'content.quiz[{i}]'
        required(question, ('question', 'options'), path)
        string(question['question'], path+'.question', 1000, nonempty=True)
        array(question['options'], path+'.options', 4, 4)
        if question.get('answer') is not None:
            integer(question['answer'], path+'.answer', 0, 3)
        if 'explanation' in question:
            string(question['explanation'], path+'.explanation')
        if 'pendingImages' in question and type(question['pendingImages']) is not bool:
            fail(path+'.pendingImages', 'expected a boolean')
        for j, option in enumerate(question['options']):
            opt_path = f'{path}.options[{j}]'
            if isinstance(option, str):
                string(option, opt_path, 500, nonempty=True)
            else:
                required(option, ('label', 'src', 'preview'), opt_path)
                string(option['label'], opt_path+'.label', 500, nonempty=True)
                paths(option, opt_path)
        if 'explanationImages' in question:
            array(question['explanationImages'], path+'.explanationImages')
            for j, image in enumerate(question['explanationImages']):
                img_path = f'{path}.explanationImages[{j}]'
                required(image, ('src',), img_path)
                paths(image, img_path)


def validate_import_options(options):
    metadata(options, 'import-options')
    if 'live_dates' in options:
        array(options['live_dates'], 'import-options.live_dates')
        seen = set()
        for i, date in enumerate(options['live_dates']):
            path = f'import-options.live_dates[{i}]'
            string(date, path, pattern=DATE_PATTERN.replace('/', r'\.'))
            if date in seen:
                fail(path, 'duplicate Live date')
            seen.add(date)
    if 'sequence_overrides' in options:
        overrides = options['sequence_overrides']
        object_value(overrides, 'import-options.sequence_overrides')
        for folder, entries in overrides.items():
            path = f'import-options.sequence_overrides[{folder!r}]'
            string(folder, path, nonempty=True, pattern=NAME_PATTERN)
            object_value(entries, path)
            for filename, number in entries.items():
                string(filename, path, nonempty=True, pattern=NAME_PATTERN)
                integer(number, f'{path}[{filename!r}]', 1)
