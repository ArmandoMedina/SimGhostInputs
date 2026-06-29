"""Gate de UX (ADR 0014) capa A: asercion estructural.

El Paso 4 (compose) NECESITA ffmpeg. Debe avisar temprano si falta (caso C19),
en vez de dejar fallar al apretar "Componer". Este test fuerza la ausencia de
ffmpeg y verifica que aparece el aviso.
"""

import shutil
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"


def test_paso4_avisa_si_falta_ffmpeg(monkeypatch):
    # which("ffmpeg") -> None (no instalado); el resto de lookups intactos.
    _real_which = shutil.which
    monkeypatch.setattr(
        shutil,
        "which",
        lambda n, *a, **k: None if n == "ffmpeg" else _real_which(n, *a, **k),
    )

    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 4
    at.run(timeout=30)

    assert not at.exception
    errores = [e.value.lower() for e in at.error]
    assert any("ffmpeg" in e for e in errores), (
        "El Paso 4 deberia avisar que falta ffmpeg. Errores vistos: %r" % errores
    )
