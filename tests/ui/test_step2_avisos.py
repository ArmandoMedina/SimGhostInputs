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


_SUMMARY_BASE = {
    "ref_laptime": 60.0,
    "drv_laptime": 62.0,
    "total_delta": 2.0,
    "avisos": [],
}


def test_paso2_aviso_cuando_no_hay_curvas(lap_factory):
    # F-10: si rows=[], el Paso 2 debe mostrar un st.info con "curvas".
    ref = lap_factory()
    drv = lap_factory()
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 2
    at.session_state["ref_lap"] = ref
    at.session_state["drv_lap"] = drv
    at.session_state["summary"] = _SUMMARY_BASE
    at.session_state["rows"] = []
    at.session_state["trace"] = []
    at.session_state["charts_paths"] = []
    at.run(timeout=30)

    assert not at.exception
    infos = [i.value.lower() for i in at.info]
    assert any("curvas" in i for i in infos), (
        "Paso 2 debe mostrar aviso de 'no se detectaron curvas' cuando rows=[] (F-10). Infos: %r"
        % infos
    )


def test_paso2_no_revienta_cuando_hay_curvas(lap_factory):
    # F-09: con rows no vacío, el Paso 2 debe renderizar sin excepciones.
    # (st.download_button no es inspeccionable via AppTest en Streamlit 1.58;
    # la presencia del botón se verifica visualmente en el Tier 5.)
    ref = lap_factory()
    drv = lap_factory()
    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 2
    at.session_state["ref_lap"] = ref
    at.session_state["drv_lap"] = drv
    at.session_state["summary"] = _SUMMARY_BASE
    at.session_state["rows"] = [
        {
            "name": "C01",
            "apex_d": 400.0,
            "ref_vmin": 80.0,
            "drv_vmin": 70.0,
            "d_vmin": -10.0,
            "time_lost": 0.3,
            "flags": "",
        }
    ]
    at.session_state["trace"] = []
    at.session_state["charts_paths"] = []
    at.run(timeout=30)

    assert not at.exception, "Paso 2 no debe reventar cuando rows tiene curvas (F-09)"


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


def test_paso2_muestra_drilldown_de_mayor_perdida(lap_factory):
    ref = lap_factory()
    drv = lap_factory()
    trace = []
    for d in range(0, 121, 10):
        trace.append(
            {
                "dist": float(d),
                "delta_t": d / 120.0 * 0.7,
                "ref_speed": 180.0,
                "drv_speed": 170.0,
                "ref_throttle": 100.0 if d >= 80 else 0.0,
                "drv_throttle": 100.0 if d >= 100 else 0.0,
                "ref_brake": 80.0 if 20 <= d <= 50 else 0.0,
                "drv_brake": 60.0 if 0 <= d <= 50 else 0.0,
                "ref_gear": 4.0,
                "drv_gear": 3.0,
                "ref_rpm": 6800.0,
                "drv_rpm": 6400.0,
            }
        )
    rows = [
        {
            "id": "C01",
            "name": "Curva chica",
            "segment_start_m": 0,
            "segment_end_m": 120,
            "apex_d": 50,
            "ref_vmin": 120,
            "drv_vmin": 118,
            "drv_vmin_d": 50,
            "d_vmin": -2,
            "time_lost": 0.1,
            "flags": "",
        },
        {
            "id": "C02",
            "name": "Curva lenta",
            "segment_start_m": 0,
            "segment_end_m": 120,
            "apex_d": 50,
            "ref_vmin": 120,
            "drv_vmin": 110,
            "drv_vmin_d": 50,
            "d_vmin": -10,
            "time_lost": 0.7,
            "ref_brake_d": 20,
            "drv_brake_d": 0,
            "d_brake_m": -20,
            "ref_gas100_d": 80,
            "drv_gas100_d": 100,
            "d_gas100_m": 20,
            "flags": "vmin+frenada",
        },
    ]

    at = AppTest.from_file(str(APP))
    at.session_state["nav_step"] = 2
    at.session_state["ref_lap"] = ref
    at.session_state["drv_lap"] = drv
    at.session_state["summary"] = _SUMMARY_BASE
    at.session_state["rows"] = rows
    at.session_state["trace"] = trace
    at.session_state["charts_paths"] = []
    at.run(timeout=30)

    assert not at.exception
    warnings = [w.value for w in at.warning]
    assert any("Pierdes 0.700 s en Curva lenta" in w for w in warnings), warnings
