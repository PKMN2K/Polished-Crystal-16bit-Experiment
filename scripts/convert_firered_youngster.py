#!/usr/bin/env python3
"""Create a *first-pass* Crystal-size Youngster from pret/pokefirered.

Source artwork is fetched from pret's public repository; the canonical target
sprite and palette are read from this checkout. This is a deterministic draft,
NOT a replacement for a reviewed pixel-by-pixel redraw.
"""
from pathlib import Path
from io import BytesIO
from urllib.request import urlopen
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://raw.githubusercontent.com/pret/pokefirered/master/graphics/trainers/front_pics/youngster_front_pic.png"
TARGET = ROOT / "gfx/trainers/youngster.png"
PALETTE = ROOT / "gfx/trainers/youngster.pal"
OUT = ROOT / "gfx/trainers/conversions"
OUT.mkdir(parents=True, exist_ok=True)

with urlopen(SOURCE, timeout=30) as response:
    source = Image.open(BytesIO(response.read())).convert("RGBA")
with Image.open(TARGET) as img:
    size = img.size
assert source.size == (64, 64), f"Unexpected FireRed size: {source.size}"
assert size == (56, 56), f"Unexpected Crystal size: {size}"
assert PALETTE.is_file()

# Preserve full FireRed character silhouette, scaled as a coherent unit.
# The original indexed PNG supplies transparency in its own metadata.
bounds = source.getbbox()
if bounds is None:
    raise ValueError("FireRed image is blank")
character = source.crop(bounds)
max_w, max_h = size[0] - 4, size[1] - 2
scale = min(max_w / character.width, max_h / character.height)
dimensions = (max(1, round(character.width * scale)), max(1, round(character.height * scale)))
character = character.resize(dimensions, Image.Resampling.NEAREST)
canvas = Image.new("RGBA", size, (255, 255, 255, 255))
canvas.alpha_composite(character, ((size[0] - dimensions[0]) // 2, size[1] - dimensions[1]))

# Explicit 2bpp-friendly grayscale (white + 2 middle tones + black).
# Save indexed PNG with exactly four used indices; palette colours in the ROM
# come from existing gfx/trainers/youngster.pal.
def level(pixel):
    r, g, b, a = pixel
    if a == 0:
        return 0
    luminance = (299 * r + 587 * g + 114 * b) // 1000
    if luminance >= 215:
        return 0
    if luminance >= 151:
        return 1
    if luminance >= 85:
        return 2
    return 3

out = Image.new("P", size)
palette = [255, 255, 255, 170, 170, 170, 85, 85, 85, 0, 0, 0] + [0, 0, 0] * 252
out.putpalette(palette)
out.putdata([level(p) for p in canvas.getdata()])
assert len(set(out.getdata())) <= 4
output = OUT / "youngster_firered.png"
out.save(output, optimize=False)
(OUT / "youngster_firered.pal").write_bytes(PALETTE.read_bytes())
print(f"Wrote {output.relative_to(ROOT)} ({size[0]}x{size[1]}, 4 indexed values) from {SOURCE}")
