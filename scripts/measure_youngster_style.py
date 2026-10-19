#!/usr/bin/env python3
"""Measure *actual* Crystal and FireRed sprites, without replacing artwork.

Outputs a machine-readable feature record, Markdown report, and an enlarged
comparison. Results are geometric statistics, NOT learned drawing instructions.
"""
import argparse
import json
from collections import Counter, deque
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw

FR_URL = ("https://raw.githubusercontent.com/pret/pokefirered/master/"
          "graphics/trainers/front_pics/youngster_front_pic.png")


def foreground(im, kind):
    width, height = im.size
    if kind == "firered":
        return [a >= 128 for a in im.convert("RGBA").getchannel("A").getdata()]
    # Four-neighbour exterior flood fill of WHITE, so enclosed white shirt
    # highlights are not mistaken for exterior background.
    white = [rgb == (255, 255, 255) for rgb in im.convert("RGB").getdata()]
    outside = [False] * (width * height)
    queue = deque()
    for y in range(height):
        for x in range(width):
            i = y * width + x
            if (x in (0, width - 1) or y in (0, height - 1)) and white[i]:
                outside[i] = True
                queue.append(i)
    while queue:
        i = queue.popleft()
        x, y = i % width, i // width
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                k = ny * width + nx
                if white[k] and not outside[k]:
                    outside[k] = True
                    queue.append(k)
    return [not v for v in outside]


def components(mask, width, height):
    sizes = []
    visited = set()
    for seed, active in enumerate(mask):
        if not active or seed in visited:
            continue
        stack = [seed]
        visited.add(seed)
        count = 0
        while stack:
            i = stack.pop()
            count += 1
            x, y = i % width, i // width
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    k = ny * width + nx
                    if mask[k] and k not in visited:
                        visited.add(k)
                        stack.append(k)
        sizes.append(count)
    return sorted(sizes, reverse=True)


