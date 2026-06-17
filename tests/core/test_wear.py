"""Tier 1 — indicadores de desgaste: slip y conteo de asistencias, con y sin canales."""
from fantasma.core.lap import Lap
from fantasma.core import wear

from conftest import make_lap


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
    idx = wear.slip_index(lap)
    assert idx is not None
    assert idx == 0.0  # sin deslizamiento real, por debajo de la banda muerta


def test_assist_count_counts_rising_edges():
    lap = Lap()
    n = 10
    lap.channels["dist"] = [i * 1.0 for i in range(n)]
    # dos activaciones de ABS (dos flancos de subida)
    lap.channels["abs"] = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
    assert wear.assist_count(lap, "abs") == 2


def test_assist_count_none_when_channel_absent():
    lap = make_lap()  # sin canal abs
    assert wear.assist_count(lap, "abs") is None


def test_wear_summary_empty_without_optional_channels():
    lap = make_lap()  # sin ruedas, abs, tcs, fuel
    assert wear.wear_summary(lap) == {}
