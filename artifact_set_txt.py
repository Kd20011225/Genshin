import csv
from pathlib import Path
from typing import List, Tuple

# ===== Default Style =====
DEFAULT_SEPARATOR = "  "   # double space
DEFAULT_COLOR_OPEN = "<color=#71db60>"
DEFAULT_COLOR_CLOSE = "</color>"


def wrap_color(text: str, open_tag: str, close_tag: str) -> str:
    """Wrap text with color tags like <color=#71db60>...</color>"""
    return f"{open_tag}{text}{close_tag}" if text else text


def load_sets(sets_csv: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    读取圣遗物套装CSV，返回列表：[ (名字, [(need, effect), ...]) ]
    """
    results: List[Tuple[str, List[Tuple[str, str]]]] = []
    with open(sets_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"{sets_csv} 缺少表头")

        # Normalize header names
        headers = {h.strip(): h for h in reader.fieldnames}

        def get(row, key):
            real = headers.get(key, key)
            return (row.get(real) or "").strip()

        for row in reader:
            name = get(row, "名字")
            if not name:
                continue

            pairs: List[Tuple[str, str]] = []
            for i in range(1, 11):
                need = get(row, f"套装需求{i}")
                eff  = get(row, f"套装效果{i}")
                if need and eff:
                    pairs.append((need, eff))
            results.append((name, pairs))
    return results


def make_block(pairs: List[Tuple[str, str]], sep: str) -> str:
    """Join need/effect pairs with separator."""
    return sep.join([f"{need}件套：{eff}" for need, eff in pairs])


def build_txt(
    sets_csv: str,
    out_txt: str,
    sep: str = DEFAULT_SEPARATOR,
    color_open: str = DEFAULT_COLOR_OPEN,
    color_close: str = DEFAULT_COLOR_CLOSE,
):
    """生成TXT输出，每个名字和效果在同一行"""
    sets = load_sets(sets_csv)
    out_lines: List[str] = []

    for name, pairs in sets:
        colored_name = wrap_color(name, color_open, color_close)
        if pairs:
            block = make_block(pairs, sep)
            out_lines.append(f"{colored_name}{sep}{block}")
        else:
            out_lines.append(colored_name)
        out_lines.append("")  # blank line between entries

    outp = Path(out_txt)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {outp.resolve()}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="从圣遗物套装.csv 生成TXT（带颜色标签）")
    ap.add_argument("--sets", required=True, help="圣遗物套装.csv 文件路径")
    ap.add_argument("--out", required=True, help="输出 TXT 文件路径")
    ap.add_argument("--sep", default=DEFAULT_SEPARATOR, help="段内分隔符（默认两个空格）")
    ap.add_argument("--hex", default="71db60", help="颜色HEX码（默认71db60）")
    args = ap.parse_args()

    color_open = f"<color=#{args.hex}>"
    color_close = "</color>"

    build_txt(args.sets, args.out, sep=args.sep, color_open=color_open, color_close=color_close)