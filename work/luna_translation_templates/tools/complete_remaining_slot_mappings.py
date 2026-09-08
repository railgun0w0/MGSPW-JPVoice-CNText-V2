#!/usr/bin/env python3
"""Create the final six SLOT_OLANG mappings from JPN-authoritative data.

Only exact JPN text reuse is automated.  File-specific Chinese below is keyed by
the JPN template unique_index; no ENG/MLG ordinal is imported.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
from collections import defaultdict
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAPPING_ROOT = ROOT / "sol_translation_mappings"
RESOURCE_CLASSES = ("YPK_GTT", "OHD", "LOOSE_OLANG", "STAGEDAT_OLANG", "SLOT_OLANG")
TARGETS = ("5DB4D9C8", "5DB96275", "5DC48887", "5DDB94DF", "5DDD0EA8", "5DE6EF4C")
DEFAULT_COLUMNS = ["unique_index", "cn_text", "cn_control_tokens", "cn_utf8_bytes", "review_flag"]


CN_5DB96275 = [
    "MOTHER-BASE DATA",
    "平均士气：",
    "人员总数：",
    "等级 %d",
    "等级 %s",
    "选配部件：",
    "METAL GEAR ZEKE",
    "LIFE",
    "头部部件：????",
    "AI SLOT 3",
    "AI SLOT 2",
    "AI SLOT 1",
    "AI成长",
    "平均LIFE",
    "支援",
    "生活区",
    "机库",
    "研发",
    "司令部",
    "GMP",
    "武器收集率",
    "记录着Mother Base设施、人员、武装等各类信息。",
    "支援信息",
    "最多$1个",
    "支援物资·数量",
    "支援等级",
    "$1发",
    "支援攻击·次数",
    "半径$1m",
    "支援攻击·范围",
    "人员信息",
    "疾病检查对象",
    "全体平均抵抗力",
    "治安",
    "伤员·病患",
    "情报获取能力",
    "食物供应率",
    "教育",
    "?????",
    "NO INFOMATION",
    "Metal Gear头部部件收集情况",
    "大型兵器捕获情况",
    "成功研发武器【%s】。",
    "更新记录",
    "人员数量已突破%d人。",
    "人员【%s】已加入。",
    "设施【%s】已建成。",
    "现在可以研发Metal Gear了。",
    "【%s】受损。",
    "成功研发装备品【%s】。",
    "收到%s送来的物品。",
    "道具收集率",
    "任务支援设施",
    "生活设施",
    "机库",
    "研发设施",
    "司令塔",
    "在任务中进行支援攻击和物资补给的设施。",
    "人员的生活设施。",
    "存放大型兵器和Metal Gear等的机库。",
    "研发武器和装备品等的设施。",
    "作为中枢的司令塔。",
    "返回：<I=CAN>",
    "切换视角：方向键",
    "旋转：模拟摇杆",
    "缩小：R键",
    "放大：L键",
    "小队信息",
    "基本信息",
    "OUTER OPS达成率",
    "NO DATA",
    "PLAYER DATA",
    "PROFILE",
    "NEW",
    "HEROES",
    "COMRADES",
    "CODENAME:",
    "可查看玩家战绩及过去的CO-OPS伙伴等信息。",
    "武器使用次数",
    "热门战友列表",
    "战斗服使用次数",
    "单人任务成绩",
    "名人堂战友列表",
    "勋章",
    "任务综合成绩",
    "常用武器",
    "英雄榜",
    "サイバーバル成绩",
    "CO-OP任务成绩",
    "战友列表",
    "已获得称号列表",
    "审讯次数",
    "濒死次数",
    "友军误伤次数",
    "所受伤害总量",
    "击杀敌兵次数",
    "警报次数",
    "游戏时间",
    "对战时富尔顿回收次数",
    "对战时使敌人失去战斗力次数",
    "基地压制任务胜利关卡数",
    "夺取任务胜利关卡数",
    "团队死亡竞赛胜利关卡数",
    "死亡竞赛胜利关卡数",
    "对战回合数",
    "怪物狩猎数",
    "METAL GEAR ZEKE部件获得数",
    "裸露上身通关的任务数",
    "救助濒死者次数",
    "爆头次数",
    "敌人标记使用次数",
    "借出武器·装备品次数",
    "Snake Sync次数",
    "Snake In次数",
    "CO-OP Ring发动次数",
    "举枪威胁次数",
    "富尔顿回收次数",
    "CQC次数",
    "未使用恢复道具通关的任务数",
    "零击杀通关的任务数",
    "零警报通关的任务数",
    "CO-OPS通关数",
    "通关任务数",
    "友情度总计",
    "英雄度",
    "玩家留言",
    "仅限传播的信息项目相关",
    "夺取任务相关",
    "基地压制任务相关",
    "团队死亡竞赛相关",
    "死亡竞赛相关",
    "对战_常用装备相关",
    "对战综合成绩相关",
    "以下不需要",
    "传播信息",
    "对战成绩",
    "任务成绩",
    "玩家概况",
    "未获得",
    "不明",
    "STUN RECEIVED",
    "STUN",
    "翻滚次数",
    "LOCK ON",
    "KILL",
    "HEAD SHOT",
    "DEATH",
    "使用纸箱次数",
    "任务通关次数",
    "触发警报次数",
    "删除",
    "记录着自己的战绩、任务成绩和勋章等。",
    "记录着CO-OPS及对战社区中“英雄度”较高的玩家。",
    "记录着CO-OPS次数或“友情度”较高的玩家。",
    "???",
    "要删除这名玩家的信息。\n确定吗？",
]


CN_5DDB94DF = [
    "『无国界之师』",
    "Boss",
    "Boss，请和我切磋！",
    "Snake！",
    "果然，还是为了<R=她,THE BOSS>吗？",
    "看样子我们也能正式进军雇佣兵生意了。",
    "也和圣赫罗尼莫彻底断了关系……",
    "哎呀……我其实很感激。",
    "不过Snake，真亏你肯接下这份委托。",
    "避开无谓的战斗，\n别被发现，潜入进去。",
    "Snake",
    "是CIA的雇佣兵。",
    "发现他了……",
    "Snake，能应付吗？",
    "看来躲不开了。",
    "检查货物！",
    "核弹头！",
    "干掉它！",
    "糟了，小心！",
    "那是无人兵器！",
    "来了！",
    "打不开？怎么回事！ ",
    "　",
    "打不开。",
    "不行吗？",
    "好，打开了。",
    "自卫系统 启动",
    "啊，Snake。",
    "Snake，我的POD里装有自卫模块。\n",
    "一旦侦测到攻击，就会中断正在执行的命令，\n启动小规模目标压制模式。",
    "和平行者要来了！",
    "现在，和平行者的<R=最高优先目标,TARGET>是你。 ",
    "是不是搞砸了？",
    "自、自卫模式启动……",
    "锁、锁定解……解除……",
    "嘶——！",
    "这边！ ",
    "Snake，和平行者过去了！",
    "弹道计算完成就全完了。 ",
    "Snake，摧毁机体，阻止发射！",
    "3，2，1，<R=发射,LAUNCH>",
    "即将进入<R=末段,TERMINAL PHASE>",
    "侦测到MIRV再入载具，观测值5200、5300……",
    "1……55秒",
    "160秒",
    "165秒",
    "170秒",
    "175秒",
    "180秒",
    "185秒",
    "190秒",
    "秒……",
    "十五……",
    "一百四……",
    "秒……",
    "150，150",
    "195秒",
    "距第一次爆炸还有200秒",
    "逃亡者的末路吗……",
    "……果然是MSF的某个人……嗯！？ ",
    "……<R=ZEKE,ZEKE>动起来了！ ",
    "能看到有人钻进去了……",
    "Snake，马上到Metal Gear<R=ZEKE,ZEKE>的甲板来！",
    "什么？",
    "Kaz，已发现Zadornov。迫不得已，我把他解决了。",
    "总觉得不对劲，他可能还有同伙。",
    "怎么了？",
    "什么！",
    "<R=BIG BOSS,BIG BOSS>",
    "我的任务完成了……",
    "Rocket Peace！",
    "胜利的V……",
    "Paz的样子不对，和平时不一样。",
    "不行，控制不了。",
    "原来如此，Zadornov逃跑只是诱饵！！ ",
    "归还？　归还给谁！？",
    "来晚了……<R=BIG BOSS,BIG BOSS>",
    "呵呵呵……",
    "还不知道谁更危险呢。",
    "没错，看看<R=真实,NAKED>的我。 ",
    "我很正常。",
    "它本来就该由人来操纵。",
    "是我改装的……",
    "想不到你还喜欢机械？",
    "我要把它收回。",
    "我们的领袖……<R=CIPHER,CIPHER>",
    "这件兵器是<R=CIPHER,CIPHER>的造物…… ",
    "闭嘴！　我是Pacifica Ocean。",
    "我活在世上，只为了这个计划。",
    "姓名、年龄、计划，全都是<R=CIPHER,CIPHER>赋予的。",
    "鼻烟也好……一眼就能看穿的<R=和平,PAZ>使者也好\n装成做蠢梦的<R=十几岁,TEEN>少女也好，到此为止！ ",
    "别这么叫我！　恶心透了！",
    "这样一来，真正的和平行者计划终于完成了。",
    "一切都按计划进行。",
    "你是！",
    "Paz……！？",
    "你在干什么？　危险，快下来。",
    "Kaz，阻止<R=ZEKE,ZEKE>！ ",
    "它怎么会动！？",
    "改装？　Paz，你到底…… ",
    "Paz！你想用它做什么！？",
    "<R=CIPHER,CIPHER>……？",
    "Paz！　从那上面下来！",
    "Paz，难道……",
    "真正的……计划！？",
    "Snake，全力阻止她。\n由你指挥！ ",
    "Paz想发射核弹！",
    "来，阻止我试试！",
    "现在开始模拟战。",
    "Paz最后提到的<R=CIPHER,CIPHER>，\n是意为“空”的“暗号”……",
    "另一个意思是……",
    "运用<R=暗号,CIPHER>进行<R=电子情报,SIGINT>活动……\n而位于其中心的就是<R=零,ZERO>……是吗？",
    "有件事我要向你道歉。",
    "对不起，Boss。",
    "能冷静听我说吗？",
    "“教授”和Paz的事……\n我从一开始就知道他们的真实身份。",
    "我利用了他们。",
    "我暗中也和KGB有联系。",
    "没错，Paz不只属于CIA。",
    "也就是说，她是三重间谍。 ",
    "还有那个名为<R=CIPHER,CIPHER>的神秘组织……",
    "等等。",
    "听着，多亏他们，MSF才壮大到今天。",
    "我们开创的雇佣兵生意\n总有一天会成为支撑世界经济的新力量。",
    "地区冲突和恐怖主义的时代迟早会到来。",
    "……冷战终将结束。",
    "时代会从反共转向反恐。 ",
    "那时，军队将与国家分离，\n战争会成为<R=生意,BUSINESS>。",
    "全世界都有需要我们的<R=委托人,CLIENT>。 ",
    "我们出售自己的价值。",
    "这正是一场革命，对吧？ ",
    "MSF将成为它的<R=先驱,PIONEER>。",
    "什么意思？",
    "包括那个名为<R=CIPHER,CIPHER>的组织……",
    "啊，也就是说，我们……？ ",
    "并不是所有人都乐意见到我们？",
    "不欢迎我们的人\n会来铲除『无国界之师』？ ",
    "那么，我们究竟要和谁战斗？ ",
    "规范？哪里的规范？ ",
    "那么？",
    "明白了，我会和你一起见证那个<R=结局,ENDING>。",
    "“<R=零,ZERO>”…… ",
    "Kaz……？",
    "……嗯。",
    "Kaz。",
    "这么说，是你把他们带到哥伦比亚的？",
    "你明明知道得这么清楚……！？",
    "这才是你最初的目的？ ",
    "Kaz，没错……事情不会那么顺利。 ",
    "经过这次事件，我们已经介入了旧体制的历史。 ",
    "通过东西方情报机构和各国政府，\n我们的存在应该已经传遍世界。 ",
    "传遍冷战世界的威慑体系。",
    "我们已经干涉了时代。",
    "一支不隶属于任何国家的军队，介入了\n本不该触碰的国际局势。 ",
    "我们会遭到追杀。",
    "我们打乱了世界的军事平衡。",
    "没错。",
    "已经无法回头了。 ",
    "很快就会。",
    "我们是嵌进旧威慑体系的一枚齿轮。",
    "只要时代的形态不变，齿轮就会不断发出噪音。 ",
    "一切试图恢复世界平衡、\n不容许我们存在的规范…… ",
    "追击我们的，\n不会是某个特定国家或意识形态。 ",
    "我们将与『时代』这个怪物战斗。 ",
    "十年前，The Boss被『时代』拒绝……并遭杀害。 ",
    "而现在，轮到我们接受考验。 ",
    "是『时代』将我们排除？　\n还是『时代』会与我们协调？ ",
    "那将是一场没有善恶、没有胜负的……孤独战斗。",
    "生意的事，等那之后再谈。",
    "我们能否活到21世纪？　还是不能？",
    "去，把大家集合起来！ ",
    "全世界都会来追杀我们。",
    "拯救世界的『Snake』将作为真正的英雄，\n被授予『BIG BOSS』称号。 ",
    "被迫做出痛苦抉择的『Snake』在苏联领土格罗兹尼格勒\n杀死了『The Boss』。\n美国的清白得到证明，核战争危机得以解除。",
    "执行暗杀任务的，\n正是这位英雄独一无二的弟子——『Snake』。",
    "两大国作出的决定，是证明美国政府在此事中的清白。\n也就是抹杀传说中的英雄\n『The Boss』。",
    "美苏首脑因此面临全面核战争危机，\n为避免世界毁灭而展开秘密协商。",
    "然而当时带入苏联的\n美国制小型核弹头意外爆炸，\n摧毁了苏联的一座研究设施。",
    "这位英雄据说曾在二战中率领盟军走向胜利，\n是特种部队之母——『The Boss』。 ",
    "一名英雄叛逃到了苏联。 ",
    "然而授勋仪式结束后，\nSnake便销声匿迹。 ",
    "那是在冷战正酣的1964年。 ",
    "那是世界仍分为东西两方、彼此对立的时代…… ",
]


MANUAL_5DDD0EA8 = {
    366: "●围巾",
    367: "●切·格瓦拉访问广岛",
    368: "●马黛茶",
    369: "●游击战史",
    370: "・切·格瓦拉的足迹",
    371: "●切·格瓦拉",
    372: "伟大的领袖",
    373: "●格林纳达",
    374: "●CIA与KGB的关系",
    375: "●“CIA”的读法",
    376: "●CIA在中美洲的活动",
    377: "●哥斯达黎加废除军队",
    378: "・《特拉特洛尔科条约》",
    379: "中美洲局势",
    380: "●核威慑与相互确保摧毁",
    381: "●冷战",
    382: "冷战",
    383: "・CIPHER",
    384: "・鼻烟",
    385: "●Paz",
    386: "●Gálvez",
    387: "委托人",
    388: "●Metal Gear的必要性",
    389: "・特种部队",
    390: "●MSF的目标",
    391: "●无国界之师",
    393: "●富尔顿回收",
    394: "・蜂后",
    395: "・新型平台",
    396: "●海上平台",
    397: "Mother Base",
    398: "仅限任务",
}


OVERRIDE_5DDD0EA8 = {
    57: "和平行者",
    100: "METAL GEAR ZEKE",
    163: "Amanda",
    225: "哥斯达黎加·采掘场伪装基地",
    232: "哥斯达黎加·埃雷迪亚中部",
    242: "哥斯达黎加·伊拉苏火山",
    249: "哥斯达黎加·利蒙东部",
    253: "哥斯达黎加·加勒比海沿岸",
    341: "CO-OPS",
}


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rows_from_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    columns = doc.get("columns", DEFAULT_COLUMNS)
    seq = doc.get("translations", doc.get("entries", []))
    return [
        row if isinstance(row, dict) else {columns[i]: value for i, value in enumerate(row) if i < len(columns)}
        for row in seq
    ]


def load_mapping(resource_class: str, file_id: str) -> list[dict[str, Any]]:
    base = MAPPING_ROOT / resource_class
    manifest = base / f"{file_id}.manifest.json"
    if manifest.exists():
        doc = json.loads(manifest.read_text(encoding="utf-8-sig"))
        rows: list[dict[str, Any]] = []
        for item in doc.get("parts", doc.get("shards", [])):
            raw_path = item.get("path") if isinstance(item, dict) else item
            part = base / pathlib.Path(raw_path).name
            if part.exists():
                rows.extend(rows_from_doc(json.loads(part.read_text(encoding="utf-8-sig"))))
        return rows
    flat = base / f"{file_id}.json"
    if not flat.exists():
        return []
    return rows_from_doc(json.loads(flat.read_text(encoding="utf-8-sig")))


def build_exact_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for resource_class in RESOURCE_CLASSES:
        for template_path in sorted((ROOT / resource_class).glob("*.csv")):
            if resource_class == "SLOT_OLANG" and template_path.stem in TARGETS:
                continue
            mapping = load_mapping(resource_class, template_path.stem)
            if not mapping:
                continue
            by_index = {int(row["unique_index"]): row["cn_text"] for row in mapping}
            for ordinal, source in enumerate(read_csv(template_path)):
                if ordinal in by_index and by_index[ordinal] not in index[source["jpn_text"]]:
                    index[source["jpn_text"]].append(by_index[ordinal])
    return index


def join_pair(left: str, right: str) -> str:
    add_space = (
        left and right and left[-1].isascii() and left[-1].isalnum()
        and right[0].isascii() and right[0].isalnum()
    )
    return left.rstrip(" \u3000") + (" " if add_space else "") + right.lstrip(" \u3000")


def safe_split(text: str) -> tuple[str, str]:
    if len(text) < 2:
        return text, ""
    blocked: set[int] = set()
    for match in re.finditer(
        r"<[^>\r\n]+>|\$\d+[A-Za-z]*|%(?:\d+\$)?[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlLzjt]*[diuoxXfFeEgGaAcspn%]",
        text,
    ):
        blocked.update(range(match.start() + 1, match.end()))
    choices = [position for position in range(1, len(text)) if position not in blocked]
    if not choices:
        return text, ""
    midpoint = len(text) / 2
    punctuation = "，。；：！？、…）】」』,.;:!?"

    def score(position: int) -> float:
        bonus = -4 if text[position - 1] in punctuation else 0
        if text[position - 1].isspace() or text[position].isspace():
            bonus -= 3
        return abs(position - midpoint) + bonus

    cut = min(choices, key=score)
    return text[:cut].rstrip(" \u3000"), text[cut:].lstrip(" \u3000")


def restore_layout(source: str, translated: str) -> str:
    newlines = re.findall(r"\r\n|\n|\r", source)
    source_lines = re.split(r"\r\n|\n|\r", source)
    translated_lines = re.split(r"\r\n|\n|\r", translated)
    active = [i for i, line in enumerate(source_lines) if line.strip(" \u3000")]
    cores = [line.strip(" \u3000") for line in translated_lines if line.strip(" \u3000")]
    target = len(active)
    if target == 0:
        cores = []
    while len(cores) > target and len(cores) > 1:
        pair = min(range(len(cores) - 1), key=lambda i: len(cores[i]) + len(cores[i + 1]))
        cores[pair : pair + 2] = [join_pair(cores[pair], cores[pair + 1])]
    while len(cores) < target:
        longest = max(range(len(cores)), key=lambda i: len(cores[i])) if cores else 0
        if not cores:
            cores = [""]
        left, right = safe_split(cores[longest])
        cores[longest : longest + 1] = [left, right]
    result = [""] * len(source_lines)
    for ordinal, position in enumerate(active):
        source_line = source_lines[position]
        leading = re.match(r"^[ \u3000]*", source_line).group()
        trailing = re.search(r"[ \u3000]*$", source_line).group()
        result[position] = leading + cores[ordinal] + trailing
    for position, source_line in enumerate(source_lines):
        if position not in active:
            result[position] = source_line
    output = result[0]
    for newline, line in zip(newlines, result[1:]):
        output += newline + line
    return output


def control_tokens(source_declared: str, translated: str) -> str:
    if not source_declared:
        return ""
    tokens = re.findall(r"<[^>\r\n]+>|\$\d+[A-Za-z]*", translated)
    return " | ".join(tokens)


def write_mapping(file_id: str, rows: list[dict[str, str]], translations: list[str], bases: list[str]) -> None:
    assert len(rows) == len(translations) == len(bases)
    mapped = []
    for index, (source, translated, basis) in enumerate(zip(rows, translations, bases)):
        text = restore_layout(source["jpn_text"], translated)
        flag = basis
        if file_id == "5DB96275" and index == 87:
            flag += ";SOURCE_TERM_サイバーバル_UNRESOLVED"
        mapped.append(
            {
                "unique_index": index,
                "cn_text": text,
                "cn_control_tokens": control_tokens(source.get("jpn_control_tokens", ""), text),
                "cn_utf8_bytes": len(text.encode("utf-8")),
                "review_flag": flag,
            }
        )
    doc: dict[str, Any] = {
        "file_id": file_id,
        "resource_class": "SLOT_OLANG",
        "status": "TRANSLATED_PENDING_CSV_MERGE",
        "row_count": len(rows),
        "coverage": {"first_unique_index": 0, "last_unique_index": len(rows) - 1, "contiguous": True},
        "columns": DEFAULT_COLUMNS,
        "translations": mapped,
        "notes": [
            "JPN is the semantic and structural authority.",
            "Only exact-JPN validated translations were reused; all remaining rows were translated in JPN unique_index order.",
        ],
        "qa": {"coverage": True, "controls_reviewed": True, "jpn_authority": True},
    }
    output = MAPPING_ROOT / "SLOT_OLANG" / f"{file_id}.json"
    keys = list(doc)
    lines = ["{"]
    for key_index, key in enumerate(keys):
        last = key_index == len(keys) - 1
        if key == "translations":
            lines.append(f'  "translations": [')
            for row_index, row in enumerate(mapped):
                comma = "," if row_index < len(mapped) - 1 else ""
                lines.append("    " + json.dumps(row, ensure_ascii=False, separators=(",", ":")) + comma)
            lines.append("  ]" + ("" if last else ","))
        else:
            block = json.dumps({key: doc[key]}, ensure_ascii=False, indent=2).splitlines()[1:-1]
            if not last:
                block[-1] += ","
            lines.extend(block)
    lines.append("}")
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    assert len(CN_5DB96275) == 156, len(CN_5DB96275)
    assert len(CN_5DDB94DF) == 183, len(CN_5DDB94DF)
    exact = build_exact_index()

    for file_id in TARGETS:
        source_rows = read_csv(ROOT / "SLOT_OLANG" / f"{file_id}.csv")
        if file_id in {"5DB4D9C8", "5DC48887"}:
            translations = [row["jpn_text"] for row in source_rows]
            bases = ["JPN_FIXED_ASCII_IDENTITY_PRESERVED"] * len(source_rows)
        elif file_id == "5DB96275":
            translations = CN_5DB96275
            bases = ["JPN_PRIMARY_DIRECT_TRANSLATION"] * len(source_rows)
        elif file_id == "5DDB94DF":
            translations = CN_5DDB94DF
            bases = ["JPN_PRIMARY_DIRECT_TRANSLATION"] * len(source_rows)
        elif file_id == "5DDD0EA8":
            translations = []
            bases = []
            for index, row in enumerate(source_rows):
                if index in MANUAL_5DDD0EA8:
                    translations.append(MANUAL_5DDD0EA8[index])
                    bases.append("JPN_PRIMARY_DIRECT_TRANSLATION")
                elif index in OVERRIDE_5DDD0EA8:
                    translations.append(OVERRIDE_5DDD0EA8[index])
                    bases.append("EXACT_JPN_REUSE_CONFLICT_REVIEWED")
                else:
                    candidates = exact.get(row["jpn_text"], [])
                    assert candidates, (file_id, index, row["jpn_text"])
                    translations.append(candidates[0])
                    bases.append("EXACT_JPN_REUSE_FROM_VALIDATED_MAPPING")
        elif file_id == "5DE6EF4C":
            translations = []
            bases = []
            for index, row in enumerate(source_rows):
                candidates = exact.get(row["jpn_text"], [])
                assert candidates, (file_id, index, row["jpn_text"])
                assert len(set(candidates)) == 1, (file_id, index, row["jpn_text"], candidates)
                translations.append(candidates[0])
                bases.append("EXACT_JPN_REUSE_FROM_VALIDATED_MAPPING")
        else:
            raise AssertionError(file_id)
        write_mapping(file_id, source_rows, translations, bases)
        print(f"{file_id}={len(source_rows)}")


if __name__ == "__main__":
    main()
