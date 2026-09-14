# V1 实机问题与下一轮修复标准

更新时间：2026-09-14（Asia/Hong_Kong）

状态：`OPEN`

本文件记录第一版完整测试包的实机反馈。现有自动检查已经证明目标资源可以完成结构、容量、控制符、metadata、allocation 和 parser round-trip；运行时资源覆盖、任务结算字段、BRIEFING 排版和固定 UI 长文本已通过当前实机验收。当前剩余重点为字库覆盖，因此版本仍定义为 **V1 完整测试版**，尚不是正式发布版。

## 总体结论

当前需要补充的验收层有五类：

1. 字库 codepoint/glyph 覆盖。
2. 游戏运行时实际读取资源的文本覆盖。
3. 界面语境中的翻译正确性。
4. 屏幕文本框的可视宽度、行数和换行。
5. 原版英文、数字、符号及 UI 字形回归保护。

后续修复仍须从 clean JPN original 统一构建。不得直接修改测试 DAT，也不得因为实机问题而放弃已经验证的 JPN-authoritative 结构规则。

## ISSUE-001：中文缺字显示为点或方框

优先级：`P0`

状态：`OPEN`

### 实机已观察事实

- 部分应为汉字的位置显示为居中点 `·`。
- 部分应为汉字的位置显示为方框 `□`。
- 已观察到的显示形态包括：
  - `……我·来……利·言。`
  - `虽然经验还□，但会说7种语言。`
  - `你□升为英雄BIG BOSS。`
  - `被击中的对手会承受不住而昏□`
  - `要□束对手，`
- 未翻译的日文无线电中也有部分日文字符显示为方框。

### 尚未确认

- 个别 `·` 是否已经存在于正式 `cn_text`，还是由缺失 glyph/fallback glyph 产生。
- 三个 XPR 字体文件各自负责的界面、字号和 glyph 表范围。
- 缺字是 glyph bitmap 缺失、codepoint→glyph 映射缺失，还是错误覆盖原 glyph index。

### 修复要求

1. 对每个截图文本先核对正式 `cn_text`，区分“译文本身错误”和“字库渲染错误”。
2. 建立最终补丁全部可见文本 codepoint 清单。
3. 字库至少覆盖最终中文、仍保留的日文、ASCII、拉丁字母、数字、标点和必要符号。
4. 不再假设三份 XPR 可以用同一种方式整体替换；应先确定各字体用途。
5. 中文字形扩充不得破坏原有 glyph index、UI 字符和字体度量。

### 验收标准

- 所有已报告场景不再出现非预期 `·`、`□` 或空白字形。
- 最终译文所用的每个 codepoint 均能映射到有效 glyph。
- 未被汉化但运行时仍可能出现的日文不会因中文字库而变成方框。
- ASCII、英文、数字、标点和按钮符号保持正常。

## ISSUE-002：任务结束后的无线电仍为日文

优先级：`P0`

状态：`RESOLVED_INGAME_2026-09-14`

### 实机已观察事实

- 任务结束后出现的 Miller/Snake 无线电文本仍为完整日文。
- 当前统一包中的 241 个 file_id 没有使这段运行时文本变为中文。
- 日文内容涉及《特拉特洛尔科条约》、据点位置及路线情报等对话。

### 2026-09-14 实机回归

- 加入 BRIEFING 的新候选包已在任务结束无线电路径中实机命中，文字已显示为中文。
- 人物立绘、说话人和文本调用均正常；原“完整日文残留”问题可标记为已解决。
- 同次测试发现中文长句不会由该界面自动换行，会越出屏幕；该残留问题单独记录为 ISSUE-006，不重新打开运行时资源覆盖问题。

### 解决结论

- 该路径属于此前尚未进入旧五类 production 的 BRIEFING MISSION oEbN 文本；纳入冻结的 106 blocks / 835 rows 后，运行时已正确命中中文。
- BRIEFING FILES 与 MISSION 保持独立物理 row、独立 translation unit 和 clean-JPN fixed-layout 构建，没有按相邻 ordinal 猜测或改写结构。
- 运行时资源覆盖问题至此关闭；换行和可视宽度不属于该问题，继续由 ISSUE-006 跟踪。

### 验收标准

- 同一任务结束后的整段无线电均显示中文。
- 对话人物、顺序和触发时机正确。
- 不再出现日文残留或因字库缺失产生的方框。
- 新资源继续满足 JPN metadata/结构保留和 clean-JPN rebuild 原则。

## ISSUE-003：任务结算武器经验字段译文异常

优先级：`P1`

状态：`RESOLVED_INGAME_2026-09-14`

### 实机已观察事实

- `MISSION RESULT` 画面的“武器经验值”区域中，动态等级和经验数字（如 `LV.1(+109)`）正常。
- 每个武器条目最右侧的固定文本显示为无意义或乱码式中文。
- 同一异常文本在多个武器条目中重复出现。

### 2026-09-14 实机回归

- 当前统一包实机测试中，任务结算武器经验字段显示通过，动态等级、经验数字和固定字段均未发现异常。
- 本次仅记录运行时验收结果；具体原因尚未确认，不据此反推 mapping、reference 或 control token 的修改原因。