def measure(im, kind):
    width, height = im.size
    fg = foreground(im, kind)
    coords = [(i % width, i // width) for i, ok in enumerate(fg) if ok]
    if not coords:
        raise ValueError("Empty sprite")
    xs, ys = [x for x, y in coords], [y for x, y in coords]
    l, t, r, b = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    n = len(coords)
    rgba = list(im.convert("RGBA").getdata())
    colors = Counter(p[:3] for p, yes in zip(rgba, fg) if yes)
    border = 0
    for x, y in coords:
        if any(not (0 <= x + dx < width and 0 <= y + dy < height)
               or not fg[(y + dy) * width + x + dx]
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            border += 1
    color_cluster_sizes = []
    for color in colors:
        cmask = [visible and rgba[i][:3] == color
                 for i, visible in enumerate(fg)]
        color_cluster_sizes.extend(components(cmask, width, height))
    row_counts = [sum(fg[y * width:(y + 1) * width])
                  for y in range(height)]
    occupied_tiles = sum(
        any(fg[y * width + x] for y in range(by, min(by + 8, height))
            for x in range(bx, min(bx + 8, width)))
        for by in range(0, height, 8) for bx in range(0, width, 8))
    return {
        "canvas_px": [width, height],
        "bounds_xyxy_exclusive": [l, t, r, b],
        "visible_size_px": [r - l, b - t],
        "foreground_pixels": n,
        "canvas_coverage_percent": round(100 * n / (width * height), 2),
        "foreground_colors_used": len(colors),
        "foreground_color_counts": [
            {"rgb": list(color), "count": count}
            for color, count in colors.most_common()],
        "silhouette_connected_components": len(components(fg, width, height)),
        "boundary_foreground_percent": round(100 * border / n, 2),
        "single_pixel_same_color_clusters": sum(s == 1 for s in color_cluster_sizes),
        "same_color_cluster_count": len(color_cluster_sizes),
        "occupied_8x8_tiles": occupied_tiles,
        "foreground_pixels_by_row": row_counts,
        "center_of_mass_px": [round(sum(xs)/n, 2), round(sum(ys)/n, 2)],
    }


def comparison(native, firered, output):
    scale = 6
    panel = 64 * scale + 20
    sheet = Image.new("RGB", (2 * panel + 20, 64 * scale + 65),
                      (232, 232, 232))
    draw = ImageDraw.Draw(sheet)
    for i, (im, title) in enumerate(((native, "CRYSTAL / native"),
                                      (firered, "FIRERED / source"))):
        rgba = Image.new("RGBA", im.size, (255, 255, 255, 255))
        rgba.alpha_composite(im.convert("RGBA"))
        enlarged = rgba.convert("RGB").resize(
            (im.width * scale, im.height * scale), Image.Resampling.NEAREST)
        x = 8 + i * (panel + 20)
        sheet.paste(enlarged, (x, 26))
        draw.text((x, 7), title, fill=(0, 0, 0))
        draw.text((x, 64 * scale + 35), f"{im.width}x{im.height} canvas",
                  fill=(0, 0, 0))
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path,
                        default=Path("gfx/trainers/youngster.png"))
    parser.add_argument("--firered-path", type=Path,
                        help="Use a local source PNG instead of downloading")
    parser.add_argument("--out", type=Path,
                        default=Path("reports/youngster-style-analysis"))
    args = parser.parse_args()
    with Image.open(args.native) as im:
        native = im.copy()
    if args.firered_path:
        with Image.open(args.firered_path) as im:
            firered = im.copy()
    else:
        with urlopen(FR_URL, timeout=30) as stream:
            with Image.open(BytesIO(stream.read())) as im:
                firered = im.copy()
    assert native.size == (56, 56), native.size
    assert firered.size == (64, 64), firered.size
    n, f = measure(native, "crystal"), measure(firered, "firered")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps({
        "source_crystal": str(args.native), "source_firered": FR_URL,
        "foreground_method": "Crystal: exterior-white flood fill; FireRed: alpha >=128",
        "native": n, "firered": f}, indent=2) + "\n")
    comparison(native, firered, args.out / "comparison.png")
    report = f"""# Youngster sprite pixel analysis

These are measured properties of the original PNGs. The battle engine stores
finished pixel data; it does not contain the original drawing instructions.

| Property | Polished Crystal | FireRed |
| --- | ---: | ---: |
| Canvas | {n['canvas_px'][0]}x{n['canvas_px'][1]} | {f['canvas_px'][0]}x{f['canvas_px'][1]} |
| Visible bounds (exclusive right/bottom) | {n['bounds_xyxy_exclusive']} | {f['bounds_xyxy_exclusive']} |
| Visible size | {n['visible_size_px'][0]}x{n['visible_size_px'][1]} | {f['visible_size_px'][0]}x{f['visible_size_px'][1]} |
| Foreground pixels | {n['foreground_pixels']} | {f['foreground_pixels']} |
| Canvas coverage | {n['canvas_coverage_percent']}% | {f['canvas_coverage_percent']}% |
| Foreground colours | {n['foreground_colors_used']} | {f['foreground_colors_used']} |
| Boundary/foreground | {n['boundary_foreground_percent']}% | {f['boundary_foreground_percent']}% |
| Single-pixel same-colour clusters | {n['single_pixel_same_color_clusters']} | {f['single_pixel_same_color_clusters']} |
| Occupied 8x8 tiles | {n['occupied_8x8_tiles']} | {f['occupied_8x8_tiles']} |

See metrics.json for foreground-by-row profiles, colour distributions, and
connected-component statistics; see comparison.png for actual pixel artwork.

## Method / cautions

- FireRed's indexed PNG transparency defines its foreground.
- Crystal is opaque grayscale: white pixels reachable from the outer border
  are considered background. Enclosed white details remain part of the sprite.
- A pixel cluster is a four-connected region of identical RGB values.
- The boundary metric measures silhouette edges, NOT dark-outline quality.
- These statistics cannot infer faces, limbs, lighting intent, or artistic quality.
- One Crystal trainer is not a generalizable training dataset. Next experiment:
  aggregate several native trainer sprites and test held-out reconstruction.
- No sprite is regenerated or installed by this analyzer.

Source FireRed PNG: {FR_URL}
Source Crystal PNG: gfx/trainers/youngster.png
"""
    (args.out / "README.md").write_text(report)
    print(report)
    print("Wrote:", args.out.resolve())


if __name__ == "__main__":
    main()
