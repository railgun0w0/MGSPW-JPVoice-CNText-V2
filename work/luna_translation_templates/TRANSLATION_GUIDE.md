# JPVoice_CNText_V2 翻译模板说明

本目录是从 clean JPN 主表提取的翻译准备数据，供人工或网页版 GPT 按 `file_id` 翻译使用。

本目录不是正式构建输入，不包含 DAT、KEY 或 compiled manifest。完成翻译后，必须经过本地校验和批准，才能进入正式构建。

## 目录结构

```text
luna_translation_templates/
├── OHD/
├── LOOSE_OLANG/
├── STAGEDAT_OLANG/
├── SLOT_OLANG/
├── YPK_GTT/
├── reference_masters/
└── TRANSLATION_GUIDE.md
```

### `reference_masters/`

这里保存五类 JPN master 的副本。每个 master 都是从 JPN 原始 DAT 解包得到的结构主表，并保留已有的辅助参考字段：

- `jpn_ohd_master.csv`
- `jpn_loose_olang_master.csv`
- `jpn_stagedat_text_master.csv`
- `jpn_slot_olang_master.csv`
- `jpn_gtt_master.csv`

这些表中的重要字段包括：

- `jpn_text`：JPN 原文，唯一语义权威；
- `mlg_cn_reference`：MLG 中文补丁候选；
- `eng_reference`：ENG 候选；
- `reference_status`、`reference_method`、`reference_reason`：候选来源和可靠性说明；
- record/reference/entity/segment/timing/容量等结构字段。

MLG_CN 和 ENG 只能作为辅助资料，不能决定 JPN 的对象对应关系。

### 各 resource class 目录

每个 `file_id` 一个 CSV。当前共准备：

- `SLOT_OLANG`：144 个 file_id；
- `STAGEDAT_OLANG`：46 个 file_id；
- `YPK_GTT`：36 个 file_id；
- `LOOSE_OLANG`：14 个 file_id；
- `OHD`：1 个 file_id。

合计 241 个 file_id，来源对象 91,609 个，file_id 内精确去重后 21,041 行。

## file_id CSV 格式

当前模板沿用正式 file_id CSV 的 21 列：

```text
file_id
unique_index
first_reference_index
reference_indices
reference_count
scene_context
entity_context
previous_jpn_text
jpn_text
next_jpn_text
jpn_control_tokens
cn_text
cn_control_tokens
control_structure_status
jpn_utf8_bytes
cn_utf8_bytes
translation_status
build_status
ingame_status
translation_basis
notes
```

### 去重规则

- JPN master 保留全部真实对象，不去重；
- file_id CSV 只在同一个 file_id 内对完全相同的 `jpn_text` 精确去重；
- 空格、换行、markup、控制符和全角字符都参与比较；
- 不进行语义去重，不把相似句子合并；
- `reference_indices` 和 `reference_count` 用于保留同一译文对应的全部真实 reference；
- OHD/YPK 没有 reference_index 的对象，相关 reference 字段留空，record/segment 身份保存在 `entity_context` 中；
- `unique_index` 只用于模板行定位，不能替代 JPN 的真实对象索引。

### 当前状态

所有机械模板都保持：

```text
cn_text = 空
cn_control_tokens = 空
cn_utf8_bytes = 空
control_structure_status = NOT_CHECKED
translation_status = NOT_STARTED
build_status = NOT_BUILT
ingame_status = NOT_TESTED
```

模板不得直接用于构建 DAT。

## 网页 GPT 的推荐工作方式

每次只处理一个 file_id，或一个很小的同类资源集合：

1. 读取对应 resource class 的 file_id 模板；
2. 从 `reference_masters/` 读取同一 file_id 的 JPN 行；
3. 使用 `jpn_text` 作为主文本；
4. 使用 `mlg_cn_reference` 和 `eng_reference` 作为辅助参考；
5. 保留同一 file_id 的前后文和术语一致性；
6. 只输出译文映射，不修改 JPN 字段、结构字段或索引。

