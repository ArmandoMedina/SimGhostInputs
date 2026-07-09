"""Smoke tests de fantasma/viz/charts.py — generación de gráficas con matplotlib.

Deterministas y sin ffmpeg. Se alimenta el pipeline real (detect_corners →
extract_milestones → compare) y se verifica que `render_charts` produce PNGs
sin reventar, más el camino de degradación cuando matplotlib no está.
"""

import pytest

from fantasma.viz import charts


def _pipeline(lap_factory):
    from fantasma.core.compare import compare
    from fantasma.core.corners import detect_corners, extract_milestones

    ref = lap_factory(base_speed=200)
    drv = lap_factory(base_speed=188)
    ev, _ = detect_corners(ref)
    corners = extract_milestones(ref, ev)
    trace, rows, summary = compare(ref, drv, corners=corners)
    return trace, rows, corners


def test_render_charts_genera_pngs(tmp_path, lap_factory):
    pytest.importorskip("matplotlib", reason="matplotlib no instalado")
    trace, rows, corners = _pipeline(lap_factory)

    out = charts.render_charts(trace, rows, corners, str(tmp_path))

    assert out, "render_charts debe devolver al menos una gráfica"
    for path in out:
        p = tmp_path / path.split("\\")[-1].split("/")[-1]
        assert p.exists() and p.stat().st_size > 0
    # las gráficas globales siempre deberían salir
    nombres = " ".join(out)
    assert "delta" in nombres or "full_lap" in nombres


def test_render_charts_sin_matplotlib_devuelve_vacio(tmp_path, lap_factory, monkeypatch):
    trace, rows, corners = _pipeline(lap_factory)
    # simula matplotlib ausente: render_charts debe degradar a [] sin crash
    monkeypatch.setattr(charts, "_mpl", lambda: None)

    assert charts.render_charts(trace, rows, corners, str(tmp_path)) == []
