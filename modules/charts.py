import plotly.express as px
import plotly.graph_objects as go


def comparison_chart(df, compare):

    if compare == "genre":
        data = (
            df.explode("genres_parsed")
            .groupby("genres_parsed", as_index=False)["score"]
            .mean()
            .sort_values("score", ascending=False)
        )

        fig = px.bar(
            data,
            x="genres_parsed",
            y="score",
            labels={
                "genres_parsed": "Genre",
                "score": "Average Bechdel score",
            },
            title="Bechdel score by genre",
        )

    # elif compare == "country":
    #     data = (
    #         df.explode("origin_country_iso3")
    #         .groupby("origin_country_iso3", as_index=False)["score"]
    #         .mean()
    #         .sort_values("score", ascending=False)
    #     )

    #     fig = px.bar(
    #         data,
    #         x="origin_country_iso3",
    #         y="score",
    #         labels={
    #             "origin_country_iso3": "Country",
    #             "score": "Average Bechdel score",
    #         },
    #         title="Bechdel score by country",
    #     )

    elif compare == "year":
        data = (
            df.groupby("release_year", as_index=False)["score"]
            .mean()
            .sort_values("release_year")
        )

        fig = px.line(
            data,
            x="release_year",
            y="score",
            labels={
                "release_year": "Release year",
                "score": "Average Bechdel score",
            },
            title="Bechdel score by release year",
        )

    elif compare in ["vote_average", "runtime", "budget", "revenue"]:

        labels = {
            "vote_average": "TMDB rating",
            "runtime": "Runtime",
            "budget": "Budget",
            "revenue": "Revenue",
        }

        data = df[[compare, "score"]].dropna()

        fig = px.box(
            data,
            x=compare,
            y="score",
            orientation="h",
            points=False,
            category_orders={"score": [0, 1, 2, 3]},
            labels={
                "score": "Bechdel score",
                compare: labels[compare],
            },
            title=f"{labels[compare]} by Bechdel score",
        )

        fig.update_yaxes(
            tickmode="array",
            tickvals=[0, 1, 2, 3],
            range=[-0.5, 3.5],
        )

    else:
        fig = px.scatter(
            title="Select a comparison",
        )

    fig.update_yaxes(
        range=[0, 3],
        dtick=1,
    )

    return fig


def country_map(df, on_country_click):
    data = df.explode("origin_country_iso3").dropna(
        subset=["origin_country_iso3", "score"]
    )

    country_scores = data.groupby("origin_country_iso3", as_index=False).agg(
        average_score=("score", "mean"),
        movies=("title", "count"),
    )

    fig = px.choropleth(
        country_scores,
        locations="origin_country_iso3",
        color="average_score",
        locationmode="ISO-3",
        hover_name="origin_country_iso3",
        hover_data={
            "average_score": ":.2f",
            "movies": True,
            "origin_country_iso3": False,
        },
        labels={
            "average_score": "Average Bechdel score",
            "movies": "Movies",
        },
        title="Average Bechdel score by country",
        range_color=(0, 3),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
    )

    # Convert to FigureWidget so we can capture clicks
    widget = go.FigureWidget(fig)

    # Listen for clicks on the map
    widget.data[0].on_click(on_country_click)

    return widget
