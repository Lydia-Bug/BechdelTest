from shiny import ui
from shinywidgets import output_widget

from .data import (
    APP_DIR,
    MIN_YEAR,
    MAX_YEAR,
    ALL_GENRES,
    ALL_COUNTRIES,
    COMPARISON_CHOICES,
)

app_ui = ui.page_fluid(
    # Browser tab title
    ui.tags.head(
        ui.tags.title("Bechdel Test Dashboard"),
    ),
    # CSS
    ui.include_css(APP_DIR / "www/styles.css"),
    # ==================================================================
    # Dashboard
    # ==================================================================
    ui.div(
        # ==============================================================
        # Sidebar
        # ==============================================================
        ui.div(
            ui.input_select(
                "compare",
                "Compare",
                choices=COMPARISON_CHOICES,
                selected="genre",
            ),
            ui.hr(),
            # ----------------------------------------------------------
            # Release year
            # ----------------------------------------------------------
            ui.input_slider(
                "year_range",
                "Release year",
                min=MIN_YEAR,
                max=MAX_YEAR,
                value=(
                    MIN_YEAR,
                    MAX_YEAR,
                ),
                sep="",
            ),
            # ----------------------------------------------------------
            # Genre
            # ----------------------------------------------------------
            ui.input_selectize(
                "genre_filter",
                "Genre",
                choices=ALL_GENRES,
                multiple=True,
            ),
            # ----------------------------------------------------------
            # Country
            # ----------------------------------------------------------
            # ui.input_selectize(
            #     "country_filter",
            #     "Origin country",
            #     choices=ALL_COUNTRIES,
            #     multiple=True,
            # ),
            class_="sidebar",
        ),
        # ==============================================================
        # Main content
        # ==============================================================
        ui.div(
            # ----------------------------------------------------------
            # Tabs
            # ----------------------------------------------------------
            ui.div(
                ui.navset_card_tab(
                    ui.nav_panel(
                        "Compare",
                        output_widget("comparison_plot"),
                        ui.output_ui("country_movies"),
                    ),
                    ui.nav_panel(
                        "Table",
                        ui.output_data_frame("movie_table"),
                    ),
                ),
                class_="tabs",
            ),
            class_="main",
        ),
        class_="dashboard",
    ),
)