### 解决结论

- 该问题暂不再作为当前生产阻塞。
- 保留原始调查记录，若后续再次出现，应按 file_id、reference、场景和运行时截图重新定位，不直接修改已通过的译文。

### 历史调查记录

- 原因是译文语义错误、短文本跨上下文误复用、辅助 reference 错位，还是控制符/参数附近的映射错误。
- 该字段的准确日文原文及运行时用途。

### 修复要求

1. 定位该字段对应的 JPN file_id/reference/object。
2. 查看整个任务结算界面上下文和原日文含义。
3. 不因完全相同的短日文或辅助候选而跨界面套用错误译文。
4. 保持武器名、`RANK`、`LV`、经验数字和运行时参数不变。

### 验收标准

- 右侧字段显示自然、准确、统一的中文。
- 三个武器条目的动态数字和等级仍然正确。
- 不出现乱码、缺字、错误控制参数或跨列错位。

## ISSUE-004：固定 UI 长文本超出可视区域

优先级：`P1`

状态：`RESOLVED_INGAME_2026-09-14`

### 实机已观察事实

- 标题阶段“注意事项”页面的长文本横向超出面板和屏幕边界。
- 文本左右均被裁切，当前换行不能适应该界面的固定宽度。
- 现有 UTF-8/container capacity 检查没有检测出该问题。

### 2026-09-14 实机回归

- 当前统一包实机测试中，固定 UI 长文本已能在目标分辨率和 UI 比例下完整显示。
- 未发现左右裁切、遮挡按钮或标题、行间重叠及底部裁切。

### 解决结论

- 固定 UI 长文本验收通过，不再作为当前 MVP 阻塞。
- 后续新增或改动文本仍需执行显示宽度和换行回归。

### 结论

这是 **visual layout overflow**，不同于 GTT hard capacity、OLANG body size 或 SLOT block overflow。二进制能容纳文本，不代表游戏 UI 能完整显示。

### 修复要求

1. 为固定宽度 UI 增加独立的显示宽度/行数审核。
2. 优先使用符合原意的简洁译文；必要时加入明确换行。
3. 参考原 JPN 界面的最大行数、文本框宽度和安全边距。
4. 长法律文本、帮助说明、人物介绍和任务说明作为重点排版对象。

### 验收标准

- 文本不超出左右边界。
- 不遮挡按钮、标题或其他行。
- 不发生行间重叠或底部裁切。
- 在目标分辨率和当前 UI 比例下可以完整阅读。

## ISSUE-005：标题界面英文菜单字形消失

优先级：`P0`

状态：`VERIFIED_INGAME`

### 实机已观察事实

- 标题画面中仍能看到菜单选择条，但 `NEW GAME`、`DELETE` 等英文菜单字符没有显示。
- 游戏标题本身和部分其他英文仍能正常显示，说明不同标题/UI 元素可能使用不同字体资源或 glyph 区域。

### 已确认

- 缺失菜单由日版小号 UI 字体负责；该字体没有本次新增的中文 glyph。
- 保留 JPN ASCII 标签可以复用原有 glyph index、映射和字体度量。

### 2026-09-09 定位结果

- 标题菜单来自 loose OLANG `007E2F18`。
- JPN 原文为 ASCII：`NEW GAME`、`LOAD GAME`、`DELETE`。
- V1 正式译文将其改成了 `新游戏`、`载入游戏`、`删除`。
- 该标题菜单使用未扩充中文的日版小号 UI 字体，因此选择条仍存在，但三个中文标签无法显示。
- 本问题不需要替换或扩展小号字体；最小安全修复是保留原 JPN ASCII 标签。

已修改 authoritative mapping 的 `unique_index`：

- `390`：`新游戏` → `NEW GAME`
- `397`：`载入游戏` → `LOAD GAME`
- `402`：`删除` → `DELETE`

production compile、loose OLANG rebuild 和结构 round-trip 已通过，随后已完成 Steam 实机确认。

### 2026-09-09 修复与实机结果

针对“JPN 原文为纯 ASCII、但中文译文改成了 CJK 后由日版 UI 字体无法显示”的同类回归，
已对正式 production translations 做全局审查，并将高风险的 ASCII UI 文本恢复为 clean JPN
原文。此次修复不是按字体分组猜测，而是以 JPN 原文、现有 MLG_CN 行为和实际辅助 reference
证据共同筛选；无可靠辅助 reference 的纯 ASCII UI 也采用可读的 JPN 英文回退。

修复统计：

- 审查正式行：`21,041`
- ASCII 源文且被改为 CJK 的候选：`1,539`
- 实际恢复/保留 ASCII 的高风险目标：`351` 行
- 涉及 file_id：`38`
- 覆盖资源：`SLOT_OLANG`、`LOOSE_OLANG`、`STAGEDAT_OLANG`
- `YPK/GTT`、`OHD` 结构未被本次 UI 回归修复改写

随后从 clean JPN 重新编译、重建并安装统一测试包。实机已确认标题菜单
`NEW GAME`、`LOAD GAME`、`DELETE` 正常显示，选择位置和菜单状态正常；本项不再是待验证问题。

