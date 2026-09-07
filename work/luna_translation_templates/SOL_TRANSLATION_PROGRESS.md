# Sol Translation Progress

Branch: `sol-translation`

Purpose: durable checkpoint for translation work under `work/luna_translation_templates/` so work can resume safely across chat turns.

Historical checkpoint archive:
- `SOL_TRANSLATION_PROGRESS_ARCHIVE_2026-09-07_10603.md` — exact pre-compaction tracker snapshot through 10603 rows / 177 file_ids / SLOT 80/144.

## Rules
- JPN is the sole semantic and structural authority; MLG_CN / ENG are auxiliary only.
- Preserve markup, controls, placeholders, indices/references, ordering, timing, significant whitespace and resource identity.
- Work only under `work/luna_translation_templates/` / `sol_translation_mappings/`; do not touch formal build inputs or DAT/KEY.
- Use pending-review semantics; never mark Sol output `APPROVED`.
- Large files may use contiguous shards + manifest.
- For multiline CSVs, use logical `unique_index`, never physical line number.
- Bind current-row identity strictly by `unique_index` + `jpn_text`; previous/next are context only.
- If a mapping/shard already exists, fetch and verify it rather than overwriting concurrent progress.
- Completed file_ids are committed and immediately reflected in this tracker.

## Current totals
| Metric | Progress |
|---|---:|
| Total template file_ids | 241 |
| Total template rows | 21041 |
| Translation work safely persisted | **11293 / 21041 rows** |
| file_ids with complete persisted translation | **196 / 241** |
| YPK_GTT | **36 / 36 complete** |
| OHD | **1 / 1 complete** |
| LOOSE_OLANG | **14 / 14 complete** |
| STAGEDAT_OLANG | **46 / 46 complete** |
| SLOT_OLANG | **99 / 144 complete** |

## Resource-class accounting
- YPK_GTT: **2080 rows / 36 complete file_ids**.
- OHD: **226 rows / 1 complete file_id**.
- LOOSE_OLANG: **1719 rows / 14 complete file_ids**.
- STAGEDAT_OLANG: **5687 rows / 46 complete file_ids**.
- SLOT_OLANG: **1581 rows / 99 complete file_ids**.

## STAGEDAT checkpoint
STAGEDAT_OLANG is complete (46 / 46). `LANG_MISSION_INFO` manifest commit: `9738fa4604e7ba659bc9a6fa95b54c95c819590e`.

## Archive boundary
- Full detailed history through `5D3B0112` is preserved byte-for-byte in `SOL_TRANSLATION_PROGRESS_ARCHIVE_2026-09-07_10603.md`.
- Boundary mapping: `5D3B0112` — 23 rows, commit `866a6f5f0e279aba9a96ffce338961cbfd7b51a4`.
- Boundary totals: **10603 / 21041 rows**, **177 / 241 file_ids**, SLOT **80 / 144**, **891 rows**.

