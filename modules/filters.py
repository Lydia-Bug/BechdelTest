def filter_movies(
    df,
    year_range,
    genres,
    countries,
):
    """Apply dashboard filters to the movie dataframe."""

    df = df.copy()

    # --------------------------------------------------------------
    # Release year
    # --------------------------------------------------------------

    df = df.copy()

    lo, hi = year_range
    df = df[df["release_year"].between(lo, hi)]

    # # --------------------------------------------------------------
    # # Genre
    # # --------------------------------------------------------------

    if genres:

        selected_genres = set(genres)

        df = df[
            df["genres_parsed"].apply(
                lambda movie_genres: bool(selected_genres & set(movie_genres))
            )
        ]

    # # --------------------------------------------------------------
    # # Origin country
    # # --------------------------------------------------------------

    if countries:

        selected_countries = set(countries)

        df = df[
            df["origin_country_parsed"].apply(
                lambda movie_countries: bool(selected_countries & set(movie_countries))
            )
        ]

    return df
