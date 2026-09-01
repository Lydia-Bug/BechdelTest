from shiny import App

from modules.ui import app_ui
from modules.server import server

app = App(app_ui, server)
