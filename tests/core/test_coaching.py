"""Drill-down por curva: coaching determinista sobre row + trace."""

from fantasma.core.compare import corner_coaching


def _trace(include_gear=True, include_glat=True):
    rows = []
    for d in range(0, 121, 10):
        row = {
            "dist": float(d),
            "delta_t": d / 120.0 * 0.6,
            "ref_speed": 180.0 - max(0, 60 - abs(d - 50)),
            "drv_speed": 180.0 - max(0, 70 - abs(d - 50)),
            "ref_throttle": 100.0 if d >= 80 else 0.0,
            "drv_throttle": 100.0 if d >= 100 else 0.0,
            "ref_brake": 80.0 if 20 <= d <= 50 else 0.0,
            "drv_brake": 60.0 if 0 <= d <= 50 else 0.0,
            "ref_steering": 15.0,
            "drv_steering": 15.0,
            "ref_glong": -1.1 if d <= 50 else 0.4,
            "drv_glong": -0.8 if d <= 50 else 0.4,
            "ref_rpm": 6800.0,
            "drv_rpm": 6400.0,
        }
        if include_gear:
            row["ref_gear"] = 4.0
            row["drv_gear"] = 3.0
        if include_glat:
            row["ref_glat"] = -2.2
            row["drv_glat"] = -1.8
        rows.append(row)
    return rows


def _row(**extra):
    base = {
        "id": "C01",
        "name": "Curva 1",
        "segment_start_m": 0,
        "segment_end_m": 120,
        "apex_d": 50,
        "ref_vmin": 120,
        "drv_vmin": 110,
        "drv_vmin_d": 50,
        "d_vmin": -10,
        "time_lost": 0.6,
        "ref_brake_d": 20,
        "drv_brake_d": 0,
        "d_brake_m": -20,
        "ref_gas100_d": 80,
        "drv_gas100_d": 100,
        "d_gas100_m": 20,
        "flags": "vmin+frenada",
    }
    base.update(extra)
    return base


def test_corner_coaching_prioriza_palancas_de_mayor_perdida():
    coaching = corner_coaching(_row(), _trace())

    assert coaching["status"] == "loss"
    assert coaching["time_lost"] == 0.6
    assert "Pierdes 0.600 s" in coaching["summary"]
    assert coaching["braking"]["delta_start_m"] == -20
    assert coaching["braking"]["delta_peak_pct"] == -20
    assert coaching["apex"]["delta_vmin_kmh"] == -10
    assert coaching["throttle"]["delta_gas100_m"] == 20
    assert coaching["lateral"]["delta_peak_g"] == -0.4
    assert coaching["gear"]["same_gear"] is False
    assert any("Acelera antes" in action for action in coaching["actions"])
    assert any("velocidad minima" in action for action in coaching["actions"])


def test_corner_coaching_omite_canales_ausentes_sin_crashear():
    coaching = corner_coaching(_row(), _trace(include_gear=False, include_glat=False))

    assert coaching["status"] == "loss"
    assert "gear" not in coaching["gear"]["ref"]
    assert "gear" not in coaching["gear"]["drv"]
    assert coaching["gear"]["delta_rpm"] == -400
    assert coaching["lateral"] == {}
    assert coaching["summary"]
    assert coaching["actions"]


def test_corner_coaching_reconoce_curva_donde_el_piloto_gana():
    coaching = corner_coaching(
        _row(time_lost=-0.25, drv_vmin=125, d_vmin=5, d_brake_m=0, d_gas100_m=-10),
        _trace(),
    )

    assert coaching["status"] == "gain"
    assert "Ganas 0.250 s" in coaching["summary"]
    assert any("usa esta curva como referencia" in action for action in coaching["actions"])
