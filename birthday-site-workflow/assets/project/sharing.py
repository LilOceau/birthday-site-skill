"""Static icon and social metadata. No runtime packages or network requests."""
import hashlib
import html
import struct
import xml.etree.ElementTree as ET
from urllib.parse import quote


def png_dimensions(path):
    with path.open('rb') as stream:
        header = stream.read(33)
    if len(header) < 33 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[8:16] != b'\0\0\0\rIHDR':
        raise ValueError('expected a PNG image with an IHDR header')
    width, height = struct.unpack('>II', header[16:24])
    if not width or not height:
        raise ValueError('PNG dimensions must be positive')
    return width, height


def validate_assets(config, asset):
    """Resolve all paths even before a public URL is configured."""
    for key, value in config['icons'].items():
        label = 'site.icons.'+key
        try:
            path = asset(value)
            if key == 'favicon':
                if path.suffix.lower() != '.svg':
                    raise ValueError('expected an SVG favicon')
                root = ET.parse(path).getroot()
                if root.tag != '{http://www.w3.org/2000/svg}svg':
                    raise ValueError('expected an SVG root with the SVG namespace')
            else:
                size = 32 if key == 'fallback' else 180
                if path.suffix.lower() != '.png' or png_dimensions(path) != (size, size):
                    raise ValueError(f'expected a {size} x {size} PNG')
        except (ValueError, ET.ParseError) as error:
            raise ValueError(f'{label}: {error}') from error
    try:
        path = asset(config['sharing']['image'])
        if path.suffix.lower() != '.png':
            raise ValueError('expected a PNG social image')
        width, height = png_dimensions(path)
        if width > 8192 or height > 8192 or path.stat().st_size > 5*1024*1024:
            raise ValueError('social image must be at most 8192 px per side and 5 MiB')
    except ValueError as error:
        raise ValueError(f'site.sharing.image: {error}') from error


def render_head(site, config, asset):
    def escaped(value):
        return html.escape(str(value), quote=True)
    def versioned(path):
        with asset(path).open('rb') as stream:
            version = hashlib.file_digest(stream, 'sha256').hexdigest()[:16]
        return quote(path, safe='/.-_~')+'?v='+version
    icons = config['icons']
    lines = [
        f'<link rel="icon" type="image/png" sizes="32x32" href="{escaped(versioned(icons["fallback"]))}">',
        f'<link rel="icon" type="image/svg+xml" sizes="any" href="{escaped(versioned(icons["favicon"]))}">',
        f'<link rel="apple-touch-icon" sizes="180x180" href="{escaped(versioned(icons["appleTouch"]))}">'
    ]
    sharing = config['sharing']
    if not sharing['url']:
        return '\n  '.join(lines)
    title = sharing['title'] or site['title']
    description = sharing['description'] or site['description']
    image_url = sharing['url']+versioned(sharing['image'])
    width, height = png_dimensions(asset(sharing['image']))
    lines.append(f'<link rel="canonical" href="{escaped(sharing["url"])}">')
    for key, value in [('og:type', 'website'), ('og:url', sharing['url']), ('og:title', title),
                       ('og:description', description), ('og:locale', 'zh_CN'),
                       ('og:image', image_url), ('og:image:type', 'image/png'),
                       ('og:image:width', width), ('og:image:height', height),
                       ('og:image:alt', sharing['imageAlt'])]:
        lines.append(f'<meta property="{key}" content="{escaped(value)}">')
    for key, value in [('twitter:card', 'summary_large_image'), ('twitter:title', title),
                       ('twitter:description', description), ('twitter:image', image_url),
                       ('twitter:image:alt', sharing['imageAlt'])]:
        lines.append(f'<meta name="{key}" content="{escaped(value)}">')
    return '\n  '.join(lines)
