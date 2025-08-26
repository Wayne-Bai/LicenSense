from pathlib import Path
import os
import re
import json
from typing import List, Dict, Tuple

# ----- config -----
# Empty string => process ALL matching files; e.g., set KEYWORD = "BRSET" to process only that one
KEYWORD = ""

# ----- helpers -----
def safe_name(s: str, maxlen: int = 100) -> str:
    """Make a string safe for filenames."""
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    return s[:maxlen].strip("._-")

def collect_files(keyword: str, base_dir: Path | None = None) -> List[Path]:
    """
    Collect JSON files from the 'main entrance' directory (current working dir via $PWD or os.getcwd()).
      - If keyword is provided => exactly that single file.
      - Else => all files matching final_processed_huggingface_*.json.
    """
    if base_dir is None:
        base_dir = Path(os.environ.get("PWD", os.getcwd())).resolve()

    if keyword:
        fname = f"final_processed_huggingface_{safe_name(keyword)}.json"
        candidate = base_dir / fname
        if not candidate.exists():
            raise FileNotFoundError(f"Expected file not found: {candidate}")
        return [candidate]
    else:
        files = sorted(base_dir.glob("final_processed_huggingface_*.json"))
        if not files:
            raise FileNotFoundError(
                f"No files found in {base_dir} matching: final_processed_huggingface_*.json"
            )
        return files

def infer_keyword_from_filename(path: Path) -> str:
    """
    Extract the keyword from a filename like 'final_processed_huggingface_<keyword>.json'.
    Returns the sanitized keyword part (whatever is in the filename).
    """
    stem = path.stem  # e.g., 'final_processed_huggingface_BRSET'
    prefix = "final_processed_huggingface_"
    return stem[len(prefix):] if stem.startswith(prefix) else stem

def normalize_items(data) -> list:
    """
    Ensure we have a list of repo-like dicts.
    Accepts either:
      - a list (returned as-is),
      - a dict with a list under common keys (huggingface/items/data),
      - a single dict (wrapped).
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("huggingface", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]  # single dict
    return []

def count_coarse_and_fine(items: list) -> Tuple[int, int]:
    """
    coarse = number of items
    fine   = number of items with downstream_usage.is_downstream == True
    """
    coarse = len(items)
    fine = 0
    for repo in items:
        if isinstance(repo, dict):
            if repo.get("downstream_usage", {}).get("is_downstream", False):
                fine += 1
    return coarse, fine

# ----- main -----
def main():
    files = collect_files(KEYWORD)

    # per-keyword metrics
    per_kw: Dict[str, Dict[str, int]] = {}
    grand_coarse = 0
    grand_fine = 0

    for path in files:
        kw = infer_keyword_from_filename(path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        items = normalize_items(data)
        coarse, fine = count_coarse_and_fine(items)

        grand_coarse += coarse
        grand_fine += fine

        per_kw[kw] = {
            "coarse": coarse,
            "fine": fine,
            "total": coarse,  # per-keyword total == number of items (coarse)
        }

    # ---- prints ----
    print("\nPer-keyword stats:")
    for kw in sorted(per_kw):
        c = per_kw[kw]["coarse"]
        f = per_kw[kw]["fine"]
        t = per_kw[kw]["total"]
        pct = (f / c * 100.0) if c else 0.0
        print(f"  - {kw}: coarse={c}, fine={f} ({pct:.1f}%), total={t}")

    print("\nGrand totals:")
    g_pct = (grand_fine / grand_coarse * 100.0) if grand_coarse else 0.0
    print(f"  coarse={grand_coarse}, fine={grand_fine} ({g_pct:.1f}%), keywords={len(per_kw)}, files={len(files)}")

if __name__ == "__main__":
    main()

