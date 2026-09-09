from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "translations" / "ypk_gtt"
BACKUP = ROOT / "build" / "translation" / "overflow_review_backup"
REVIEW = ROOT / "build" / "translation" / "overflow_review_after.csv"


CANDIDATES: dict[str, dict[int, str]] = {
    "1C0FB26B": {
        30: "怎么了？敌人？",
        40: "不害怕吗……？\n真厉害……",
        73: "听说俘虏都是优秀游击队员。\n一定要回收。",
        226: "不杀士兵，全部制服后用富尔顿回收。",
    },
    "1C677327": {
        76: "目的地在云雾林另一边，\n是伪装成遗迹的研究所。",
    },
    "1C7679A5": {
        66: "被发现了。\n他们会来搜查。",
        69: "被发现了。\n逃走，或制服全部敌兵。",
        144: "LIFE太低！\n现在还打无线电？",
        172: "你、干什么？",
        194: "战士的宿命……",
        195: "你杀的……？",
        200: "是敌人也太过分了……",
        203: "是敌人也太残忍了……",
        261: "结实的胸膛……",
    },
    "1C79F36D": {
        19: "啾——！啾——！\n……嗯？够了吗？",
    },
    "1C79F46D": {
        68: "圆周率……",
        69: "大约3。",
    },
    "1C7A72ED": {
        84: "这些人霸占村子……不可原谅。",
    },
    "1C7A736D": {
        46: "实战果然不同……这机动性真惊人……",
    },
    "1C7B72AD": {
        18: "恐龙脚印……？",
        19: "……鸟？",
        23: "像恐龙的脚印……不会吧。",
    },
    "1C7C72ED": {
        18: "现在，进去！",
    },
    "1CC276E9": {
        1: "不摧毁直升机，\n制服敌军即可取胜。",
        23: "部队长已倒。\n回收即完成任务。",
        36: "看准直升机路线，布置空中地雷。",
        47: "也可以先制服士兵。",
        60: "你的武器难以制服装甲车。",
        62: "你的武器难以制服坦克。",
        63: "你的武器难以制服直升机。",
    },
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    changed: list[dict[str, str]] = []
    for file_id, candidates in CANDIDATES.items():
        path = TRANSLATIONS / f"{file_id}.csv"
        backup_path = BACKUP / path.name
        if not backup_path.exists():
            shutil.copy2(path, backup_path)
        fields, rows = read_csv(path)
        seen: set[int] = set()
        for row in rows:
            index = int(row["unique_index"])
            if index not in candidates:
                continue
            seen.add(index)
            old = row["cn_text"]
            new = candidates[index]
            row["cn_text"] = new
            row["cn_utf8_bytes"] = str(len(new.encode("utf-8")))
            changed.append(
                {
                    "file_id": file_id,
                    "unique_index": str(index),
                    "jpn_text": row["jpn_text"],
                    "old_cn_text": old,
                    "new_cn_text": new,
                    "old_utf8_bytes": str(len(old.encode("utf-8"))),
                    "new_utf8_bytes": row["cn_utf8_bytes"],
                }
            )
        missing = set(candidates) - seen
        if missing:
            raise RuntimeError(f"{file_id}: missing production unique_index {sorted(missing)}")
        write_csv(path, fields, rows)

    review_fields = [
        "file_id",
        "unique_index",
        "jpn_text",
        "old_cn_text",
        "new_cn_text",
        "old_utf8_bytes",
        "new_utf8_bytes",
    ]
    write_csv(REVIEW, review_fields, changed)
    print(f"FILES={len(CANDIDATES)}")
    print(f"ROWS={len(changed)}")
    print(f"BACKUP={BACKUP}")
    print(f"REVIEW={REVIEW}")


if __name__ == "__main__":
    main()
