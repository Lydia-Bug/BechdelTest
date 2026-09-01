"""
fetch_tmdb_data.py
-------------------
Reads bechdel_movies.csv (imdb_id, score, explanation, name) and, for each
imdb_id, looks the movie up on TMDB to pull additional data: title, genres,
runtime, rating, vote count, budget, revenue, release date, and director(s).

Writes the result to tmdb_data.csv, in a shape that mirrors imdb_data.csv so
it's a drop-in replacement in the Shiny app (just point the app at this file
and join on imdb_id instead of id).

Setup
-----
1. Get a free TMDB API key: https://www.themoviedb.org/settings/api
2. pip install tmdbsimple python-dotenv
3. Put your key in a .env file next to this script (don't commit it):

     TMDB_API_KEY=your_key_here

   (Alternatively, set it as a real environment variable, or pass --api-key.)

Run
---
    python fetch_tmdb_data.py
    python fetch_tmdb_data.py --input data/bechdel_movies.csv --output data/tmdb_data.csv
    python fetch_tmdb_data.py --limit 50          # just do the first 50, for testing

The script writes progress to tmdb_data.csv incrementally and skips imdb_ids
that are already in the output file, so if it gets interrupted (rate limit,
network blip, Ctrl-C) you can just re-run it and it'll pick up where it left
off.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests
import tmdbsimple as tmdb
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env")  # loads TMDB_API_KEY from the .env next to this script

OUTPUT_FIELDNAMES = None


def get_api_key(cli_value: str | None) -> str:
    key = cli_value or os.environ.get("TMDB_API_KEY")
    if not key:
        sys.exit(
            "No TMDB API key found. Set the TMDB_API_KEY environment variable "
            "or pass --api-key YOUR_KEY. Get a free key at "
            "https://www.themoviedb.org/settings/api"
        )
    return key


def call_with_retries(func, *args, max_retries: int = 5, **kwargs):
    """Call a tmdbsimple method, retrying on rate limits / transient errors.

    tmdbsimple raises requests.exceptions.HTTPError on non-2xx responses,
    with the original response attached, so we inspect that.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None

            if status == 404:
                return None

            if status == 429:
                wait = float(exc.response.headers.get("Retry-After", 1))
                time.sleep(wait)
                continue

            if status is not None and 500 <= status < 600:
                time.sleep(attempt)  # simple backoff
                continue

            # Anything else (401 bad key, etc.) - fail loudly, retrying won't help
            raise

    print(f"  Giving up after {max_retries} retries")
    return None


def find_tmdb_movie(imdb_id: str) -> dict | None:
    """Look up a TMDB movie by its IMDb id."""
    find = tmdb.Find(imdb_id)
    data = call_with_retries(find.info, external_source="imdb_id")
    if not data:
        return None
    results = data.get("movie_results") or []
    return results[0] if results else None


def get_movie_details(tmdb_id: int) -> dict | None:
    """Fetch full movie details + credits in one call."""
    movie = tmdb.Movies(tmdb_id)
    return call_with_retries(movie.info, append_to_response="credits")


def extract_directors(details: dict) -> str:
    crew = details.get("credits", {}).get("crew", [])
    directors = [person["name"] for person in crew if person.get("job") == "Director"]
    return ", ".join(directors)


def build_row(imdb_id: str, details: dict) -> dict:
    """Keep all TMDB movie fields, plus directors and IMDb ID."""

    row = details.copy()

    # Remove credits from the main movie fields.
    # We only want the directors from credits.
    row.pop("credits", None)

    # Add IMDb ID used for matching
    row["imdb_id"] = imdb_id

    # Extract directors
    row["directors"] = extract_directors(details)

    return row


def load_already_fetched(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    with output_path.open(newline="", encoding="utf-8") as f:
        return {row["imdb_id"] for row in csv.DictReader(f)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(SCRIPT_DIR / "bechdel_movies.csv"))
    parser.add_argument("--output", default=str(SCRIPT_DIR / "tmdb_data.csv"))
    parser.add_argument("--api-key", default=None, help="TMDB API key (or set TMDB_API_KEY env var)")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows (for testing)")
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="Seconds to sleep between requests, to be polite to the API (default: %(default)s)",
    )
    args = parser.parse_args()

    tmdb.API_KEY = get_api_key(args.api_key)
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        sys.exit(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    already_fetched = load_already_fetched(output_path)
    if already_fetched:
        print(f"Resuming: {len(already_fetched)} movies already in {output_path}, will skip those.")

    with input_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if args.limit:
        rows = rows[: args.limit]

    write_header = not output_path.exists() or output_path.stat().st_size == 0

    n_found = 0
    n_not_found = 0
    n_skipped = 0

    with output_path.open("a", newline="", encoding="utf-8") as out_f:
        writer = None

        for i, row in enumerate(rows, start=1):
            imdb_id = row["imdb_id"].strip()

            if imdb_id in already_fetched:
                n_skipped += 1
                continue

            print(f"[{i}/{len(rows)}] {row.get('name', imdb_id)} ({imdb_id})", end=" ")

            match = find_tmdb_movie(imdb_id)

            if not match:
                print("-> not found on TMDB")
                n_not_found += 1
                time.sleep(args.sleep)
                continue

            details = get_movie_details(match["id"])

            if not details:
                print("-> found but couldn't fetch details")
                n_not_found += 1
                time.sleep(args.sleep)
                continue

            out_row = build_row(imdb_id, details)

            # Create CSV writer once we know all the fields
            if writer is None:
                fieldnames = list(out_row.keys())
                writer = csv.DictWriter(
                    out_f,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                )
                writer.writeheader()

            writer.writerow(out_row)
            out_f.flush()

            n_found += 1
            print("-> OK")
            time.sleep(args.sleep)

    print()
    print("=" * 60)
    print(f"Found on TMDB:     {n_found}")
    print(f"Not found:         {n_not_found}")
    print(f"Skipped (cached):  {n_skipped}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()