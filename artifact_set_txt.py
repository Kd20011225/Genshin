import csv
from pathlib import Path

SEPARATOR = "  "  # double space between segments

def load_sets(sets_csv: str):
    """
    读取套装CSV，返回列表：[ (名字, [(need, effect), ...]) ]
    """
    results = []
    with open(sets_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise SystemExit(f"{sets_csv} 缺少表头")
        for row in r:
            name = (row.get("名字") or "").strip()
            if not name:
                continue
            pairs = []
            # 最多支持10段，可按需加大
            for i in range(1, 11):
                need = (row.get(f"套装需求{i}") or "").strip()
                eff  = (row.get(f"套装效果{i}") or "").strip()
                if need and eff:
                    pairs.append((need, eff))
            results.append((name, pairs))
    return results

def make_block(pairs):
    """
    用**两个空格**连接“{need}件套：{eff}”行
    """
    lines = [f"{need}件套：{eff}" for need, eff in pairs]
    return SEPARATOR.join(lines)

def build_txt(sets_csv: str, out_txt: str):
    sets = load_sets(sets_csv)
    out_lines = []
    for name, pairs in sets:
        if not pairs:
            # 没有效果就只写名字与空行
            out_lines.append(name)
            out_lines.append("")
            out_lines.append("")
            continue

        block = make_block(pairs)
        out_lines.append(name)
        out_lines.append(block)
        out_lines.append("")  # 分隔空行

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="从圣遗物套装.csv 生成TXT（仅真实效果文本，段内以两个空格分隔）")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv")
    ap.add_argument("--out", required=True, help="输出 TXT 路径")
    args = ap.parse_args()
    build_txt(args.sets, args.out)