#!/usr/bin/env python3
"""Extract native trainer pixel-cluster statistics (NOT aesthetic-quality scores)."""
import argparse
import csv
import json
from collections import Counter, deque
from pathlib import Path
from PIL import Image

FIELDS = {
    'coverage_pct':'Foreground coverage (%)',
    'bbox_width':'Visible width (px)',
    'bbox_height':'Visible height (px)',
    'boundary_pct':'Boundary pixels / foreground (%)',
    'dark_boundary_pct':'Darkest-colour boundary (%)',
    'singleton_color_pct':'Single-pixel same-colour clusters (%)',
    'clusters_per_100px':'Colour clusters / 100 foreground px',
    'occupied_tiles':'8x8 tiles occupied',
    'center_x_pct':'Horizontal centroid (%)',
    'upper_quarter_pct':'Foreground in upper quarter (%)',
    'lower_quarter_pct':'Foreground in lower quarter (%)',
}
def mask_and_pixels(im):
    w,h=im.size
    p=list(im.convert('RGBA').getdata())
    if any(a<128 for *_,a in p):
        return [px[3]>=128 for px in p],p
    # Opaque GBC PNGs: preserve enclosed white features; flood-fill exterior
    corners=(p[0][:3],p[w-1][:3],p[-w][:3],p[-1][:3])
    bg=Counter(corners).most_common(1)[0][0]
    exterior=bytearray(w*h);q=deque()
    for y in range(h):
        for x in range(w):
            i=y*w+x
            if (x in (0,w-1) or y in (0,h-1)) and p[i][:3]==bg and not exterior[i]:
                exterior[i]=1;q.append(i)
    while q:
        i=q.popleft();x=i%w;y=i//w
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h:
                j=yy*w+xx
                if not exterior[j] and p[j][:3]==bg:
                    exterior[j]=1;q.append(j)
    return [not v for v in exterior],p

def components(mask,w,h):
    visited=bytearray(w*h);sizes=[]
    for seed,active in enumerate(mask):
        if not active or visited[seed]:continue
        q=[seed];visited[seed]=1;size=0
        while q:
            i=q.pop();size+=1;x=i%w;y=i//w
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=xx<w and 0<=yy<h:
                    j=yy*w+xx
                    if mask[j] and not visited[j]:visited[j]=1;q.append(j)
        sizes.append(size)
    return sizes

