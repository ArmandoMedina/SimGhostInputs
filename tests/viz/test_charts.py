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


# ── _corner_lo / plot_corner: propiedad de la frenada (ADR 0031) ─────────────


def test_corner_lo_extiende_hasta_brake_start_previo_al_segmento():
    """Frenada que empieza (850) antes de segment_m[0] (1000) con hueco de 150 m > pad_m.

    Con el pad fijo de 120 m la ventana bajaba solo a 880 y TRUNCABA el inicio de
    la frenada (850) en silencio. Derivada del hito, la ventana baja hasta 850.
    """
    c = {"segment_m": [1000, 1300], "milestones": {"brake_start": {"d": 850}}}
    assert charts._corner_lo(c, 1000) == 850


def test_corner_lo_no_recorta_curva_normal():
    # brake_start (1050) dentro del segmento: la ventana no se mueve del segment_m[0]
    c = {"segment_m": [1000, 1300], "milestones": {"brake_start": {"d": 1050}}}
    assert charts._corner_lo(c, 1000) == 1000


def test_corner_lo_sin_brake_start_cae_al_segmento():
    c = {"segment_m": [1000, 1300], "milestones": {}}
    assert charts._corner_lo(c, 1000) == 1000


def test_plot_corner_incluye_frenada_extendida(tmp_path):
    """plot_corner con una frenada que precede al segmento por mas que el pad fijo:
    la traza recortada llega hasta el inicio real de la frenada, no la trunca."""
    pytest.importorskip("matplotlib", reason="matplotlib no instalado")
    corner = {
        "id": "T7",
        "name": "T7",
        "segment_m": [1000, 1300],
        "milestones": {"apex": {"d": 1150, "v": 90}, "brake_start": {"d": 850}},
    }
    # traza densa que cubre desde antes de la frenada hasta pasado el apex
    trace = [
        {"dist": float(x), "ref_speed": 200.0, "drv_speed": 190.0, "ref_brake": 0, "drv_brake": 0}
        for x in range(700, 1400, 5)
    ]
    path = charts.plot_corner(trace, corner, None, str(tmp_path))
    assert path is not None
    # la ventana debe incluir el brake_start (850); con pad_m=120 el borde es 730
    lo = charts._corner_lo(corner, corner["segment_m"][0]) - 120
    assert lo <= 850, "la ventana del chart debe cubrir el inicio real de la frenada"
