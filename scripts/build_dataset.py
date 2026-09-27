"""Build the analysis dataset. Run: python scripts/build_dataset.py"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config              # noqa: E402
from src.data_loader import load_raw  # noqa: E402
from src.preprocessing import clean   # noqa: E402


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=None)
    args = parser.parse_args()

    df, report = clean(load_raw(args.raw))
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.PROCESSED_FILE, index=False)
    config.CLEANING_REPORT_FILE.write_text(json.dumps(report, indent=2))

    print(f"\nWrote {len(df):,} rows -> {config.PROCESSED_FILE}")
    for r in report:
        print(f"  {r['step']:<22} removed {r['rows_removed']:>8,}  -> {r['rows_after']:>8,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())