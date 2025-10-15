import csv
from pathlib import Path

GREEN = "#71db60"

def load_sets(sets_csv: str):
    """
    Load sets into:
      { set_name: summary_text }
    Prefers column '套装效果简略描述' (single summary for all effects).
    If not found (or empty), falls back to joining 套装效果1..3 (without 2/4件套前缀).
    """
    m = {}
    with open(sets_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise SystemExit(f"{sets_csv} 缺少表头")
        headers = [h or "" for h in r.fieldnames]

        has_single_summary = ("套装效果简略描述" in headers)

        for row in r:
            name = (row.get("名字") or "").strip()
            if not name:
                continue

            summary = ""
            if has_single_summary:
                summary = (row.get("套装效果简略描述") or "").strip()

            if not summary:
                # fall back: concat all 套装效果N with '；'
                effects = []
                for i in range(1, 11):
                    eff = (row.get(f"套装效果{i}") or "").strip()
                    if eff:
                        effects.append(eff)
                summary = "；".join(effects) if effects else ""

            m[name] = summary
    return m

def detect_set_column(headers):
    """Find the single set column. Accepts '套装' or legacy '套装1'."""
    if "套装" in headers:
        return "套装"
    if "套装1" in headers:
        return "套装1"
    raise SystemExit(f"圣遗物.csv 需要列：套装（或 套装1）；实际列：{headers}")

def build_block(base_effect: str, set_name: str, summary: str):
    """
    Build one block using literal \\n:
      (基础效果)\\n<color=#71db60>套装名</color>\\n{简略描述}
    """
    parts = []
    if base_effect:
        parts.append(f"({base_effect})")
    parts.append(f"<color={GREEN}>{set_name}</color>")
    parts.append(summary or "")
    return "\\n".join(parts)

def main(items_csv: str, sets_csv: str, out_txt: str):
    sets_map = load_sets(sets_csv)

    out_lines = []
    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        headers = [(h or "").strip() for h in (r.fieldnames or [])]

        # Required columns (single set)
        for col in ("卡牌标题", "基础效果"):
            if col not in headers:
                raise SystemExit(f"{items_csv} 需要列：{col}；实际列：{headers}")
        set_col = detect_set_column(headers)

        for row in r:
            title = (row.get("卡牌标题") or "").strip()
            if not title:
                continue
            base  = (row.get("基础效果") or "").strip()
            sname = (row.get(set_col) or "").strip()

            if not sname:
                # still write title with empty block
                out_lines.append(title)
                out_lines.append("")
                out_lines.append("")
                continue

            summary = sets_map.get(sname, "")
            block = build_block(base, sname, summary)

            out_lines.append(title)
            out_lines.append(block)
            out_lines.append("")  # blank separator

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="从单套装圣遗物.csv 与 圣遗物套装.csv 生成 TXT（仅写 套装效果简略描述；含(基础效果)；套装名后有字面 \\n）")
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 TXT 路径")
    args = ap.parse_args()
    main(args.items, args.sets, args.out)