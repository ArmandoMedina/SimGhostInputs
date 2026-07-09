"""Tests para el helper `make_lap` (tests/conftest.py), no para fantasma/.

make_lap muestrea por distancia fija (`step_m`) por defecto, lo que produce
Hz variable (dt cambia con la velocidad local). El parámetro `dt_s` permite
fijar la tasa de muestreo real (Hz = 1/dt_s, como un data logger) para poder
probar código de `core/` calibrado por dt a tasas distintas de las que
produce el muestreo por distancia -- ver tests/core/test_corners.py.
"""

from conftest import make_lap


def test_make_lap_dt_s_samples_at_fixed_time_interval():
    lap = make_lap(dt_s=0.02, length_m=900.0)
    time = lap.channels["time"]
    deltas = {round(time[i + 1] - time[i], 9) for i in range(len(time) - 1)}
    assert deltas == {0.02}


def test_make_lap_dt_s_ignores_step_m():
    # con dt_s dado, step_m se ignora: el paso en distancia varia porque la
    # velocidad varia (muestreo por tiempo, no por distancia fija).
    lap = make_lap(dt_s=0.05, length_m=900.0, step_m=1.0)
    dist = lap.channels["dist"]
    deltas = {round(dist[i + 1] - dist[i], 3) for i in range(len(dist) - 1)}
    assert len(deltas) > 1


def test_make_lap_default_step_m_still_distance_based():
    # regresion: sin dt_s, el comportamiento historico (paso fijo en
    # distancia, dt variable) no cambia.
    lap = make_lap(length_m=900.0, step_m=1.0)
    dist = lap.channels["dist"]
    deltas = {round(dist[i + 1] - dist[i], 6) for i in range(len(dist) - 1)}
    assert deltas == {1.0}
