# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

## Rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing and resource identity.
- Work only under `work/luna_translation_templates/` / `sol_translation_mappings/`; do not touch formal build inputs or DAT/KEY.
- Use pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- Bind current-row identity strictly by `unique_index` + `jpn_text`; `previous_jpn_text` / `next_jpn_text` are context only and must not be used to infer the current row.
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.

## Current totals

| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **9812 / 21041 rows** |
| file_ids with complete persisted translation | **110 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **13 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **100 rows / 13 complete file_ids**.

## Recent completed STAGEDAT
- `LANG_ITEM_TEXT.OLANG` — 803 rows, 17 shards + manifest.
- `LANG_MYOUTER_STAFF.OLANG` — 146 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP.OLANG` — 167 rows, two shards + manifest.
- `LANG_MYOUTER_DEVELOP_METAL.OLANG` — 592 rows, seven shards + manifest.
- `LANG_VOCALOID_KEYBOARD.OLANG` — 175 rows, three shards + manifest. English pronunciation examples and VOCALOID phoneme data are preserved; only actual keyboard/help/error UI is localized.
- `LANG_MYOUTER_STAFF_COMMENT.OLANG` — 356 rows, eight shards + manifest, complete.
- `LANG_MYOUTER_TOP.OLANG` — 202 rows, four shards + manifest, complete. Latest manifest commit `22ce7419a230ad2d0016c6d9c5619cc8b0990e71`.
- `LANG_MISSION_RESULT.OLANG` — 357 rows, four shards + manifest, complete. Manifest commit `5fdd621aaf20f3d01724cedfaaabdc3ac663ea40`.
- `LANG_WEAPON_TEXT.OLANG` — 388 rows, eight shards + manifest, complete. Manifest commit `bb9e266b6a894174c4584bdadd3aedfbd92e9080`.
- `LANG_MISSION_INFO.OLANG` — **482 logical rows, ten shards + manifest, complete**. Manifest commit `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Recent completed SLOT
- `5D02EB62` — 1 row, complete. JPN `PRISONER` is a plain semantic UI label rather than a verified fixed code, localized as `俘虏`. Mapping commit `0ae4820a1ea17a845e1b6d7d6cd2a2302ad98839`.
- `5D0A5DB1` — 5 rows, complete. Source `(不要)` markers/fullwidth test numbers are preserved; long scrolling-message test stays intentionally long; JPN final row remains a declarative “skip training and continue” rather than the auxiliary question form. Mapping commit `f5fd37dde91d66c49b9c797d950907e5b7c2e8a8`.
- `5D1708FB` — 5 rows, complete. Source `（不要）` communication-test markers and intentionally long scrolling text are preserved; `$1` remains in place; JPN communication-status messages are localized to Chinese rather than copied from auxiliary English UI. Mapping commit `c92b2c3f3152c3a7f0de49d810f138f3ff00ff0e`.
- `5D0A7130` — 7 rows, complete. Information-restriction message keeps MAIN OPS context and source multiline layout; the cutscene-skip prompt remains interrogative as in JPN; zoom/move/confirm/auto-zoom/attack UI labels are localized. Mapping commit `20327cda6caf631468d5c7c85c74b31421960986`.
- `5D06A8D5` — 69 rows, two shards + manifest, complete. Mother Base system-log messages preserve `(不要)`, `#`, `【！】`, `*log_type_34`, `$1/$2`, icon controls, unique_index 7 trailing newline and unique_index 10 trailing ASCII space. Fixed feature identities such as RECRUIT/TRADE/DELIVERY/OUTER OPS/METAL GEAR ZEKE remain authoritative. Manifest commit `d45b0971ddf094c5b3e55b60c9edbe4ba006eb24`.
- `5D3AF952` — **1 row, complete**. JPN `見つかった！` is localized as `被发现了！` from stealth-context semantics; auxiliary `Curses!` substitution was rejected and the interpretation remains review-flagged. Mapping commit `aee19a3c2d55a8974fbe09b68c6a6945dfe7b61e`.
- `5D22E834` — **1 row, complete**. JPN direct command `静かに！` is localized as `安静！`; auxiliary-added parentheses are rejected because they are absent from JPN. Mapping commit `ef61ad3d4623e6edace05ace7c59415ee0f16449`.
- `5DBF136F` — **1 row, complete**. JPN `STARTボタン：全訓練終了` is localized as `START按钮：结束全部训练`; auxiliary narrowing to “tutorial” was rejected and fixed `START` identity is preserved. Latest mapping commit `72745e87cb16f239b5e6c0be99f186937329e8f9`.
- `5D3AFE0D` — **2 rows, complete**. `連れて行け` preserves JPN's lack of terminal punctuation as `把他带走`; `フン…` keeps one ellipsis mark as `哼…`. Auxiliary punctuation was not imported. Mapping commit `3f66bb800a24f2899ac15d145d7d536591cdacb7`.
- `5D3B01ED` — **2 rows, complete**. JPN `くそっ ` keeps its trailing ASCII space and rejects auxiliary ellipsis substitution; `頑張れ…！` is localized as `坚持住…！` with punctuation preserved. Mapping commit `bcc28be12452fea34830ea70f6c4ec790c28d5ea`.
- `5D7E43B7` — **2 rows, complete**. Fixed device identities `REPTILE POD` and `AIPOD` are preserved exactly from JPN; auxiliary normalization `AI POD` is rejected. Mapping commit `e460ad2217b0037e818647e40d31e0d87ef8b98a`.
- `5D62E635` — **2 rows, complete**. JPN training dialogue is localized as `训练结束了` / `那么 开始射击训练`; the internal ASCII space in the second row and JPN's lack of terminal punctuation are preserved, while auxiliary punctuation and “target practice” narrowing are rejected. Mapping commit `a6220f5dac6efae6f32639ca3dda1d6c2cfd7c54`.
- `5D3B092D` — **2 rows, complete**. Monster Hunter crossover cat dialogue preserves the two JPN internal ASCII spaces; `トレニャー` uses auxiliary `特雷亚` only as transliteration reference, and final `ニャ` is rendered as `喵` without importing auxiliary punctuation. Mapping commit `6a34eb114831e7ae1eb3bfa595263a13325a1abe`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected; hunting double-angle titles remain parser-false-positive review items.
- `LANG_ITEM_TEXT`: JPN weapon/item/brand identity, hidden rows, fixed ASCII short labels/codes and document types remain authoritative over auxiliary substitutions.
- `LANG_MYOUTER_DEVELOP_METAL`: ZEKE configuration, parts, VOCALOID/AI settings and AI memory-board identifiers follow JPN identity; fixed English codes remain fixed.
- `LANG_VOCALOID_KEYBOARD`: English pronunciation examples and phoneme syntax remain exact; only actual UI/help/error text is localized.
- `LANG_MYOUTER_STAFF_COMMENT`: all 356 rows complete. JPN `祖母` overrides auxiliary `mother`; `無力化` stays distinct from killing; source `(不要)` voice-actor placeholders remain; named-character dialogue and biographies were reviewed separately from generic staff chatter.
- `LANG_MYOUTER_TOP`: all 202 rows complete. Printf placeholders remain text placeholders and are not misclassified as runtime controls; `$1/$2/$3` order follows JPN. Source `(不要)` rows remain. Fixed ASCII labels such as `OUTER OPS`, `MECHA`, `KEY CONFIG`, `DEVELOP`, `MOTHER-BASE` follow JPN identity. Auxiliary errors claiming a battle begins instead of ends, euphemizing explicit soldier death, adding an extra support marker, inserting Memory Stick icon controls, and substituting `SENDBOX` were rejected. Source `METAL GEAR ZEK` spelling at row 96 is preserved and flagged as a likely source typo. Source trailing ASCII whitespace at unique_index 159 is also preserved.
- `LANG_MISSION_RESULT`: all 357 logical rows complete. Single-space placeholders, `$1/$2` order, `$1 %` spacing, multiline layouts, fullwidth indentation and `ENTRY　GATE` fullwidth spacing follow JPN. `BLAVO`, `ALFA`, `SQUARE`, `AUSCAM DESERT`, fixed ASCII result labels and hero-spirit punctuation/intensity were not normalized from auxiliary text. Nonlexical `キェーーー` and `はいだらー！` are identity-preserved and flagged.
- `LANG_WEAPON_TEXT`: all 388 logical rows complete. JPN control icons and whitespace are preserved, including `<I=RIGH>`, `<I=ATK>`, `<I=HHA>`, trailing newlines and significant ASCII spaces. JPN weapon/model identities and short codes remain authoritative over auxiliary normalizations. `気力回復弾` remains distinct from LIFE recovery. Publication identities/codes follow JPN, and auxiliary substitutions such as `M37(ACM)`, `RAILGUN` for `RAIL GUN`, `PR` for `MR`, and generic/Solid/Liquid magazine labels were rejected. Human-slingshot wordplay remains review-flagged.
- `LANG_MISSION_INFO`: all 482 logical rows complete. Mapping identity follows `unique_index + jpn_text`; previous/next columns are context only. Shared deduplicated titles/descriptions were preserved without inventing logical rows. Part4 equipment-retrieval and part6 Fulton-recovery boundaries were repaired and rechecked against JPN. The 298/299/300 boundary is `EXTRA 034` title / its Claymore description / `EXTRA 061` title. Auxiliary-added `<I=CPY>` around literal `©CAPCOM CO., LTD.` was rejected. Shared DEMO interrogation text remains one logical row at 439; `尋問` is localized as `审讯`, `独房` as `牢房`.

## Remaining STAGEDAT
None. **STAGEDAT_OLANG is complete (46 / 46).**

## Next resource class
`SLOT_OLANG` — **13 / 144 complete**. Continue with the next unstarted SLOT file_id after checking for newer concurrent mappings; prefer smaller files first for durable checkpoints.

## Last safe checkpoint
- Safe translation total: **9812 rows / 110 complete file_ids**.
- STAGEDAT_OLANG: **46 / 46 complete**.
- SLOT_OLANG: **13 / 144 complete**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D3B092D.json`.
- Latest mapping commit: `6a34eb114831e7ae1eb3bfa595263a13325a1abe`.
- Resume next: **next unstarted SLOT_OLANG file_id**, selecting a small file after checking existing mappings.
