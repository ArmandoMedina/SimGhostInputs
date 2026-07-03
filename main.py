from nicegui import ui

from fantasma.ui.ng_app import main_page  # noqa: F401 — registers @ui.page("/")

ui.run(storage_secret="sgi-v2-secret", host="127.0.0.1")
