import csv, json, re, sys
from pathlib import Path

DEFAULT_OUTER_STRUCT_ID = "1077936138"
DEFAULT_INNER_STRUCT_ID = "1077936139"
DEFAULT_ALT_COLOR = "#86e1f1"

def to_int_str(v, default="0"):
    s = str(v).strip() if v is not None else ""
    if s == "":
        return default
    try:
        return str(int(float(s)))
    except Exception:
        return default

# Find "(...)" groups
PAREN_RE = re.compile(r"\(([^()]*)\)")

def split_alts(s: str):
    return [part.strip() for part in s.split("/")]

def collect_groups(desc: str):
    groups = []
    for m in PAREN_RE.finditer(desc):
        groups.append(split_alts(m.group(1)))
    return groups

def derive_level_count(groups, limit_int: int):
    if not groups:
        return max(1, limit_int or 1)
    max_alts = max(len(g) for g in groups)
    if limit_int and limit_int > 0:
        return min(max_alts, limit_int)
    return max_alts

def wrap_color(text: str, color: str):
    t = text.strip()
    if "<color=" in t and "</color>" in t:
        return text  # already colored
    return f"<color={color}>{t}</color>"

def normalize_literal_newlines(s: str) -> str:
    """Ensure the string contains literal backslash+n sequences, not actual newline chars."""
    if s is None:
        return ""
    # First, replace Windows CRLF and lone CR with \n literal
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Then convert any real newline chars to literal backslash-n
    s = s.replace("\n", "\\n")
    return s

def build_final_text(desc_template: str, groups, level_idx: int, alt_color: str, prefix_newline: bool):
    gi = 0
    def repl(m):
        nonlocal gi
        alts = groups[gi] if gi < len(groups) else [""]
        choice = alts[level_idx] if level_idx < len(alts) else alts[-1]
        gi += 1
        if alt_color:
            choice = wrap_color(choice, alt_color)
        return choice
    s = PAREN_RE.sub(repl, desc_template)
    # Normalize any actual newlines the template might have
    s = normalize_literal_newlines(s)
    # Prepend literal \n if requested and not already present
    if prefix_newline and not s.startswith("\\n"):
        s = "\\n" + s
    return s

def derive_pairs_from_desc(desc: str, limit: str, alt_color: str, prefix_newline: bool):
    try:
        limit_int = int(float(str(limit).strip())) if str(limit).strip() else 0
    except Exception:
        limit_int = 0
    groups = collect_groups(desc)
    n_levels = derive_level_count(groups, limit_int)
    finals = [build_final_text(desc, groups, i, alt_color=alt_color, prefix_newline=prefix_newline) for i in range(n_levels)]
    pairs = []
    if n_levels == 1:
        pairs.append((finals[0], finals[0]))
    else:
        pairs.append((finals[0], finals[0]))
        for i in range(1, n_levels):
            trans = finals[i-1] + "\\n\\n↓\\n\\n" + finals[i]
            pairs.append((trans, finals[i]))
    return pairs, str(n_levels)

def build_level_struct(transition_text: str, final_text: str, inner_struct_id: str):
    # Normalize any real newlines (from explicit pairs) into literal "\n"
    transition_text = normalize_literal_newlines(transition_text)
    final_text = normalize_literal_newlines(final_text)
    return {
        "param_type": "Struct",
        "value": {
            "structId": inner_struct_id,
            "type": "Struct",
            "value": [
                {"param_type": "String", "value": transition_text},
                {"param_type": "String", "value": final_text},
            ],
        },
    }

