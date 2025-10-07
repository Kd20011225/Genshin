import csv, re, sys
from pathlib import Path

GREEN = "#71db60"

def load_sets(path):
    m = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get("名字") or "").strip()
            if not name:
                continue
            pairs = []
            # up to 10 pairs is plenty; adjust if you need more
            for i in range(1, 11):
                need = (row.get(f"套装需求{i}") or "").strip()
                eff  = (row.get(f"套装效果{i}") or "").strip()
                if need and eff:
                    pairs.append((need, eff))
            m[name] = pairs
    return m

def build_set_section(set_name, pairs):
    segs = [f"<color={GREEN}>{set_name}</color>"]
    for need, eff in pairs:
        segs.append(f"{need}件套：{eff}")
    # literal backslash-n in file
    return "\\n".join(segs)

def main(items_csv, sets_csv, out_txt, max_title_len=200, max_block_len=0, allow_long=False):
    sets_map = load_sets(sets_csv)

    offenders = []  # (row_idx, title, block_len)
    out_lines = []

    with open(items_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        headers = [ (h or "").strip() for h in (r.fieldnames or []) ]
        # find 套装N columns
        set_cols = sorted(
            [h for h in headers if re.match(r"^套装\d+$", h)],
            key=lambda x: int(re.findall(r"\d+", x)[0])
        )

        # sanity check
        for col in ("卡牌标题", "基础效果"):
            if col not in headers:
                raise SystemExit(f"items CSV 需要列：{col}；实际列：{headers}")

        for idx, row in enumerate(r, start=2):  # header is row 1
            title = (row.get("卡牌标题") or "").strip()
            if not title:
                continue

            # title-length check
            if max_title_len and len(title) > max_title_len:
                raise SystemExit(
                    f"Error: 第{idx}行 卡牌标题 超过{max_title_len}字符（len={len(title)}）：{title}"
                )

            base_eff = (row.get("基础效果") or "").strip()

            parts = []
            if base_eff:
                parts.append(f"({base_eff})")

            for col in set_cols:
                sname = (row.get(col) or "").strip()
                if not sname:
                    continue
                pairs = sets_map.get(sname, [])
                parts.append(build_set_section(sname, pairs))

            block_line = "\\n".join(parts) if parts else ""

            # block-length check (counts spaces and literal '\n')
            if max_block_len and len(block_line) > max_block_len:
                offenders.append((idx, title, len(block_line)))

            # write output
            out_lines.append(title)
            out_lines.append(block_line)
            out_lines.append("")

    # fail if offenders exist and not allowed
    if offenders and not allow_long:
        preview = "\n".join(
            f"  - 第{row}行《{title}》 block长度={blen}"
            for row, title, blen in offenders[:10]
        )
        more = "" if len(offenders) <= 10 else f"\n  ...(还有 {len(offenders)-10} 条)"
        raise SystemExit(
            f"Error: {len(offenders)} 个条目 block 长度超过 {max_block_len}。\n{preview}{more}\n"
            f"可用 --allow-long 跳过，或提高 --max-block-len。"
        )

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="由两张CSV生成描述TXT（含(基础效果)；可校验标题/块长度）")
    ap.add_argument("--items", required=True, help="圣遗物.csv")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 TXT 路径")
    ap.add_argument("--max-title-len", type=int, default=200, help="卡牌标题最大长度（默认200）")
    ap.add_argument("--max-block-len", type=int, default=0, help="块文本最大长度（默认0=不检查）")
    ap.add_argument("--allow-long", action="store_true", help="存在超长块时也继续输出并返回0")
    args = ap.parse_args()
    main(args.items, args.sets, args.out, args.max_title_len, args.max_block_len, args.allow_long)