## Post-archive SLOT checkpoints
- `5DCDD1C4` 25; briefing-files UI/speaker table follows JPN structure: fixed `BRIEFING FILES`, `NEXT`, `UNKNOWN`, `BACK` identities remain untranslated; `・`, adjacent `$1$2`, fullwidth digits `１/２`, ideographic separator in save/quit, fullwidth `＆` in `Snake＆Miller`, and `－－` placeholder are preserved. Mapping `d066c8ce1066e6455f7570e76477b559359561b8`.
- `5DA7D877` 16; high-reuse map/HUD identity table preserves every JPN fixed ASCII label exactly, including `CAFETAL AROMA ENCANTADO`, `CRATER BASE`, `LOS CANTOS` variants, `TARGET`, `SNAKE`, and `GOAL`. Mapping `038d9f6c529d55601843cd57b4eaa0e1b5ba2389`.
- `5D483717` 24; AI-weapon battle/system table follows JPN rather than auxiliary narrowing: abdomen threat and direct attack semantics are retained, `潰してやる！！` keeps double exclamation, paired punctuation variants remain distinct, and `応急処置` is rendered as emergency handling rather than auxiliary override. Mapping `6ee6f323de2a440252a1ec074c6bcda76b941e0b`.
- `5D81E50B` 31; mission-record statistics table preserves fixed JPN English/rank labels exactly (`TOTAL:`, `OTHER INFORMATION`, `CO-OPS`, `OK`, etc.); Japanese report/stat fields are localized, auxiliary-added parentheses are rejected, and `項目０６/０５` retain fullwidth digits. Mapping `1d15d159468675583188638b42a72df7516ff950`.
- `5D472837` 30; Kidnapper/railgun AI-weapon battle table follows current JPN: device identity is preserved as `Kidnapper`, single/double exclamation distinctions and internal ASCII spaces remain exact, `ワイヤー射出` stays wire launch, `チェインガン掃射` stays chaingun sweep fire, and auxiliary punctuation/semantic narrowing is rejected. Mapping `b063faead0fe35dcb954b1c6552b3ed05e00c871`.
- `5D272813` 27; camera/control setup tutorial follows JPN structure: multiline button instructions and ` + ` spacing are preserved, the exact five-ideographic-space placeholder survives, and all auxiliary-added `<I=△>/<I=×>/<I=□>/<I=○>` controls are rejected because JPN contains only literal button glyphs/text. Mapping `68c46f5e9d3d775aa671a4c740cd7b6664c44cbf`.
- `5D396407` 47; Japanese-version staff/cast credits are preserved byte-for-byte from JPN: fixed English role/name identities stay unchanged, embedded name-list newlines and the producer blank line survive, JPN `REAL-TIME DEMO ARTIST` overrides auxiliary wording, and all auxiliary English-dub cast substitutions are rejected in favor of the Japanese cast. Mapping `1bc85f9ca38e07140a04ebacd75e9da9eb74f514`.
- `5D22B9C8` 31; WLAN/network and mission-restriction messages follow JPN: exact three-space placeholder, WLAN/WIRELESS OFF/ON identities, JPN `HOST` capitalization, `???`, embedded/double newlines, `$1`–`$4` order, `通信ON/OFF`, and mission equipment restrictions are preserved; auxiliary-added access-point text and ONLINE/OFFLINE substitutions are rejected. Mapping `0b96dd3d58681b0d93f279ea476a428e4db47105`.
- `5D2088CC` 47; Cunningham interrogation dialogue is restored strictly from current JPN: FOX/BIGBOSS/MISSION ruby conventions match prior mappings, shifted auxiliary wake/drug lines are corrected, Japanese line breaks and structural spaces survive, fixed identities remain authoritative, and the interrogation-policy quote keeps its exact internal spacing. Mapping `7373f726edb960785496d84739d953a65578a004`.
- `5D24C900` 62; Staff Trade network/UI table follows JPN: fixed `USER NAME`, `SEARCH HOST`, `CREATE HOST`, `TRADE`, `TRADE LOBBY`, `HOST`, `OK`, `TRADE EXECUTION`, `PARTNER'S LIST`, and `YOUR LIST` identities remain authoritative; ASCII/ideographic-space placeholders, `<I=CAN>/<I=DEC>` controls, line breaks, CO-OPS/Mother Base restrictions, and trade confirmation flow are preserved; auxiliary `(不要)`, `LOBBY`, reordered labels, and added `OK` wording are rejected where absent from JPN. Mapping `7eb5e8a825290db38d6bed76bcafd48ac9f6f9a0`.
- `5D06A8D5` 69; concurrent Mother Base log/status mapping verified against JPN before inclusion: unique indices are contiguous 0–68; `(不要)` and `#` internal markers, the salvage trailing newline, `$1/$2` ordering and trailing ASCII space, fixed ZEKE/RECRUIT/TRADE/DELIVERY/OUTER OPS identities, fullwidth `【！】` and `５０`, and `<I=DEC>/<I=CAN>` controls are preserved. Mapping `7aca7524fc56e9141815f8813c05347f86b40ee3`.
- `5D2DCCC3` 24; large-weapon/vehicle encyclopedia text follows JPN paragraph structure and exact model identities: AH56A-B/R, BTR-60PA/PB, `KPz 70`, LAV-TYPE-C/G, MBTk-70, Mi-24A/D, T-72A/U; all source line breaks/blank lines, numeric specifications, `“改”` markers, ERA/CIA/CO-OPS-style fixed terms, and anti-infantry/anti-vehicle tactical advice are retained without auxiliary model-spacing normalization. Mapping `c5a22873a33cec2f6d33477435d34214898cd4ea`.
- `5D3AF5CD` 79; Amanda/Chico cutscene dialogue restored by strict `unique_index + current JPN` binding after multiple large auxiliary shifts. Ruby count/order and semantic identities are preserved for Delegado, Mi Viejo, Comandante, Sandinista, Cigar/Cuba, CODESA, CIA, Monstruo, Nica/Frente, Compa, Irazu, Barge, Rio del Jade, Esperanza and Cacique; unique 31 ideographic-space placeholder, source line breaks, fullwidth punctuation, and unique 76 ruby-internal ` 司 令 官 ` spacing remain intact. UTF-8 byte metadata was recomputed from the final Chinese strings and read back after correction. Mapping QA commit `ed33c9d86fc9f34286132aa4ebc9be9fdba4719f`.
- `5DC1E6A9` 22; repeated weapon/class identity table follows JPN current spelling and structural typography: `LAV-typeG`, `T-72U`, `Mi-24A` remain exact; fullwidth `２`, ideographic spaces, and `・` are preserved; established AI weapon identities use `PUPA`, `CHRYSALIS`, `COCOON`, `PEACE WALKER`, `METAL GEAR ZEKE`; crossover identities align with existing project forms `TIGREX`, `LIOLAEUS`, `GEAR REX` rather than auxiliary regional normalization. Mapping `211d351c6ed0205230ec674b5f5742d7d9be98e3`.
- `5D3B05AD` 30; endgame AI/control-room dialogue follows current JPN rather than heavily shifted auxiliary references: Mammal/Reptile are normalized as `哺乳舱` / `爬虫舱`; `<R=这个国家,美国>` and `<R=遗志,WILL>` are rebuilt from JPN ruby identity; source newlines, internal/trailing ASCII spaces, deterrence/retaliation semantics, and the `6` minute countdown are preserved. Ambiguous segmented `ボスの ママルの仕業じゃない` remains conservatively rendered and review-flagged instead of being silently reinterpreted. Mapping `98a34f89390c471173aa3d83a610283faf1a2e2b`.
- `5D3B052D` 32; final approach/control-tower dialogue follows JPN current-row identity: unique 8 remains an exact single ASCII-space placeholder; `Coldman`, `Snake`, `Kaz`, `Paz`, `MSF` stay fixed; ruby controls preserve `<R=  火速  ,on the double>` including internal double spaces, `<R=撑,こた>`, `<R=『无国界之师』,MSF>`, and `<R=基地,ベース>`; JPN line breaks, ideographic/internal spaces, Soviet/Spetsnaz semantics, and control ordering are retained while shifted auxiliary lines are rejected. Mapping `4a8c4c7f6b731ef2b123bb4a5538e5d42db412c6`.
- `5D3B090D` 29; Monster Hunter crossover/Trenya dialogue follows strict current JPN binding despite heavily shifted auxiliary rows. Cat-speech `ニャ` is localized consistently as `喵`; fixed crossover name uses `Trenya` with review flag; `<R=家伙,モンスター>` and `<R=怪 物 狩 猎 ,モンスター ハンティング>` preserve ruby count/order, Japanese readings, and the latter's unusual inter-character/trailing spaces. `Pokke` Farm, `《狩猎任务》`, source newlines, ideographic spaces, line-final ASCII spaces, and cat-call punctuation are preserved. Mapping QA `dbd6f84e16bdcb69d21d61d12f3aa4f38c239a88`.
- `5D3B022D` 32; The Boss/Snake Eater flashback dialogue is restored strictly from current JPN after severe auxiliary shifting. Fixed identities use `Boss`, `The Boss`, `Snake`, `Volgin`, and `Sokolov`; `<R=弟子,サン>`, `<R=她,ザ・ボス>`, and `<R=任务,ミッション>` preserve ruby count/order and Japanese readings; source newlines, internal/trailing ASCII spaces, false-defection, forced death, public-history disgrace, Soviet nuclear-criminal and American traitor semantics remain tied to the current JPN row rather than auxiliary chronology. Mapping `f3b04de8dee2d0270cce73527a26f55d2f84f79e`.
- `5D3B050D` 33; mixed The Boss historical debriefing and current nuclear-launch approach dialogue follows JPN current-row structure. Ruby identities preserve Hero, Honor, Debriefing, Patriot, Target, and two FSLN references with Japanese/Latin readings; current mission identities keep `MSF`, `Mother Base`, `Peace Walker`, `Kaz`, `Miller`, `Snake`, `Amanda`, and `Paz`. Source line breaks, internal/trailing spaces and the space before the final FSLN ruby were QA-restored. Mapping QA `d237ba2a0e1e041549efa6e9ac44ae2e9588ed81`.

