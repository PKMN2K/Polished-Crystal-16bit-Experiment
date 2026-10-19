# Crystal outline learner (experimental)

Trained on **126** real trainer sprites, tested on **26**
disjoint trainer sprites and on native Youngster separately. Training never
includes native Youngster.

| Boundary-dark prediction | Learned | All-black-border baseline |
| --- | ---: | ---: |
| 26 held-out trainers | 80.53% | 85.49% |
| Native Youngster | 80.00% | 86.50% |

Applied silhouette-contour predictions to an independent FireRed candidate;
98 boundary pixels changed of 225.
The output uses four grayscale shades and is **not** a professional redraw.

Only outer dark pixels are learned. Shape, expression, anatomy and interior
pixel clusters are inherited from the earlier reduced FireRed candidate.
Statistics alone cannot prove artistic quality. The game's active Youngster
PNG remains unchanged. The Lua/Aseprite runtime was not used.
