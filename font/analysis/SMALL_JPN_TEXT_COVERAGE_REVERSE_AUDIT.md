# SMALL_JPN_TEXT_COVERAGE_REVERSE_AUDIT

## 结论

本轮只做 JPN 原文字符覆盖反推；没有修改 XPR、translation、mapping，也没有进行 EXE callsite 或 runtime probe。

- 扫描 canonical production corpus：`translations/**`，共 `26686` 条非空 `jpn_text` 记录。
- `work/luna_translation_templates/**` 的有效 production-key 记录与 `translations/**` 完全重复，因此不重复计数；其中额外的无 production index 模板行不作为实际资源记录。
- 001c 完整覆盖文本：**3778**。
- 其中 HIGH_VALUE_CANDIDATE：**1110**；其它字体也同样完整覆盖的 ORDINARY_CANDIDATE：**2668**。
- 连续 001c-complete region：**2154**；其中包含 Loading positive fixture 的 region：**2**；其余候选 region：**2151**。

`FONT_COVERAGE_CANDIDATE` 只表示字符集合与 JPN001C 完整相交；不表示已经确认 runtime 使用 001c。

## JPN/MLG comparison collection 的有效 charmap

本表的四个来源是官方 JPN `001c/00c7` 与官方 MLG `000e/0007` 的本地比较集合；不应解释为官方 JPN 的四套字体。

record 0 / fallback 不计入有效 mapped codepoint。完整逐 codepoint 导出见 [jpn_font_codepoint_sets.csv](jpn_font_codepoint_sets.csv)。

| font | XPR | records | mapped codepoints | texture | encrypted SHA256 | decrypted SHA256 |
|---|---|---:|---:|---|---|---|
| MLG0007 | `0007ccd8.xpr` | 643 | 642 | 4096x4096 | `835975f4568188ecb81e384887cc6520b57e595a88b02e12d400ec25c1f0da28` | `92db6945d00d77d6ea992e0d4947876fc3f8b747ac9efca560bff14e90ba0b87` |
| MLG000E | `000ebbe8.xpr` | 459 | 458 | 2048x1024 | `cee3223a7edee8f98209bfcdb9f63506301ea9969617c10fa58fba13cfbd2a88` | `7c3a369f52b2136e374f955296dce784bf1094a7ed3590c6548a9105c0484ff9` |
| JPN001C | `001cbbd1.xpr` | 359 | 358 | 2048x1024 | `5625066b835e6f26f310781fbbd3ef4f9ea93a77be2a4044289c11b74a767414` | `f4fdb335a56f81bee4e4a13be71f5518827ebcf42fbfa86d30d2f1de3c6dd025` |
| JPN00C7 | `00c7c9f9.xpr` | 2309 | 2308 | 4096x4096 | `1f7a18f28d0d67d7a6a65a5286a1e48c97d595829b4c99325fb2b5772b921e8d` | `31b8eb9a7c86b1429fb7fa0d12688c65c9123e307c5f0e8c42f1df67a7cd9e6b` |

## Coverage 定义

- `jpn_text` 是唯一输入；不读取 `cn_text`。
- `<R=base,ruby>` 保留 `base` 和 `ruby` 两部分，因为两者均为实际显示文字。
- 其它 `<...>` 控制/markup、`$placeholder`、printf placeholder、`{placeholder}`、换行、空格和 Unicode control/format 字符排除。
- 每条记录以去重后的实际显示字符集合计算 coverage；coverage = mapped 字符数 / visible unique 字符数。
- 001c 完整但其它任一 JPN/MLG comparison source 低于 100% 时标记 `HIGH_VALUE_CANDIDATE`；四个比较来源均为 100% 时仅标记 `ORDINARY_CANDIDATE`。

## 已知 Loading positive fixture

Loading 锚定区域为 `LOOSE_OLANG/00D0C740.csv` 的 unique_index `20–56`，排除 `33`，共 `36` 条原始 JPN 记录。
这 36 条只作为已知 positive fixture 分析，不把其 001c coverage 当成其它资源的 runtime 证明。

