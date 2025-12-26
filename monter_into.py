import csv
import json


CSV_PATH = "怪物介绍.csv"   
OUTPUT_JSON = "角斗士介绍.json"
STRUCT_ID = "1077936134"

COL_ID = "元件ID"
COL_NAME = "名字"
COL_DESC = "介绍"

result = {
    "type": "Dict",
    "key_type": "EntityReference",
    "value_type": "Struct",
    "value": [],
    "value_structId": STRUCT_ID
}

seen_ids = set()

with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    # 简单检查列名是否存在
    required = {COL_ID, COL_NAME, COL_DESC}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"CSV 缺少列: {missing}. 当前列: {reader.fieldnames}")

    for i, row in enumerate(reader, start=2):  
        monster_id = str(row[COL_ID]).strip()
        name = (row[COL_NAME] or "").strip()
        desc = (row[COL_DESC] or "").strip()

        if not monster_id:
            raise ValueError(f"第 {i} 行 元件ID 为空")

        if monster_id in seen_ids:
            raise ValueError(f"第 {i} 行 元件ID 重复: {monster_id}")
        seen_ids.add(monster_id)

        entry = {
            "key": {"param_type": "EntityReference", "value": monster_id},
            "value": {
                "param_type": "Struct",
                "value": {
                    "structId": STRUCT_ID,
                    "type": "Struct",
                    "value": [
                        {"param_type": "String", "value": name},
                        {"param_type": "String", "value": desc}
                    ]
                }
            }
        }
        result["value"].append(entry)

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"生成完成：{OUTPUT_JSON}（共 {len(result['value'])} 条）")