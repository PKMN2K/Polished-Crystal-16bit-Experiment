# Native Crystal trainer pixel-style corpus

Processed **153** / 153 source PNGs.
**152** trainers are 56x56 references excluding Youngster.
All statistics hold out native Youngster. These are descriptive measures, **not artistic-quality scores**.

| Feature | p10 | Median | p90 |
|---|---:|---:|---:|
| Foreground coverage (%) | 27.309 | 33.594 | 49.19 |
| Visible width (px) | 27.1 | 40.0 | 53.0 |
| Visible height (px) | 48.1 | 55.0 | 56.0 |
| Boundary pixels / foreground (%) | 13.223 | 18.463 | 23.491 |
| Darkest-colour boundary (%) | 69.716 | 88.669 | 96.522 |
| Single-pixel same-colour clusters (%) | 39.504 | 50.447 | 63.101 |
| Colour clusters / 100 foreground px | 14.796 | 21.296 | 28.601 |
| 8x8 tiles occupied | 23.0 | 29.0 | 39.0 |
| Horizontal centroid (%) | 46.23 | 49.806 | 52.936 |
| Foreground in upper quarter (%) | 10.323 | 20.375 | 26.068 |
| Foreground in lower quarter (%) | 13.804 | 19.305 | 25.939 |

## Held-out native Youngster

1 features outside the native p05–p95 reference intervals.

## Candidate deviation counts

- preview_00_luma.png: 3 feature(s) outside range.
- preview_01_regions.png: 2 feature(s) outside range.
- preview_02_cleanup.png: 2 feature(s) outside range.

**Warning:** A bad sprite can match every measurement. A good distinctive pose can be outside a typical interval. Neither result establishes pixel-art quality.

All PNGs are measured without alteration; unusual dimensions are listed separately in corpus.json.