def measure(im):
    w,h=im.size
    visible,p=mask_and_pixels(im)
    ids=[i for i,b in enumerate(visible) if b]
    if not ids:raise ValueError('No foreground pixels')
    n=len(ids);xs=[i%w for i in ids];ys=[i//w for i in ids]
    cols=Counter(p[i][:3] for i in ids)
    dark=min(cols,key=lambda rgb:299*rgb[0]+587*rgb[1]+114*rgb[2])
    boundary=[i for i in ids if
        i%w==0 or i%w==w-1 or i//w==0 or i//w==h-1 or
        any(not visible[j] for j in (i-1,i+1,i-w,i+w))]
    cluster=[]
    for color in cols:
        cluster.extend(components(
            [active and p[i][:3]==color for i,active in enumerate(visible)],w,h))
    tiles=sum(any(visible[y*w+x] for y in range(by,min(by+8,h))
                  for x in range(bx,min(bx+8,w)))
              for by in range(0,h,8) for bx in range(0,w,8))
    pct=lambda k,total:round(100*k/total,3) if total else 0
    return dict(
        canvas_w=w,canvas_h=h,foreground_pixels=n,foreground_colors=len(cols),
        coverage_pct=pct(n,w*h),
        bbox_width=max(xs)-min(xs)+1,bbox_height=max(ys)-min(ys)+1,
        boundary_pct=pct(len(boundary),n),
        dark_boundary_pct=pct(sum(p[i][:3]==dark for i in boundary),len(boundary)),
        singleton_color_pct=pct(sum(k==1 for k in cluster),len(cluster)),
        clusters_per_100px=round(100*len(cluster)/n,3),
        occupied_tiles=tiles,center_x_pct=round(100*sum(xs)/(n*w),3),
        upper_quarter_pct=pct(sum(y<h/4 for y in ys),n),
        lower_quarter_pct=pct(sum(y>=3*h/4 for y in ys),n))

def qntl(values,f):
    v=sorted(values);pos=(len(v)-1)*f;i=int(pos)
    return round(v[i] if i==len(v)-1 else
                 v[i]+(v[i+1]-v[i])*(pos-i),3)

def profile(rows):
    return {k:{tag:qntl([r[k] for r in rows],q)
               for tag,q in [('p05',.05),('p10',.1),('median',.5),('p90',.9),('p95',.95)]}
            for k in FIELDS}

def deviations(row,prof):
    return {k:{'value':row[k],'p05':s['p05'],'p95':s['p95']}
            for k,s in prof.items() if row[k]<s['p05'] or row[k]>s['p95']}

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--trainer-dir',type=Path,default=Path('gfx/trainers'))
    a.add_argument('--candidate-dir',type=Path,default=Path('build/aseprite-youngster'))
    a.add_argument('--out',type=Path,default=Path('reports/trainer-style-corpus'))
    a.add_argument('--min-reference',type=int,default=20)
    args=a.parse_args()
    rows=[];errors=[]
    paths=sorted(args.trainer_dir.glob('*.png'))
    for path in paths:
        try:
            with Image.open(path) as im:r=measure(im)
            rows.append({'name':path.stem,**r})
        except (ValueError,OSError) as e:errors.append({'file':path.name,'error':str(e)})
    fixed=[r for r in rows if (r['canvas_w'],r['canvas_h'])==(56,56)]
    train=[r for r in fixed if r['name']!='youngster']
    young=[r for r in fixed if r['name']=='youngster']
    if len(train)<args.min_reference:
        raise ValueError(f'Only {len(train)} independent 56x56 trainers (<{args.min_reference})')
    if len(young)!=1:raise ValueError(f'Expected one 56x56 Youngster; got {len(young)}')
    prof=profile(train)
    candidates=[]
    for filename in ('preview_00_luma.png','preview_01_regions.png','preview_02_cleanup.png'):
        path=args.candidate_dir/filename
        if path.exists():
            with Image.open(path) as im:r=measure(im)
            candidates.append({'name':filename,'measurements':r,'outside_native_p05_p95':deviations(r,prof)})
    result={
        'explanation':'Statistical descriptors only; not an artistic-quality metric',
        'measurement_method':'exterior background flood fill; four-connected RGB clusters',
        'png_count':len(paths),'processed_count':len(rows),
        'native_56x56_trainers_excluding_youngster':len(train),
        'other_size_pngs':[{'name':r['name'],'canvas':[r['canvas_w'],r['canvas_h']]}
                           for r in rows if (r['canvas_w'],r['canvas_h'])!=(56,56)],
        'errors':errors,'native_reference_profile':prof,
        'heldout_youngster':{'measurements':young[0],
                            'outside_native_p05_p95':deviations(young[0],prof)},
        'diagnostic_candidates':candidates,'per_trainer':rows,
    }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'corpus.json').write_text(json.dumps(result,indent=2)+'\n')
    with (args.out/'trainers.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['name','canvas_w','canvas_h',*FIELDS])
        writer.writeheader()
        writer.writerows({k:r[k] for k in writer.fieldnames} for r in rows)
    report=['# Native Crystal trainer pixel-style corpus','',
            f'Processed **{len(rows)}** / {len(paths)} source PNGs.',
            f'**{len(train)}** trainers are 56x56 references excluding Youngster.',
            'All statistics hold out native Youngster. These are descriptive measures, **not artistic-quality scores**.',
            '', '| Feature | p10 | Median | p90 |','|---|---:|---:|---:|']
    for k,label in FIELDS.items():
        s=prof[k]
        report.append(f"| {label} | {s['p10']} | {s['median']} | {s['p90']} |")
    report.extend(['','## Held-out native Youngster','',
                   f"{len(deviations(young[0],prof))} features outside the native p05–p95 reference intervals.",
                   '','## Candidate deviation counts',''])
    for c in candidates:
        report.append(f"- {c['name']}: {len(c['outside_native_p05_p95'])} feature(s) outside range.")
    report.extend(['','**Warning:** A bad sprite can match every measurement. '
                   'A good distinctive pose can be outside a typical interval. '
                   'Neither result establishes pixel-art quality.',
                   '','All PNGs are measured without alteration; unusual dimensions '
                   'are listed separately in corpus.json.'])
    (args.out/'README.md').write_text('\n'.join(report)+'\n')
    print(f'Analyzed {len(rows)} source sprites, {len(train)} independent 56x56 reference trainers')
    print('Native heldout Youngster outliers:',len(deviations(young[0],prof)))
    for c in candidates:print(c['name'],'outliers:',len(c['outside_native_p05_p95']))
    print('Wrote',args.out)
if __name__=='__main__':main()
