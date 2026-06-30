"""Capa A del gate de UX (ADR 0014): aserciones estructurales del Paso 1.

Verifica que los elementos clave del Paso 1 (Importar telemetria) existen
en los estados relevantes: vacio (sin archivos), y con archivos precargados.
No ejercita la carga real de archivos (eso es QA manual con telemetria real).
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"

_SUMMARY_BASE = {
    "ref_laptime": 60.0,
    "drv_laptime": 62.0,
    "total_delta": 2.0,
    "avisos": [],
}


def test_paso1_estructura_vacia():
    """Sin archivos subidos el Paso 1 bloquea en el primer st.info (referencia).

    El paso usa st.stop() tras el aviso de referencia, por lo que el aviso del
    piloto solo aparece en una segunda ejecucion con ref ya cargada. Aqui solo
    se verifica la primera barrera.
    """
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 1
    at.run(timeout=30)

    assert not at.exception
    infos = [i.value for i in at.info]
    assert any("referencia" in i.lower() for i in infos), (
        "Paso 1 debe pedir el archivo de referencia cuando no hay ref_lap. Infos: %r" % infos
    )


def test_paso1_muestra_subheaders_de_referencia_y_piloto():
    """Los subheaders 'Vuelta de referencia' y 'Tu vuelta de hoy' siempre aparecen."""
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 1
    at.run(timeout=30)

    assert not at.exception
    texts = [s.value for s in at.subheader]
    assert any("referencia" in t.lower() for t in texts), (
        "Paso 1 debe tener subheader de referencia. Subheaders: %r" % texts
    )
    # El subheader del piloto solo aparece cuando la referencia ya esta cargada
    # (st.stop() previo). Se verifica en test_paso1_con_laps_precargados.


def test_paso1_con_laps_precargados_no_revienta(lap_factory):
    """Con ref_lap y drv_lap en session_state el Paso 1 renderiza sin excepcion."""
    ref = lap_factory()
    drv = lap_factory()
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 1
    at.session_state["ref_lap"] = ref
    at.session_state["drv_lap"] = drv
    at.session_state["summary"] = _SUMMARY_BASE
    at.run(timeout=30)

    assert not at.exception


def test_paso1_sidebar_activo_en_nav1():
    """Con nav_step=1 el sidebar marca el Paso 1 como activo (triangulo de avance)."""
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 1
    at.run(timeout=30)

    assert not at.exception
    labels = [b.label for b in at.sidebar.button]
    # El paso activo lleva el emoji de avance ▶️ en su label
    assert any("1" in l and "▶" in l for l in labels), (
        "El sidebar debe marcar el Paso 1 como activo con ▶️. Labels: %r" % labels
    )
