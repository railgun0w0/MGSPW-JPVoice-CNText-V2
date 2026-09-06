# Sol Translation Progress

Branch: `sol-translation`

Purpose: track translation progress for `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules

- JPN is the sole semantic authority.
- MLG_CN / ENG are auxiliary evidence only; do not trust ordinal alignment blindly.
- Preserve structure, markup, control tokens, indices, references, timing and metadata.
- Write translations only to `cn_text` plus mechanical translation/QC fields allowed by `TRANSLATION_GUIDE.md`.
- Keep `build_status=NOT_BUILT` and `ingame_status=NOT_TESTED`.
- Use `TRANSLATED_PENDING_REVIEW`, never `APPROVED`.
- Do not build DAT/KEY or touch formal `translations/` / manifest.
- For large CSVs where connector writes require full-file replacement, persist a per-file translation mapping first before mechanical merge so completed translation work cannot be lost.

## Completed (merged into 28-column CSV)

| Resource class | file_id | Rows | Commit | Notes |
|---|---:|---:|---|---|
| YPK_GTT | `1C79F3AD` | 8 | `573836a53c3adad52c28a0e85572b4b6f4f98fd6` | Full file translated; auxiliary bird-count over-expansion not copied. |
| YPK_GTT | `1C79F36D` | 22 | `44bd91ff8ad6d424b58b23610a4d51d7501adf9f` | Full file translated; unreliable rows handled from JPN/context; ruby preserved. |
| YPK_GTT | `1C79F2ED` | 39 | `4441e4ddb97a89ceee9f4a6a7b4220d5fa63e10b` | Full file translated; many unreliable mappings handled from JPN/context. |
| YPK_GTT | `1C79F3ED` | 46 | `f5d2b02baace9ab133ccf983ae15cc65d95adb56` | Training terminology normalized; ruby/control preserved. |
| YPK_GTT | `1C7CF2AD` | 3 | `436145406a5ae0a82eb4d06e5dc8d400fdf5b914` | Armored-vehicle objective lines. |
| YPK_GTT | `1C7B736D` | 8 | `6e18e18e16d65eff96b501864d66c1b1cd8ec3f4` | Alert-door / Peace Walker hangar guidance. |
| YPK_GTT | `1C7AF2AD` | 11 | `776b16b943937f5f94e9cc8088469623b5728ce1` | Compound infiltration/tutorial; shifted cardboard-box refs ignored. |
| YPK_GTT | `1C7AF2ED` | 13 | `fd799bef10756ac58f83470ebb8340867a5cbde1` | Train/Basilisco/neutralization/plant lines. |
| YPK_GTT | `1C7B73AD` | 17 | `c7915f47641632c576cb2db5d587732b42261096` | Bridge/control-tower/chaff guidance; contradictory launcher aux ignored. |
| YPK_GTT | `1C7BF36D` | 17 | `7aeda6078d24489f41ab07460497f7355ceb0996` | Shutter tutorial and Peace Walker hangar approach. |
| YPK_GTT | `1C7A73AD` | 21 | `8bc6f3816abfe4ebd4dd30c5d026e8ed1896b240` | Dock/control-tower approach; bird-count aux over-expansion rejected. |
| YPK_GTT | `1C7AF3AD` | 20 | `024ff61ccfce4e7f767673478896a59a950b5186` | Control-tower approach; repeated bird-count line kept JPN-authoritative. |
| YPK_GTT | `1C7C72AD` | 19 | `e663241a5e0d897bb161643e5b08c3a38db7655b` | Fulton/equipment tutorial and butterfly/Amanda guidance. |
| YPK_GTT | `1C7BF2AD` | 20 | `b258496e7322e1f2f1a6d8ded4dd165781f6f818` | FSLN/comandante contact and gun-turret tutorial; boathouse aux mismatch ignored. |
| YPK_GTT | `1C7C73AD` | 25 | `01bcff424f1b707e4a08971487688f471dd0cdd3` | Gate/elevator/pry-open tutorial; shifted auxiliary sequencing ignored. |
| YPK_GTT | `1C7B72AD` | 29 | `5b8be1f51f102e54fb1788781bd74dde67d9bae1` | Radio/FSLN boathouse, ELUDE hanging, river/dinosaur-footprint dialogue, Amanda guidance. |
| YPK_GTT | `1C7CF3AD` | 31 | `eb9ae65765e1c22b1304a1bc9ef276d4c3975285` | Gunship/control-tower battle; local ammo procurement and cover-destruction wording kept JPN-authoritative. |
| YPK_GTT | `1C7CF2ED` | 33 | `f0f34b239b01bac6456983d72bbeb3b02a23da25` | Fence/prison route, COMPA rescue lines, coffee/terminal/aqueduct/plant dialogue; repeated terminology reused. |
| YPK_GTT | `1C7C736D` | 35 | `d963bcb027c52f6aaa997f381ca96193a77000ef` | Cell escape/co-op/jigsaw/interrogation lines; `ウタうな` interpreted as `别招供`; alert-door guidance. |
| YPK_GTT | `1C7BF2ED` | 36 | `dd1f7c4cfb0b84866efabc41fe2d8ad6a19d8de8` | Fort infiltration / ELUDE / gun-turret tutorial / mountain entrance / plant dialogue; `銃座` kept as `机枪座`, auxiliary sniper and ladder-direction additions rejected. |
| YPK_GTT | `1C7B72ED` | 38 | `80a5b1785ecbe51dfc6314804101c39f06c0dc0f` | Transport-route / two-level walkway / ELUDE / bunker tactics / mountain entrance / plant dialogue; repeated terminology reused. |

## Persisted translations pending mechanical CSV merge

| Resource class | file_id | Rows | Mapping commit | Mapping path | Notes |
|---|---:|---:|---|---|---|
| YPK_GTT | `1C79F42D` | 80 | `1adb7231a2d7048de526a4b821ea1a94865e7180` | `sol_translation_mappings/YPK_GTT/1C79F42D.json` | Full file translated; Monster Hunter crossover; shifted auxiliary mappings ignored. |
| YPK_GTT | `1C79F46D` | 93 | `066f4c34feb13b46a68682977d767775b6884e70` | `sol_translation_mappings/YPK_GTT/1C79F46D.json` | Full file translated; intentional AI corruption/test/gibberish preserved from JPN. |

## Totals

- Completed merged file_ids: 21 / 241
- Completed merged template rows: 491 / 21041
- Persisted pending-merge file_ids: 2
- Persisted pending-merge rows: 173
- Total translation work safely persisted: 664 rows
- YPK_GTT translation coverage: 23 / 36 (21 merged + 2 pending merge)

## Current queue

Continue unprocessed YPK_GTT resources by ascending manageable size. Next candidates: `1C7C72ED`, `1C7BF3AD`, `1C7BF32D`, then other medium/large files. Large files use complete-file JSON mapping before merge.

## Risk / review log

- `1C79F3AD`, `1C7A73AD`, `1C7AF3AD`: JPN only says many birds would die; auxiliary `millions` rejected.
- `1C79F36D` / `1C7B72AD` / `1C7BF2ED` / `1C7B72ED`: `エルード` treated as hanging/grabbing; ruby occurrence `<R=悬挂,ELUDE>` where markup exists; review global gameplay terminology later.
- `1C79F2ED` / `1C7CF2ED` / `1C7BF2ED` / `1C7B72ED`: `绞刑台镇`, `大叶蚁塔`, `CAFETAL`, `TERMINAL`, `SOMBRILLA DE POBRE`, `CHAMPA` kept consistent; global glossary review later.
- `1C79F42D`: Monster Hunter shifted refs ignored; `耐性` kept `抗性`; review SOMOZA/Cecile/cat speech/Stun Rod/catchphrase/onomatopoeia.
- `1C79F46D`: corrupted numeric strings, station names and MGS2-style gibberish preserved literally; unrelated aux ignored.
- `1C7C72AD`: `キジマドクチョウ` -> `黄条袖蝶`; other butterfly names follow attached MLG terminology.
- `1C7BF2AD`: opening auxiliary `船库 / boathouse` conflicts with JPN `FSLNの小屋`; JPN hut meaning used.
- `1C7C73AD`: gate-pry tutorial auxiliary rows partially shifted; JPN operation order preserved.
- `1C7B72AD`: radio-tab auxiliary content shifted across adjacent rows; JPN sequence preserved. `ウラギンドクチョウ` follows attached Juno Silverspot terminology pending glossary review.
- `1C7CF3AD`: `どんどんムかれていく` rendered contextually as cover being stripped away (`掩体正一个个被削掉`) rather than generic aux `crumbling`.
- `1C7CF2ED`: `<R=同志,コンパ>` normalized as `<R=同志,COMPA>`; auxiliary extra `Snake` in coffee line and extra thanks in no-more-comrades line were not copied.
- `1C7C736D`: `糸鋸` standardized as `钢丝锯`; interrogation slang `ウタうな` rendered `别招供`, not generic auxiliary `don't break`. A few Chinese lines exceed JPN byte count; final YPK aligned-capacity validator remains authoritative before approval/build.
- `1C7BF2ED`: auxiliary maps JPN `銃座` to snipers and adds ladder direction not present in JPN; both rejected. Row 23 has aggregated multi-reference auxiliary variants; JPN `<I=CAMERA>` used as authority.
- `1C7B72ED`: repeated two-level walkway / ELUDE / bunker / mountain entrance lines kept consistent with earlier files; no auxiliary wording allowed to override JPN sequencing.
