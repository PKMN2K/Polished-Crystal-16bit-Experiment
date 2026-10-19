#!/usr/bin/env python3
"""Create an honest, reproducible reference pack for Sprite Studio.
This prepares references; it does not invoke an AI model or redraw pixels.
"""
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from PIL import Image, ImageDraw
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "sprite-studio-youngster"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE_URL = "https://raw.githubusercontent.com/pret/pokefirered/master/graphics/trainers/front_pics/youngster_front_pic.png"
with urlopen(SOURCE_URL, timeout=40) as response:
    source = Image.open(BytesIO(response.read())).convert("RGBA")
native = Image.open(ROOT / "gfx/trainers/youngster.png").convert("RGBA")
assert source.size == (64, 64), source.size
assert native.size == (56, 56), native.size
source.save(OUT / "firered_youngster_original_64.png")
native.save(OUT / "crystal_youngster_style_reference_56.png")
for image, name in [(source, "firered_youngster_8x.png"), (native, "crystal_youngster_8x.png")]:
    image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST).save(OUT / name)
prompt = """Identity reference: firered_youngster_original_64.png.
Sprite-work reference ONLY: crystal_youngster_style_reference_56.png.
Reconstruct the FireRed Youngster's identity, clothing, pose, gesture, hair,
and silhouette in native Crystal-era battle trainer pixel craftsmanship.
One 56x56 canvas. Up to 4 opaque palette colours (including black and white)
and transparent background, one-pixel deliberate clusters, upper-left light,
no antialiasing, no gradients, no generated subpixels, minimal dithering.
Reduce detail with purposeful hand-placed pixels, not generic pixelation.
Do NOT copy the Crystal Youngster character design.
Export a native-size PNG, not an 8x preview. Do not animate.
"""
(OUT / "SPRITE_STUDIO_PROMPT.txt").write_text(prompt, encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps({
    "identity_file": "firered_youngster_original_64.png",
    "style_file": "crystal_youngster_style_reference_56.png",
    "target_canvas": [56, 56],
    "max_opaque_palette_entries": 4,
    "ai_generation_performed": False,
    "original": SOURCE_URL,
    "note": "Reference pack only. Sprite Studio requires an external configured generation agent."
}, indent=2) + "\n", encoding="utf-8")
print("Generated Sprite Studio reference pack:", OUT)
