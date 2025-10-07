import csv, json, sys
from pathlib import Path

DEFAULT_STRUCT_ID = "1077936135"

def to_int_str(v, default="0"):
    s = "" if v is None else str(v).strip()
    if s == "":
        return default
    try:
        return str(int(float(s)))
    except Exception:
        return default

def safe_get(row, idx, default=""):
    return row[idx].strip() if (idx is not None and idx < len(row) and row[idx] is not None) else default

def main(csv_path: str, out_path: str, struct_id: str = DEFAULT_STRUCT_ID):
    entries = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit("CSV is empty.")
        header = [(h or "").strip() for h in header]

        # Required columns
        try:
            idx_name = header.index("名字")
            idx_id   = header.index("ID")
            idx_req1 = header.index("套装需求1")
            idx_req2 = header.index("套装需求2")
            idx_req3 = header.index("套装需求3")
        except ValueError as e:
            raise SystemExit(f"Missing required headers. Got: {header}")

        # Collect the three 状态效果ID columns in order of appearance
        state_id_idxs = [i for i, h in enumerate(header) if h == "状态效果ID"]
        if len(state_id_idxs) < 3:
            state_id_idxs = state_id_idxs + [None] * (3 - len(state_id_idxs))

        for row in reader:
            # Pad to header length
            if len(row) < len(header):
                row = row + [""] * (len(header) - len(row))

            name = safe_get(row, idx_name)
            set_id = safe_get(row, idx_id)
            if not name or not set_id:
                continue  # skip rows without key info

            req1 = to_int_str(safe_get(row, idx_req1))
            req2 = to_int_str(safe_get(row, idx_req2))
            req3 = to_int_str(safe_get(row, idx_req3), default="99")

            sid1 = to_int_str(safe_get(row, state_id_idxs[0]), default="0")
            sid2 = to_int_str(safe_get(row, state_id_idxs[1]), default="0")
            sid3 = to_int_str(safe_get(row, state_id_idxs[2]), default="0")

            entry = {
                "key": {"param_type": "ConfigReference", "value": set_id},
                "value": {
                    "param_type": "Struct",
                    "value": {
                        "structId": struct_id,
                        "type": "Struct",
                        "value": [
                            {"param_type": "String", "value": name},
                            {"param_type": "Int32", "value": req1},
                            {"param_type": "ConfigReference", "value": sid1},
                            {"param_type": "Int32", "value": req2},
                            {"param_type": "ConfigReference", "value": sid2},
                            {"param_type": "Int32", "value": req3},
                            {"param_type": "ConfigReference", "value": sid3},
                            {"param_type": "ConfigReference", "value": set_id},
                        ]
                    }
                }
            }
            entries.append(entry)

    obj = {
        "type": "Dict",
        "key_type": "ConfigReference",
        "value_type": "Struct",
        "value": entries,
        "value_structId": struct_id
    }

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as w:
        json.dump(obj, w, ensure_ascii=False, indent=2)

    print(f"Wrote {outp} with {len(entries)} entries.")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Convert 圣遗物套装 CSV to Dict<ConfigReference, Struct> JSON.")
    ap.add_argument("--csv", required=True, help="Input CSV path (UTF-8/UTF-8-SIG).")
    ap.add_argument("--out", required=True, help="Output JSON path.")
    ap.add_argument("--struct-id", default=DEFAULT_STRUCT_ID, help="StructId for entries (default 1077936135).")
    args = ap.parse_args()
    main(args.csv, args.out, struct_id=args.struct_id)
