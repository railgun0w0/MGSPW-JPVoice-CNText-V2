# 4096×4096 atlas capacity simulation

Status: **PLANNING ESTIMATE — NOT A RASTERIZED BUILD**

This is a deterministic `FIXED_CELL_CAPACITY` simulation for the complete production union. It is not the simple `(4096 / cell_size)^2` estimate: retained clean glyphs use their actual clean GlyphRecord rectangles, generated glyphs use the tested fixed cell, and all rectangles are run through shelf first-fit-decreasing packing without rotation.

Planning policy: preserve unique non-Han clean JPN glyph records plus fallback record 0; generate every production Han from the future SC font (including same-codepoint clean-JPN overrides); add any production non-Han codepoint missing from the clean selector. Existing clean Han records outside the translation union are not retained. Chinese punctuation source remains undecided; mapped punctuation uses its clean rectangle only for this capacity estimate, without locking the final glyph-source policy.

Selector corpus is `UNKNOWN / UNION_REQUIRED`; both large and small are simulated against the entire union.

| selector | px | padding | retained clean | Han override | new missing Han | missing non-Han | final glyphs | usage | free texels | packed height | overflow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 00c7c9f9.xpr | 52 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 54.152% | 7691959 | 2271 | NO |
| 00c7c9f9.xpr | 52 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 58.220% | 7009589 | 2423 | NO |
| 00c7c9f9.xpr | 56 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 61.456% | 6466679 | 2593 | NO |
| 00c7c9f9.xpr | 56 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 65.784% | 5740549 | 2751 | NO |
| 00c7c9f9.xpr | 58 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 65.303% | 5821219 | 2733 | NO |
| 00c7c9f9.xpr | 58 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 69.761% | 5073209 | 2893 | NO |
| 00c7c9f9.xpr | 60 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 69.280% | 5153879 | 2877 | NO |
| 00c7c9f9.xpr | 60 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 73.869% | 4383989 | 3039 | NO |
| 00c7c9f9.xpr | 62 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 73.389% | 4464659 | 3025 | NO |
| 00c7c9f9.xpr | 62 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 78.108% | 3672889 | 3255 | NO |
| 00c7c9f9.xpr | 64 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 77.627% | 3753559 | 3243 | NO |
| 00c7c9f9.xpr | 64 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 82.477% | 2939909 | 3411 | NO |
| 00c7c9f9.xpr | 66 | 1 | 343 | 1144 | 1577 | 14 | 3078 | 81.996% | 3020579 | 3401 | NO |
| 00c7c9f9.xpr | 66 | 2 | 343 | 1144 | 1577 | 14 | 3078 | 86.976% | 2185049 | 3571 | NO |
| 001cbbd1.xpr | 52 | 1 | 142 | 143 | 2578 | 119 | 2982 | 52.772% | 7923488 | 2202 | NO |
| 001cbbd1.xpr | 52 | 2 | 142 | 143 | 2578 | 119 | 2982 | 56.715% | 7261976 | 2394 | NO |
| 001cbbd1.xpr | 56 | 1 | 142 | 143 | 2578 | 119 | 2982 | 60.356% | 6651168 | 2524 | NO |
| 001cbbd1.xpr | 56 | 2 | 142 | 143 | 2578 | 119 | 2982 | 64.570% | 5944216 | 2670 | NO |
| 001cbbd1.xpr | 58 | 1 | 142 | 143 | 2578 | 119 | 2982 | 64.351% | 5980928 | 2664 | NO |
| 001cbbd1.xpr | 58 | 2 | 142 | 143 | 2578 | 119 | 2982 | 68.700% | 5251256 | 2876 | NO |
| 001cbbd1.xpr | 60 | 1 | 142 | 143 | 2578 | 119 | 2982 | 68.481% | 5287968 | 2870 | NO |
| 001cbbd1.xpr | 60 | 2 | 142 | 143 | 2578 | 119 | 2982 | 72.966% | 4535576 | 3026 | NO |
| 001cbbd1.xpr | 62 | 1 | 142 | 143 | 2578 | 119 | 2982 | 72.747% | 4572288 | 3020 | NO |
| 001cbbd1.xpr | 62 | 2 | 142 | 143 | 2578 | 119 | 2982 | 77.367% | 3797176 | 3180 | NO |
| 001cbbd1.xpr | 64 | 1 | 142 | 143 | 2578 | 119 | 2982 | 77.148% | 3833888 | 3174 | NO |
| 001cbbd1.xpr | 64 | 2 | 142 | 143 | 2578 | 119 | 2982 | 81.904% | 3036056 | 3406 | NO |
| 001cbbd1.xpr | 66 | 1 | 142 | 143 | 2578 | 119 | 2982 | 81.685% | 3072768 | 3400 | NO |
| 001cbbd1.xpr | 66 | 2 | 142 | 143 | 2578 | 119 | 2982 | 86.576% | 2252216 | 3640 | NO |

`free texels` is atlas area minus padded rectangle area and may be negative. `overflow` is the result of the actual deterministic shelf placement, so it can be `YES` even when raw area alone appears sufficient. Real source-font bboxes, baseline and advance are unavailable in Phase 1; candidate comparison must rerun the same packer with identical raster settings.

The CSV is the authoritative full matrix for 52/56/58/60/62/64/66 px and padding 1/2.
