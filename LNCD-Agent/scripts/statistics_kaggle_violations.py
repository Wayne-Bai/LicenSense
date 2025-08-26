from pathlib import Path
import os
import re
import json
from typing import List, Dict
from collections import Counter

# ----- config -----
# Empty string => process ALL matching files; e.g., set KEYWORD = "Adience" to process only that one
KEYWORD = ""

# Categories to count
RULES = ["non_commercial", "sharealike", "no_derivatives", "give_credit"]

# ----- helpers -----
def safe_name(s: str, maxlen: int = 100) -> str:
    """Make a string safe for filenames."""
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    return s[:maxlen].strip("._-")

def collect_files(keyword: str, base_dir: Path | None = None) -> List[Path]:
    """
    Collect JSON files from the 'main entrance' directory (current working dir via $PWD or os.getcwd()).
      - If keyword is provided => exactly that single file.
      - Else => all files matching violations_kaggle_*.json.
    """
    if base_dir is None:
        base_dir = Path(os.environ.get("PWD", os.getcwd())).resolve()

    if keyword:
        fname = f"violations_kaggle_{safe_name(keyword)}.json"
        candidate = base_dir / fname
        if not candidate.exists():
            raise FileNotFoundError(f"Expected file not found: {candidate}")
        return [candidate]
    else:
        files = sorted(base_dir.glob("violations_kaggle_*.json"))
        if not files:
            raise FileNotFoundError(
                f"No files found in {base_dir} matching: violations_kaggle_*.json"
            )
        return files

def infer_keyword_from_filename(path: Path) -> str:
    """
    Extract the keyword from a filename like 'violations_kaggle_<keyword>.json'.
    Returns the sanitized keyword part (whatever is in the filename).
    """
    stem = path.stem  # e.g., 'violations_kaggle_Adience'
    prefix = "violations_kaggle_"
    return stem[len(prefix):] if stem.startswith(prefix) else stem

def normalize_items(data) -> list:
    """
    Ensure we have a list of repo-like dicts.
    Accepts either:
      - a list (returned as-is),
      - a dict with a list under common keys (kaggle/items/data),
      - a single dict (wrapped).
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("kaggle", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]  # single dict
    return []

def count_rule_violations(items: list) -> Counter:
    """
    Count violation entries per RULE across all kaggle in the list.
    (Counts every listed violation entry; does not deduplicate per repo.)
    """
    cnt = Counter({r: 0 for r in RULES})
    for repo in items:
        if not isinstance(repo, dict):
            continue
        violations = repo.get("violations") or []
        if isinstance(violations, list):
            for v in violations:
                if isinstance(v, dict):
                    r = v.get("rule")
                    if r in RULES:
                        cnt[r] += 1
    return cnt

# ----- main -----
def main():
    files = collect_files(KEYWORD)

    per_dataset: Dict[str, Counter] = {}
    totals = Counter({r: 0 for r in RULES})

    for path in files:
        ds_name = infer_keyword_from_filename(path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items = normalize_items(data)
        counts = count_rule_violations(items)
        per_dataset[ds_name] = counts
        totals.update(counts)

    # ---- prints ----
    print("\nPer-dataset violations by category:")
    for ds in sorted(per_dataset):
        c = per_dataset[ds]
        parts = [f"{r}={c.get(r, 0)}" for r in RULES]
        print(f"  - {ds}: " + ", ".join(parts))

    print("\nTotal violations across all datasets:")
    for r in RULES:
        print(f"  {r}: {totals.get(r, 0)}")

    print(f"\nDatasets processed: {len(per_dataset)}  Files: {len(files)}")

if __name__ == "__main__":
    main()
