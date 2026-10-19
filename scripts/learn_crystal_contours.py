#!/usr/bin/env python3
"""Empirical contour classifier trained on Crystal trainers, with disjoint evaluation.

Learns probability of darkest shade at each silhouette-boundary pixel from
only mask geometry and non-boundary interior shades. This is NOT a sprite artist.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from PIL import Image, ImageDraw

SIDES=((0,-1),(1,0),(0,1),(-1,0))
DIAGS=((-1,-1),(1,-1),(1,1),(-1,1))
SHADES=(255,170,85,0)

def silhouette(im):
    rgba=im.convert("RGBA");w,h=rgba.size
    pixels=list(rgba.getdata())
    if any(a<128 for _,_,_,a in pixels):
        return [p[3]>=128 for p in pixels],pixels
    bg=Counter((pixels[0][:3],pixels[w-1][:3],pixels[-w][:3],pixels[-1][:3])).most_common(1)[0][0]
    exterior=bytearray(w*h);q=deque()
    for y in range(h):
        for x in range(w):
            i=y*w+x
            if (x in (0,w-1) or y in (0,h-1)) and pixels[i][:3]==bg and not exterior[i]:
                exterior[i]=1;q.append(i)
    while q:
        i=q.popleft();x,y=i%w,i//w
        for dx,dy in SIDES:
            xx,yy=x+dx,y+dy
            if 0<=xx<w and 0<=yy<h:
                j=yy*w+xx
                if not exterior[j] and pixels[j][:3]==bg:
                    exterior[j]=1;q.append(j)
    return [not p for p in exterior],pixels

def observe(im,mask=None):
    w,h=im.size
    if (w,h)!=(56,56):raise ValueError(f"Invalid sprite dimension {w}x{h}")
    if mask is None:mask,pixels=silhouette(im)
    else:pixels=list(im.convert("RGBA").getdata())
    shades=[min(range(4),key=lambda k:abs(SHADES[k]-round(.299*r+.587*g+.114*b)))
            for r,g,b,a in pixels]
    pixels_on_edge=[]
    for y in range(h):
        for x in range(w):
            i=y*w+x
            if not mask[i]:continue
            outside=0
            for bit,(dx,dy) in enumerate(SIDES):
                xx,yy=x+dx,y+dy
                if not (0<=xx<w and 0<=yy<h and mask[yy*w+xx]):
                    outside|=1<<bit
            if not outside:continue
            diagonals=sum(not (0<=x+dx<w and 0<=y+dy<h and mask[(y+dy)*w+x+dx])
                          for dx,dy in DIAGS)
            interior=[]
            for dx,dy in SIDES:
                xx,yy=x+2*dx,y+2*dy
                if not (0<=xx<w and 0<=yy<h):continue
                j=yy*w+xx
                if mask[j] and all(0<=xx+a<w and 0<=yy+b<h and mask[(yy+b)*w+xx+a]
                                   for a,b in SIDES):
                    interior.append(shades[j])
            tone=round(sum(interior)/len(interior)) if interior else -1
            feature=(outside,diagonals,y//14,tone)
            pixels_on_edge.append((i,feature,shades[i]==3))
    return pixels_on_edge,shades

def keys(feature):
    d,g,y,t=feature
    return (feature,(d,g,t),(d,g),(d,),())

def fit(paths):
    tables=[defaultdict(lambda:[0,0]) for _ in range(5)]
    total=[0,0]
    for path in paths:
        with Image.open(path) as im:edge,_=observe(im)
        for _,feature,dark in edge:
            total[int(dark)]+=1
            for table,k in zip(tables,keys(feature)):
                table[k][int(dark)]+=1
    if not sum(total):raise ValueError("No training boundary pixels")
    return tables,total

def chance(model,feature):
    tables,total=model
    p=total[1]/sum(total)
    for table,k in reversed(list(zip(tables,keys(feature)))):
        neg,pos=table.get(k,(0,0));n=neg+pos
        if n:p=(n/(n+16))*(pos/n)+(16/(n+16))*p
    return p

def classify(edge,model):
    empirical=model[1][1]/sum(model[1])
    ordered=sorted(((chance(model,f),i) for i,f,_ in edge),
                   key=lambda x:(-x[0],x[1]))
    chosen={i for _,i in ordered[:round(empirical*len(edge))]}
    return chosen,empirical

def assess(paths,model):
    tp=fp=fn=tn=0
    for path in paths:
        with Image.open(path) as im:edge,_=observe(im)
        chosen,_=classify(edge,model)
        for i,f,is_dark in edge:
            pred=i in chosen
            if pred and is_dark:tp+=1
            elif pred:fp+=1
            elif is_dark:fn+=1
            else:tn+=1
    n=tp+fp+fn+tn
    if not n:raise ValueError("Empty evaluation set")
    return {"trainers":len(paths),"edge_pixels":n,
            "learned_accuracy":round((tp+tn)/n,5),
            "all_dark_baseline_accuracy":round((tp+fn)/n,5),
            "learned_dark_precision":round(tp/(tp+fp),5) if tp+fp else 0,
            "learned_dark_recall":round(tp/(tp+fn),5) if tp+fn else 0}

def convert(src,alpha_path,model):
    with Image.open(src) as im:
        base=im.convert("RGB")
    with Image.open(alpha_path) as im:
        mask=[px[3]>=128 for px in im.convert("RGBA").getdata()]
    edge,shades=observe(base,mask)
    chosen,empirical=classify(edge,model)
    old=sum(dark for _,_,dark in edge)
    changed=sum((i in chosen)!=dark for i,_,dark in edge)
    for i,f,dark in edge:
        # Only silhouette border is rewritten; leave interior and pose intact.
        shades[i]=3 if i in chosen else max(1,min(2,shades[i]))
    output=Image.new("L",(56,56));output.putdata([SHADES[x] for x in shades])
    assert set(output.getdata())<=set(SHADES)
    return output,{"edge_pixels":len(edge),"dark_pixels_before":old,
                   "dark_pixels_after":len(chosen),"modified_edge_pixels":changed,
                   "learned_dark_ratio":round(empirical,5)}

def comparison(native,original,derived,path):
    sheet=Image.new("RGB",(1110,385),(232,232,232));d=ImageDraw.Draw(sheet)
    panels=[(native,"Native Crystal"),(original,"Previous preview"),(derived,"Learned contours")]
    for index,(im,name) in enumerate(panels):
        if isinstance(im,Path):
            with Image.open(im) as src:im=src.convert("RGB")
        x=11+index*367
        sheet.paste(im.convert("RGB").resize((336,336),Image.Resampling.NEAREST),(x,26))
        d.text((x,8),name,fill=(0,0,0))
    sheet.save(path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--trainer-dir",type=Path,default=Path("gfx/trainers"))
    p.add_argument("--candidate-dir",type=Path,default=Path("build/aseprite-youngster"))
    p.add_argument("--out",type=Path,default=Path("reports/learned-contours"))
    p.add_argument("--min-training",type=int,default=50)
    a=p.parse_args()
    files=[f for f in sorted(a.trainer_dir.glob("*.png")) if f.stem!="youngster"]
    keep=[]
    for f in files:
        with Image.open(f) as im:
            if im.size==(56,56):keep.append(f)
    hold=[f for f in keep if int(hashlib.sha256(f.stem.encode()).hexdigest()[:8],16)%5==0]
    train=[f for f in keep if f not in hold]
    if len(train)<a.min_training or not hold:
        raise ValueError(f"Insufficient training/holdout: {len(train)}/{len(hold)}")
    model=fit(train)
    validation=assess(hold,model)
    native=a.trainer_dir/"youngster.png"
    if not native.is_file():raise ValueError("Missing native held-out Youngster")
    youngster=assess([native],model)
    source=a.candidate_dir/"preview_02_cleanup.png"
    output,changes=convert(source,a.candidate_dir/"firered_placed_56.png",model)
    a.out.mkdir(parents=True,exist_ok=True)
    output_path=a.out/"youngster_firered_learned_contour.png"
    output.save(output_path)
    comparison(native,source,output,a.out/"comparison.png")
    result={"training_trainers":len(train),"validation_trainers":len(hold),
            "method":"trainer-disjoint statistical outline dark-pixel classification",
            "validation":validation,"heldout_native_youngster":youngster,
            "candidate":changes,"heldout_trainer_names":[f.stem for f in hold],
            "native_youngster_used_for_training":False,
            "limits":["Not overall artistic quality","Anatomy not rebuilt",
                      "Aseprite Lua is not executed by this Python prototype"]}
    (a.out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    report=f"""# Crystal outline learner (experimental)

Trained on **{len(train)}** real trainer sprites, tested on **{len(hold)}**
disjoint trainer sprites and on native Youngster separately. Training never
includes native Youngster.

| Boundary-dark prediction | Learned | All-black-border baseline |
| --- | ---: | ---: |
| {len(hold)} held-out trainers | {validation['learned_accuracy']:.2%} | {validation['all_dark_baseline_accuracy']:.2%} |
| Native Youngster | {youngster['learned_accuracy']:.2%} | {youngster['all_dark_baseline_accuracy']:.2%} |

Applied silhouette-contour predictions to an independent FireRed candidate;
{changes['modified_edge_pixels']} boundary pixels changed of {changes['edge_pixels']}.
The output uses four grayscale shades and is **not** a professional redraw.

Only outer dark pixels are learned. Shape, expression, anatomy and interior
pixel clusters are inherited from the earlier reduced FireRed candidate.
Statistics alone cannot prove artistic quality. The game's active Youngster
PNG remains unchanged. The Lua/Aseprite runtime was not used.
"""
    (a.out/"README.md").write_text(report)
    print(report)

if __name__=="__main__":
    main()
