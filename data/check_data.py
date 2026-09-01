"""
check_data.py
-------------
Standalone helper (no Shiny required) that inspects the two source CSVs and
reports:

  1. How many rows are in each file.
  2. How many rows in bechdel_movies.csv have an imdb_id that does NOT
     appear in imdb_data.csv's id column (i.e. would be dropped by an
     inner join).
  3. A preview of those unmatched rows, plus an optional CSV export of
     the full list so you can inspect them all.

Run with:
    python check_data.py
    python check_data.py --bechdel path/to/bechdel_movies.csv --imdb path/to/imdb_data.csv
    python check_data.py --export unmatched.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def normalize_id(series: pd.Series) -> pd.Series:
    """Trim whitespace and cast to string so ids compare cleanly."""
    return series.astype(str).str.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bechdel",
        default="data/bechdel_movies.csv",
        help="Path to bechdel_movies.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--imdb",
        default="data/imdb_data.csv",
        help="Path to imdb_data.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--export",
        default=None,
        help="Optional path to write the full list of unmatched rows as CSV",
    )
    parser.add_argument(
        "--export-dupes",
        default=None,
        help=(
            "Optional path PREFIX to write the full duplicate rows as CSV. "
            "Writes '<prefix>_bechdel.csv' and '<prefix>_imdb.csv' for "
            "whichever file(s) actually have duplicates."
        ),
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=20,
        help="How many unmatched rows to print to the console (default: %(default)s)",
    )
    args = parser.parse_args()

    bechdel_path = Path(args.bechdel)
    imdb_path = Path(args.imdb)

    for p in (bechdel_path, imdb_path):
        if not p.exists():
            raise SystemExit(f"File not found: {p}")

    bechdel = pd.read_csv(bechdel_path)
    imdb = pd.read_csv(imdb_path)

    print("=" * 60)
    print("ROW COUNTS")
    print("=" * 60)
    print(f"{bechdel_path.name:<25} {len(bechdel):>8,} rows")
    print(f"{imdb_path.name:<25} {len(imdb):>8,} rows")

    # --- required columns check -------------------------------------------------
    missing_cols = []
    if "imdb_id" not in bechdel.columns:
        missing_cols.append(f"'imdb_id' missing from {bechdel_path.name}")
    if "id" not in imdb.columns:
        missing_cols.append(f"'id' missing from {imdb_path.name}")
    if missing_cols:
        raise SystemExit("Column check failed:\n  " + "\n  ".join(missing_cols))

    # --- duplicate id checks -----------------------------------------------------
    bechdel_ids = normalize_id(bechdel["imdb_id"])
    imdb_ids = normalize_id(imdb["id"])

    dupe_bechdel_ids = sorted(bechdel_ids[bechdel_ids.duplicated(keep=False)].unique())
    dupe_imdb_ids = sorted(imdb_ids[imdb_ids.duplicated(keep=False)].unique())

    print()
    print("=" * 60)
    print("DUPLICATE IDS")
    print("=" * 60)
    print(f"Duplicate imdb_id values in {bechdel_path.name}: {len(dupe_bechdel_ids)}")
    if dupe_bechdel_ids:
        for dup_id in dupe_bechdel_ids[: args.preview]:
            n_rows = (bechdel_ids == dup_id).sum()
            print(f"  {dup_id}  ({n_rows} rows)")
        if len(dupe_bechdel_ids) > args.preview:
            print(f"  ... and {len(dupe_bechdel_ids) - args.preview} more")

    print(f"Duplicate id values in {imdb_path.name}: {len(dupe_imdb_ids)}")
    if dupe_imdb_ids:
        for dup_id in dupe_imdb_ids[: args.preview]:
            n_rows = (imdb_ids == dup_id).sum()
            print(f"  {dup_id}  ({n_rows} rows)")
        if len(dupe_imdb_ids) > args.preview:
            print(f"  ... and {len(dupe_imdb_ids) - args.preview} more")

    if args.export_dupes:
        if dupe_bechdel_ids:
            out_path = f"{args.export_dupes}_bechdel.csv"
            bechdel[bechdel_ids.isin(dupe_bechdel_ids)].to_csv(out_path, index=False)
            print(f"Full duplicate rows from {bechdel_path.name} written to: {out_path}")
        if dupe_imdb_ids:
            out_path = f"{args.export_dupes}_imdb.csv"
            imdb[imdb_ids.isin(dupe_imdb_ids)].to_csv(out_path, index=False)
            print(f"Full duplicate rows from {imdb_path.name} written to: {out_path}")

    # --- unmatched rows -----------------------------------------------------------
    imdb_id_set = set(imdb_ids)
    bechdel_work = bechdel.copy()
    bechdel_work["_imdb_id_norm"] = bechdel_ids
    unmatched = bechdel_work[~bechdel_work["_imdb_id_norm"].isin(imdb_id_set)].drop(
        columns="_imdb_id_norm"
    )

    n_unmatched = len(unmatched)
    pct_unmatched = (n_unmatched / len(bechdel) * 100) if len(bechdel) else 0

    print()
    print("=" * 60)
    print("BECHDEL ROWS WITH NO MATCH IN IMDB DATA")
    print("=" * 60)
    print(
        f"{n_unmatched:,} of {len(bechdel):,} bechdel rows "
        f"({pct_unmatched:.1f}%) have an imdb_id not found in {imdb_path.name}"
    )

    if n_unmatched:
        print()
        display_cols = [c for c in ["imdb_id", "name", "score"] if c in unmatched.columns]
        preview = unmatched[display_cols].head(args.preview)
        print(f"Preview (first {min(args.preview, n_unmatched)} unmatched rows):")
        print(preview.to_string(index=False))
        if n_unmatched > args.preview:
            print(f"... and {n_unmatched - args.preview} more")

    if args.export:
        unmatched.to_csv(args.export, index=False)
        print()
        print(f"Full list of unmatched rows written to: {args.export}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()