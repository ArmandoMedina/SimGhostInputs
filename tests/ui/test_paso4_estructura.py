"""Capa A del gate de UX (ADR 0014): aserciones estructurales del Paso 4.

Verifica el Paso 4 (Componer video final) con ffmpeg presente: estructura
del formulario y elementos clave. El caso sin ffmpeg ya esta cubierto en
test_step4_ffmpeg.py.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"


def test_paso4_con_ffmpeg_no_revienta(lap_factory):
    """Con ffmpeg disponible el Paso 4 renderiza sin excepcion."""
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        at = AppTest.from_file(str(APP))
        at.session_state["nav_step"] = 4
        at.session_state["drv_lap"] = lap_factory()
        at.run(timeout=30)

    assert not at.exception


def test_paso4_boton_componer_existe(lap_factory):
    """El boton 'Componer video' existe cuando ffmpeg esta disponible."""
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        at = AppTest.from_file(str(APP))
        at.session_state["nav_step"] = 4
        at.session_state["drv_lap"] = lap_factory()
        at.run(timeout=30)

    assert not at.exception
    labels = [b.label for b in at.button]
    assert any("Componer" in l for l in labels), (
        "Paso 4 debe tener boton 'Componer video' con ffmpeg disponible. Botones: %r" % labels
    )


def test_paso4_aviso_audio_visible(lap_factory):
    """El aviso de audio del motor es visible en el Paso 4 con ffmpeg."""
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        at = AppTest.from_file(str(APP))
        at.session_state["nav_step"] = 4
        at.run(timeout=30)

    assert not at.exception
    warnings = [w.value for w in at.warning]
    assert any("audio" in w.lower() for w in warnings), (
        "Paso 4 debe mostrar el aviso de audio del motor. Warnings: %r" % warnings
    )
