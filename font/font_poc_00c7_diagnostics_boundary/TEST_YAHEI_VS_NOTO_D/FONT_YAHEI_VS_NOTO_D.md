# FONT_YAHEI_VS_NOTO_D

CONTROL_D = runtime PASS

YAHEI_REGULAR_BEST =
font file: C:\Windows\Fonts\msyh.ttc
actual family/style: ['Microsoft YaHei', '微软雅黑'] / ['Arrunta', 'Navadno', 'Normaali', 'Normal', 'Normale', 'Normalny', 'Normál', 'Normálne', 'Regular', 'Standaard', 'Standard', 'obyčejné', 'Κανονικά', 'Обычный']
px: 57
offset: x=-1, y=0
bbox: [0, 7, 56, 59]
coverage: 38.24%
gray mean: 206.995

YAHEI_BOLD_BEST =
font file: C:\Windows\Fonts\msyhbd.ttc
actual family/style: ['Microsoft YaHei', '微软雅黑'] / ['Bold', 'Fet', 'Fett', 'Félkövér', 'Gras', 'Grassetto', 'Halvfet', 'Kalın', 'Krepko', 'Lihavoitu', 'Lodia', 'Negreta', 'Negrita', 'Negrito', 'Pogrubiony', 'Tučné', 'Vet', 'fed', 'tučné', 'Έντονα', 'Полужирный']
px: 55
offset: x=0, y=0
bbox: [1, 8, 56, 59]
coverage: 50.335%
gray mean: 217.133

STATIC_RECOMMENDATION = D
FINAL_RUNTIME_WINNER = PENDING

## 三者对比

| 版本 | 来源 | size | offset | bbox | coverage | gray mean | runtime |
|---|---|---:|---|---|---:|---:|---|
| D | Noto Sans SC Bold | 56 | control | `[2, 7, 56, 59]` | 47.658% | 215.07 | PASS |
| Y1 | Microsoft YaHei Regular | 57 | `-1,0` | `[0, 7, 56, 59]` | 38.24% | 206.995 | PENDING |
| Y2 | Microsoft YaHei Bold | 55 | `0,0` | `[1, 8, 56, 59]` | 50.335% | 217.133 | PENDING |

## 字体 metadata

- Regular 实际 metadata：`{"file": "C:\\Windows\\Fonts\\msyh.ttc", "face_index": 0, "family_name_id_1": ["Microsoft YaHei", "微软雅黑"], "subfamily_name_id_2": ["Arrunta", "Navadno", "Normaali", "Normal", "Normale", "Normalny", "Normál", "Normálne", "Regular", "Standaard", "Standard", "obyčejné", "Κανονικά", "Обычный"], "full_name_id_4": ["Microsoft YaHei", "微软雅黑"], "postscript_name_id_6": ["MicrosoftYaHei", "MicrosoftYaHeiRegular"]}`
- Bold 实际 metadata：`{"file": "C:\\Windows\\Fonts\\msyhbd.ttc", "face_index": 0, "family_name_id_1": ["Microsoft YaHei", "微软雅黑"], "subfamily_name_id_2": ["Bold", "Fet", "Fett", "Félkövér", "Gras", "Grassetto", "Halvfet", "Kalın", "Krepko", "Lihavoitu", "Lodia", "Negreta", "Negrita", "Negrito", "Pogrubiony", "Tučné", "Vet", "fed", "tučné", "Έντονα", "Полужирный"], "full_name_id_4": ["Microsoft YaHei Bold", "Microsoft YaHei Fet", "Microsoft YaHei Fett", "Microsoft YaHei Félkövér", "Microsoft YaHei Gras", "Microsoft YaHei Grassetto", "Microsoft YaHei Halvfet", "Microsoft YaHei Kalın", "Microsoft YaHei Krepko", "Microsoft YaHei Lihavoitu", "Microsoft YaHei Lodia", "Microsoft YaHei Negreta", "Microsoft YaHei Negrita", "Microsoft YaHei Negrito", "Microsoft YaHei Pogrubiony", "Microsoft YaHei Tučné", "Microsoft YaHei Vet", "Microsoft YaHei fed", "Microsoft YaHei tučné", "Microsoft YaHei Έντονα", "Microsoft YaHei Полужирный", "微软雅黑 Bold"], "postscript_name_id_6": ["MicrosoftYaHei-Bold"]}`
- 两个候选都直接从已实机通过的 D 结构生成，仅改变 `厥` atlas slot；没有改变 glyph count、charmap、GlyphRecord、metrics、USER、UV 或 XPR descriptors。

## 参考字与限制

对照图包含当前 MLG 的 `昏、眩、晕、棒、器、厢、厌、决、卷`，以及 D/Y1/Y2。静态指标只用于筛选；D 已有实机优势，Y1/Y2 不能仅凭统计指标判定胜出。

- 对照图：`D:\GAME\test\steam 合金装备大师合集2 合金装备和平行者汉化补丁\JPVoice_CNText_V2\font\font_poc_00c7_diagnostics_boundary\TEST_YAHEI_VS_NOTO_D\yahei_vs_noto_d.png`
- XPR：`CONTROL_D/00c7c9f9.xpr`、`Y1_BEST_REGULAR/00c7c9f9.xpr`、`Y2_BEST_BOLD/00c7c9f9.xpr`。
- 详细参数、SHA256、保护检查和 metadata：`yahei_vs_noto_d_manifest.json`。

当前结论：D 保持现有 fallback profile；Y1/Y2 等待用户实机比较。暂停批量生成和正式 FONT builder 修改。
