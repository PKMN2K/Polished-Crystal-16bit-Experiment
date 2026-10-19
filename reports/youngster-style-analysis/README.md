# Youngster sprite pixel analysis

These are measured properties of the original PNGs. The battle engine stores
finished pixel data; it does not contain the original drawing instructions.

| Property | Polished Crystal | FireRed |
| --- | ---: | ---: |
| Canvas | 56x56 | 64x64 |
| Visible bounds (exclusive right/bottom) | [11, 4, 52, 55] | [16, 15, 50, 63] |
| Visible size | 41x51 | 34x48 |
| Foreground pixels | 903 | 697 |
| Canvas coverage | 28.79% | 17.02% |
| Foreground colours | 4 | 15 |
| Boundary/foreground | 22.15% | 27.12% |
| Single-pixel same-colour clusters | 73 | 126 |
| Occupied 8x8 tiles | 26 | 23 |

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

Source FireRed PNG: https://raw.githubusercontent.com/pret/pokefirered/master/graphics/trainers/front_pics/youngster_front_pic.png
Source Crystal PNG: gfx/trainers/youngster.png
