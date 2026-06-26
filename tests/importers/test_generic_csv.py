"""Tier 2 — importador de CSV genérico: auto-detección de columnas y mapeo manual."""

import pytest

from fantasma.importers import generic_csv


def _write(tmp_path, text, name="generic.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_guesses_common_column_names(tmp_path):
    # encabezados típicos de SimHub/loggers genéricos -> canónicos sin --map
    path = _write(
        tmp_path,
        "SessionTime,LapDist,Speed_kmh,Throttle_pct,Brake_pct\n0.0,0,100,80,0\n0.1,5,98,0,50\n",
    )
    lap = generic_csv.load(path)
    assert lap.has("time") and lap.has("dist")
    assert lap.has("speed") and lap.has("throttle") and lap.has("brake")
    assert lap.col("speed")[0] == 100.0


def test_column_map_overrides_guess(tmp_path):
    path = _write(tmp_path, "t,d,v\n0.0,0,100\n0.1,5,99\n")
    lap = generic_csv.load(path, column_map={"v": "speed", "t": "time", "d": "dist"})
    assert lap.col("speed")[0] == 100.0


def test_missing_time_or_dist_raises(tmp_path):
    # sin distancia: el importador no puede normalizar por distancia
    path = _write(tmp_path, "SessionTime,Speed_kmh\n0.0,100\n0.1,99\n")
    with pytest.raises(ValueError):
        generic_csv.load(path)


def test_bad_values_default_to_zero(tmp_path):
    path = _write(
        tmp_path, "time,dist,speed\n0.0,0,100\n0.1,,abc\n"
    )  # dist vacío y speed no numérico
    lap = generic_csv.load(path)
    assert lap.col("dist")[1] == 0.0
    assert lap.col("speed")[1] == 0.0
