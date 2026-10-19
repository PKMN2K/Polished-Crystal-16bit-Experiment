#!/usr/bin/env python3
"""Review an externally generated Youngster image; never claim this creates AI art."""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

def quantize_candidate(src):
    src=src.convert("RGBA")
    alpha=src.getchannel("A")
    # Some image generators make a solid backdrop instead of transparency.
    # Never silently erase backdrop pixels; surface that problem as a warning.
    rgb=Image.new("RGB",src.size,(255,255,255))
    rgb.paste(src,mask=alpha)
    backdrop=all(a==255 for a in alpha.getdata())
    bbox=alpha.getbbox()
    if not bbox: raise ValueError("Empty alpha content")
    content=src.crop(bbox)
    scale=min(52/content.width,54/content.height)
    nw=max(1,round(content.width*scale)); nh=max(1,round(content.height*scale))
    content=content.resize((nw,nh),Image.Resampling.NEAREST)
    target=Image.new("RGBA",(56,56),(255,255,255,0))
    target.alpha_composite(content,((56-nw)//2,55-nh))
    pixels=[]
    for r,g,b,a in target.getdata():
        if a<128: pixels.append((0,0,0,0));continue
        lum=round(0.2126*r+0.7152*g+0.0722*b)
        c=min((0,85,170,255),key=lambda q:abs(q-lum))
        pixels.append((c,c,c,255))
    target.putdata(pixels)
    return target,backdrop

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--output",default="build/youngster-review")
    ap.add_argument("--crystal",default="gfx/trainers/youngster.png")
    ap.add_argument("--firered",default="gfx/trainers/conversions/youngster_firered.png")
    args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    image=Image.open(args.candidate)
    converted,opaque_background=quantize_candidate(image)
    converted.save(out/"youngster_candidate_56.png")
    refs=[("Crystal reference",args.crystal),("Earlier conversion",args.firered)]
    pics=[]
    for label,path in refs:
        if Path(path).exists(): pics.append((label,Image.open(path).convert("RGBA")))
    pics.append(("AI candidate - normalized",converted))
    tile=280
    canvas=Image.new("RGB",(tile*len(pics),310),(229,229,229))
    d=ImageDraw.Draw(canvas)
    for i,(label,pic) in enumerate(pics):
        scale=4 if pic.size[0]>56 else 5
        preview=pic.resize((pic.width*scale,pic.height*scale),Image.Resampling.NEAREST)
        backing=Image.new("RGBA",preview.size,(255,255,255,255))
        backing.alpha_composite(preview)
        canvas.paste(backing.convert("RGB"),(i*tile+(tile-preview.width)//2,8))
        d.text((i*tile+8,285),label,fill="black")
    canvas.save(out/"comparison.png")
    colors=set(converted.getdata())
    report={"source":args.candidate,"dimensions":[56,56],
            "opaque_colours":len({p[:3] for p in colors if p[3]>0}),
            "transparent_pixels":sum(p[3]==0 for p in converted.getdata()),
            "input_opaque_background":opaque_background,
            "review_required":True,
            "ai_generation_performed":False,
            "warnings":(["Input has no transparency: backgrounds may be mistaken for sprite content."] if opaque_background else [])
                       +["Nearest-neighbor resizing and quantization are NOT semantic pixel-art reconstruction; review shape, anatomy and shading manually."]}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    assert converted.size==(56,56)
    assert report["opaque_colours"]<=4
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
