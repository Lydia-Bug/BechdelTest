from pathlib import Path
import ast
import pycountry
import pandas as pd

APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / "data"


def iso2_to_iso3(code):
    try:
        country = pycountry.countries.get(alpha_2=code)
        return country.alpha_3 if country else None
    except (AttributeError, KeyError):
        return None


def iso2_to_name(code):
    try:
        country = pycountry.countries.get(alpha_2=code)
        return country.name if country else None
    except (AttributeError, KeyError):
        return None


def parse_list(value):
    """
    Convert a string representation of a Python list/dictionary
    into an actual Python object.

    Examples:
        "['GB', 'US']"
        -> ['GB', 'US']

        "[{'id': 27, 'name': 'Horror'}]"
        -> [{'id': 27, 'name': 'Horror'}]
    """

    if pd.isna(value):
        return []

    try:
        result = ast.literal_eval(value)

        if isinstance(result, list):
            return result

        return []

    except (ValueError, SyntaxError):
        return []


def load_data() -> pd.DataFrame:
    """Load and prepare the Bechdel and TMDB datasets."""

    bechdel = pd.read_csv(DATA_DIR / "bechdel_movies.csv")

    tmdb = pd.read_csv(DATA_DIR / "tmdb_data.csv")

    # --------------------------------------------------------------
    # Normalise IMDb IDs
    # --------------------------------------------------------------

    bechdel["imdb_id"] = bechdel["imdb_id"].astype(str).str.strip()

    tmdb["imdb_id"] = tmdb["imdb_id"].astype(str).str.strip()

    # --------------------------------------------------------------
    # Merge datasets
    # --------------------------------------------------------------

    merged = bechdel.merge(
        tmdb,
        on="imdb_id",
        how="inner",
        suffixes=("_bechdel", "_tmdb"),
    )

    # --------------------------------------------------------------
    # Release date / year
    # --------------------------------------------------------------

    if "release_date" in merged.columns:

        merged["release_date"] = pd.to_datetime(
            merged["release_date"],
            errors="coerce",
        )

        merged["release_year"] = merged["release_date"].dt.year

    # --------------------------------------------------------------
    # Bechdel score
    # --------------------------------------------------------------

    if "score" in merged.columns:

        merged["score"] = merged["score"].astype("Int64")

    # --------------------------------------------------------------
    # Genres
    # --------------------------------------------------------------

    if "genres" in merged.columns:

        merged["genres_parsed"] = merged["genres"].apply(
            lambda x: [
                genre["name"]
                for genre in parse_list(x)
                if (isinstance(genre, dict) and "name" in genre)
            ]
        )

    else:

        merged["genres_parsed"] = [[] for _ in range(len(merged))]

    # --------------------------------------------------------------
    # Origin countries
    # --------------------------------------------------------------

    if "origin_country" in merged.columns:

        merged["origin_country_parsed"] = merged["origin_country"].apply(parse_list)

    else:

        merged["origin_country_parsed"] = [[] for _ in range(len(merged))]

    merged["origin_country_iso3"] = merged["origin_country_parsed"].apply(
        lambda countries: [
            iso2_to_iso3(country) for country in countries if iso2_to_iso3(country)
        ]
    )

    merged["origin_country_name"] = merged["origin_country_parsed"].apply(
        lambda countries: [
            iso2_to_name(country) for country in countries if iso2_to_name(country)
        ]
    )

    return merged


# Load the data once when the application starts
movies = load_data()


# ------------------------------------------------------------------
# Filter choices
# ------------------------------------------------------------------

if "release_year" in movies.columns:

    valid_years = movies["release_year"].dropna()

    if not valid_years.empty:
        MIN_YEAR = int(valid_years.min())
        MAX_YEAR = int(valid_years.max())
    else:
        MIN_YEAR = 1900
        MAX_YEAR = 2025

else:

    MIN_YEAR = 1900
    MAX_YEAR = 2025


ALL_GENRES = sorted({genre for genres in movies["genres_parsed"] for genre in genres})


ALL_COUNTRIES = sorted(
    {country for countries in movies["origin_country_parsed"] for country in countries}
)

COMPARISON_CHOICES = {
    "genre": "Genre",
    "year": "Year",
    "country": "Country",
    "vote_average": "TMDB rating",
    "runtime": "Runtime",
    "budget": "Budget",
    "revenue": "Revenue",
}
