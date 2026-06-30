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
    # timeout generoso: el default de AppTest (3 s) es demasiado ajustado y da
    # falsos rojos (timeout) cuando la maquina de CI esta cargada — un gate flaky
    # pierde autoridad (ver ADR 0014). El arranque real tarda < 1 s holgado.
    at = AppTest.from_file(str(APP)).run(timeout=30)
    assert not at.exception


def test_paso0_no_marcado_en_sesion_nueva():
    # B-01: en sesion nueva, flow_chosen NO existe => _step_done(0) debe False.
    # El boton del Paso 0 en el sidebar debe mostrar ▶️ (activo), no ✅.
    at = AppTest.from_file(str(APP)).run(timeout=30)
    assert not at.exception
    labels = [b.label for b in at.sidebar.button]
    paso0 = next((l for l in labels if "0 ·" in l), None)
    assert paso0 is not None, "Debe existir boton de Paso 0 en el sidebar"
    assert "✅" not in paso0, (
        "Paso 0 NO debe marcarse completado en sesion nueva (B-01). Label: %r" % paso0
    )


def test_paso0_marcado_cuando_flow_chosen():
    # B-01: con flow_chosen en session_state y nav en Paso 1, el Paso 0 debe ✅.
    at = AppTest.from_file(str(APP))
    at.session_state["flow_chosen"] = True
    at.session_state["nav_step"] = 1
    at.run(timeout=30)
    assert not at.exception
    labels = [b.label for b in at.sidebar.button]
    paso0 = next((l for l in labels if "0 ·" in l), None)
    assert paso0 is not None
    assert "✅" in paso0, (
        "Paso 0 debe marcarse completado cuando flow_chosen=True (B-01). Label: %r" % paso0
    )


def test_paso4_marcado_cuando_video_compuesto():
    # B-02: con last_compose_video en session_state, el Paso 4 debe ✅.
    at = AppTest.from_file(str(APP))
    at.session_state["last_compose_video"] = "/tmp/out.mp4"
    at.session_state["nav_step"] = 0
    at.run(timeout=30)
    assert not at.exception
    labels = [b.label for b in at.sidebar.button]
    paso4 = next((l for l in labels if "4 ·" in l), None)
    assert paso4 is not None
    assert "✅" in paso4, (
        "Paso 4 debe marcarse completado cuando last_compose_video existe (B-02). Label: %r" % paso4
    )
