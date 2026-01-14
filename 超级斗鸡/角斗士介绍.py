import csv
import json

csv_file = "怪物介绍.csv"
json_file = "怪物介绍.json"

items = []

with open(csv_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        item = {
            "key": {
                "param_type": "EntityReference",
                "value": row["元件id"]
            },
            "value": {
                "param_type": "Struct",
                "value": {
                    "structId": "1077936134",
                    "type": "Struct",
                    "value": [
                        {
                            "param_type": "String",
                            "value": row["名字"]
                        },
                        {
                            "param_type": "String",
                            "value": row["介绍"]
                        }
                    ]
                }
            }
        }
        items.append(item)

with open(json_file, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print("已生成：", json_file)