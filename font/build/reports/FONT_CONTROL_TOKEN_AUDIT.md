# MGSPW production FONT control-token audit

Status: **PASS** (raw-token inventory completed; ambiguous forms are listed explicitly).

## Corpus and rule provenance

- Old five-class compiled production manifest: **91,609** rows.
- `BRIEFING_NBE`: **469** files / **5,645** physical rows.
- Total production rows audited: **97,254**.
- Scope is the current compiled object manifest plus current `translations/briefing/*.csv`; historical experiments, backups, fixtures, and reference-only text are excluded.
- Angle classification reuses the production compilers' `angle_control_signature`: valid Ruby, `<I=...>`, `<C=...>`, `<->`, and named angle controls are controls; other complete angle literals remain visible text.
- Width-bearing printf classification uses the repository's existing broad `tools/Build-FontXprV2.py` rule because `%02d` and `%2d` occur in production; this closes the Phase 1 narrow-regex boundary.
- Nested forms such as `<$1>` appear once as an angle token and once in the overlapping dollar inventory, matching the existing compiler inventory model.

## Required probe tokens

| probe | observed occurrence count | result |
|---|---:|---|
| `<MISSION>` | 0 | NOT OBSERVED |
| `<ALERT>` | 0 | NOT OBSERVED |
| `<HUNTING QUEST>` | 0 | NOT OBSERVED |
| `$NAME` | 0 | NOT OBSERVED |
| `$100` | 0 | NOT OBSERVED |
| `%s` | 136 | OBSERVED |
| `%d` | 117 | OBSERVED |
| `%02d` | 52 | OBSERVED |
| `%u` | 0 | NOT OBSERVED |
| `%x` | 0 | NOT OBSERVED |
| `%.2f` | 0 | NOT OBSERVED |
| `\r` | 132 | OBSERVED |
| `\n` | 26,476 | OBSERVED |
| `\t` | 0 | NOT OBSERVED |

## Raw token inventory

