"""Tier 2 — importador MoTeC i2 CSV con un fixture diminuto sintético.

El fixture `motec_mini.csv` es el ÚNICO dato versionado: 24 filas sintéticas
con el layout real de i2 (metadatos + fila 'Time' + unidades), sin datos personales.
"""

import os

import pytest

from fantasma.importers import load_laps, motec_csv

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
MINI = os.path.join(FIXTURES, "motec_mini.csv")


def test_maps_motec_columns_to_canonical_channels():
    lap = motec_csv.load(MINI)
    # nombres MoTeC traducidos a canónicos
    for ch in ("time", "dist", "speed", "throttle", "brake", "gear", "glat", "abs"):
        assert lap.has(ch), "falta el canal %s" % ch
    # primer valor de velocidad parseado correctamente
    assert lap.col("speed")[0] == 120.0
    assert len(lap) == 24


def test_unknown_column_is_ignored_not_crashes():
    # "Custom Unknown" no está en MOTEC_MAP -> se ignora, no aparece como canal
    lap = motec_csv.load(MINI)
    assert "Custom Unknown" not in lap.channels
    assert not lap.has("custom")


def test_metadata_is_parsed():
    lap = motec_csv.load(MINI)
    assert lap.meta.get("Venue") == "TestTrack"
    assert lap.meta.get("Vehicle") == "Test GT3"
    assert lap.meta.get("source_file") == "motec_mini.csv"


def test_non_motec_file_raises(tmp_path):
    bad = tmp_path / "no_motec.csv"
    bad.write_text("foo,bar\n1,2\n3,4\n", encoding="utf-8")
    with pytest.raises(motec_csv.NotMotecFormat):
        motec_csv.load(str(bad))


def test_beacon_markers_parsed_as_floats(tmp_path):
    csv_text = (
        '"Venue","X"\n'
        '"Beacon Markers","399.220 777.622 "\n'
        "\n"
        '"Time","Distance","Ground Speed"\n'
        '"s","m","km/h"\n'
        "\n"
        '"0.000","0","100"\n'
        '"0.020","2","101"\n'
    )
    p = tmp_path / "beacons.csv"
    p.write_text(csv_text, encoding="utf-8")
    lap = motec_csv.load(str(p))
    assert lap.meta["beacons"] == [399.220, 777.622]


def test_load_laps_splits_by_lap_number():
    laps = load_laps(MINI)
    # dos números de vuelta (3 y 4) -> dos vueltas
    assert len(laps) == 2


def test_semicolon_separator_supported(tmp_path):
    # export europeo con separador ';' (decimales con punto)
    csv_text = (
        '"Venue";"X"\n'
        '"Time";"Distance";"Ground Speed"\n'
        '"s";"m";"km/h"\n'
        "\n"
        '"0.000";"0";"100"\n'
        '"0.020";"2";"101"\n'
    )
    p = tmp_path / "euro.csv"
    p.write_text(csv_text, encoding="utf-8")
    lap = motec_csv.load(str(p))
    assert lap.col("speed")[0] == 100.0
    assert len(lap) == 2


def test_semicolon_with_decimal_comma(tmp_path):
    # export europeo: separador ';' Y coma decimal ('100,5')
    csv_text = (
        '"Venue";"X"\n'
        '"Time";"Distance";"Ground Speed"\n'
        '"s";"m";"km/h"\n'
        "\n"
        '"0,000";"0";"100,5"\n'
        '"0,020";"2,5";"101,250"\n'
    )
    p = tmp_path / "euro_comma.csv"
    p.write_text(csv_text, encoding="utf-8")
    lap = motec_csv.load(str(p))
    assert lap.col("speed")[0] == 100.5
    assert lap.col("dist")[1] == 2.5
    assert lap.col("time")[1] == 0.02


def test_duplicate_columns_to_same_canonical_no_double_append(tmp_path):
    """'Ground Speed' y 'Speed' ambas mapean a 'speed': primera gana, sin double-append (H-01)."""
    csv_text = (
        '"Venue","X"\n'
        '"Time","Distance","Ground Speed","Speed"\n'
        '"s","m","km/h","km/h"\n'
        "\n"
        '"0.000","0","120","99"\n'
        '"0.020","2","121","100"\n'
    )
    p = tmp_path / "dup_speed.csv"
    p.write_text(csv_text, encoding="utf-8")
    lap = motec_csv.load(str(p))
    # serie alineada: len(speed) == len(time)
    assert len(lap.col("speed")) == len(lap.col("time")) == 2
    # gana la primera columna mapeada ("Ground Speed" = 120, no "Speed" = 99)
    assert lap.col("speed")[0] == 120.0


def test_truncated_row_skipped_no_indexerror(tmp_path):
    """Fila mas corta que el header se descarta sin IndexError (H-02)."""
    csv_text = (
        '"Venue","X"\n'
        '"Time","Distance","Ground Speed"\n'
        '"s","m","km/h"\n'
        "\n"
        '"0.000","0","100"\n'
        '"0.020"\n'
        '"0.040","4","102"\n'
    )
    p = tmp_path / "truncated.csv"
    p.write_text(csv_text, encoding="utf-8")
    # no debe lanzar IndexError
    lap = motec_csv.load(str(p))
    # la fila truncada se descarta; quedan las dos filas completas
    assert len(lap.col("time")) == 2
    assert lap.col("speed")[1] == pytest.approx(102.0)
