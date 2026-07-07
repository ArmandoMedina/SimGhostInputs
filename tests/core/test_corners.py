"""Tier 1 — detección de curvas e hitos sobre trazados sintéticos de valles conocidos."""

import pytest

from conftest import make_lap
from fantasma.core.corners import detect_corners, extract_milestones
from fantasma.core.lap import Lap


def test_detects_one_event_per_valley():
    valleys = [
        {"center": 300.0, "vmin": 80.0, "half_width": 120.0, "direction": "right"},
        {"center": 800.0, "vmin": 60.0, "half_width": 120.0, "direction": "left"},
        {"center": 1300.0, "vmin": 70.0, "half_width": 120.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1700.0, valleys=valleys)
    events, _ = detect_corners(lap)
    assert len(events) == 3
    assert all(kind == "vmin" for kind, _ in events)


def test_detect_requires_speed_channel():
    lap = Lap()
    lap.channels = {"time": [0.0, 1.0], "dist": [0.0, 10.0]}  # sin 'speed'
    with pytest.raises(ValueError):
        detect_corners(lap)


def test_detect_requires_dist_channel():
    # Export real sin canal de distancia (ej. ORECA 07 vía sim-to-motec): debe
    # degradar con un ValueError claro, no propagar un KeyError('dist') desnudo.
    lap = Lap()
    lap.channels = {"time": [0.0, 1.0], "speed": [100.0, 90.0]}  # sin 'dist'
    with pytest.raises(ValueError):
        detect_corners(lap)


def test_milestones_have_apex_and_brake_start():
    lap = make_lap()
    corners = extract_milestones(lap)
    assert len(corners) == 2
    for c in corners:
        assert "apex" in c["milestones"]
        assert "brake_start" in c["milestones"]
        # el ápex es el punto más lento (V-Min)
        assert c["milestones"]["apex"]["v"] in (60, 80)


def test_corner_direction_matches_valley():
    valleys = [
        {"center": 400.0, "vmin": 80.0, "half_width": 120.0, "direction": "left"},
        {"center": 1000.0, "vmin": 70.0, "half_width": 120.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1500.0, valleys=valleys)
    corners = extract_milestones(lap)
    assert corners[0]["direction"] == "left"
    assert corners[1]["direction"] == "right"


def test_detection_without_glat_still_finds_vmin_corners():
    # degradación graceful: sin glat no hay kinks ni g_lat_max, pero las curvas V-Min siguen
    sin_glat = ("throttle", "brake", "steering", "gear")
    lap = make_lap(channels=sin_glat)
    corners = extract_milestones(lap)
    assert len(corners) == 2
    assert all("g_lat_max" not in c["milestones"] for c in corners)


def _lap_with_custom_pedals(brake_range, onset_d, blip_range=None):
    """Vuelta sintética de una curva con freno/gas artesanales (no derivados
    de la forma del valle de make_lap), para controlar con precisión el hueco
    entre frenada y gas: roces fugaces, coast y overlap.
    """
    lap = make_lap(
        length_m=900.0,
        valleys=[{"center": 310.0, "vmin": 80.0, "half_width": 250.0, "direction": "right"}],
        channels=("throttle", "brake"),
    )
    dist = lap.channels["dist"]
    throttle, brake = [], []
    for d in dist:
        b = 90.0 if brake_range[0] <= d <= brake_range[1] else 0.0
        t = 40.0 if d >= onset_d else 0.0
        if blip_range and blip_range[0] <= d <= blip_range[1]:
            t = 20.0
        throttle.append(t)
        brake.append(b)
    lap.channels["throttle"] = throttle
    lap.channels["brake"] = brake
    return lap


def test_throttle_on_ignores_fleeting_blip_and_anchors_on_sustained_gas():
    # roce fugaz de pedal en ~316-318 (freno-motor / ruido) durante el coast;
    # el gas real, sostenido, entra en 393 — el hito debe anclar ahí, no en el roce.
    lap = _lap_with_custom_pedals(
        brake_range=(150.0, 270.0), onset_d=393.0, blip_range=(316.0, 318.0)
    )
    corners = extract_milestones(lap)
    assert len(corners) == 1
    ms = corners[0]["milestones"]
    assert "throttle_on" in ms
    assert ms["throttle_on"]["d"] >= 390


def test_coast_detected_between_brake_release_and_sustained_throttle():
    lap = _lap_with_custom_pedals(brake_range=(150.0, 270.0), onset_d=393.0)
    corners = extract_milestones(lap)
    ms = corners[0]["milestones"]
    assert "coast_start" in ms
    assert "coast_end" in ms
    assert (
        ms["brake_release"]["d"]
        < ms["coast_start"]["d"]
        <= ms["coast_end"]["d"]
        < ms["throttle_on"]["d"]
    )


def test_throttle_on_ignores_blip_at_tail_of_segment():
    # blip corto (3 muestras >umbral) pegado al final del segmento (limite
    # `hi`): sin la guarda de longitud, seg[j:j+throttle_on_window] devuelve
    # menos de throttle_on_window muestras ahi y all() pasa trivialmente,
    # anclando throttle_on en un roce que nunca se sostuvo 15 muestras.
    lap = _lap_with_custom_pedals(brake_range=(150.0, 270.0), onset_d=10_000.0)
    dist = lap.channels["dist"]
    throttle = lap.channels["throttle"]
    for i, d in enumerate(dist):
        if 658.0 <= d <= 660.0:
            throttle[i] = 20.0
    corners = extract_milestones(lap)
    ms = corners[0]["milestones"]
    assert "throttle_on" not in ms


def test_no_coast_when_gas_overlaps_brake():
    # gas pegado al freno (overlap, dentro de la ventana de busqueda de 0.6s
    # antes del apex): no hay hueco, no hay coast.
    lap = _lap_with_custom_pedals(brake_range=(150.0, 306.0), onset_d=300.0)
    corners = extract_milestones(lap)
    c = corners[0]
    assert c.get("overlap_m", 0) > 0
    assert "coast_start" not in c["milestones"]
    assert "coast_end" not in c["milestones"]
