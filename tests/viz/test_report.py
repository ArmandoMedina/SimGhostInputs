"""Tests de fantasma/viz/report.py — reporte Markdown y CSVs de salida.

Deterministas y sin ffmpeg. Cubren `render_markdown` rama por rama con dicts
sintéticos y un test de integración que alimenta el pipeline real
(detect_corners → extract_milestones → compare) para asegurar que las formas
de datos que produce el motor no rompen el reporte.
"""

import csv

import pytest

from fantasma.viz.report import _fmt_t, render_markdown, write_outputs


def _summary(**over):
    base = {"ref_laptime": 90.0, "drv_laptime": 91.5}
    base.update(over)
    return base


def _corner(**over):
    base = {
        "name": "C1",
        "apex_d": 1200,
        "ref_vmin": 120,
        "drv_vmin": 115,
        "d_vmin": -5,
        "d_brake_m": None,
        "time_lost": 0.4,
        "flags": "",
    }
    base.update(over)
    return base


# --- _fmt_t ----------------------------------------------------------------


def test_fmt_t_formatea_minutos_y_signo():
    assert _fmt_t(90.5) == "1:30.500"
    assert _fmt_t(5.0) == "0:05.000"
    # negativo lleva el signo delante del minuto
    assert _fmt_t(-1.25).startswith("-0:01.25")


# --- render_markdown: cabecera y tiempo ------------------------------------


def test_render_markdown_cabecera_y_delta_de_vuelta():
    md = render_markdown([], [], _summary(ref_laptime=90.0, drv_laptime=91.5))
    assert "# 👻 SimGhostInputs — Debrief" in md
    assert "Tiempo de vuelta" in md
    # delta = drv - ref = +1.500 s
    assert "**+1.500 s**" in md
    # footer con licencia
    assert "AGPL-3.0-or-later" in md


def test_render_markdown_meta_agrega_contexto_y_omite_vacios():
    md = render_markdown([], [], _summary(), meta={"Referencia": "ref.csv", "Piloto": ""})
    assert "Referencia: ref.csv" in md
    # el valor vacío del piloto no debe aparecer como "Piloto: "
    assert "Piloto:" not in md


# --- render_markdown: filas de desgaste ------------------------------------


def test_render_markdown_incluye_filas_de_desgaste_cuando_estan_en_ambos():
    s = _summary(
        ref_wear={
            "slip_index": 1.0,
            "abs_count": 2,
            "tcs_count": 1,
            "tyre_temp_avg": 80.0,
            "fuel_used": 3.0,
        },
        drv_wear={
            "slip_index": 1.5,
            "abs_count": 5,
            "tcs_count": 4,
            "tyre_temp_avg": 88.0,
            "fuel_used": 3.4,
        },
    )
    md = render_markdown([], [], s)
    assert "Índice de deslizamiento" in md
    assert "Activaciones de ABS" in md
    assert "Activaciones de TCS" in md
    assert "Temp. media de gomas" in md
    assert "Combustible usado" in md


def test_render_markdown_omite_desgaste_si_falta_en_un_lado():
    s = _summary(ref_wear={"slip_index": 1.0}, drv_wear={})
    md = render_markdown([], [], s)
    assert "Índice de deslizamiento" not in md


# --- render_markdown: avisos -----------------------------------------------


def test_render_markdown_pinta_avisos():
    md = render_markdown([], [], _summary(avisos=["gomas frías", "combustible bajo"]))
    assert "> **Aviso:** gomas frías" in md
    assert "> **Aviso:** combustible bajo" in md


# --- render_markdown: top de pérdidas --------------------------------------


