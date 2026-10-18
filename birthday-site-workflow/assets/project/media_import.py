"""Portable incremental imports. Source files are read-only; old assets are retained."""
import argparse
import copy
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import uuid
from project_lib import ROOT,read_json,digest,commit_content,write_json,valid_date

EXTENSIONS={'.png','.jpg','.jpeg','.webp','.mp4'}

def sequence(path,options):
    override=options.get('sequence_overrides',{}).get(path.parent.name,{}).get(path.name)
    if override is not None:
        if type(override) is not int or override<1:raise ValueError('Sequence override must be a positive integer')
        return override
    # Prefer explicit suffix numbering over a timestamp-like leading number.
    match=re.search(r'[-_](\d+)$',path.stem) or re.match(r'^(\d+)(?:\D|$)',path.stem)
    if not match or len(match[1])>6:raise ValueError('Add a sequence_overrides entry for '+path.name)
    number=int(match[1])
    if number<1:raise ValueError('Sequence must be positive')
    return number

def ffmpeg(args):
    import imageio_ffmpeg
    return subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error',*args],check=True,capture_output=True).stdout

def stream_hash(path):
    return ffmpeg(['-i',str(path),'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-']).decode().strip()

def image_sizes(source,out,preview_size=1800):
    from PIL import Image,ImageOps
    with Image.open(source) as image:
        oriented=ImageOps.exif_transpose(image).convert('RGB')
        width,height=oriented.size
        for name,size in [('preview.webp',preview_size),('thumb.webp',320)]:
            result=oriented.copy();result.thumbnail((size,size));result.save(out/name,'WEBP',quality=88)
    return width,height

def convert(source,kind):
    source_sha=digest(source)
    identity=hashlib.sha256((source_sha+kind+'portable-v1').encode()).hexdigest()[:24]
    final=ROOT/'dist/assets/imported'/identity
    # A new directory is used for each attempt, so a failed conversion cannot corrupt existing output.
    stage=ROOT/'.work'/uuid.uuid4().hex
    stage.mkdir(parents=True)
    report={'source':source.name,'sourceSha256':source_sha,'kind':kind}
    if kind in ['image','collage']:
        original=stage/('original'+source.suffix.lower());shutil.copy2(source,original)
        width,height=image_sizes(source,stage,1400 if kind=='collage' else 1800)
        photo={'src':'preview.webp','thumb':'thumb.webp','original':original.name,'type':'image'}
        if kind=='collage':photo={'src':original.name,'preview':'preview.webp','thumb':'thumb.webp','width':width,'height':height}
        assert digest(original)==source_sha
    else:
        output=stage/('motion.live.mp4' if kind=='live' else 'video.mp4')
        # Reject unsupported source video before writing content. No implicit re-encoding.
        ffmpeg(['-i',str(source),'-map','0:v:0','-c:v','copy','-bsf:v','h264_mp4toannexb','-f','null','-'])
        ffmpeg(['-y','-i',str(source),'-map','0:v:0',*(['-map','0:a?'] if kind=='video' else []),'-c','copy',*(['-an'] if kind=='live' else []),'-movflags','+faststart',str(output)])
        source_stream=stream_hash(source)
        if stream_hash(output)!=source_stream:raise ValueError('Video stream changed')
        ffmpeg(['-y','-i',str(source),'-frames:v','1','-c:v','png',str(stage/'frame.png')])
        width,height=image_sizes(stage/'frame.png',stage,900)
        from PIL import Image
        with Image.open(stage/'frame.png') as frame:frame.convert('RGB').save(stage/'still-full.webp','WEBP',lossless=True)
        photo={'src':output.name,'thumb':'thumb.webp','poster':'preview.webp','type':kind}
        if kind=='live':photo['original']='still-full.webp'
        report['videoStreamHash']=source_stream
    if digest(source)!=source_sha:raise ValueError('Source changed during import')
    outputs=sorted(p for p in stage.iterdir() if p.name!='frame.png')
    # Different FFmpeg builds may write different MP4 metadata with the same video stream.
    # Keep the original output intact and address this variant by its actual output bytes.
    if any((final/p.name).exists() and digest(final/p.name)!=digest(p) for p in outputs):
        variant=hashlib.sha256(''.join(p.name+digest(p) for p in outputs).encode()).hexdigest()[:16]
        final=final.with_name(identity+'-'+variant)
    final.mkdir(parents=True,exist_ok=True)
    for path in outputs:
        target=final/path.name
        if target.exists() and digest(target)!=digest(path):raise ValueError('Existing content-addressed asset differs; retain both for review')
        if not target.exists():shutil.copy2(path,target)
    # .work is ignored and may be removed after a successful import; never remove input files.
    for key in ['src','thumb','poster','preview','original']:
        if key in photo:photo[key]=(final/photo[key]).relative_to(ROOT/'dist').as_posix()
    report['outputs']={p.relative_to(ROOT/'dist').as_posix():digest(p) for p in final.iterdir() if p.is_file()}
    return photo,report

