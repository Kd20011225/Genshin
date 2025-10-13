import csv, json, sys
from pathlib import Path

STRUCT_ID = "1077936134"
SET_NAME_COLOR = "#71db60"
NEED_PREFIX_COLOR = "#FFFFFFBF"  # 仅 2/4 件套的前缀高亮

def to_int_str(v: str) -> str:
    try:
        return str(int(float(str(v).strip())))
    except Exception:
        return "0"

def load_sets(sets_csv: str):
    """
    读取“圣遗物套装.csv”，返回：{ 套装名: {need1,eff1,need2,eff2,need3,eff3} }
    """
    m = {}
    with open(sets_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise SystemExit("圣遗物套装.csv 缺少表头。")
        r.fieldnames = [ (h or "").strip() for h in r.fieldnames ]
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

def _normalize_need(n: str) -> str:
    trans = str.maketrans("０１２３４５６７８９", "0123456789")
    return (n or "").strip().translate(trans)

def _fmt_need_line(need: str, eff: str):
    if not need or not eff:
        return None
    prefix = f"{need}件套："
    n_norm = _normalize_need(need)
    if n_norm in ("2", "4"):
        return f"<color={NEED_PREFIX_COLOR}>{prefix}</color>{eff}"
    return f"{prefix}{eff}"

def build_desc(base_effect: str, set_name: str, sets_map: dict) -> str:
    """
    单一套装版本描述，使用**字面** \\n 连接每行。
    """
    lines = []
    base_effect = (base_effect or "").strip()
    set_name = (set_name or "").strip()

    if base_effect:
        lines.append(f"({base_effect})")  # 基础效果加括号
        lines.append("")                  # 空一行

    if set_name:
        lines.append(f"<color={SET_NAME_COLOR}>{set_name}</color>")
        row = sets_map.get(set_name)
        if row:
            for ln in (
                _fmt_need_line(row["need1"], row["eff1"]),
                _fmt_need_line(row["need2"], row["eff2"]),
                _fmt_need_line(row["need3"], row["eff3"]),
            ):
                if ln:
                    lines.append(ln)

    return "\\n".join(lines)

def make_entry(key_index: int, title: str, config_id: str, tag_color: str, price: str, desc: str, struct_id: str = STRUCT_ID):
    """
    第一项为 String(卡牌标题) —— 你要求用名字。
    """
    return {
        "key": {"param_type": "Int32", "value": str(key_index)},
        "value": {
            "param_type": "Struct",
            "value": {
                "structId": struct_id,
                "type": "Struct",
                "value": [
                    {"param_type": "String",          "value": title},
                    {"param_type": "ConfigReference", "value": str(config_id)},
                    {"param_type": "Int32",           "value": to_int_str(tag_color)},
                    {"param_type": "Int32",           "value": to_int_str(price)},
                    {"param_type": "String",          "value": desc},
                ]
            }
        }
    }

def main(items_csv: str, sets_csv: str, out_json: str, struct_id: str = STRUCT_ID, start_index: int = 1):
    sets_map = load_sets(sets_csv)
    entries = []

    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise SystemExit("圣遗物.csv 缺少表头。")
        r.fieldnames = [ (h or "").strip() for h in r.fieldnames ]

        # 只有一个“套装”列的版本
        needed = ["卡牌标题", "ID", "基础效果", "套装", "标签颜色", "价格"]
        for c in needed:
            if c not in r.fieldnames:
                raise SystemExit(f"圣遗物.csv 缺少必需列: {c}；实际列：{r.fieldnames}")

        idx = int(start_index)
        for row in r:
            title = (row.get("卡牌标题") or "").strip()
            cfg   = (row.get("ID") or "").strip()
            base  = (row.get("基础效果") or "").strip()
            set_name = (row.get("套装") or "").strip()
            tagc  = (row.get("标签颜色") or "0").strip()
            price = (row.get("价格") or "0").strip()
            if not title or not cfg:
                continue

            desc = build_desc(base, set_name, sets_map)
            entries.append(make_entry(idx, title, cfg, tagc, price, desc, struct_id))
            idx += 1

    obj = {
        "type": "Dict",
        "key_type": "Int32",
        "value_type": "Struct",
        "value": entries,
        "value_structId": struct_id
    }

    outp = Path(out_json)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"Wrote {outp}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="从两张表生成最终JSON（单一套装版本，首字段为卡牌标题String，Dict键为Int32）。")
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 JSON 路径")
    ap.add_argument("--struct-id", default=STRUCT_ID, help="StructId (默认 1077936134)")
    ap.add_argument("--start-index", type=int, default=1, help="键的起始序号（默认 1）")
    args = ap.parse_args()
    main(args.items, args.sets, args.out, struct_id=args.struct_id, start_index=args.start_index)