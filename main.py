from fantasma.ui.ng_app import main_page  # noqa: F401 — registers @ui.page("/")
from nicegui import ui

ui.run(storage_secret="sgi-v2-secret")
