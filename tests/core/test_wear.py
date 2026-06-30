"""Tier 1 — indicadores de desgaste: slip y conteo de asistencias, con y sin canales."""

from conftest import make_lap

from fantasma.core import wear
from fantasma.core.lap import Lap


def _rolling_lap(ratio=1.0, n=200, speed=120.0):
    """Vuelta de rodadura libre limpia: velocidad de rueda = speed * ratio,
    sin freno ni G longitudinal (cumple las condiciones de calibración)."""
    lap = Lap()
    lap.channels["time"] = [i * 0.1 for i in range(n)]
    lap.channels["dist"] = [i * 5.0 for i in range(n)]
    lap.channels["speed"] = [speed] * n
    lap.channels["brake"] = [0.0] * n
    lap.channels["glong"] = [0.0] * n
    for w in wear.WHEELS:
        lap.channels["ts_" + w] = [speed * ratio] * n
    return lap


def _slip_lap(speed=120.0):
    """Vuelta con 3 tramos: rodadura libre (calibra ratio=1.0), bloqueo en frenada
    (rueda 20% más lenta = slip negativo) y patinaje en tracción (rueda 20% más
    rápida = slip positivo). Sirve para verificar el signo y que el índice da > 0."""
    lap = Lap()
    n_free, n_lock, n_spin = 120, 40, 40
    n = n_free + n_lock + n_spin
    lap.channels["time"] = [i * 0.1 for i in range(n)]
    lap.channels["dist"] = [i * 5.0 for i in range(n)]
    lap.channels["speed"] = [speed] * n
    lap.channels["brake"] = [0.0] * n_free + [50.0] * n_lock + [0.0] * n_spin
    lap.channels["glong"] = [0.0] * n_free + [-1.0] * n_lock + [1.0] * n_spin
    ts = [speed] * n_free + [speed * 0.8] * n_lock + [speed * 1.2] * n_spin
    for w in wear.WHEELS:
        lap.channels["ts_" + w] = list(ts)
    return lap


def test_calibrate_returns_none_without_wheel_channels():
    lap = make_lap()  # no tiene ts_fl..rr
    assert wear.calibrate(lap) is None
    assert wear.slip_series(lap) is None


def test_calibrate_finds_ratio_with_wheel_channels():
    lap = _rolling_lap(ratio=1.0)
    ratios = wear.calibrate(lap)
    assert ratios is not None
    for w in wear.WHEELS:
        assert abs(ratios[w] - 1.0) < 1e-6


def test_clean_rolling_has_low_slip_index():
    lap = _rolling_lap(ratio=1.0)
    idx = wear._slip_index(lap)
    assert idx is not None
    assert idx == 0.0  # sin deslizamiento real, por debajo de la banda muerta


def test_slip_series_signs_locking_and_spinning():
    s = wear.slip_series(_slip_lap())
    assert s is not None
    assert min(s) < -10  # bloqueo en frenada: rueda más lenta -> slip negativo
    assert max(s) > 10  # patinaje en tracción: rueda más rápida -> slip positivo


def test_slip_index_positive_with_real_slip():
    idx = wear._slip_index(_slip_lap())
    assert idx is not None
    assert idx > 0  # con deslizamiento real por encima de la banda muerta


# --- slip_load: carga de deslizamiento extensiva (ADR 0009) --------------------


def test_slip_load_none_without_wheels():
    assert wear.slip_load(make_lap()) is None


def test_slip_load_zero_clean_rolling():
    assert wear.slip_load(_rolling_lap(ratio=1.0)) == 0.0


def test_slip_load_positive_with_real_slip():
    assert wear.slip_load(_slip_lap()) > 0


def test_slip_load_is_additive_over_distance():
    """La carga es EXTENSIVA: la de dos tramos contiguos suma la del total
    (a diferencia de slip_index, que es un promedio y no se puede sumar)."""
    lap = _slip_lap()
    d = lap.col("dist")
    mid = (d[len(d) // 2] + d[len(d) // 2 + 1]) / 2.0  # punto entre dos muestras
    whole = wear.slip_load(lap)
    part1 = wear.slip_load(lap, 0, mid)
    part2 = wear.slip_load(lap, mid, d[-1])
    assert abs((part1 + part2) - whole) < 0.05


def test_assist_count_counts_rising_edges():
    lap = Lap()
    n = 10
    lap.channels["dist"] = [i * 1.0 for i in range(n)]
    # dos activaciones de ABS (dos flancos de subida)
    lap.channels["abs"] = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
    assert wear._assist_count(lap, "abs") == 2


def test_assist_count_none_when_channel_absent():
    lap = make_lap()  # sin canal abs
    assert wear._assist_count(lap, "abs") is None


def test_wear_summary_empty_without_optional_channels():
    lap = make_lap()  # sin ruedas, abs, tcs, fuel
    assert wear.wear_summary(lap) == {}


# --- wear_budget: desgaste acumulable tipo gasolina (ADR 0004) -----------------

_TH = {"yellow": 30, "red": 40, "burst": 50}


def test_wear_budget_none_without_rates():
    assert wear.wear_budget([], _TH) is None
    assert wear.wear_budget(None, _TH) is None


def test_wear_budget_accumulates_and_projects():
    b = wear.wear_budget([7.3, 7.3, 7.3], _TH)
    assert b["cumulative"] == 21.9
    assert b["rate_recent"] == 7.3
    assert b["laps_done"] == 3
    assert b["status"] == "ok"  # 21.9 < 30
    assert b["laps_to_burst"] == 3.8  # (50 - 21.9) / 7.3
    assert b["est_total_laps"] == 6.8  # 3 vueltas hechas + 3.8 estimadas


def test_wear_budget_status_thresholds():
    assert wear.wear_budget([10, 10, 15], _TH)["status"] == "yellow"  # 35
    assert wear.wear_budget([15, 15, 15], _TH)["status"] == "red"  # 45
    burst = wear.wear_budget([20, 20, 20], _TH)  # 60 >= 50
    assert burst["status"] == "burst"
    assert burst["laps_to_burst"] == 0.0  # ya pasado el reventón, no negativo


def test_wear_budget_recent_n_averages_last_laps():
    b = wear.wear_budget([10, 5, 7], _TH, recent_n=2)
    assert b["rate_recent"] == 6.0  # media de [5, 7]


def test_wear_budget_ignores_none_rates():
    b = wear.wear_budget([7.0, None, 7.0], _TH)
    assert b["cumulative"] == 14.0
    assert b["laps_done"] == 2


def test_wear_budget_recent_n_beyond_length_uses_all():
    b = wear.wear_budget([4.0, 6.0], _TH, recent_n=5)
    assert b["rate_recent"] == 5.0  # media de todas las vueltas disponibles


def test_wear_budget_partial_thresholds():
    # solo umbral de reventón: estado ok hasta cruzarlo, y aun así proyecta
    b = wear.wear_budget([10, 10], {"burst": 50})
    assert b["status"] == "ok"
    assert b["laps_to_burst"] == 3.0  # (50 - 20) / 10


def test_wear_budget_no_projection_without_burst_or_rate():
    # sin umbral de reventón: no se proyecta
    assert "laps_to_burst" not in wear.wear_budget([10, 10], {"yellow": 30})
    # sin desgaste medible (rate 0): no se proyecta, no divide por cero
    zero = wear.wear_budget([0.0, 0.0], _TH)
    assert zero["status"] == "ok"
    assert "laps_to_burst" not in zero