def build_entry_row(name: str, limit_val: str, state_id: str, desc: str, pairs: list, outer_struct_id: str, inner_struct_id: str, alt_color: str, prefix_newline: bool):
    level_values = []
    if not pairs:
        pairs, computed_levels = derive_pairs_from_desc(desc, limit_val, alt_color=alt_color, prefix_newline=prefix_newline)
        limit_val = to_int_str(limit_val or computed_levels, default=computed_levels)
    else:
        fixed = []
        for (t, f) in pairs:
            # Preserve explicit text, but normalize any real newlines to literal \n
            t = normalize_literal_newlines(str(t))
            f = normalize_literal_newlines(str(f) if (f is not None and str(f).strip() != "") else str(t))
            fixed.append((t, f))
        pairs = fixed

    for (t, f) in pairs:
        level_values.append(build_level_struct(t, f, inner_struct_id))

    return {
        "key": {"param_type": "String", "value": name},
        "value": {
            "param_type": "Struct",
            "value": {
                "structId": outer_struct_id,
                "type": "Struct",
                "value": [
                    {"param_type": "String", "value": name},
                    {
                        "param_type": "StructList",
                        "value": {
                            "structId": inner_struct_id,
                            "value": level_values
                        }
                    },
                    {"param_type": "Int32", "value": to_int_str(limit_val, default=str(len(level_values)))},
                    {"param_type": "Int32", "value": to_int_str(state_id, default="0")},
                ],
            },
        },
    }

def parse_csv(path_csv: str, outer_struct_id: str, inner_struct_id: str, alt_color: str, prefix_newline: bool):
    entries = []
    with open(path_csv, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        try:
            header = next(r)
        except StopIteration:
            return entries

        header = [ (h or "").strip() for h in header ]
        try:
            idx_name = header.index("名字")
            idx_limit = header.index("上限")
            idx_state = header.index("状态ID")
            idx_desc = header.index("描述")
        except ValueError as e:
            raise SystemExit(f"CSV 缺少必需列（名字/上限/状态ID/描述）。实际列: {header}")

        for row in r:
            if len(row) < len(header):
                row = row + [""] * (len(header) - len(row))

            name = (row[idx_name] or "").strip()
            if not name:
                continue
            limit_val = row[idx_limit] if idx_limit < len(row) else ""
            state_id  = row[idx_state]  if idx_state  < len(row) else ""
            desc      = row[idx_desc]   if idx_desc   < len(row) else ""

            tail = row[idx_desc+1:] if (idx_desc+1) <= len(row) else []
            while tail and (tail[-1] is None or str(tail[-1]).strip() == ""):
                tail.pop()

            pairs = []
            i = 0
            while i < len(tail):
                t = tail[i] if i < len(tail) else ""
                f = tail[i+1] if (i+1) < len(tail) else t
                pairs.append((str(t), str(f)))
                i += 2

            entries.append(build_entry_row(name, limit_val, state_id, desc, pairs, outer_struct_id, inner_struct_id, alt_color=alt_color, prefix_newline=prefix_newline))

    return entries

def build_json(path_csv: str, out_path: str, outer_struct_id: str = DEFAULT_OUTER_STRUCT_ID, inner_struct_id: str = DEFAULT_INNER_STRUCT_ID, alt_color: str = DEFAULT_ALT_COLOR, prefix_newline: bool = True):
    entries = parse_csv(path_csv, outer_struct_id, inner_struct_id, alt_color=alt_color, prefix_newline=prefix_newline)
    obj = {
        "type": "Dict",
        "key_type": "String",
        "value_type": "Struct",
        "value": entries,
        "value_structId": outer_struct_id
    }
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return str(outp)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Parse traits CSV into nested Struct/StructList JSON with literal '\\n' sequences and auto-colored alts.")
    ap.add_argument("--csv", required=True, help="Path to CSV (UTF-8/UTF-8-SIG). Headers: 名字,上限,状态ID,描述,(pairs...)")
    ap.add_argument("--out", required=True, help="Output JSON file path")
    ap.add_argument("--outer-struct-id", dest="outer_struct_id", default=DEFAULT_OUTER_STRUCT_ID, help="Outer structId (default 1077936138)")
    ap.add_argument("--inner-struct-id", dest="inner_struct_id", default=DEFAULT_INNER_STRUCT_ID, help="Inner structId for levels (default 1077936139)")
    ap.add_argument("--alt-color", default=DEFAULT_ALT_COLOR, help="Color to wrap alternatives chosen from '(...)' (e.g., #86e1f1). Empty to disable.")
    ap.add_argument("--no-prefix-newline", action="store_true", help="Do not prefix derived strings with literal '\\n'.")
    args = ap.parse_args()
    path = build_json(args.csv, args.out, args.outer_struct_id, args.inner_struct_id, alt_color=(args.alt_color or ""), prefix_newline=(not args.no_prefix_newline))
    print(f"Wrote {path}")
