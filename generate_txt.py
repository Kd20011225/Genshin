import csv
import re
import sys
from pathlib import Path

GREEN = "#71db60"
MAX_TITLE_LEN = 200
MAX_BLOCK_LEN = 200  # literal characters, spaces and the two chars '\'+'n' both count

def detect_set_columns(headers):
    """Return headers like 套装1, 套装2, ... sorted by number."""
    cols = [h for h in headers if re.fullmatch(r"套装\d+", h or "")]
    cols.sort(key=lambda x: int(re.findall(r"\d+", x)[0]))
    return cols

def load_sets(path_sets):
    """
    Load set definitions.
    Returns: { set_name: [(need, eff_full, eff_short), ...] }
    """
    m = {}
    with open(path_sets, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise SystemExit(f"{path_sets} 缺少表头")
        for row in r:
            name = (row.get("名字") or "").strip()
            if not name:
                continue
            triples = []
            # support up to 10 pairs
            for i in range(1, 11):
                need = (row.get(f"套装需求{i}") or "").strip()
                eff_full  = (row.get(f"套装效果{i}") or "").strip()
                eff_short = (row.get(f"套装效果{i}简略描述") or "").strip()
                if need and eff_full:
                    triples.append((need, eff_full, eff_short))
            m[name] = triples
    return m

def build_set_section(set_name, triples):
    """
    Build one set section using 简略描述优先:
      <color=#71db60>套装名</color>\\n{need}件套：{short_or_full}\\n...
    """
    segs = [f"<color={GREEN}>{set_name}</color>"]
    for need, eff_full, eff_short in triples:
        eff = eff_short if eff_short else eff_full
        segs.append(f"{need}件套：{eff}")
    return "\\n".join(segs)  # keep literal backslash-n

def make_block_text(item_row, set_cols, sets_map):
    """
    Compose the whole block for one item (always short-or-full):
      (基础效果)\\n<colored set A>...\\n<colored set B>...\\n...
    """
    base_eff = (item_row.get("基础效果") or "").strip()
    parts = []
    if base_eff:
        parts.append(f"({base_eff})")

    for col in set_cols:
        sname = (item_row.get(col) or "").strip()
        if not sname:
            continue
        triples = sets_map.get(sname, [])
        if triples:
            parts.append(build_set_section(sname, triples))
        else:
            # set not found => show only the colored name
            parts.append(f"<color={GREEN}>{sname}</color>")

    return "\\n".join(parts) if parts else ""

def main(items_csv, sets_csv, out_txt):
    sets_map = load_sets(sets_csv)

    out_lines = []

    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        headers = [(h or "").strip() for h in (r.fieldnames or [])]

        # required columns
        for col in ("卡牌标题", "基础效果"):
            if col not in headers:
                raise SystemExit(f"{items_csv} 需要列：{col}；实际列：{headers}")

        set_cols = detect_set_columns(headers)

        for csv_row, row in enumerate(r, start=2):  # header is line 1
            title = (row.get("卡牌标题") or "").strip()
            if not title:
                continue

            # Title length guard
            if len(title) > MAX_TITLE_LEN:
                raise SystemExit(
                    f"Error: 第{csv_row}行 卡牌标题 超过{MAX_TITLE_LEN}字符（len={len(title)}）：{title}"
                )

            block = make_block_text(row, set_cols, sets_map)

            # Block length guard (counts spaces and literal '\n')
            if len(block) > MAX_BLOCK_LEN:
                raise SystemExit(
                    f"Error: 第{csv_row}行《{title}》 描述长度超过 {MAX_BLOCK_LEN}（len={len(block)}）。"
                )

            out_lines.append(title)
            out_lines.append(block)
            out_lines.append("")

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="由两张CSV生成描述TXT；始终使用套装简略描述（缺失则回退完整描述），并强制200字符限制。"
    )
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 TXT 路径")
    args = ap.parse_args()
    main(args.items, args.sets, args.out)