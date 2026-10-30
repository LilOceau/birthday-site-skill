"""Create envelope icons and a 1200 x 630 PNG card; see 操作说明.txt."""
import argparse
import io
import pathlib
from configuration import resolve_options
from data_validation import ASSET_PATTERN, string, validate_site
from project_lib import ROOT, read_json, atomic_write, backup


def branding_files(site, subtitle, font_path=None):
    from PIL import Image, ImageDraw, ImageFont
    validate_site(site)
    config=resolve_options(site);colors=config['theme']
    title=config['sharing']['title'] or site['title']
    # The bundled Pillow font is Latin-only. Do not silently draw missing CJK glyphs.
    if font_path is None and not (title+subtitle).isascii():
        raise ValueError('Chinese/non-ASCII text requires --font pointing to a font that supports it; see 操作说明.txt')
    def font(size):
        return ImageFont.truetype(str(font_path),size) if font_path else ImageFont.load_default(size=size)
    def png(image):
        stream=io.BytesIO();image.save(stream,'PNG',optimize=True);return stream.getvalue()
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="16" fill="{colors['ink']}"/>
<rect x="10" y="17" width="44" height="32" rx="3" fill="{colors['paper']}"/>
<path d="M11 19 32 35 53 19M11 47 26 34M53 47 38 34" fill="none" stroke="{colors['accent']}" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M32 41 25 34C19 28 27 23 32 29C37 23 45 28 39 34Z" fill="{colors['ink']}"/>
</svg>
'''
    def envelope_icon(size):
        image=Image.new('RGB',(256,256),colors['ink']);d=ImageDraw.Draw(image)
        d.rounded_rectangle((40,68,216,196),radius=12,fill=colors['paper'])
        d.line([(44,76),(128,140),(212,76)],fill=colors['accent'],width=10)
        d.line([(44,188),(104,136)],fill=colors['accent'],width=8)
        d.line([(212,188),(152,136)],fill=colors['accent'],width=8)
        d.ellipse((96,108,132,144),fill=colors['ink']);d.ellipse((124,108,160,144),fill=colors['ink'])
        d.polygon([(98,132),(158,132),(128,164)],fill=colors['ink'])
        return image.resize((size,size),Image.Resampling.LANCZOS)
    card=Image.new('RGB',(1200,630),colors['background']);d=ImageDraw.Draw(card)
    # A restrained stationery card, with large text inside a crop-safe margin.
    d.rounded_rectangle((42,38,1158,592),radius=12,outline=colors['accent'],width=2)
    d.text((88,84),'A LITTLE BIRTHDAY LETTER',font=font(19),fill=colors['ink'])
    d.line((88,125,342,125),fill=colors['accent'],width=2)
    def wrap(text,size,width):
        lines=['']
        for character in text:
            candidate=lines[-1]+character
            if character=='\n':lines.append('')
            elif d.textlength(candidate,font=font(size))>width and lines[-1]:lines.append(character)
            else:lines[-1]=candidate
        return [line.strip() for line in lines]
    for size in range(64,23,-2):
        lines=wrap(title,size,640)
        if len(lines)<=3:break
    if len(lines)>3:raise ValueError('Sharing title is too long for the card; shorten sharing.title')
    y=188
    for line in lines:d.text((88,y),line,font=font(size),fill=colors['ink']);y+=size+12
    subtitle_lines=wrap(subtitle,24,625)
    if len(subtitle_lines)>2:raise ValueError('Subtitle is too long; keep it to two short lines')
    for i,line in enumerate(subtitle_lines):d.text((88,440+i*34),line,font=font(24),fill=colors['ink'])
    d.text((88,548),'MEMORIES  /  MOMENTS  /  YOU',font=font(16),fill=colors['ink'])
    d.rounded_rectangle((805,191,1095,435),radius=9,fill=colors['envelope'])
    d.rounded_rectangle((825,151,1075,375),radius=3,fill=colors['paper'])
    for y,line_width in [(194,145),(220,185),(246,166)]:d.line((855,y,855+line_width,y),fill=colors['accent'],width=3)
    d.polygon([(805,254),(950,354),(1095,254),(1095,435),(805,435)],fill=colors['envelope'])
    d.line([(805,435),(900,340)],fill=colors['accent'],width=2)
    d.line([(1095,435),(1000,340)],fill=colors['accent'],width=2)
    d.ellipse((932,323,954,345),fill=colors['ink']);d.ellipse((950,323,972,345),fill=colors['ink'])
    d.polygon([(934,339),(970,339),(952,361)],fill=colors['ink'])
    return {'favicon.svg':svg.encode(), 'favicon-32.png':png(envelope_icon(32)),
            'apple-touch-icon.png':png(envelope_icon(180)), 'social-card.png':png(card)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='assets/branding',help='Directory relative to dist, inside assets/')
    parser.add_argument('--subtitle',help='Short card subtitle; defaults to letterDescription')
    parser.add_argument('--font',type=pathlib.Path,help='Local font supporting all title/subtitle characters')
    parser.add_argument('--replace',action='store_true',help='Back up and replace the four generated files')
    args=parser.parse_args()
    string(args.output,'--output',pattern=ASSET_PATTERN)
    output=(ROOT/'dist'/args.output).resolve()
    if not output.is_relative_to((ROOT/'dist/assets').resolve()):parser.error('Output must stay inside dist/assets')
    site=read_json(ROOT/'site.json')
    files=branding_files(site,args.subtitle if args.subtitle is not None else site['letterDescription'],args.font)
    targets=[output/name for name in files]
    if any(p.is_symlink() or p.resolve().parent!=output for p in targets):parser.error('Linked output requires review')
    if any(p.exists() for p in targets) and not args.replace:parser.error('Output exists; use a new --output directory or --replace to retain a backup')
    if any(p.exists() for p in targets):print('Backup:',backup(targets).relative_to(ROOT))
    for name,data in files.items():atomic_write(output/name,data)
    print('Created four assets in',output.relative_to(ROOT))
    print('Set site.json icons/sharing.image to these paths if using a new directory; then run python build.py.')


if __name__=='__main__':main()
