"""Independent geometry, glyph-fit and evidence checks for authored design assets."""
from pathlib import Path
from PIL import Image,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/demo-visuals-v018'
data=json.loads((Path(__file__).parent/'slides.json').read_text())
issues=[];texts=0;pngs=[]
for s in data['slides']:
    image=OUT/'assets'/(s['id']+'.png')
    with Image.open(image) as im:
        if im.size!=(1920,1080):issues.append([s['id'],'wrong PNG canvas',list(im.size)])
    pngs.append(str(image.relative_to(ROOT)))
    boxes=[]
    for o in s['objects']:
        if min(o['x'],o['y'],o['w'],o['h'])<0 or o['x']+o['w']>1920 or o['y']+o['h']>900:
            issues.append([s['id'],o['name'],'outside content or caption-safe boundary'])
        if o['kind']!='text':continue
        texts+=1
        font=('/usr/share/fonts/truetype/dejavu/DejaVuSansMono' if 'Mono' in o['font'] else '/usr/share/fonts/truetype/dejavu/DejaVuSans')+('-Bold' if o['bold'] else '')+'.ttf'
        face=ImageFont.truetype(font,o['size'])
        for n,line in enumerate(o['text'].split('\n')):
            width=face.getlength(line)
            if width>o['w']:issues.append([s['id'],o['name'],'glyph width exceeds box',width,o['w']])
            # Match SVG baseline positions, including actual glyph ascender/descender.
            x0,y0,x1,y1=face.getbbox(line,anchor='ls')
            base=o['y']+o['size']+n*o['size']*1.36
            boxes.append((o['name'],o['x']+x0,base+y0,o['x']+x1,base+y1))
        if o['size']<22:issues.append([s['id'],o['name'],'unreadable authored label size'])
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            if a[0]==b[0]:continue
            dx=min(a[3],b[3])-max(a[1],b[1]);dy=min(a[4],b[4])-max(a[2],b[2])
            if dx>2 and dy>2:issues.append([s['id'],'text intersection',a[0],b[0],dx,dy])
manifest=json.loads((OUT/'evidence-manifest.json').read_text())
for source in manifest['inputs']:
    if hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()!=source['sha256']:issues.append(['changed evidence',source['path']])
summary=json.loads((ROOT/'reports/validation-expansion5/summary.json').read_text())
assert summary['stages']['baseline']['matches']==3
assert summary['stages']['repaired_development']['matches']==4
assert summary['stages']['first_holdout']['matches']==4
assert summary['stages']['legacy_regression']['matches']==63
receipt=dict(slides=len(data['slides']),editable_text_objects=texts,canvas=[1920,1080],caption_safe_from_y=900,evidence_hashes_verified=True,metric_sources_verified=True,issues=issues,pngs=pngs,automated_checks_only='Glyph metrics and package checks supplement, not replace, individual visual review.')
(OUT/'design-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='pngs'},indent=2))
if issues:raise SystemExit(1)
