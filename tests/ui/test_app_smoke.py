"""Tier 4 — smoke de la UI: que `app.py` arranque sin excepción.

Barato y de alto valor: este test habría atrapado en CI el ImportError del
refactor 0.6.3 (imports relativos en app.py ejecutado como script por Streamlit).
Si streamlit no está instalado, se omite.
"""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"


def test_app_starts_without_exception():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
