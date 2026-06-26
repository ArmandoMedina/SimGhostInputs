"""Tier 1 — normalización por distancia: rejilla, interpolación, separación de vueltas."""
from conftest import make_lap

from fantasma.core.lap import Lap
from fantasma.core.normalize import fastest_lap, resample, split_laps


def test_resample_grid_spacing():
    lap = make_lap(length_m=1000.0)
    r = resample(lap, step=5.0)
    grid = r.col("dist")
    assert grid[0] == 0.0
    # paso uniforme de 5 m
    assert all(round(grid[i + 1] - grid[i], 6) == 5.0 for i in range(len(grid) - 1))
    assert r.meta["resample_step_m"] == 5.0


def test_resample_linear_interpolation_in_range():
    # canal lineal: a mitad de camino entre dos muestras el valor debe ser el punto medio
    lap = Lap()
    lap.channels["dist"] = [0.0, 10.0]
    lap.channels["speed"] = [100.0, 200.0]
    r = resample(lap, step=5.0)
    # grid = [0, 5, 10]; en dist=5 -> 150
    assert r.col("speed")[1] == 150.0


def test_resample_keeps_gear_discrete():
    # gear es discreto: el remuestreo no debe producir valores fraccionarios
    lap = make_lap()
    original_gears = set(lap.col("gear"))
    r = resample(lap, step=5.0)
    for g in r.col("gear"):
        assert g in original_gears  # nunca interpola a 2.5


def test_split_laps_by_lap_number():
    # outing con 3 vueltas marcadas por el canal lap_number
    out = Lap()
    t, d, ln = [], [], []
    clock = 0.0
    for lapno in range(3):
        for k in range(20):
            t.append(clock)
            d.append(k * 10.0)
            ln.append(float(lapno))
            clock += 1.0
    out.channels = {"time": t, "dist": d, "lap_number": ln, "speed": [120.0] * 60}
    laps = split_laps(out)
    assert len(laps) == 3
    # cada vuelta re-referencia su tiempo a 0
    assert all(l.col("time")[0] == 0.0 for l in laps)


def test_fastest_lap_picks_lowest_time():
    rapida = make_lap(base_speed=200.0)
    lenta = make_lap(base_speed=120.0)
    assert fastest_lap([lenta, rapida]) is rapida
