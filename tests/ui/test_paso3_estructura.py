"""Capa A del gate de UX (ADR 0014): aserciones estructurales del Paso 3.

Verifica que los elementos clave del Paso 3 (Generar overlay HUD) existen:
guarda de acceso (sin ref_lap), y estructura del formulario con laps cargados.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"


def test_paso3_sin_laps_muestra_guarda():
    """Sin ref_lap el Paso 3 bloquea con warning y boton de vuelta al Paso 1."""
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 3
    at.run(timeout=30)

    assert not at.exception
    warnings = [w.value for w in at.warning]
    assert any("Paso 1" in w for w in warnings), (
        "Paso 3 sin ref_lap debe pedir ir al Paso 1. Warnings: %r" % warnings
    )
    labels = [b.label for b in at.button]
    assert any("Paso 1" in l for l in labels), (
        "Paso 3 sin ref_lap debe mostrar boton de vuelta al Paso 1. Botones: %r" % labels
    )


def test_paso3_con_laps_no_revienta(lap_factory):
    """Con ref_lap y drv_lap el Paso 3 renderiza sin excepcion."""
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 3
    at.session_state["ref_lap"] = lap_factory()
    at.session_state["drv_lap"] = lap_factory()
    at.run(timeout=30)

    assert not at.exception


def test_paso3_boton_generar_overlay_existe(lap_factory):
    """El boton 'Generar overlay' existe cuando hay laps cargados."""
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 3
    at.session_state["ref_lap"] = lap_factory()
    at.session_state["drv_lap"] = lap_factory()
    at.run(timeout=30)

    assert not at.exception
    labels = [b.label for b in at.button]
    assert any("overlay" in l.lower() for l in labels), (
        "Paso 3 debe tener boton 'Generar overlay'. Botones: %r" % labels
    )
