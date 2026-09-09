# V1 实机问题与下一轮修复标准

更新时间：2026-09-09（Asia/Hong_Kong）

状态：`OPEN`

本文件记录第一版完整测试包的实机反馈。现有自动检查已经证明目标资源可以完成结构、容量、控制符、metadata、allocation 和 parser round-trip，但本轮实机测试确认仍有字库覆盖、运行时资源覆盖、翻译语义和画面排版问题。因此当前版本定义为 **V1 完整测试版**，尚不是正式发布版。

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

状态：`OPEN`

### 实机已观察事实

- 任务结束后出现的 Miller/Snake 无线电文本仍为完整日文。
- 当前统一包中的 241 个 file_id 没有使这段运行时文本变为中文。
- 日文内容涉及《特拉特洛尔科条约》、据点位置及路线情报等对话。

### 尚未确认

- 该无线电属于尚未提取的 resource class/file_id，还是已有资源的另一份运行时 physical occurrence。
- 游戏实际读取的是 SLOT、loose OLANG、STAGEDAT，还是当前尚未纳入 catalog 的其他文件。
- 是否存在区域副本、任务后专用资源或未覆盖的运行时选择路径。

### 修复要求

1. 用截图中的完整日文原句反查 clean JPN 数据。
2. 明确实际文件路径、resource class、file_id、对象索引和 physical occurrence。
3. 如果资源未被 catalog 覆盖，将其加入 JPN master、worklist、正式翻译和构建流程。
4. 如果已有翻译但未命中运行时副本，修正 occurrence/build 覆盖，不按相邻 ordinal 猜测。
5. 按同一段任务后无线电的完整上下文翻译和检查，不只修截图中的单句。

### 验收标准

- 同一任务结束后的整段无线电均显示中文。
- 对话人物、顺序、分页、换行和触发时机正确。
- 不再出现日文残留或因字库缺失产生的方框。
- 新资源继续满足 JPN metadata/结构保留和 clean-JPN rebuild 原则。

## ISSUE-003：任务结算武器经验字段译文异常

优先级：`P1`

状态：`OPEN`

### 实机已观察事实

- `MISSION RESULT` 画面的“武器经验值”区域中，动态等级和经验数字（如 `LV.1(+109)`）正常。
- 每个武器条目最右侧的固定文本显示为无意义或乱码式中文。
- 同一异常文本在多个武器条目中重复出现。

### 尚未确认

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

状态：`OPEN`

### 实机已观察事实

- 标题阶段“注意事项”页面的长文本横向超出面板和屏幕边界。
- 文本左右均被裁切，当前换行不能适应该界面的固定宽度。
- 现有 UTF-8/container capacity 检查没有检测出该问题。

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

## 下一轮执行顺序

1. 建立完整 codepoint/glyph 覆盖检查，修复中文和保留日文缺字。
2. 定位并纳入任务结束后的无线电资源。
3. 定位并纠正任务结算武器经验字段。
4. 对固定 UI 长文本进行显示宽度和换行审核。
5. 对 UI 英文 ASCII 保留规则做持续回归检查，防止后续翻译重新覆盖已修复菜单。
6. 从 clean JPN 重新生成统一测试包。
7. 重跑结构、容量、控制符、metadata、非目标 payload 和 round-trip 检查。
8. 对剩余问题逐一实机复测。

## V1.1 候选版统一通过条件

- `UNEXPECTED_DOT_GLYPH=0`
- `MISSING_GLYPH_BOX=0`
- `TITLE_UI_MISSING_TEXT=0`（已通过 2026-09-09 实机验证）
- `POST_MISSION_RADIO_JPN_REMAINS=0`
- `MISSION_RESULT_SEMANTIC_ERROR=0`
- `VISUAL_LAYOUT_OVERFLOW=0`
- GTT `HARD_OVERFLOW=0`
- SLOT/STAGEDAT `BLOCK_OVERFLOW=0`
- control/markup/placeholder errors = 0
- clean-JPN rebuild 与所有 parser round-trip 继续通过

只有上述条件全部满足，并完成对应实机场景复测，才可将 V1 测试版升级为可发布候选版本。