def test_render_markdown_top_perdidas_ordena_y_describe_frenada():
    rows = [
        _corner(name="Lenta", apex_d=500, time_lost=0.8, d_brake_m=-12, d_vmin=-8),
        _corner(name="Tarde", apex_d=900, time_lost=0.3, d_brake_m=20),
        _corner(name="Buena", apex_d=1500, time_lost=0.0),  # <=0 se omite del top
    ]
    md = render_markdown([], rows, _summary())
    top = md.split("Donde se va el tiempo")[1]
    # la de mayor pérdida aparece primero
    assert top.index("Lenta") < top.index("Tarde")
    # descripciones de frenada temprana/tardía y V-Min
    assert "frenas 12m antes" in top
    assert "V-Min -8 km/h" in top
    assert "frenas 20m tarde" in top
    # la curva sin pérdida no entra en el top
    assert "Buena" not in top.split("Tabla por curva")[0]


def test_render_markdown_detalle_por_defecto_revisar_trazada():
    # pérdida sin causa clara (frenada y vmin dentro de umbral) -> fallback
    rows = [_corner(name="Difusa", time_lost=0.5, d_brake_m=0, d_vmin=1)]
    md = render_markdown([], rows, _summary())
    assert "revisar trazada" in md


def test_render_markdown_tabla_por_curva_lista_todas():
    rows = [_corner(name="C1", time_lost=0.4), _corner(name="C2", time_lost=0.0)]
    md = render_markdown([], rows, _summary())
    tabla = md.split("Tabla por curva")[1]
    # la tabla lista TODAS las curvas (a diferencia del top)
    assert "C1" in tabla and "C2" in tabla


# --- write_outputs ---------------------------------------------------------


def test_write_outputs_crea_los_tres_archivos_y_devuelve_report(tmp_path):
    trace = [{"dist": 0, "delta_t": 0.0}, {"dist": 5, "delta_t": 0.1}]
    rows = [_corner(name="C1", time_lost=0.4)]
    out = write_outputs(str(tmp_path), trace, rows, _summary(), meta={"Referencia": "r"})

    assert out == str(tmp_path / "report.md")
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "delta.csv").exists()
    assert (tmp_path / "corners_compare.csv").exists()
    # delta.csv tiene los encabezados del trace y una fila por muestra
    with open(tmp_path / "delta.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 2 and filas[0]["dist"] == "0"


def test_write_outputs_sin_trace_ni_curvas_solo_reporte(tmp_path):
    write_outputs(str(tmp_path), [], [], _summary())
    assert (tmp_path / "report.md").exists()
    # sin datos no se escriben los CSV
    assert not (tmp_path / "delta.csv").exists()
    assert not (tmp_path / "corners_compare.csv").exists()


def test_write_outputs_corners_csv_une_llaves_heterogeneas(tmp_path):
    # filas con llaves distintas: el encabezado debe ser la UNIÓN. Se parte de
    # _corner() (las llaves que el reporte da por hecho) y cada fila suma una propia.
    rows = [_corner(name="A", extra=1), _corner(name="B", otra=2)]
    write_outputs(str(tmp_path), [], rows, _summary())
    with open(tmp_path / "corners_compare.csv", encoding="utf-8") as f:
        header = f.readline().strip()
    for k in ("name", "time_lost", "apex_d", "extra", "otra"):
        assert k in header


# --- integración con el pipeline real --------------------------------------


@pytest.mark.usefixtures("_sane_fantasma_modules")
def test_render_markdown_con_datos_del_pipeline(lap_factory):
    """Las formas que produce comp() no rompen el reporte."""
    from fantasma.core.compare import compare
    from fantasma.core.corners import detect_corners, extract_milestones

    ref = lap_factory(base_speed=200)
    drv = lap_factory(base_speed=190)
    ev, _ = detect_corners(ref)
    corners = extract_milestones(ref, ev)
    trace, rows, summary = compare(ref, drv, corners=corners)

    md = render_markdown(trace, rows, summary, meta={"Referencia": "ref", "Piloto": "drv"})
    assert "Debrief" in md
    assert "Tabla por curva" in md
    # el piloto es más lento (base 190 vs 200) -> delta positivo
    assert summary["drv_laptime"] > summary["ref_laptime"]
