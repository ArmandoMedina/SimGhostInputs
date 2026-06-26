"""Tier 1 — comparación piloto vs referencia.

Aquí viven las afirmaciones que SON la promesa del producto:
- piloto más lento => delta_t POSITIVO (= "pierdes tiempo");
- ápex más rápido => d_vmin POSITIVO;
- faltar un canal opcional (gear/glat) NO rompe la comparación (degradación graceful).
"""

from conftest import make_lap

from fantasma.core.compare import compare, delta_trace


def test_identical_laps_have_zero_delta():
    ref = make_lap()
    drv = make_lap()
    trace = delta_trace(ref, drv, step=5.0)
    # vueltas idénticas -> delta nulo en todo punto
    assert max(abs(row["delta_t"]) for row in trace) < 1e-6


def test_slower_driver_loses_time_positive_delta():
    ref = make_lap(base_speed=200.0)
    drv = make_lap(base_speed=150.0)  # más lento en todas partes
    trace = delta_trace(ref, drv, step=5.0)
    # convención confirmada: piloto más lento => delta acumulado POSITIVO
    assert trace[-1]["delta_t"] > 0.0


def test_faster_apex_gives_positive_d_vmin():
    ref = make_lap(
        valleys=[{"center": 700.0, "vmin": 70.0, "half_width": 150.0, "direction": "right"}],
        length_m=1500.0,
    )
    drv = make_lap(
        valleys=[{"center": 700.0, "vmin": 90.0, "half_width": 150.0, "direction": "right"}],
        length_m=1500.0,
    )
    _, rows, _ = compare(ref, drv, step=5.0)
    assert rows  # se detectó la curva
    # piloto pasa más rápido por el ápex (90 vs 70) => d_vmin positivo
    assert rows[0]["d_vmin"] > 0


def test_summary_counts_corners_and_laptimes():
    ref = make_lap()  # dos valles por defecto
    drv = make_lap(base_speed=160.0)
    _, rows, summary = compare(ref, drv, step=5.0)
    assert summary["corners"] == len(rows) == 2
    assert summary["drv_laptime"] > summary["ref_laptime"]  # drv más lento
    assert summary["total_delta"] > 0


def test_compare_without_gear_channel_does_not_crash():
    # degradación graceful: sin canal de marcha la comparación sigue funcionando
    sin_gear = tuple(c for c in ("throttle", "brake", "steering", "glat", "glong") if c != "gear")
    ref = make_lap(channels=sin_gear)
    drv = make_lap(channels=sin_gear, base_speed=160.0)
    _, rows, _ = compare(ref, drv, step=5.0)
    assert rows
    # no debe haberse inventado una marcha
    assert "vmin_gear" not in rows[0]


def test_compare_without_glat_channel_does_not_crash():
    sin_glat = tuple(c for c in ("throttle", "brake", "steering", "gear", "glong") if c != "glat")
    ref = make_lap(channels=sin_glat)
    drv = make_lap(channels=sin_glat, base_speed=160.0)
    _, rows, summary = compare(ref, drv, step=5.0)
    assert rows
    assert summary["corners"] == 2
