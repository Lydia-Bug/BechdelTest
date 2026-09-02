from shiny import reactive, render, ui
from shinywidgets import render_widget

from .data import movies
from .filters import filter_movies
from .charts import comparison_chart, country_map


def server(input, output, session):

    # Map chart

    selected_country = reactive.value(None)

    def on_country_click(trace, points, state):
        if points.point_inds:
            index = points.point_inds[0]
            country = trace.locations[index]
            selected_country.set(country)

    # ==================================================================
    # Filtered data
    # ==================================================================

    @reactive.calc
    def filtered_data():

        result = filter_movies(
            df=movies,
            year_range=input.year_range(),
            genres=input.genre_filter(),
            # countries=input.country_filter(),
        )

        return result

    # ==================================================================
    # Movie table
    # ==================================================================

    @render.data_frame
    def movie_table():

        df = filtered_data()

        columns = [
            column
            for column in [
                "name",
                "title",
                "score",
                "release_year",
                "genres",
                "origin_country",
                "vote_average",
                "vote_count",
                "runtime",
                "budget",
                "revenue",
                "directors",
            ]
            if column in df.columns
        ]

        return render.DataGrid(
            df[columns],
            filters=True,
            height="500px",
        )

    # Chart
    @render_widget
    def comparison_plot():
        df = filtered_data()
        compare = input.compare()

        if compare == "country":
            return country_map(df, on_country_click)

        return comparison_chart(df, compare)

    @render.ui
    def country_movies():
        country = selected_country.get()

        if country is None:
            return ui.p("Click a country on the map to see its movies.")

        df = filtered_data()

        movies = df[
            df["origin_country_iso3"].apply(lambda countries: country in countries)
        ].copy()

        if movies.empty:
            return ui.p(f"No movies found for {country}.")

        movie_cards = []

        for _, movie in movies.iterrows():
            poster_path = movie.get("poster_path")

            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w200{poster_path}"

                movie_cards.append(
                    ui.div(
                        ui.tags.img(
                            src=poster_url,
                            class_="movie-poster",
                        ),
                        ui.p(
                            movie["title"],
                            class_="movie-title",
                        ),
                        class_="movie-card",
                    )
                )
            else:
                movie_cards.append(
                    ui.div(
                        ui.p(movie["title"]),
                        class_="movie-card",
                    )
                )

        return ui.div(
            ui.h3(f"Movies from {country}"),
            ui.div(
                *movie_cards,
                class_="movie-grid",
            ),
        )