安装包写入 Steam 后的文件校验为 `VERIFY_MISMATCHES=0`，原文件已保存在独立备份目录。

### 修复要求

1. 定位标题菜单实际使用的 XPR 和 glyph index。
2. 对比 clean JPN 原字体与当前中文字体的 ASCII/Latin glyph 表。
3. 中文扩充必须保留既有英文字形、UV、advance/width 和索引关系。
4. 同步抽查 `RANK`、`LV`、人物英文名、武器名和按钮提示等英文 UI。

### 验收标准

- `NEW GAME`、`LOAD GAME`、`DELETE` 等标题菜单全部正常显示。
- 选择状态、位置和间距正常。
- 其他英文、数字和 UI 符号没有新增回归。

## ISSUE-006：BRIEFING 无线电长句不自动换行

优先级：`P0`

状态：`RESOLVED_INGAME_2026-09-14`

### 2026-09-14 实机已观察事实

- BRIEFING FILES 和任务结束 BRIEFING MISSION 均能正确调用中文，但字幕界面不会为不含换行符的中文自动折行。
- 长句以单行绘制，左右两端超出画面，造成不可读。这是视觉布局问题，不是 oEbN block 容量、parser 或 runtime 命中失败。
- 已确认的两个样本：
  - `BRIEFING_FILES_BLOCK_000D00 / unique_index 0`：`Snake，要把在现场发现的俘虏和被打昏的佣兵回收到母基地，就得使用富尔顿回收系统。`
  - `BRIEFING_MISSION_BLOCK_36DD60 / unique_index 15`：`谢谢。Snake，关于哥斯达黎加的事什么都可以问我。地理、气候、植物，还有历史和法律，我都很熟。`
- 两个 JPN 权威源行本身分别带有 2 行和 3 行语义分段，而现有 `cn_text` 丢掉了这些换行。

### 解决结论

- 仅在对应 `cn_text` 中插入 LF，未修改中文文字、row identity、Ruby、control token 或 block 结构。
- 两条已知 FILES 行宽超限已修复；重新生成 production CSV、BRIEFING DAT、全量 package 后，layout audit 为 0 overflow，离线 round-trip 继续通过，实机测试通过。

### 修复要求

1. 不拆分 translation unit，不改 `file_id` / `unique_index` / 物理 row；只在对应权威 mapping 的 `cn_text` 内加入显式 `LF` 换行。
2. 先以 JPN 原文的语义分行为锚点，再按画面实际可视宽度缩短或调整断句；不能仅根据 UTF-8 字节容量判定。
3. 扫描全部 5,645 条 BRIEFING `cn_text`，列出“无换行且可视长度高风险”的 row；由人工按 FILES/MISSION 场景复核，不盲目机械折行。
4. 更新 `cn_utf8_bytes`，重跑 BRIEFING production `--check`、clean-JPN builder、block fit 和全盘 round-trip。如新增 LF 导致 block 容量不足，先缩短同一句译文，不改 block 边界。
5. 生成新的 21 文件候选包，实机复测两个已知 row，再抽查其他长句、ruby 和多行对话。

### 验收标准

- 已知两句在字幕区域内完整显示，不裁切、不重叠，说话人和时序不变。
- FILES 和 MISSION 长句高风险清单完成人工复核。
- `BRIEFING_LINE_WRAP_OVERFLOW=0`，同时保持 469 blocks / 5,645 rows、0 overflow 和全盘 round-trip PASS。

## 后续验收与优化顺序

1. 建立完整 codepoint/glyph 覆盖检查，修复中文和保留日文缺字。
2. 任务结束无线电、ISSUE-003 任务结算武器经验字段和 ISSUE-006 BRIEFING 已知长句已通过当前实机验收；新增场景继续回归。
3. 对 UI 英文 ASCII 保留规则做持续回归检查，防止后续翻译重新覆盖已修复菜单。
4. GTT 容量、alignment spill、压缩余量和相关文本长度优化统一放到中文润色完成后的后续优化项目，不在当前生产版本中继续改动。
5. 对剩余问题逐一实机复测。

## V1.1 候选版统一通过条件

- `UNEXPECTED_DOT_GLYPH=0`
- `MISSING_GLYPH_BOX=0`
- `TITLE_UI_MISSING_TEXT=0`（已通过 2026-09-09 实机验证）
- `POST_MISSION_RADIO_JPN_REMAINS=0`（已通过 2026-09-14 实机验证）
- `BRIEFING_LINE_WRAP_OVERFLOW=0`
- `MISSION_RESULT_SEMANTIC_ERROR=0`
- `VISUAL_LAYOUT_OVERFLOW=0`
- GTT `HARD_OVERFLOW=0`
- SLOT/STAGEDAT `BLOCK_OVERFLOW=0`
- control/markup/placeholder errors = 0
- clean-JPN rebuild 与所有 parser round-trip 继续通过

只有上述条件全部满足，并完成对应实机场景复测，才可将 V1 测试版升级为可发布候选版本。
