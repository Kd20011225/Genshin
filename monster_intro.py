import argparse
import csv
import json
import os


def build_entry(monster_id: str, name: str, desc: str, struct_id: str) -> dict:
    return {
        "key": {"param_type": "EntityReference", "value": monster_id},
        "value": {
            "param_type": "Struct",
            "value": {
                "structId": struct_id,
                "type": "Struct",
                "value": [
                    {"param_type": "String", "value": name},
                    {"param_type": "String", "value": desc},
                ],
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Generate monster intro JSON from CSV")
    parser.add_argument("--csv", required=True, help="input csv path (e.g. 怪物介绍.csv)")
    parser.add_argument("--out", required=True, help="output json path (e.g. build/怪物介绍.json)")
    parser.add_argument("--struct-id", required=True, help="structId, e.g. 1077936134")

    # 允许你以后 CSV 列名变了也不用改代码
    parser.add_argument("--id-col", default="元件ID", help="column name for entity id (default: 元件ID)")
    parser.add_argument("--name-col", default="名字", help="column name for name (default: 名字)")
    parser.add_argument("--desc-col", default="介绍", help="column name for description (default: 介绍)")

    args = parser.parse_args()

    in_path = args.csv
    out_path = args.out
    struct_id = str(args.struct_id)

    result = {
        "type": "Dict",
        "key_type": "EntityReference",
        "value_type": "Struct",
        "value": [],
        "value_structId": struct_id,
    }

    seen = set()

    with open(in_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV 似乎是空的或没有表头")

        required_cols = {args.id_col, args.name_col, args.desc_col}
        missing = required_cols - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV 缺少列: {missing}. 当前列: {reader.fieldnames}")

        for line_no, row in enumerate(reader, start=2):  # 第1行表头
            monster_id = str(row.get(args.id_col, "")).strip()
            name = (row.get(args.name_col, "") or "").strip()
            desc = (row.get(args.desc_col, "") or "").strip()

            if not monster_id:
                raise ValueError(f"第 {line_no} 行：{args.id_col} 为空")
            if monster_id in seen:
                raise ValueError(f"第 {line_no} 行：{args.id_col} 重复: {monster_id}")
            seen.add(monster_id)

            result["value"].append(build_entry(monster_id, name, desc, struct_id))

    # 确保输出目录存在
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"OK: wrote {out_path} ({len(result['value'])} entries)")


if __name__ == "__main__":
    main()