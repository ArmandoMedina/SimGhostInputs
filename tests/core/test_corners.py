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
