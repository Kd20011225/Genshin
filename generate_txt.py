import csv
import re
import sys
from pathlib import Path

GREEN = "#71db60"
MAX_TITLE_LEN = 200
MAX_BLOCK_LEN = 200

def detect_set_columns(headers):
    cols = [h for h in headers if re.fullmatch(r"套装\d+", h or "")]
    cols.sort(key=lambda x: int(re.findall(r"\d+", x)[0]))
    return cols

def load_sets(path_sets):
    """
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
            for i in range(1, 11):
                need = (row.get(f"套装需求{i}") or "").strip()
                eff_full  = (row.get(f"套装效果{i}") or "").strip()
                eff_short = (row.get(f"套装效果{i}简略描述") or "").strip()
                if need and eff_full:
                    triples.append((need, eff_full, eff_short))
            m[name] = triples
    return m

def build_set_section(set_name, triples, use_short=False):
    """
    Section text with literal \\n inside:
      <color=#71db60>套装名</color>\\n{need}件套：{effect}\\n...
    """
    segs = [f"<color={GREEN}>{set_name}</color>"]
    for need, eff_full, eff_short in triples:
        eff = eff_short if (use_short and eff_short) else eff_full
        segs.append(f"{need}件套：{eff}")
    return "\\n".join(segs)

def make_block_parts(item_row, set_cols, sets_map):
    """
    Returns:
      base_line: "(基础效果)" or ""
      sections: list of dicts, one per referenced set:
        {
          "name": set_name,
          "full": full_section_text,
          "short": short_section_text,   # may == full if no short available
          "gain": len(full) - len(short) # >= 0
        }
    """
    base_eff = (item_row.get("基础效果") or "").strip()
    base_line = f"({base_eff})" if base_eff else ""

    sections = []
    for col in set_cols:
        sname = (item_row.get(col) or "").strip()
        if not sname:
            continue
        triples = sets_map.get(sname, [])
        if triples:
            full = build_set_section(sname, triples, use_short=False)
            short = build_set_section(sname, triples, use_short=True)
        else:
            # set not found => just show the colored name
            full = f"<color={GREEN}>{sname}</color>"
            short = full
        gain = max(0, len(full) - len(short))
        sections.append({"name": sname, "full": full, "short": short, "gain": gain})
    return base_line, sections

def join_block(base_line, section_texts):
    """
    Compose the final literal-\\n block string.
    """
    parts = []
    if base_line:
        parts.append(base_line)
    parts.extend(section_texts)
    return "\\n".join(parts) if parts else ""

def minimal_shorten_block(base_line, sections):
    """
    Try to keep as many full sections as possible.
    If length > MAX_BLOCK_LEN, replace sections with biggest gains first
    until length <= MAX_BLOCK_LEN (or all replaced).
    Returns final block text and a flag indicating if fully within limit.
    """
    # Start with all full
    current_texts = [s["full"] for s in sections]
    block = join_block(base_line, current_texts)
    if len(block) <= MAX_BLOCK_LEN:
        return block, True

    # Sort by potential savings (gain) desc
    order = sorted(range(len(sections)), key=lambda i: sections[i]["gain"], reverse=True)

    for idx in order:
        if len(block) <= MAX_BLOCK_LEN:
            break
        # Replace this section with short if it actually saves anything
        if sections[idx]["gain"] > 0:
            current_texts[idx] = sections[idx]["short"]
            block = join_block(base_line, current_texts)

    return block, (len(block) <= MAX_BLOCK_LEN)

def main(items_csv, sets_csv, out_txt, allow_long=False, stdout=False):
    sets_map = load_sets(sets_csv)

    offenders = []  # rows that still exceed after minimal-shortening
    out_lines = []

    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        headers = [(h or "").strip() for h in (r.fieldnames or [])]
        for col in ("卡牌标题", "基础效果"):
            if col not in headers:
                raise SystemExit(f"{items_csv} 需要列：{col}；实际列：{headers}")

        set_cols = detect_set_columns(headers)

        for csv_row, row in enumerate(r, start=2):  # header = line 1
            title = (row.get("卡牌标题") or "").strip()
            if not title:
                continue

            # Title length guard
            if len(title) > MAX_TITLE_LEN:
                raise SystemExit(
                    f"Error: 第{csv_row}行 卡牌标题 超过{MAX_TITLE_LEN}字符（len={len(title)}）：{title}"
                )

            base_line, sections = make_block_parts(row, set_cols, sets_map)

            # First try: all full
            full_block = join_block(base_line, [s["full"] for s in sections])
            if len(full_block) <= MAX_BLOCK_LEN:
                final_block = full_block
            else:
                # Minimal shortening
                final_block, ok = minimal_shorten_block(base_line, sections)
                if not ok and not allow_long:
                    offenders.append((csv_row, title, len(final_block)))

            # Write output (title, block, blank line)
            out_lines.append(title)
            out_lines.append(final_block)
            out_lines.append("")

    if offenders and not allow_long:
        preview = "\n".join(
            f"  - 第{rowno}行《{title}》 block长度={blen}"
            for rowno, title, blen in offenders[:10]
        )
        more = "" if len(offenders) <= 10 else f"\n  ...(还有 {len(offenders)-10} 条)"
        raise SystemExit(
            f"Error: {len(offenders)} 个条目使用最小化简略后仍超过 {MAX_BLOCK_LEN}。\n"
            f"{preview}{more}\n"
            f"可加 --allow-long 跳过。"
        )

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp}")
    if stdout:
        print(outp.read_text(encoding="utf-8"))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="由两张CSV生成描述TXT；仅在块长度>200时按最小化原则替换为简略描述。"
    )
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 TXT 路径")
    ap.add_argument("--allow-long", action="store_true", help="即使仍超200也继续输出并返回0")
    ap.add_argument("--stdout", action="store_true", help="同时把结果打印到终端")
    args = ap.parse_args()
    main(args.items, args.sets, args.out, allow_long=args.allow_long, stdout=args.stdout)
