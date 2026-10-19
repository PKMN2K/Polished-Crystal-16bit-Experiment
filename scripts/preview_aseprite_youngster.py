#!/usr/bin/env python3
"""Diagnostic Pillow implementation of Aseprite Lua candidate rules.

This preview DOES NOT run Aseprite, create an editable document, or establish
artistic quality. Preview filenames are distinct from Lua candidate outputs.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw

SHADES=(255,170,85,0)
def level(pixel,id,semantic):
    r,g,b=pixel[:3]
    value=(299*r+587*g+114*b+500)//1000
    lo,mid,hi=64,128,200
    if semantic:
        if id in (1,7):lo,mid,hi=76,148,210
        elif id in (2,4,5,8):lo,mid,hi=70,135,195
        elif id==6:lo,mid,hi=65,126,187
        else:lo,mid,hi=68,127,196
    if value<lo:return 3
    if value<mid:return 2
    if value<hi:return 1
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dir",type=Path,default=Path("build/aseprite-youngster"))
    opt=p.parse_args()
    root=opt.dir
    placed=Image.open(root/"firered_placed_56.png").convert("RGBA")
    regions=Image.open(root/"regions_56.png").convert("RGBA")
    native=Image.open(root/"crystal_reference_56.png").convert("RGB")
    def get(semantic):
        grid=[[0]*56 for _ in range(56)]
        for y in range(56):
            for x in range(56):
                col=placed.getpixel((x,y));id=regions.getpixel((x,y))[0]//20
                if col[3]>=128 and id:
                    grid[y][x]=level(col,id,semantic)
        return grid
    basic,regional=get(False),get(True)
    cleaned=[row.copy() for row in regional]
    changes=0
    for y in range(1,55):
        for x in range(1,55):
            id=regions.getpixel((x,y))[0]//20
            if id not in (6,7,8) or regional[y][x]==3:continue
            adjacent=((x-1,y),(x+1,y),(x,y-1),(x,y+1))
            if any(regions.getpixel(pt)[0]//20!=id for pt in adjacent):continue
            winner,n=Counter(regional[ny][nx] for nx,ny in adjacent).most_common(1)[0]
            if n>=3 and winner!=3 and winner!=regional[y][x]:
                cleaned[y][x]=winner;changes+=1
    def as_image(grid):
        im=Image.new("L",(56,56),255)
        im.putdata([SHADES[i] for row in grid for i in row])
        assert set(im.getdata()).issubset(SHADES)
        return im
    imgs=[as_image(g) for g in (basic,regional,cleaned)]
    for name,img in zip(("preview_00_luma.png","preview_01_regions.png",
                         "preview_02_cleanup.png"),imgs):
        img.save(root/name)
    multiple=5
    sheet=Image.new("RGB",(4*56*multiple+50,56*multiple+55),"#d9d9d9")
    draw=ImageDraw.Draw(sheet)
    for index,(img,title) in enumerate(zip([native,*imgs],
             ("Native Crystal","00: Luminance","01: Region palette","02: Cluster cleanup"))):
        x=10+index*(56*multiple+10)
        sheet.paste(img.resize((56*multiple,56*multiple),Image.Resampling.NEAREST),(x,26))
        draw.text((x,8),title,fill=(0,0,0))
    sheet.save(root/"candidate_comparison.png")
    differing=sum(a!=b for aa,bb in zip(basic,regional) for a,b in zip(aa,bb))
    assert differing>0,"Expected palette regions to change some pixels"
    metrics={"previews_are_python_not_aseprite":True,
             "dimensions":[56,56],"palette_intensities":list(SHADES),
             "pixel_differences_luma_vs_regions":differing,
             "pixel_differences_regions_vs_cleanup":changes,
             "warning":"These are mechanically valid diagnostic previews, not Crystal-quality art"}
    (root/"preview_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    main()