| token | occurrence_count | resource_classes | classification | classification_source | rendered_effect |
|---|---:|---|---|---|---|
| `\n` | 26,083 | BRIEFING_NBE, LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | builder rendered_text physical CR/LF/TAB rule | layout byte removed |
| `<C=FF4040>` | 2,105 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<C=R>` | 2,105 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `$1` | 797 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `$2` | 423 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `\n` | 393 | YPK_GTT | CONTROL | builder layout rule and production text encoding conventions | layout syntax removed |
| `<R=总部,ＨＱ>` | 304 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=ATK>` | 200 | BRIEFING_NBE, LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=CAN>` | 196 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=DEC>` | 177 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=前进,MOVE>` | 152 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=TM>` | 150 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `%s` | 136 | SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | tools/Build-FontXprV2.py PRINTF_RE; production format-preservation notes | syntax removed |
| `\r` | 132 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | builder rendered_text physical CR/LF/TAB rule | layout byte removed |
| `<I=△>` | 129 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `%d` | 117 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | tools/Build-FontXprV2.py PRINTF_RE; production format-preservation notes | syntax removed |
| `$1sec` | 100 | SLOT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<I=ACT>` | 96 | BRIEFING_NBE, LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=HHA>` | 85 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=AIM>` | 84 | BRIEFING_NBE, LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=ZEKE,ZEKE>` | 78 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=失去敌踪,LOST CONTACT>` | 76 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=失去目标,TARGET LOST>` | 76 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=总部,HQ>` | 76 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=MOVE>` | 55 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=RIGH>` | 55 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=CIPHER,CIPHER>` | 53 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `%02d` | 52 | SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | tools/Build-FontXprV2.py PRINTF_RE; production format-preservation notes | syntax removed |
| `<I=USE>` | 50 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=CAMERA>` | 48 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=BIG BOSS,BIG BOSS>` | 40 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=无法派出增援,NEGATIVE>` | 38 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `$3` | 37 | SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<R=老爸,MI VIEJO>` | 37 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=FSLN,SANDINISTA>` | 34 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=同志,COMPA>` | 34 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=□>` | 33 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=REG>` | 28 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=任务,MISSION>` | 26 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=STA>` | 23 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=人工智能,AI>` | 23 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=指挥官,COMANDANTE>` | 23 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=研究设施,LAB>` | 23 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=铁路货运站,TERMINAL>` | 23 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国,NICARAGUA>` | 19 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `$1MB` | 18 | STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<I=CPY>` | 18 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=CQC>` | 18 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=机器,MACHINE>` | 17 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=L2>` | 16 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=R2>` | 16 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=她,THE BOSS>` | 16 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=STANCE>` | 15 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=×>` | 15 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=CIA,LA CIA>` | 13 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<$1>` | 12 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production mapping review_flag: ANGLE_WRAPPED_$1_RUNTIME_PLACEHOLDER_PRESERVED | syntax removed; nested placeholder is not a glyph |
| `<R=侦察,SCOUT>` | 12 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国民警卫队,LA GUARDIA>` | 12 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=穷人的伞,SOMBRILLA DE POBRE>` | 12 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平,PAZ>` | 11 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=目标,TARGET>` | 11 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=区域,AREA>` | 10 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=应答,ACKNOWLEDGE>` | 10 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=零,ZERO>` | 10 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=幽灵,FANTASMA>` | 9 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=爬虫类,REPTILE>` | 9 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美国,AMERICA>` | 9 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=狙击手,SNIPER>` | 8 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<BAD STATE>` | 7 | SLOT_OLANG, STAGEDAT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<I=EQUIPWINDOW>` | 7 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=ESEARCH>` | 7 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=○>` | 7 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<PARAMETER>` | 7 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: named angle control | syntax removed |
| `<R=天堂,HEAVEN>` | 7 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=委托人,CLIENT>` | 7 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=尼加拉瓜湖,LAGO COCIBOLCA>` | 7 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=意志,WILL>` | 7 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国,AMERICA>` | 7 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=雪茄,CIGAR>` | 7 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<SKILL>` | 7 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: named angle control | syntax removed |
| `$4` | 6 | SLOT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<I=INTERROGATE>` | 6 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MACHINGUN_ZOOM>` | 6 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=FSLN,FRENTE>` | 6 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=信号情报,SIGINT>` | 6 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=塑料布,CHAMPA>` | 6 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=缓和,DÉTENTE>` | 6 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=设施,LAB>` | 6 | SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=LEFT>` | 5 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=LR>` | 5 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=先驱,PIONEER>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=十几岁,TEEN>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=发射,LAUNCH>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=山区,IRAZÚ>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=总部,LANGLEY>` | 5 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=投降,HOLD UP>` | 5 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=暗号,CIPHER>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=最高优先目标,TARGET>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=末段,TERMINAL PHASE>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=生意,BUSINESS>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=相互确保摧毁,MAD>` | 5 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=真实,NAKED>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国,NICA>` | 5 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=结局,ENDING>` | 5 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美国国家航空航天局,NASA>` | 5 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蛤蟆,SOMOZA>` | 5 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=香蕉园,BANANAL>` | 5 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=ＳＡＳ,Special Air Service>` | 5 | SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `$1F` | 4 | SLOT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `%2d` | 4 | SLOT_OLANG | PLACEHOLDER | tools/Build-FontXprV2.py PRINTF_RE; production format-preservation notes | syntax removed |
| `<->` | 4 | SLOT_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=OPTION_MUTE>` | 4 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=RELOAD>` | 4 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=SEL>` | 4 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=WEAPONWINDOW>` | 4 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=UMA,UMA>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=世外天堂,OUTER HEAVEN>` | 4 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=发展公司,CODESA>` | 4 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哺乳类,MAMMAL>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=希望,ESPERANZA>` | 4 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=新人,HOMBRE NUEVO>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=猎人,HUNTER>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美洲国家组织,OAS>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自动瞄准,AUTO AIM>` | 4 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=靶标,TARGET>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=领袖,CACIQUE>` | 4 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=驳船,BARGE>` | 4 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=高级研究计划局,ARPA>` | 4 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<狩猎任务: GEAR REX>` | 4 | SLOT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<狩猎任务: 轰龙>` | 4 | SLOT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<狩猎任务: 雄火龙>` | 4 | SLOT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `$1KB` | 3 | SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `$3m` | 3 | LOOSE_OLANG, SLOT_OLANG, STAGEDAT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<I=CONF>` | 3 | LOOSE_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=KEY_TAB>` | 3 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=TITLE_START>` | 3 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=CIA,COLDMAN>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『无国界军队』,MSF>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=业,KARMA>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=举手投降,HOLD UP>` | 3 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=他们,CIA>` | 3 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=伏击,AMBUSH>` | 3 | BRIEFING_NBE, SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=六边形,HEX>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=原爆伤害调查委员会,ABCC>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=命令,ATTENTION>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平,LA PAZ>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平行者计划,PEACE WALKER>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=咖啡园,CAFETAL>` | 3 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地狱,HELL>` | 3 | BRIEFING_NBE, SLOT_OLANG, STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=她,MAMMAL POD>` | 3 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=尼加拉瓜人,NICA>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怪物,MONSTER>` | 3 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怪物,MONSTRUO>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=悬挂,ELUDE>` | 3 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=我们必胜,VENCEREMOS>` | 3 | SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=指示,TAGGING>` | 3 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=未确认动物,UMA>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=本体,PLATFORM>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=洲际弹道导弹,ICBM>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=米,ARROZ>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=联系,CALL>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=观鸟者,BIRDER>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=象征,ICON>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这里,MOTHER BASE>` | 3 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=长矛,SPEAR>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=香烟,CIGARETTE>` | 3 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<I=ETAG>` | 2 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=KEY_F>` | 2 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=PAUSE>` | 2 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=ZOOMIN>` | 2 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=ZOOMOUT>` | 2 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=0,ZERO>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=30瓦拉,25m>` | 2 | SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Basilisk,Basilisco>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=EVA,EVA>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=SALT II,SALT II>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Z,ZULU>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『OUTER OPS』,OUTER OPS>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『UMA』,UMA>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=两人一组,TWO-MAN CELL>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=了解,READY>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=代表,DELEGADO>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=任务报告,DEBRIEFING>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=伟大力量,英雄度>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=何处,哪里>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=你,SNAKE>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=便携式,PORTABLE>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=假想敌国,某个国家>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=刺客,ASSASSIN>` | 2 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=卷烟,CIGARETTE>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=呼叫,CALL>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哈德河,RIO DEL JADE>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哥斯达黎加发展公司,CODESA>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=喜悦,JOY>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国家军事指挥中心,NMCC>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=圣约翰,San Juan>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=圣胡安河,Río San Juan>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地图,MAP>` | 2 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=均衡,BALANCE>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=基地,BASE>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=夜视装置,NVG>` | 2 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大脑AI,MAMMAL POD>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=天堂,CIELO>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=奇怪,STRANGE>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=女人,人>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=存 在 主 义,EXISTENTIALISME>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=存储程序,STORED PROGRAM>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=孩子,CHICO>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=宇宙船,MERCURY>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=年龄,AGE>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=幽灵,GHOST>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=弟子,SON>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=我们,SANDINISTA>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=扫荡,clearing>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=拉丁美洲禁止核武器组织,OPANAL>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=指 挥 官,COMANDANTES DE LA REVOLUCION>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=指定,TAGGING>` | 2 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=放射性沉降物,FALLOUT>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=本国,AMERICA>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核　炮　弹,DAVY CROCKETT>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=桑地诺派,FRENTE>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=母基地,MSF PLANT>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=混蛋,son of a bitch>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=潜伏特工,SLEEPER>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=爱国者,PATRIOT>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=狙击,SNIPE>` | 2 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=狩猎,HUNT>` | 2 | BRIEFING_NBE, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=狼,Lobo>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=知识,KNOWLEDGE>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=私生女,BASTARD>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=第一设计局,OKB-1>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=级,CLASS>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=结局,WILL>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美国,STATES>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美国政府,WHITE HOUSE>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胜利,VICTORY>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=脏活,BLACK OPS>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=英雄,HERO>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=荣誉,HONOR>` | 2 | BRIEFING_NBE, SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蜂巢,HONEYCOMB>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=近身战斗训练设施,KILL HOUSE>` | 2 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这里,COSTA RICA>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=选项,OPTIONS>` | 2 | SLOT_OLANG, YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那家伙,Chicolibri>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=部队,FRENTE>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=雪茄,CUBA>` | 2 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=马卡龙,MACAROON>` | 2 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<狩猎任务：Gear REX>` | 2 | STAGEDAT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<狩猎任务：轰龙>` | 2 | STAGEDAT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<狩猎任务：雄火龙>` | 2 | STAGEDAT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `$1m` | 1 | SLOT_OLANG | PLACEHOLDER | production compiler DOLLAR_RE / docs/TECHNICAL_FOUNDATION.md §5 | syntax removed |
| `<ADD STAGE>` | 1 | LOOSE_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<Add Stage>` | 1 | SLOT_OLANG | VISIBLE | production compiler angle_control_signature: non-control angle literal | literal angle-bracket text retained |
| `<I=AUTOAIM>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=COOPS_CANCEL>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=COOPS_COMMS>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=DIR>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=EXTRA_PLAY_STOP>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=KEYCAN>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=KEYDEC>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=KNOCK_WALL>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_IT_*INFO_MODEL>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_IT_*INFO_TOP>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_IT_*INFO_TOP_JAMP_0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_IT_*INFO_TOP_JAMP_1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_MECHA_*INFO_TOP>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_METAL_*INFO_HELP_MODEL_VIEW01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_METAL_*INFO_HELP_MODEL_VIEW02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_WP_*INFO_MODEL>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_WP_*INFO_TOP>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_WP_*INFO_TOP_JAMP_0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_DEV_WP_*INFO_TOP_JAMP_1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*HELP_CONTENT1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*HELP_CONTENT2>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER01_ASSIGN01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER01_ASSIGN02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER02_ASSIGN01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER02_ASSIGN02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER04_ASSIGN01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER04_ASSIGN02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER05_ASSIGN01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER05_ASSIGN02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER06_ASSIGN01>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MODEL_VIEWER_*VIEWER06_ASSIGN02>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MO_STATUS_*HELP_CONTENT1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_MO_STATUS_*HELP_CONTENT2>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_STAFF_*INFO_DETAIL_VIEWER_0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_STAFF_*INFO_DETAIL_VIEWER_1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_TRADE_EXE_*INFO_WAIT_CLIENT_INVITE>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=MO_TRADE_EXE_*INFO_WAIT_CLIENT_PARTY>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=PADCAN>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=PADDEC>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=PADSTA>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=QUITAIM>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=SAW_L>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=SAW_R>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=TAB_LEFT>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=TAB_RIGHT>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=TOGGLE_ZAPPIN>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=UD>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=VSOPS_START>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=WALK>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=aipod_menu_*AIPOD_RSRC_IDX_KEYHELP>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=charaedit_lang_*suit_equip_help>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=item_exp_IT_EQ_LOVE_CBOARD_R1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=kotodamaedit_lang_*helptext>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=mo_cyberval_log_*Log_KeyHelpText>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=pw_extra_dummy_*key_square>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=pw_extra_dummy_*key_tri1>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=pw_title_option_dummy_*keyhelp_voice>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=v906_135_gam_inst_2_*0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=v906_138_gam_inst_2_*0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=v906_139_gam_inst_2_*0>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_AK47_A_R2>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_AK47_B_R2>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_A_R4>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_A_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_A_SHT_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_B_GRN_R4>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_B_R4>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_B_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_C_R4>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_M16A1_C_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_XM177_A_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_XM177_B_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<I=weapon_exp_WP_XM177_C_R5>` | 1 | LOOSE_OLANG | CONTROL | production compiler angle_control_signature | syntax removed |
| `<R=10年,DECADE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=14瓦拉,12m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=1954年的试验,CASTLE BRAVO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=1瓦拉,80cm>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=2瓦拉,1.6m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=2瓦拉,约1.6m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=3瓦拉,2.5m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=4瓦拉,3m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=70瓦拉,50m>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=A,ALPHA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Boss的仿制品,AI>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=CIA,COMPANY>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=CIA,THEM>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=C　4,Composition 4>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=FOX,FOX>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=FSLN战士,SANDINISTA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Frontières,FRONTIÈRES>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Gálvez教授,KGB>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=HU-1,HUEY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=KGB,LUBYANKA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=KGB,TSENTR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=KGB,Tsentr>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=MAMMAL POD,AI>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=MAMMAL POD,THAT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=MIRV,分导式多弹头>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=MSF,MSF>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=MSF,我们>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Militaires,MILITAIRES>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=NASA的发射场,CAPE CANAVERAL>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=NORAD,CHEYENNE MOUNTAIN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=NORAD,NORAD>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=RDS-220,沙皇炸弹>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Sans,SANS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=V,PEACE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=ZEKE,这个>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=Zero,CIPHER>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=chrysalis,CHRYSALIS>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=‘凤尾绿咬鹃’,Resplendent Quetzal>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=‘成虫’,Imago>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=‘捉迷藏’结束了。说吧，你是谁？,Fini de jouer a cache-cache. Dit moi qui tu es.>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“从此幸福地生活”,HAPPY EVER AFTER>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“儿子们”,BACKUP PLAN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“她”,MAMMAL POD>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“怪物”,METAL GEAR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“教授”,GALVEZ>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“机器中的幽灵”,GHOST IN THE MACHINE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“永远走向胜利”,Hasta la victoria siempre>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“潜友”,FRIEND>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=“长矛”,SPEAR>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『DELIVERY』,DELIVERY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『RECRUIT』,RECRUIT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『TRADE』,TRADE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『ZEKE』,ZEKE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『世外天堂』,OUTER HEAVEN>` | 1 | STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『任务』,MISSION>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=『新人』,HOMBRE NUEVO>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=一 击 必 杀,one shot one kill>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=专家,EXPERT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=世界,COMMUNE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=中南美洲,LATIN AMERICA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=中央保安部,CSS>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=中美洲,这边>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=乐园,ELYSIUM>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=乐园,哥斯达黎加>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=乳之森,Selva de la Leche>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=争取民心行动,Hearts and Minds>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=亡灵,GHOST>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=亲美政权,SOMOZA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=人　形,IVAN IVANOVICH>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=人力情报,HUMINT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=他,THE SORROW>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=他人,HITO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=他们,FSLN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=代号,CODE NAME>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=休息,休息>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=伙伴,FSLN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=伪装,Camouflage>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=伪装,模拟>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=你,VOS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=你的基地,MOTHER BASE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=依赖,RELY>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=便携式核炮弹,DAVY CROCKETT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=保护对象,红色名录>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=借来,抄来>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=偏远地区,偏远地区>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=公海,OFFSHORE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=公牛鲨,tiburón toro>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=共产主义者,RED>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=共情能力,EMPATHY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=冲突,CONFLICT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=准军事部队,PARAMILITARY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=出 口 主 义,EXITENTIALISME>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=分类学家,Taxonomist>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=初始目标,TARGET>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=制服,西装男>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=加勒比海对岸,CUBA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=加勒比海沿岸,CARIBBEAN COAST>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=加州理工学院,CALTECH>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=北美防空司令部,NORAD>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=千层酥,MILLE-FEUILLE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=半岛战争,西班牙独立战争>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=半瓦拉,40cm>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=危险,RISK>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=原住民,indígena>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=参谋部民政局,GS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=参谋长联席会议主席,CJCS>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=反政府组织,FSLN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=口粮,RATION>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=古典,CLASSIC>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=可否认的,DENIABLE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=合众国,美国>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=同伴,COMPA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=同步,Sync>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=同源异形词,doublet>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=否则只有死亡,VICTORIA O MUERTE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=启动,启动>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=命,LIFE槽>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=命中精度,CEP>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平,KAZUHIRA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平,PEACE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=和平行者,这家伙>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哥伦比亚,这里>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哥斯达黎加,这里>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=哥斯达黎加人,Tico>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=噩梦,FICTION>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=回收,RECOVERY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=回收地点,GOAL>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国境,圣胡安河>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国家侦察局,NRO>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国家安全局,NSA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国防,D>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国防情报局,DIA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国防部语言学院,DLI>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=国防高级研究计划局,DARPA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=圈,CO-OP环>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=圈,环>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地　狱,OUTER HEAVEN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地下核试验限制条约,TTBT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地点 B,POINT BRAVO>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地点,LOCATION>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=地点,POINT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=基因,GENE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=基地,基地>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=复合长波信号,MLF>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=外星人带来的怪物,ALIEN ANIMAL>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=外来者,WALKER>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大二,SOPHOMORE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大家,FRENTE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大战期间,ONCE>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大本营,MOTHER BASE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=大锅,CALDERA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=奇爱博士,DR. STRANGELOVE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=她,KUDRYAVKA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=她,PEACE WALKER>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=她,STRANGELOVE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=她们,FSLN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=委托,提议>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=威慑力,话>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=子弹,子弹>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=官方记录,DEBRIEFING>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=实验体,GUINEA PIG>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=家伙,MONSTER>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=家畜,CATTLE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=宿命,KARMA>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=对接,JOINT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=将军的名字,Sandino>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=小型核弹头,DAVY CROCKETT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=小战士,奇科>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=尼加拉瓜人民,NICA>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=居住区,BARRACKS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=工作,BUSINESS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=巴黎马卡龙,MACARON PARISIEN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=干得不错,Well done>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=干扰,BLACKOUT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=弹出式,POP-UP>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=弹道导弹预警系统,BMEWS>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=强制收容所,LAGER>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=当地特工,AGENT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=征兆,迹象>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=待机,STANDBY>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=忠诚,loyalty>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怀古录,NOSTALGIA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怪 物 之 岛,ISLA DEL MONSTRUO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怪物狩猎,MONSTER HUNT>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=怪物狩猎,MONSTER HUNTING>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=悲伤,Sorrow>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=情 报 机 构,INTELLIGENCE COMMUNITY>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=成交,DEAL>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=成果,WAZA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=我们,日本人>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=我们的Boss,SNAKE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=战争之犬,DOGS OF WAR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=战士,War fighter>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=战士,war fighter>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=战略武器限制谈判,SALT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=战略空军,SAC>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=房间,APPARTEMENT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=手榴弹,pineapple>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=扮演角色,ROLE PLAY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=技术人员,TARGET>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=抓走,abduct>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=抓走,raptar>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=拿手好戏,惯用手段>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=掠过,FLY PAST>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=掩护,COVER>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=搭档,Miller>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=撑,承受>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=操作,ACTION>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=支援,BACKUP>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=改装,TUNE-UP>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=攻击直升机,GUNSHIP>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=政府机关报,IZVESTIA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=故乡,美国>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=敌兵,LIVE TARGET>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=无人飞机,UAV>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=无国界军队,MILITAIRES SANS FRONTIÈRES>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=无国界军队,MSF>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=旱季,Dry Season>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=暴徒,NOMAD>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=最后思念,遗愿>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=有钱人,BOURGEOIS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=未确认飞行物体,UFO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=本 体,PLATFORM>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=杏仁粉,POUDRE D'AMANDE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核不扩散条约,NPT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核弹头,CARGO>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核当量,YIELD>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核心,FOCO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=核武器,Davy Crockett>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=桑地诺民族解放阵线,FSLN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=欢喜,JOY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=死之灰,FALLOUT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=死手,DEAD HAND>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=母基地,PLANT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=毒品,COCAINE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=民兵,MINUTEMAN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=河边据点,RIO DEL JADE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=法国人吗,A French...>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=泡芙,CHOU A LA CREME>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=泥,El Cenegal>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=活死人,LIVING DEAD>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=流浪之民,NOMAD>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=流浪者,Nomad>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=海洋温差发电,OTEC>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=消灭叛徒计划,食蛇者行动>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=潜入任务,SNEAKING MISSION>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=火速,on the double>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=灵魂,ESPÍRITU>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=灵魂,GHOST>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=炸弹皇帝,TSAR BOMBA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=热带云雾林,CLOUD FOREST>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=热带云雾林,JUNGLE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=热血,Hot>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=熔岩之路,Camino de Lava>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=爆药保管库,IGLOO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=爱国心,patriotism>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=特效,SFX>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=特权阶级,NOMENKLATURA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=犹豫,迟疑>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=狙击,sniping>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=猎犬,hound>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=理由,缘由>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=生命,LIFE>` | 1 | STAGEDAT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=电子计算机,COMPUTER>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=电子防谍,SIGINT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=电磁挠痒棒,LAUGHING ROD>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=电磁脉冲,EMP>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=盟军最高司令官总司令部,GHQ>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=目的,任务>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=着陆,LANDING>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=瞄准线,LOS>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=研究室,LAB>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=研究所,LAB>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=确认处理,确认>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=碍事,PESKY>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国,尼加拉瓜>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国或死亡,Patria o Muerte>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国自由或死亡,Patria Libre o Morir>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=祖国自由，或死亡,PATRIA LIBRE O MORIR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=秘密军事组织,OAS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=稻草人,DECOY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=空,CIPHER>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=空中指挥所,COVERALL>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=空投区,DROP ZONE>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=突然变异,MUTATION>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=站长,Station Chief>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=第一代索摩查,Tacho>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=第二次战略武器制,SALT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=策划,策划>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=糕点师,PATISSIER>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=组织,MSF>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=终结,THE END>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=结合,ASSEMBLE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=结束,游戏结束>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=绞刑架,El Cadalso>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=绿色,VIRIDIAN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=美国国防部,五角大楼>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=老兵,veteran>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=耶稣,Jesús>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=联络船,GONDOLA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=背叛,SOMU>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胜利,VICTORIA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胜利,Victory>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胜利或死亡,Victoria o Muerte>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胜利的,VIC>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=胡言乱语,胡话>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=能有,NEED>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=脆弱,薄弱>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=脚,PEACE WALKER>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自主步行核兵器,移动发射台>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自动报复,Fail-deadly>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自尊,武士>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自己人,COLDMAN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自然活动,SIGNATURE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=自由人的将军,General de Hombres Libres>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=船,MERCURY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=苏军总参谋部情报总局,GRU>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=苏联第一设计局,OKB-1>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=英国人,SAS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=英雄,THE BOSS>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=茧,Cocoon>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=葫芦,porongo>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蒸汽机车,SL>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蛇,SERPIENTE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蛇王,Basilisco>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蛹,Pupa>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=蜂鸟,COLIBRI>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=行动,MISSION>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=行政中枢,WASHINGTON DC>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=被你找到了,Ah, tu m'as trouve!>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=装备,items>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=西瓜,sandía>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=计划,GAME>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=设计局,OKB-1>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=误射同伴,友军误伤>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=说到底,SHOSEN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=谈,II>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=谈判专家,NEGOTIATOR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=费南雪,FINANCIER>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=辅助人员,Para>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=边境,NICARAGUA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=过错,MISTAKE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这一带,COSTA RICA>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这个国家,美国>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这次我当鬼,C'est moi le loup!>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=这边,MOTHER BASE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=追捕,HUNT DOWN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=通信结束,OUT>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=遗志,WILL>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=遗迹,实验室>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=遥测,TELEMETRY>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=避风港,HAVEN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那个AI,MAMMAL POD>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那个女人,STRANGELOVE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那孩子,PAZ>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那家伙,COLDMAN>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那帮家伙,CIA AND KGB>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=那座搬运设施,PUERTO DEL ALBA>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=金刚石,bort>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=金属齿轮,METAL GEAR>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=长期人民战争派,GPP>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=闪电泡芙,ECLAIR>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=防弹衣,body armor>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=阶段,PHASE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=附加内容,EXTRAS>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=集装箱,TARGET>` | 1 | YPK_GTT | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=零式,ZEKE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=预先,ADVANCE>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=领导者,COMANDANTE>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=飞行,FLIGHT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=饭,GALLO PINTO>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=马,ANDALUSIAN>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=马卡罗尼,MACARONI>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=马卡龙,MACARON>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=麻省理工学院,MIT>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=黄金之国,Zipangu>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=黄金果实,fruta de oro>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=黑豆,FRIJOLES>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=鼻烟,鼻烟>` | 1 | SLOT_OLANG | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |
| `<R=龙,DRAGON>` | 1 | BRIEFING_NBE | CONTROL | production compiler angle_control_signature: RUBY; docs/TECHNICAL_FOUNDATION.md §5 | base and reading payload retained; delimiters removed |

## Ambiguous tokens

Ambiguous distinct tokens: **0**.

None found in the current production corpus.

## Charset consequence

Only CONTROL and PLACEHOLDER syntax is removed by the builder. VISIBLE angle literals remain glyph text. AMBIGUOUS forms, if any, remain in the rendered stream and are reported instead of being silently deleted.
