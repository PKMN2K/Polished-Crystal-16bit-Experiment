#!/usr/bin/env python3
"""Prepare a *review candidate* using real FireRed and Polished Crystal art.

This is an algorithmic outline/shading cleanup, NOT a hand-drawn Gen 2
sprite. Keep both draft and candidate so neither is confused with a final.
"""
from pathlib import Path
from io import BytesIO
from urllib.request import urlopen
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "gfx/trainers/conversions"
SOURCE = "https://raw.githubusercontent.com/pret/pokefirered/master/graphics/trainers/front_pics/youngster_front_pic.png"
REFERENCE = ROOT / "gfx/trainers/youngster.png"
DRAFT = DIR / "youngster_firered.png"
FINAL = DIR / "youngster_firered_refined.png"
PALETTE = [255,255,255,170,170,170,85,85,85,0,0,0] + [0,0,0]*252

with urlopen(SOURCE, timeout=30) as response:
    fr = Image.open(BytesIO(response.read())).convert("RGBA")
with Image.open(REFERENCE) as image:
    native = image.convert("RGBA")
with Image.open(DRAFT) as image:
    draft = image.convert("P")
assert fr.size == (64,64) and native.size == (56,56)
assert draft.size == (56,56)
w,h = draft.size

# Derive the sprite shape from the FireRed source, not from whiteness in the
# four-colour draft (white legitimately appears on the clothing).
alpha = fr.getchannel("A")
bbox = alpha.getbbox()
if bbox is None:
    raise RuntimeError("Source has no opaque pixels")
cut = alpha.crop(bbox)
scale = min((w - 4)/cut.width, (h - 2)/cut.height)
scaled_size = (max(1,round(cut.width*scale)), max(1,round(cut.height*scale)))
cut = cut.resize(scaled_size, Image.Resampling.NEAREST)
mask = Image.new("L",(w,h),0)
mask.paste(cut,((w-scaled_size[0])//2,h-scaled_size[1]))
mask = mask.point(lambda x: 255 if x >= 128 else 0)

pix = list(draft.getdata())
occupied = [v > 0 for v in mask.getdata()]
def xy(x,y):
    return y*w+x
def ink(x,y):
    return 0 <= x < w and 0 <= y < h and occupied[xy(x,y)]
out = list(pix)
# A sharply legible, one-pixel dark boundary, avoiding unnecessary extra
# black strokes over unoccupied white background.
for y in range(h):
    for x in range(w):
        i = xy(x,y)
        if not occupied[i]:
            out[i] = 0
        elif any(not ink(x+dx,y+dy) for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))):
            out[i] = 3

candidate = Image.new("P",(w,h))
candidate.putpalette(PALETTE)
candidate.putdata(out)
assert len(set(candidate.getdata())) <= 4
candidate.save(FINAL, optimize=False)

# Visual comparison artifact for an actual human art review in GitHub Actions.
def preview(image):
    image = image.convert("RGBA")
    image.putalpha(Image.new("L",image.size,255))
    return image.resize((224,224),Image.Resampling.NEAREST)
sheet = Image.new("RGB",(3*240,270),"#ddd")
for i,(pic,label) in enumerate(((native,"Crystal reference"),(draft,"FireRed draft"),(candidate,"Outlined candidate"))):
    sheet.paste(preview(pic).convert("RGB"),(i*240+8,8))
    ImageDraw.Draw(sheet).text((i*240+8,238),label,fill="#111")
sheet.save(DIR / "youngster_comparison.png")
print(f"Wrote {FINAL.relative_to(ROOT)} and comparison image; requires artist review")