不要把五个完整 master 或整个 DAT 一次性放入上下文。应按 file_id 截取，避免无关资源干扰判断。

推荐输出：

```json
{
  "file_id": "5D3B058D",
  "translations": [
    {
      "unique_index": 0,
      "reference_indices": "0",
      "cn_text": "中文译文",
      "review_flag": ""
    }
  ]
}
```

输出应使用 `unique_index` 或 `reference_indices` 定位，不得依赖返回行顺序。

## 翻译优先级

1. JPN 原文和同一 file_id 的完整上下文；
2. 已确认的统一术语表和既有中文译法；
3. MLG_CN 的中文措辞；
4. ENG 的剧情说明和歧义辅助。

如果 ENG/MLG_CN 与 JPN 的行号、entity、reference 或 record 错位：

- 放弃位置映射；
- 保留候选作为语义和剧情参考；
- 通过同一 file_id 的上下文确认其是否表达同一内容；
- 无法确认时，只根据 JPN 翻译。

不得把 ENG/CN 的顺序直接套到 JPN。

## 文本标准

- 使用自然、简洁、符合角色语气的简体中文；
- 不改变 JPN 原意、说话者关系和剧情因果；
- 不删除或改写 markup；
- 保留原有换行意图，必要时可为中文显示重新安排换行；
- 不留下未经确认的日文假名；专有名词、代码和固定读法可以保留；
- 同一个 file_id 内完全相同的 JPN 文本必须使用同一中文译文；
- 不截断文本；容量不足时优先重新措辞缩短，不改变结构。

## 控制符和 ruby

必须原样保护以下内容的结构、数量和顺序：

- `<R=...,...>`
- `<I=...>`
- `<->`
- `$1`、`$2` 等参数；
- 其他运行时 `<...>` 或 `$...` 控制符。

`<R>` 的显示文字可以中文化，ruby/读音优先使用已确认的英文或拉丁形式。例如：

```text
<R=BIG BOSS,BIG BOSS>
<R=机器,MACHINE>
<R=她,THE BOSS>
```

不得丢失参数、图标编号或控制符边界。

## 各类资源的翻译边界

### YPK/GTT

- 按 JPN record 和 timed segment 翻译；
- record 数量、顺序和 `segment_count` 不变；
- timing、trigger、style、metadata 不变；
- 只能修改文本和 text boundary；
- 不扩大 `record_size` 或 aligned frame；
- 使用 alignment slack 也不等于扩大 record；
- 超容量时缩短译文，仍不足则标记 `HARD_OVERFLOW`。

### OHD

- 按 JPN record 翻译；
- 保留 metadata、record 顺序和固定容量；
- 只写入文本字段和 NUL/padding；
- 不移动后续 record，不扩大 frame。

### SLOT/loose OLANG

- 按 JPN reference 翻译；
- 保留 entity table、entity key、reference 数量和顺序；
- 只重建文字 body 和 text offset；
- 不把 ENG/CN 的 entity 或 reference ordinal 直接移植过来。

### STAGEDAT

- 按 JPN 内嵌 OLANG reference 翻译；
- 保留 page、DAR/RBX 顺序、entity/reference metadata 和原 allocation；
- 只修改目标文字 body；
- 不改变非目标 entry payload。

## 完成翻译后的本地检查

网页 GPT 输出后，必须在本地检查：

- file_id 和 unique_index 完整；
- 没有漏行、重复行或额外行；
- JPN 字段未被改动；
- `cn_text` 非空；
- 控制符结构 MATCH；
- UTF-8 编码正确；
- 同一 JPN 文本没有冲突译文；
- YPK/OHD 容量满足要求；
- 未生成或修改 manifest/DAT，直到人工确认完成。

只有通过人工语义审核和本地结构检查后，才能把模板转为正式翻译 CSV 并标记 `APPROVED`。