| unique_index | reference_index | JPN001C | MLG0007 | MLG000E | JPN00C7 | JPN |
|---:|---:|---:|---:|---:|---:|---|
| 20 | 124 | 100.00% | 76.47% | 82.35% | 100.00% | 私が知りたいのはひとつ。“真実”だ。  |
| 21 | 130 | 100.00% | 82.05% | 79.49% | 100.00% | 創られた虚構ではなく…。<br>ボスの真実…最期のボスの意志を確かめたい。<br>それこそお前が知りたい事でもあるはずだ。 |
| 22 | 136 | 100.00% | 82.35% | 79.41% | 100.00% | 愛した彼女に答えを聴くまで死ぬことも出来ない…。<br>お前と同じ、生ける屍だ。 |
| 23 | 142 | 100.00% | 78.57% | 78.57% | 100.00% | 任務という権力のために真の英雄を殺した。<br>それがお前の“忠”か？ |
| 24 | 148 | 100.00% | 84.62% | 73.08% | 100.00% | 人殺しのご褒美に貰った穢れた名をまだぶら下げているのか。 |
| 25 | 154 | 100.00% | 90.62% | 90.62% | 100.00% | 知っているぞ。<br>10年前 お前が何をしたのかも。<br>さあ 同じように殺せ。<br>ボスと同じように。 |
| 26 | 160 | 100.00% | 85.19% | 85.19% | 100.00% | 国のためでも政府のためでもない。<br>俺達は必要とされているからこそ戦う。 |
| 27 | 166 | 100.00% | 71.88% | 68.75% | 100.00% | 革命だろうが、何だろうが、<br>銃を手にひとたび暴力に訴えれば、<br>いずれは皆地獄に堕ちる。 |
| 28 | 172 | 100.00% | 85.71% | 78.57% | 100.00% | 俺達は祖国を棄てた。<br>それでも生きてる。<br>それでも戦い続ける。<br>生きる理由は他にいくらでもある。 |
| 29 | 178 | 100.00% | 72.73% | 81.82% | 100.00% | いいか、俺達に勝利はない。 |
| 30 | 184 | 100.00% | 77.78% | 83.33% | 100.00% | 私は 平和の使者よ。<br>あなたを見守ってる。 |
| 31 | 190 | 100.00% | 88.46% | 73.08% | 100.00% | 嘆いていても、平和はやってこないし、続かない。<br>自分で向かっていかなければダメなの。<br> |
| 32 | 196 | 100.00% | 86.67% | 83.33% | 100.00% | 私の名前は“ラ・パス”。<br>私は平和を守り抜く。<br>私はそのために生かされている。 |
| 34 | 208 | 100.00% | 77.78% | 72.22% | 100.00% | 真実を知っても、過去は変えられない。 |
| 35 | 214 | 100.00% | 80.77% | 76.92% | 100.00% | あんたは国も身分も過去も理想も、何もかも棄てた。<br>しかし、まだ棄ててないものがある。 |
| 36 | 220 | 100.00% | 82.50% | 70.00% | 100.00% | 一人の人間が、人間という種の終末を、背負う事なんか出来ない。<br>だからこそ、臆病な人類はこの数千年もの間、生き延びてきたんだ。 |
| 37 | 226 | 100.00% | 80.00% | 83.33% | 100.00% | 俺たちは戦うことしかできないが…<br>国家の事情に翻弄されずに生きる。 |
| 38 | 232 | 100.00% | 75.00% | 60.71% | 100.00% | 紛争地帯を渡り歩いては その都度<br>戦場に利用されるのが望みか？ |
| 39 | 238 | 100.00% | 60.87% | 47.83% | 100.00% | 中米は北米大陸と南米大陸を繋ぐ臍の緒だ。<br>我々はここが欲しい。<br> |
| 40 | 244 | 100.00% | 90.00% | 75.00% | 100.00% | あなたを『BIGBOSS』と知っての頼みだ。 |
| 41 | 250 | 100.00% | 85.00% | 70.00% | 100.00% | 最期に人が守るものは…命ではない。名声だ！ |
| 42 | 256 | 100.00% | 76.92% | 71.79% | 100.00% | 思想に失墜したザ・ボスと共に、英雄の時代は終わった。<br>これからは“感情なきシステム”が英雄になる |
| 43 | 262 | 100.00% | 78.95% | 73.68% | 100.00% | 機械は間違いを犯さない。<br>過ちを犯すのはいつも人間だ。 |
| 44 | 268 | 100.00% | 68.18% | 59.09% | 100.00% | …博士、平和は歩いては来ない。<br>お互い歩み寄るしかないのだ。 |
| 45 | 274 | 100.00% | 77.50% | 67.50% | 100.00% | 私達の目標は『完全なる抑止力』の実現にある。<br>だが『完全なる抑止力』を誕生させるためには、<br>私達の力を世界に向けて証明する必要があるのだ。 |
| 46 | 280 | 100.00% | 90.91% | 86.36% | 100.00% | 敵がいつ来るかわからないのに、のんびり飯なんか食ってられるか！ |
| 47 | 286 | 100.00% | 93.75% | 93.75% | 100.00% | いつか俺、ハンターになりたいんだ。 |
| 48 | 292 | 100.00% | 94.74% | 89.47% | 100.00% | 見たことない生き物がいたら、知らせてくれよ。 |
| 49 | 298 | 100.00% | 86.67% | 80.00% | 100.00% | …みんなで僕を子供扱いする。<br>それが耐えられなかった。もう12なのに！ |
| 50 | 304 | 100.00% | 72.22% | 77.78% | 100.00% | なんなのここの人達、味覚の野蛮人だらけじゃない！ |
| 51 | 310 | 100.00% | 84.00% | 76.00% | 100.00% | 兵器に鳥の名前を付けるなんて、鳥に対して失礼だと思わない？ |
| 52 | 316 | 100.00% | 76.92% | 69.23% | 100.00% | 森とひとつになるのはバーダーの基本よ。<br>人間の気配を感じると鳥にも異変が生じる。<br>それじゃ正確な観察は出来ないもの。 |
| 53 | 322 | 100.00% | 73.68% | 57.89% | 100.00% | 鳥の研究はやめて、空を飛ぼうかなって思う。 |
| 54 | 328 | 100.00% | 75.00% | 61.11% | 100.00% | 革命が成功したら平和な国にしたいとは思う。<br>けれど、平和をもたらすためにはまず売国奴を排除しなくちゃならない。 |
| 55 | 334 | 100.00% | 81.25% | 68.75% | 100.00% | あたし達の仲間は、まだ多いとは言えない。でも、必ず勝つ。<br>勝利か死か。革命家の宿命よ。 |
| 56 | 340 | 100.00% | 78.95% | 84.21% | 100.00% | もしかして…あんたは偉大な指導者…。<br>あたし達を…導いて…。 |