## Important review / risk notes
- Auxiliary controls absent from JPN are always rejected.
- `<R=...,...>` control count/order must remain; display text may be localized while reading may use confirmed Latin/English.
- Fixed JPN model/code/crossover/location/UI identities are not normalized from auxiliary naming.
- Source whitespace can be structural: single-space rows, trailing ASCII spaces/newlines, fullwidth spaces, control-internal spaces and exact placeholder order must survive.
- Japanese-version cast/staff credits are authoritative over English-dub substitutions.
- `LANG_SYSTEM`: JPN `576KB` overrides auxiliary `544KB`; `サイバーバル` remains unresolved/flagged.
- `LANG_MISSION_ENDTELOP`: shifted auxiliary mission-title mapping rejected.
- `LANG_MYOUTER_STAFF_COMMENT`: JPN `祖母` overrides auxiliary `mother`; source `(不要)` placeholders remain.
- `LANG_MYOUTER_TOP`: source `METAL GEAR ZEK` spelling and unique 159 trailing ASCII whitespace preserved.
- `LANG_MISSION_RESULT`, `LANG_WEAPON_TEXT`, `LANG_MISSION_INFO`: JPN controls/identities/placeholder spacing and repaired boundaries remain authoritative.

## Next resource class
`SLOT_OLANG` — **99 / 144 complete**. Continue the next unstarted small SLOT after checking for newer concurrent mappings.

## Last safe checkpoint
- Safe translation total: **11293 rows / 196 complete file_ids**.
- SLOT_OLANG: **99 / 144 complete; 1581 rows**.
- Latest completed artifact: `sol_translation_mappings/SLOT_OLANG/5D3B050D.json`.
- Latest mapping commit: `d237ba2a0e1e041549efa6e9ac44ae2e9588ed81`.
- Resume next: **next unstarted small SLOT_OLANG file_id**.