def import_media(mode):
    parser=argparse.ArgumentParser(description=__doc__)
    if mode=='photos':parser.add_argument('--date',required=True,help='One existing MM.DD folder; importing is incremental')
    parser.add_argument('--source',type=pathlib.Path,help='Explicit source root override (read only)')
    args=parser.parse_args()
    options=read_json(ROOT/'import-options.json')
    source=(args.source or ROOT/'materials'/mode).resolve(strict=True)
    if mode=='photos':
        if not re.fullmatch(r'\d{2}\.\d{2}',args.date) or not valid_date(args.date.replace('.','/')):raise ValueError('Invalid MM.DD date')
        source=source/args.date
    if not source.is_dir() or source.is_symlink():raise ValueError('Expected a real source directory')
    items=[p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS and (mode=='photos' or p.suffix.lower()!='.mp4')]
    if not items:raise ValueError('No supported top-level media found')
    numbered=[]
    for path in items:
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):raise ValueError('Linked source requires separate review')
        numbered.append((sequence(path,options),path))
    numbered.sort(key=lambda pair:pair[0])
    if len({n for n,_ in numbered})!=len(numbered):raise ValueError('Duplicate sequence numbers; no content was changed')
    content=read_json(ROOT/'content.json');updated=copy.deepcopy(content);photos=[];reports=[]
    for number,path in numbered:
        live=mode=='photos' and path.suffix.lower()=='.mp4' and ('live' in path.stem.lower() or args.date in options.get('live_dates',[]))
        kind='collage' if mode=='collages' else 'live' if live else 'video' if path.suffix.lower()=='.mp4' else 'image'
        photo,report=convert(path,kind);photo['caption']=('拼贴 ' if mode=='collages' else args.date.replace('.','/')+' · ')+str(number).zfill(2)
        photos.append(photo);reports.append({'sequence':number,**report})
    if mode=='photos':
        date=args.date.replace('.','/');found=False
        for album in updated['memories']:
            if album['date']==date:album['photos']=photos;found=True
        if not found:updated['memories'].append({'date':date,'title':date+' 的回忆','photos':photos})
        updated['memories'].sort(key=lambda x:x['date'])
        assert updated['collage']==content['collage'] and updated['quiz']==content['quiz']
    else:
        old={i:piece for i,piece in enumerate(content['collage'])}
        # Existing custom captions remain associated with identical original assets.
        captions={p['src']:p.get('caption') for p in old.values()}
        for piece in photos:
            if captions.get(piece['src']):piece['caption']=captions[piece['src']]
        updated['collage']=photos
        assert updated['memories']==content['memories'] and updated['quiz']==content['quiz']
    saved=commit_content(updated)
    report_path=ROOT/'manifests'/('import-'+mode+'-'+uuid.uuid4().hex[:12]+'.json')
    write_json(report_path,{'mode':mode,'date':args.date if mode=='photos' else None,'files':reports,'backup':saved.relative_to(ROOT).as_posix()})
    print(json.dumps({'imported':len(photos),'manifest':report_path.relative_to(ROOT).as_posix(),'backup':saved.relative_to(ROOT).as_posix()},ensure_ascii=False))
