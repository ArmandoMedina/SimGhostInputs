"""Capa A del gate de UX (ADR 0014): asercion estructural.

Los avisos globales de compare (autos/circuitos distintos, delta sospechoso)
viven en summary["avisos"]. Antes solo se veian en el CLI/report.md; el Paso 2
de la UI ahora los MUESTRA (caso C12) para que un usuario de la UI no interprete
un reporte invalido como valido. Este test lo blinda.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[2] / "fantasma" / "ui" / "app.py"


def test_paso2_muestra_aviso_autos_distintos(lap_factory):
    # Mismas vueltas salvo el metadato Vehicle -> compare emite "autos distintos".
    ref = lap_factory(meta={"Vehicle": "BMW M4 GT3"})
    drv = lap_factory(meta={"Vehicle": "Audi R8 LMS"})

    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 2
    at.session_state["ref_lap"] = ref
    at.session_state["drv_lap"] = drv
    at.run(timeout=30)

    assert not at.exception
    avisos = [w.value.lower() for w in at.warning]
    assert any("autos distintos" in a for a in avisos), (
        "El Paso 2 deberia mostrar el aviso global de autos distintos. Avisos vistos: %r" % avisos
    )
