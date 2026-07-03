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


# ---------------------------------------------------------------------------
# FIX 2 — aviso de delta sospechosamente grande (posible circuito distinto)
# ---------------------------------------------------------------------------


def test_compare_avisa_delta_sospechoso():
    """Delta > 50 % del tiempo de vuelta de referencia dispara el aviso.

    Caso tipico de bug silencioso: ref de un circuito, piloto de otro.
    La comparacion produce un numero pero el aviso lo delata.
    """
    ref = make_lap(base_speed=180.0)
    # piloto tan lento que el delta supera con creces el 50 % del laptime de ref
    drv = make_lap(base_speed=20.0)
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("sospechosamente grande" in a for a in avisos), (
        "Se esperaba aviso de delta grande; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_delta_normal():
    """Delta normal (diferencia de segundos) NO dispara el aviso."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=175.0)  # ligeramente mas lento
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("sospechosamente grande" in a for a in avisos), (
        "Aviso inesperado de delta grande: %r" % avisos
    )


# ---------------------------------------------------------------------------
# FIX 3 — aviso informativo de autos distintos
# ---------------------------------------------------------------------------


def test_compare_avisa_autos_distintos():
    """Metadata de Vehicle distinta en ref y piloto genera aviso informativo."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap(meta={"Vehicle": "Ferrari 296 GT3"})
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("autos distintos" in a for a in avisos), (
        "Se esperaba aviso de autos distintos; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_autos_iguales():
    """Mismo auto en ref y piloto -> sin aviso de autos."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


def test_compare_sin_aviso_vehicle_ausente():
    """Si la metadata de Vehicle no esta disponible, NO avisa ni crashea."""
    ref = make_lap()  # sin meta -> meta={}
    drv = make_lap()
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


def test_compare_sin_aviso_vehicle_solo_en_ref():
    """Vehicle solo en ref (no en piloto) -> degradacion graciosa, sin aviso."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap()
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


# ---------------------------------------------------------------------------
# FIX 4 — aviso cuando piloto es más rápido que referencia (posible inversión)
# ---------------------------------------------------------------------------


def test_compare_avisa_piloto_mas_rapido():
    """Delta muy negativo (piloto mucho más rápido) dispara aviso de inversión.

    Caso típico: usuario subió los archivos al revés — referencia lenta, piloto rápido.
    """
    ref = make_lap(base_speed=100.0)  # vuelta lenta como "referencia"
    drv = make_lap(base_speed=200.0)  # piloto claramente más rápido
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("piloto más rápido" in a for a in avisos), (
        "Se esperaba aviso de piloto invertido; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_piloto_ligeramente_mas_rapido():
    """Un piloto ligeramente más rápido (delta < -1 s) NO dispara el aviso."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=182.0)  # mínimamente más rápido
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("piloto más rápido" in a for a in avisos), (
        "Aviso inesperado de inversión: %r" % avisos
    )


def test_compare_sin_aviso_piloto_mas_lento():
    """Piloto más lento (delta positivo) -> no hay aviso de inversión."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=150.0)
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("piloto más rápido" in a for a in avisos)
