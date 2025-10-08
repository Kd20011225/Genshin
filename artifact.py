import csv, json, sys
from pathlib import Path

STRUCT_ID = "1077936134"
SET_NAME_COLOR = "#71db60"
NEED_PREFIX_COLOR = "#FFFFFFBF"  # only color the prefix for 2/4-piece lines

def to_int_str(v):
    try:
        return str(int(float(str(v).strip())))
    except Exception:
        return "0"

def load_sets(sets_csv):
    m = {}
    with open(sets_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise SystemExit("圣遗物套装.csv 缺少表头。")
        r.fieldnames = [h.strip() for h in r.fieldnames]
        for row in r:
            name = (row.get("名字") or "").strip()
            if not name:
                continue
            m[name] = {
                "need1": (row.get("套装需求1") or "").strip(),
                "eff1":  (row.get("套装效果1") or "").strip(),
                "need2": (row.get("套装需求2") or "").strip(),
                "eff2":  (row.get("套装效果2") or "").strip(),
                "need3": (row.get("套装需求3") or "").strip(),
                "eff3":  (row.get("套装效果3") or "").strip(),
            }
    return m

def _normalize_need(n):
    # Normalize full-width digits to ASCII for comparison
    trans = str.maketrans("０１２３４５６７８９", "0123456789")
    return (n or "").strip().translate(trans)

def _fmt_need_line(need, eff):
    if not need or not eff:
        return None
    prefix = f"{need}件套："
    n_norm = _normalize_need(need)
    if n_norm in ("2", "4"):
        return f"<color={NEED_PREFIX_COLOR}>{prefix}</color>{eff}"
    return f"{prefix}{eff}"  # 3件套等：prefix uncolored

def build_desc(base_effect, set_names, sets_map):
    lines = [f"{base_effect}", ""]
    for s in set_names:
        sname = (s or "").strip()
        if not sname:
            continue
        lines.append(f"<color={SET_NAME_COLOR}>{sname}</color>")
        row = sets_map.get(sname)
        if row:
            for ln in (_fmt_need_line(row["need1"], row["eff1"]),
                       _fmt_need_line(row["need2"], row["eff2"]),
                       _fmt_need_line(row["need3"], row["eff3"])):
                if ln:
                    lines.append(ln)
    return "\\n".join(lines)

def make_entry(key_index, name, config_id, tag_color, price, desc, struct_id=STRUCT_ID):
    return {
        "key": {"param_type":"Int32","value": str(key_index)},
        "value": {
            "param_type":"Struct",
            "value": {
                "structId": struct_id,
                "type": "Struct",
                "value": [
                    {"param_type":"Int32","value": str(key_index)},
                    {"param_type":"ConfigReference","value":str(config_id)},
                    {"param_type":"Int32","value":to_int_str(tag_color)},
                    {"param_type":"Int32","value":to_int_str(price)},
                    {"param_type":"String","value":desc},
                ]
            }
        }
    }

def main(items_csv, sets_csv, out_json, struct_id=STRUCT_ID, start_index=1):
    sets_map = load_sets(sets_csv)

    entries = []
    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise SystemExit("圣遗物.csv 缺少表头。")
        r.fieldnames = [h.strip() for h in r.fieldnames]

        need = ["卡牌标题","ID","基础效果"]
        for c in need:
            if c not in r.fieldnames:
                raise SystemExit(f"圣遗物.csv 缺少必需列: {c}")

        idx = int(start_index)
        for row in r:
            name = (row.get("卡牌标题") or "").strip()
            cfg  = (row.get("ID") or "").strip()
            base = (row.get("基础效果") or "").strip()
            set1 = (row.get("套装1") or "").strip()
            set2 = (row.get("套装2") or "").strip()
            set3 = (row.get("套装3") or "").strip()
            tagc = (row.get("标签颜色") or "0").strip()
            price= (row.get("价格") or "0").strip()
            if not name or not cfg or not base:
                continue
            set_names = [s for s in [set1,set2,set3] if s]
            desc = build_desc(base, set_names, sets_map)
            entries.append(make_entry(idx, name, cfg, tagc, price, desc, struct_id))
            idx += 1

    obj = {
        "type":"Dict",
        "key_type":"Int32",
        "value_type":"Struct",
        "value": entries,
        "value_structId": struct_id
    }
    outp = Path(out_json)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return str(outp)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="从两张表生成最终JSON（已解析描述，无占位符）。")
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 JSON 路径")
    ap.add_argument("--struct-id", default=STRUCT_ID, help="StructId (默认 1077936134)")
    ap.add_argument("--start-index", type=int, default=1, help="键的起始序号（默认 1）")
    args = ap.parse_args()
    path = main(args.items, args.sets, args.out, struct_id=args.struct_id, start_index=args.start_index)
    print(f"Wrote {path}")
