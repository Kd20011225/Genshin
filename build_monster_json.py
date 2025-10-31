# build_monsters_json.py
import csv
import json
from pathlib import Path

DEFAULT_STRUCT_ID = "1077936130"

# CSV column names (change here if your headers differ)
COL_NAME = "怪物"
COL_ENTITY_ID = "元件ID"
COL_STRENGTH = "单体强度"   # 第二个 Int32 = 强度
COL_MIN_SPAWN = "最小生成"   # 第三个 Int32 = 最小生成

FOOTER_ROWS = {"中位数", "生命值权重", "目标强度"}

def to_int_str(v: str) -> str:
    """Convert numeric-like string to integer string. '5.0' -> '5'."""
    s = str(v or "").strip()
    if not s:
        raise ValueError("empty")
    return str(int(float(s)))

def make_entry(name: str, entity_id: str, strength: str, min_spawn: str, struct_id: str):
    """One Dict entry: key is monster name (String), value is Struct of 3 fields."""
    return {
        "key": {
            "param_type": "String",
            "value": name
        },
        "value": {
            "param_type": "Struct",
            "value": {
                "structId": struct_id,
                "type": "Struct",
                "value": [
                    {"param_type": "EntityReference", "value": entity_id},
                    {"param_type": "Int32",           "value": strength},
                    {"param_type": "Int32",           "value": min_spawn},
                ]
            }
        }
    }

def build_json_from_csv(csv_path: str, struct_id: str = DEFAULT_STRUCT_ID) -> dict:
    entries = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise SystemExit("CSV is missing header row.")
        # normalize headers (trim spaces, handle accidental blanks)
        r.fieldnames = [(h or "").strip() for h in r.fieldnames]

        needed = [COL_NAME, COL_ENTITY_ID, COL_STRENGTH, COL_MIN_SPAWN]
        for c in needed:
            if c not in r.fieldnames:
                raise SystemExit(f"Missing required column: {c} ; got: {r.fieldnames}")

        for row in r:
            name = (row.get(COL_NAME) or "").strip()
            ent  = (row.get(COL_ENTITY_ID) or "").strip()
            st   = (row.get(COL_STRENGTH) or "").strip()
            mn   = (row.get(COL_MIN_SPAWN) or "").strip()

            # Skip blanks & footer/stat rows
            if not name or not ent or name in FOOTER_ROWS:
                continue

            try:
                ent_s = to_int_str(ent)
                st_s  = to_int_str(st)
                mn_s  = to_int_str(mn)
            except ValueError:
                # Skip rows that don't have valid numeric fields
                continue

            entries.append(make_entry(name, ent_s, st_s, mn_s, struct_id))

    return {
        "type": "Dict",
        "key_type": "String",
        "value_type": "Struct",
        "value": entries,
        "value_structId": struct_id
    }

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build monster JSON (Dict<String, Struct>) from CSV.")
    ap.add_argument("--csv", required=True, help="Monsters CSV path")
    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--struct-id", default=DEFAULT_STRUCT_ID, help=f"StructId (default {DEFAULT_STRUCT_ID})")
    args = ap.parse_args()

    obj = build_json_from_csv(args.csv, struct_id=args.struct_id)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=3)
    print(f"Wrote {outp}")

if __name__ == "__main__":
    main()
