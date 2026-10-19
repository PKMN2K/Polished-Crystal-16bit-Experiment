#!/usr/bin/env python3
"""Prepare FireRed source and coarse pose masks for experimental Aseprite Lua.

The masks use hand-specified bounding boxes; they are not true semantic segmentation.
"""
import argparse
import io
import json
import urllib.request
from pathlib import Path
from PIL import Image

URL="https://raw.githubusercontent.com/pret/pokefirered/master/graphics/trainers/front_pics/youngster_front_pic.png"
REGIONS={"hat":1,"face":2,"ball":3,"throwing_arm":4,"raised_arm":5,
         "shirt":6,"shorts":7,"legs":8,"other":9}
BOXES=[
    ("ball",(15,22,24,32)),
    ("hat",(21,14,40,23)),
    ("face",(23,21,42,33)),
    ("raised_arm",(40,23,51,42)),
    ("throwing_arm",(19,28,29,41)),
    ("shirt",(27,29,41,46)),
    ("shorts",(23,44,45,52)),
    ("legs",(15,49,49,64))
]
def identify(x,y):
    for name,(left,top,right,bottom) in BOXES:
        if left<=x<right and top<=y<bottom:
            return REGIONS[name]
    return REGIONS["other"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,default=Path("gfx/trainers/youngster.png"))
    p.add_argument("--firered",type=Path)
    p.add_argument("--out",type=Path,default=Path("build/aseprite-youngster"))
    opt=p.parse_args()
    native=Image.open(opt.native).convert("RGB")
    if opt.firered:
        fr=Image.open(opt.firered).convert("RGBA")
    else:
        with urllib.request.urlopen(URL,timeout=30) as stream:
            fr=Image.open(io.BytesIO(stream.read())).convert("RGBA")
    if native.size!=(56,56) or fr.size!=(64,64):
        raise ValueError("Expected native 56x56, FireRed 64x64")
    alpha=fr.getchannel("A").point(lambda v:255 if v>=128 else 0)
    bbox=alpha.getbbox()
    if bbox is None:raise ValueError("FireRed source image has no foreground")
    target=(10,4,51,55)
    tw,th=target[2]-target[0],target[3]-target[1]
    crop=fr.crop(bbox).resize((tw,th),Image.Resampling.NEAREST)
    crop_a=crop.getchannel("A").point(lambda v:255 if v>=128 else 0)
    crop.putalpha(crop_a)
    placed=Image.new("RGBA",(56,56),(0,0,0,0))
    placed.paste(crop,target[:2])
    labels=Image.new("RGBA",(56,56),(0,0,0,0))
    for y in range(th):
        for x in range(tw):
            if crop_a.getpixel((x,y))==0:continue
            sx=min(bbox[2]-1,bbox[0]+int((x+.5)*(bbox[2]-bbox[0])/tw))
            sy=min(bbox[3]-1,bbox[1]+int((y+.5)*(bbox[3]-bbox[1])/th))
            labels.putpixel((target[0]+x,target[1]+y),
                            (identify(sx,sy)*20,0,0,255))
    opt.out.mkdir(parents=True,exist_ok=True)
    fr.save(opt.out/"firered_original_64.png")
    native.save(opt.out/"crystal_reference_56.png")
    placed.save(opt.out/"firered_placed_56.png")
    labels.save(opt.out/"regions_56.png")
    m={"source_url":URL,"source_bbox_xyxy":list(bbox),
       "target_bbox_xyxy":list(target),"regions":REGIONS,
       "source_space_priority_rectangles":[{"name":n,"bbox":list(b)} for n,b in BOXES],
       "warning":"Coarse region bounding boxes, not true semantic segmentation"}
    (opt.out/"manifest.json").write_text(json.dumps(m,indent=2)+"\n")
    print("Prepared source, native reference, coarse regions and manifest:",opt.out)

if __name__=="__main__":
    main()
