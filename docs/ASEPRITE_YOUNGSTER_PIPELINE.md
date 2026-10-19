# Youngster Aseprite Reconstruction Prototype

**Experimental v0.1: not a finished Crystal-style redraw.** This feature is isolated
on branch feature/gen2-sprite-conversions and does not overwrite
gfx/trainers/youngster.png.

## Purpose

Create reproducible, editable **diagnostic** sprite candidates based on the real
FireRed Youngster and native Polished Crystal Youngster.

- scripts/prepare_aseprite_youngster.py reads the FireRed 64x64 sprite and
  native Crystal 56x56 sprite; generates an RGBA 56x56 pose placement,
  source-region labels and manifest. The regions are manually defined
  coordinate rectangles, **not true semantic segmentation**.
- scripts/preview_aseprite_youngster.py produces Python/Pillow-only grayscale
  preview PNGs and a side-by-side contact sheet for CI. These are **not Lua
  execution**, and not evidence that Aseprite was installed.
- scripts/reconstruct_youngster.lua, when **actually run with Aseprite 1.3+**,
  creates three 56x56 opaque four-shade grayscale candidate PNGs and an
  editable .aseprite document with separate hidden Crystal/FireRed reference
  layers and individual candidate layers.

The three candidates are (00) nearest-neighbour source placement with generic
luminance mapping, (01) coarse region-dependent brightness thresholds and
(02) conservative shade cleanup limited to interior clothes/legs pixels.
No face or silhouette redrawing is performed. The candidates will probably
still look like reduced FireRed artwork, not native Crystal pixel art.

## Commands (from repo root)

Prepare and preview (Python required; GitHub Actions runs these):

    python -m pip install Pillow
    python scripts/prepare_aseprite_youngster.py
    python scripts/preview_aseprite_youngster.py

Run Lua with your own properly licensed Aseprite installation:

    aseprite -b --script-param root=build/aseprite-youngster --script scripts/reconstruct_youngster.lua

On Windows, use the full path to aseprite.exe if necessary.

Look in build/aseprite-youngster/ for candidate_comparison.png,
preview_*.png, and the manifest. After *running Lua in Aseprite*, you
should additionally see candidate_*.png and youngster_candidates.aseprite.
Inspect the latter in Aseprite and toggle layers.

## What GitHub CI verifies

CI fetches the actual pret/pokefirered Youngster, loads the repo's native
Crystal Youngster, creates the 56x56 masks, exports baseline previews,
checks that the preview colours are exactly [0,85,170,255], checks sizes,
and tests Lua syntax with a parser. It uploads diagnostic files as an artifact.

**CI does not execute the Aseprite Lua API** or claim an .aseprite file
was generated. A licensed Aseprite executable is not bundled. Only run
actual Lua after supplying your own installation. A passing CI run does
not indicate professional pixel-art quality.

## Next experiments

1. Replace source-coordinate bounding boxes with validated segmentation;
   retain manual-reviewed labels for measuring segmentation accuracy.
2. Extract statistical style profiles from many native trainer sprites.
3. Add reconstruction quality metrics and holdout tests, then human review.
4. Run the Lua stage and compare every exported candidate to its Python
   reference baseline for bit-for-bit parity.

## Upstream

- Original FireRed sprite: https://github.com/pret/pokefirered
- Aseprite source: https://github.com/aseprite/aseprite
- Aseprite Lua API: https://www.aseprite.org/api/
- Aseprite CLI: https://www.aseprite.org/docs/cli/

Aseprite is source-available under a restrictive EULA. Do not check in,
redistribute, or upload Aseprite executables to this project.