## 外部连续候选区域

下面只列出不属于已知 Loading 区域的连续候选；完整结果见 [small_jpn_candidate_regions.csv](small_jpn_candidate_regions.csv)。

| resource_class | file_id | unique_index | rows | high-value | ordinary | min 0007 | min 000e | min 00c7 | max Loading similarity | sample |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| OHD | `1E4C1146` | 0–24 | 25 | 15 | 10 | 66.67% | 66.67% | 100.00% | 0.261 | まだ終わってない！ || まだ終わってない！！ |
| SLOT_OLANG | `5D81E50B` | 0–20 | 21 | 0 | 21 | 100.00% | 100.00% | 100.00% | 0.136 | TOTAL: || SOLDIERS |
| SLOT_OLANG | `5D1A33A8` | 6–25 | 20 | 0 | 20 | 100.00% | 100.00% | 100.00% | 0.160 | GATLING GUN || A |
| SLOT_OLANG | `5D83B291` | 62–76 | 15 | 0 | 15 | 100.00% | 100.00% | 100.00% | 0.091 | OK || NO |
| SLOT_OLANG | `5D2362B8` | 9–22 | 14 | 0 | 14 | 100.00% | 100.00% | 100.00% | 0.143 | CREATE HOST || MODE |
| SLOT_OLANG | `5D74A6CA` | 7–20 | 14 | 0 | 14 | 100.00% | 100.00% | 100.00% | 0.125 | OTHERS || ITEM |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP.OLANG` | 7–20 | 14 | 0 | 14 | 100.00% | 100.00% | 100.00% | 0.125 | OTHERS || ITEM |
| LOOSE_OLANG | `007E2F18` | 260–271 | 12 | 12 | 0 | 75.00% | 61.11% | 100.00% | 1.000 | 愛した彼女に答えを聴くまで死ぬことも出来ない…。\nお前と同じ、生ける屍だ。 || 任務という権力のために真の英雄を殺した。\nそれがお前の“忠”か？ |
| SLOT_OLANG | `5D56A63D` | 655–666 | 12 | 0 | 12 | 100.00% | 100.00% | 100.00% | 0.120 | ESCORT || MECHANIC |
| STAGEDAT_OLANG | `LANG_ITEM_TEXT.OLANG` | 655–666 | 12 | 0 | 12 | 100.00% | 100.00% | 100.00% | 0.120 | ESCORT || MECHANIC |
| SLOT_OLANG | `5D52E4F8` | 355–365 | 11 | 0 | 11 | 100.00% | 100.00% | 100.00% | 0.167 | SMK G.(G) || K.PISTOL |
| SLOT_OLANG | `5D68BF67` | 8–18 | 11 | 0 | 11 | 100.00% | 100.00% | 100.00% | 0.130 | BATTLE DRESS || LIFE: |
| STAGEDAT_OLANG | `LANG_CHARAEDIT.OLANG` | 8–18 | 11 | 0 | 11 | 100.00% | 100.00% | 100.00% | 0.130 | BATTLE DRESS || LIFE: |
| STAGEDAT_OLANG | `LANG_WEAPON_TEXT.OLANG` | 355–365 | 11 | 0 | 11 | 100.00% | 100.00% | 100.00% | 0.167 | SMK G.(G) || K.PISTOL |
| SLOT_OLANG | `5D74A6CA` | 129–138 | 10 | 0 | 10 | 100.00% | 100.00% | 100.00% | 0.148 | SUBMACHINE GUN || SNIPER RIFLE |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP.OLANG` | 129–138 | 10 | 0 | 10 | 100.00% | 100.00% | 100.00% | 0.148 | SUBMACHINE GUN || SNIPER RIFLE |
| OHD | `1E4C1146` | 79–87 | 9 | 4 | 5 | 50.00% | 75.00% | 100.00% | 0.111 | 感じるぞ || 感じるぞ！ |
| SLOT_OLANG | `5D2E0FEE` | 90–98 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.167 | BLUE || BLACK |
| SLOT_OLANG | `5D52E4F8` | 314–322 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.087 | CANNON || MISSILE |
| SLOT_OLANG | `5D56AA31` | 0–8 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.125 | UNKNOWN || STAMINA |
| SLOT_OLANG | `5D83B291` | 150–158 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.167 | TDM || RES |
| SLOT_OLANG | `5DC48887` | 37–45 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.087 | CANNON || MISSILE |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP_METAL.OLANG` | 90–98 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.167 | BLUE || BLACK |
| STAGEDAT_OLANG | `LANG_WEAPON_SHORT_NAME.OLANG` | 37–45 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.087 | CANNON || MISSILE |
| STAGEDAT_OLANG | `LANG_WEAPON_TEXT.OLANG` | 314–322 | 9 | 0 | 9 | 100.00% | 100.00% | 100.00% | 0.087 | CANNON || MISSILE |
| LOOSE_OLANG | `00D0C740` | 0–7 | 8 | 5 | 3 | 87.50% | 50.00% | 100.00% | 0.213 | CO-OPS MEMBER`S FRIENDS || TO GAME SELECT |
| SLOT_OLANG | `5DDFF0A5` | 1–8 | 8 | 4 | 4 | 75.00% | 80.00% | 100.00% | 0.150 | うにゃ？ うにゃにゃ…？ || うん… |
| SLOT_OLANG | `5DA7D877` | 0–7 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.138 | CAFETAL AROMA ENCANTADO || CAFETAL AROMA ENCANTADO: ENTRANCE |
| SLOT_OLANG | `5DC48887` | 82–89 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.125 | SMK G.(G) || K.PISTOL |
| SLOT_OLANG | `5DD9B1F3` | 23–30 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.042 | $1 (WED) || $1 (TUE) |
| SLOT_OLANG | `5DE6EF4C` | 5–12 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.083 | PUMA || PIRANHA |
| STAGEDAT_OLANG | `LANG_GETTITLE_INSIGNIA_LIST.OLANG` | 5–12 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.083 | PUMA || PIRANHA |
| STAGEDAT_OLANG | `LANG_WEAPON_SHORT_NAME.OLANG` | 82–89 | 8 | 0 | 8 | 100.00% | 100.00% | 100.00% | 0.125 | SMK G.(G) || K.PISTOL |
| LOOSE_OLANG | `007E2F18` | 152–158 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.130 | GOLD || UB-NINO |
| SLOT_OLANG | `5D1A33A6` | 10–16 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.050 | M || ATTACK |
| SLOT_OLANG | `5D1A33A9` | 7–13 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.050 | M || ATTACK |
| SLOT_OLANG | `5D1A33AA` | 7–13 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.050 | M || ATTACK |
| SLOT_OLANG | `5D2E0FEE` | 27–33 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.115 | SAND || SALMON PINK |
| SLOT_OLANG | `5D56A63D` | 718–724 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.083 | AUSCAM || CHOCO-CHIP |
| SLOT_OLANG | `5D5CAF77` | 9–15 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.111 | WEAPON || USE: |
| SLOT_OLANG | `5D74A6CA` | 66–72 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.071 | MECHA SELECTOR || MECHA |
| SLOT_OLANG | `5D83B291` | 49–55 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.043 | WAIT || TIME |
| SLOT_OLANG | `5D8AED23` | 7–13 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.125 | GREETINGS || ETC |
| SLOT_OLANG | `5D97F0B2` | 1–7 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.080 | BACK || FRONT |
| SLOT_OLANG | `5DA7D879` | 0–6 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.148 | COSTA RICAN COAST || TARGET |
| SLOT_OLANG | `5DA7D87B` | 0–6 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.154 | SHOOTING RANGE || TARGET |
| SLOT_OLANG | `5DD9B1F3` | 1–7 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.136 | PRESET WORDS:%d || STAMP CARD |
| STAGEDAT_OLANG | `LANG_DEMOTELOP2.OLANG` | 9–15 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.125 | KIKUKO INOUE || HOCHU OTSUKA |
| STAGEDAT_OLANG | `LANG_ITEM_TEXT.OLANG` | 718–724 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.083 | AUSCAM || CHOCO-CHIP |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP.OLANG` | 66–72 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.071 | MECHA SELECTOR || MECHA |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP_METAL.OLANG` | 27–33 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.115 | SAND || SALMON PINK |
| STAGEDAT_OLANG | `LANG_SYSTEM.OLANG` | 9–15 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.111 | WEAPON || USE: |
| STAGEDAT_OLANG | `LANG_TITLEMENU.OLANG` | 0–6 | 7 | 0 | 7 | 100.00% | 100.00% | 100.00% | 0.130 | PRESS START BUTTON || DATA INSTALL |
| SLOT_OLANG | `5DDFF0A5` | 39–44 | 6 | 6 | 0 | 50.00% | 80.00% | 100.00% | 0.227 | 何してるの？ || どうして？ |
| SLOT_OLANG | `5DA57090` | 264–269 | 6 | 5 | 1 | 83.33% | 66.67% | 100.00% | 0.200 | やられたのか！？ || 食い止めろ！ |
| SLOT_OLANG | `5DDFF0A5` | 57–62 | 6 | 4 | 2 | 75.00% | 33.33% | 100.00% | 0.250 | えっ？ || やだ…ダメ… |
| YPK_GTT | `1C7679A5` | 193–198 | 6 | 3 | 3 | 57.14% | 57.14% | 100.00% | 0.314 | 殺したのか… || 戦士の宿命か… |
| SLOT_OLANG | `5D15C941` | 6–11 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.045 | TRD || POW |
| SLOT_OLANG | `5D1A33A7` | 6–11 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.050 | POD || P |
| SLOT_OLANG | `5D1DF209` | 72–77 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.182 | HOST SEARCH || CLIENT SEARCH |
| SLOT_OLANG | `5D2E0FEE` | 50–55 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.120 | PART02 || PART01 |
| SLOT_OLANG | `5D56A63D` | 691–696 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.071 | NKD(CHOCO) || NKD(WATR) |
| SLOT_OLANG | `5D56A63D` | 698–703 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.037 | NKD(RED) || NKD(WHITE) |
| SLOT_OLANG | `5DB4D9C8` | 42–47 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.083 | ESCORT || MECHANIC |
| SLOT_OLANG | `5DB4D9C8` | 86–91 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.071 | NKD(CHOCO) || NKD(WATR) |
| SLOT_OLANG | `5DB83C7B` | 5–10 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.154 | REMAINING TARGETS || OCCUPIED BASES |
| STAGEDAT_OLANG | `LANG_ITEM_SHORT_NAME.OLANG` | 42–47 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.083 | ESCORT || MECHANIC |
| STAGEDAT_OLANG | `LANG_ITEM_SHORT_NAME.OLANG` | 86–91 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.071 | NKD(CHOCO) || NKD(WATR) |
| STAGEDAT_OLANG | `LANG_ITEM_TEXT.OLANG` | 691–696 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.071 | NKD(CHOCO) || NKD(WATR) |
| STAGEDAT_OLANG | `LANG_ITEM_TEXT.OLANG` | 698–703 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.037 | NKD(RED) || NKD(WHITE) |
| STAGEDAT_OLANG | `LANG_MYOUTER_DEVELOP_METAL.OLANG` | 50–55 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.120 | PART02 || PART01 |
| STAGEDAT_OLANG | `LANG_MYOUTER_STAFF.OLANG` | 6–11 | 6 | 0 | 6 | 100.00% | 100.00% | 100.00% | 0.045 | TRD || POW |
| SLOT_OLANG | `5D3B0112` | 6–10 | 5 | 5 | 0 | 84.62% | 80.00% | 100.00% | 0.269 | やめて！　そうじゃない！ || 俺は…　愛する人を…　この手で…！ |
| SLOT_OLANG | `5DA57090` | 280–284 | 5 | 3 | 2 | 83.33% | 85.71% | 100.00% | 0.308 | ああ… || 敵がいるぞ！ |
| SLOT_OLANG | `5DDFF09B` | 29–33 | 5 | 3 | 2 | 93.33% | 83.33% | 100.00% | 0.242 | まだまだやれる！ || そうだな やれる！ |
| LOOSE_OLANG | `007E2F18` | 409–413 | 5 | 2 | 3 | 100.00% | 50.00% | 100.00% | 0.192 | タイトルメニューに戻りますか？ || CANCEL |
| SLOT_OLANG | `5DDFF09B` | 94–98 | 5 | 2 | 3 | 100.00% | 80.00% | 100.00% | 0.238 | どこにだ？ || まさか ボス… |
| SLOT_OLANG | `5DDFF0A5` | 11–15 | 5 | 2 | 3 | 100.00% | 75.00% | 100.00% | 0.200 | う うん… || まいりました |
| LOOSE_OLANG | `007E2F18` | 146–150 | 5 | 0 | 5 | 100.00% | 100.00% | 100.00% | 0.120 | MHT-K.MA || UB-RIKU |
| LOOSE_OLANG | `007E2F18` | 160–164 | 5 | 0 | 5 | 100.00% | 100.00% | 100.00% | 0.037 | NKD(RED) || NKD(WHITE) |

## HIGH_VALUE_CANDIDATE 说明

单条记录和高价值记录的完整清单在 `small_jpn_text_coverage_candidates.csv`：筛选 `candidate_status=FONT_COVERAGE_CANDIDATE` 且 `candidate_value=HIGH_VALUE_CANDIDATE`。这些记录的 001c 为 100%，而 MLG `0007`、`000e` 或 JPN `00c7` 至少一套低于 100%；它们比四个比较来源都能覆盖的记录更适合作为后续 SMALL_JPN 候选，但仍需 runtime 证据。

## 范围与限制

本审计只反推字符集合，不反推具体 selector、resource binding、EXE callsite 或实际渲染路径。候选区域的连续性来自同一 CSV 的 `file_id + unique_index`，不是 runtime 证明。
