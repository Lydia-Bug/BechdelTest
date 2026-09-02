import plotly.express as px
import plotly.graph_objects as go

ACCENT_COLOR = "#FF6B6B"
BACKGROUND_COLOR = "#fffafa"


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
            color_discrete_sequence=[ACCENT_COLOR],
        )
        fig.update_traces(
            hovertemplate="%{x}<br>Average score: %{y:.1f}<extra></extra>"
        )

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
            color_discrete_sequence=[ACCENT_COLOR],
        )
        fig.update_traces(
            hovertemplate="%{x}<br>Average score: %{y:.1f}<extra></extra>"
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
            color_discrete_sequence=[ACCENT_COLOR],
        )

        fig.update_yaxes(
            tickmode="array",
            tickvals=[0, 1, 2, 3],
            range=[-0.5, 3.5],
        )
        fig.update_traces(hovertemplate=f"%{{x:.1f}} {labels[compare]}<extra></extra>")

    else:
        fig = px.scatter(
            title="Select a comparison",
        )

    fig.update_yaxes(
        range=[0, 3],
        dtick=1,
    )

    fig.update_layout(
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        margin=dict(l=60, r=40, t=100, b=50),
    )

    return fig


def country_map(df, on_country_click):
    exploded = df.explode(["origin_country_iso3", "origin_country_name"]).dropna(
        subset=["origin_country_iso3", "score"]
    )

    country_scores = exploded.groupby("origin_country_iso3", as_index=False).agg(
        average_score=("score", "mean"),
        movies=("title", "count"),
        country_name=("origin_country_name", "first"),
    )

    country_scores = country_scores[country_scores["movies"] >= 3]

    fig = px.choropleth(
        country_scores,
        locations="origin_country_iso3",
        color="average_score",
        locationmode="ISO-3",
        hover_name="origin_country_iso3",
        hover_data={
            "average_score": ":.1f",
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

    fig.update_geos(
        lataxis_range=[-60, 90],  # crop out Antarctica
        projection_type="natural earth",
    )

    fig.update_layout(
        height=900,
        margin=dict(t=100),
        paper_bgcolor=BACKGROUND_COLOR,
        geo=dict(bgcolor=BACKGROUND_COLOR),
    )

    # Convert to FigureWidget so we can capture clicks
    widget = go.FigureWidget(fig)

    # Listen for clicks on the map
    widget.data[0].on_click(on_country_click)

    return widget
