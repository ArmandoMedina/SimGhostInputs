"""Paso 2 — Comparar: análisis curva a curva (NiceGUI)."""

import os
import tempfile

from nicegui import run, ui

from .ng_helpers import _fmt_lap

# ── helpers HTML ──────────────────────────────────────────────────────────────


def _build_corners_table_html(rows):
    """Devuelve el HTML completo de la tabla de curvas."""
    if not rows:
        return '<p style="color:var(--muted);padding:16px;font-size:12px">Sin datos de curvas.</p>'

    # Detectar la curva con mayor tiempo perdido
    worst_idx = None
    worst_loss = 0
    for i, row in enumerate(rows):
        loss = float(row.get("time_lost", 0) or 0)
        if loss > worst_loss:
            worst_loss = loss
            worst_idx = i

    rows_html = ""
    for i, row in enumerate(rows):
        name = row.get("name", f"C{i + 1:02d}")
        dist = row.get("apex_d", row.get("dist_m", row.get("dist", "")))
        vmin_ref = row.get("ref_vmin", row.get("vmin_ref", ""))
        vmin_drv = row.get("drv_vmin", row.get("vmin_drv", ""))
        dv = row.get("d_vmin", row.get("delta_vmin", ""))
        dt = row.get("time_lost", "")
        flags = str(row.get("flags", ""))

        # Formatear números
        try:
            dist = f"{float(dist):.0f}"
        except (TypeError, ValueError):
            pass
        try:
            vmin_ref = f"{float(vmin_ref):.1f}"
        except (TypeError, ValueError):
            pass
        try:
            vmin_drv = f"{float(vmin_drv):.1f}"
        except (TypeError, ValueError):
            pass
        try:
            dv_f = float(dv)
            dv = f"{dv_f:+.1f}"
        except (TypeError, ValueError):
            pass

        dt_html = str(dt)
        try:
            dt_f = float(dt)
            if dt_f > 0.5:
                dt_class = "delta-neg"
            elif dt_f > 0.1:
                dt_class = "delta-warn"
            elif dt_f < 0:
                dt_class = "delta-pos"
            else:
                dt_class = ""
            dt_html = f'<span class="{dt_class}">{dt_f:+.3f}</span>'
        except (TypeError, ValueError):
            pass

        # Chips de flags
        chips = ""
        if "frenada" in flags.lower():
            chips += '<span class="flag-chip brake">FRENA</span>'
        if "vmin" in flags.lower():
            chips += '<span class="flag-chip vmin">APEX</span>'

        worst_class = " worst-row" if i == worst_idx else ""
        rows_html += f"""<tr class="{worst_class}">
          <td style="color:var(--muted)">{i + 1}</td>
          <td style="font-weight:600">{name}</td>
          <td style="color:var(--muted)">{dist}</td>
          <td>{vmin_ref}</td>
          <td>{vmin_drv}</td>
          <td>{dv}</td>
          <td>{dt_html}</td>
          <td>{chips}</td>
        </tr>"""

    return f"""<table class="data-table">
      <thead><tr>
        <th>#</th><th>Nombre</th><th>Dist (m)</th>
        <th>V_min REF</th><th>V_min TU</th><th>DV (km/h)</th><th>DT (s)</th><th>Flags</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>"""


# ── render principal ──────────────────────────────────────────────────────────


async def render(state, navigate):
    ui.label("Paso 2 — Análisis por curva").classes("step-header")

    if state.ref_lap is None:
        ui.label("Primero carga los archivos en el Paso 1.").classes("text-yellow-400")
        ui.button("← Ir al Paso 1", on_click=lambda: navigate(1)).props("flat color=secondary")
        return

    ref_lap = state.ref_lap
    drv_lap = state.drv_lap
    corners = state.corners

    if state.summary is None:
        spinner = ui.spinner("dots").classes("text-blue-400")
        status_lbl = ui.label("Comparando vuelta metro a metro...").classes("text-gray-400")

        def _do_compare():
            from fantasma.core.compare import compare
            from fantasma.core.corners import detect_corners, extract_milestones

            _corners = corners
            if not _corners:
                _evs, _ = detect_corners(ref_lap)
                _corners = extract_milestones(ref_lap, _evs)
            t, r, s = compare(ref_lap, drv_lap, step=1.0, corners=_corners)
            return {"trace": t, "rows": r, "summary": s, "corners": _corners}

        try:
            result = await run.io_bound(_do_compare)
            state.trace = result["trace"]
            state.rows = result["rows"]
            state.summary = result["summary"]
            if not state.corners:
                state.corners = result["corners"]
            state.charts_paths = None
            spinner.delete()
            status_lbl.delete()
        except Exception as e:
            spinner.delete()
            status_lbl.delete()
            ui.label(f"Error en comparacion: {e}").classes("text-red-400")
            return

    summary = state.summary
    rows = state.rows
    trace = state.trace

    # Avisos del motor
    for av in summary.get("avisos") or []:
        ui.label(f"⚠ {av[0].upper() + av[1:] if av else av}").classes(
            "text-yellow-300 bg-yellow-950 px-3 py-2 rounded mb-1"
        )

    # ── Barra de resumen (5 celdas) ──────────────────────────────────────────
    ref_time = _fmt_lap(summary["ref_laptime"])
    drv_time = _fmt_lap(summary["drv_laptime"])
    delta_s = summary["total_delta"]
    delta_class = "delta-neg" if delta_s > 0 else "delta-pos"
    delta_str = "%+.3f s" % delta_s
    track_name = getattr(ref_lap, "meta", {}).get("track", "—") if ref_lap else "—"
    date_str = getattr(ref_lap, "meta", {}).get("date", "—") if ref_lap else "—"

    ui.html(f"""<div class="summary-bar">
  <div class="summary-cell">
    <div class="summary-label-sm">Referencia</div>
    <div class="summary-value ref">{ref_time}</div>
    <div class="summary-sub-sm">vuelta base</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label-sm">Tu vuelta</div>
    <div class="summary-value own">{drv_time}</div>
    <div class="summary-sub-sm">tu mejor</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label-sm">Delta total</div>
    <div class="summary-value {delta_class}">{delta_str}</div>
    <div class="summary-sub-sm">vs referencia</div>
  </div>
  <div class="summary-cell">
    <div class="summary-label-sm">Pista</div>
    <div class="summary-value" style="font-size:13px">{track_name}</div>
    <div class="summary-sub-sm"> </div>
  </div>
  <div class="summary-cell">
    <div class="summary-label-sm">Fecha</div>
    <div class="summary-value" style="font-size:12px;color:var(--muted)">{date_str}</div>
    <div class="summary-sub-sm"> </div>
  </div>
</div>""")

    # Generar gráficas si no existen
    if state.charts_paths is None:
        _out = tempfile.mkdtemp()
        charts_err = None
        try:
            from fantasma.viz.charts import render_charts

            state.charts_paths = render_charts(trace, rows, state.corners or [], _out, top=None)
        except ImportError:
            state.charts_paths = []
            charts_err = 'matplotlib no instalado — ejecuta: pip install "fantasma-inputs[charts]"'
        except Exception as e:
            state.charts_paths = []
            charts_err = str(e)
        if charts_err:
            ui.label(charts_err).classes("text-yellow-400 text-sm mb-2")

    _charts = state.charts_paths or []

    def _charts_of(prefix):
        return [p for p in _charts if os.path.basename(p).startswith(prefix)]

    # ── Layout de dos columnas ────────────────────────────────────────────────
    with ui.html('<div class="analysis-cols">').classes("w-full"):
        # COLUMNA IZQUIERDA: tabla de curvas
        with ui.html('<div class="panel">'):
            # CSV download preparado
            import pandas as _pd

            dl_df = (
                _pd.DataFrame(rows)[
                    ["name", "apex_d", "ref_vmin", "drv_vmin", "d_vmin", "time_lost", "flags"]
                ]
                if rows
                else _pd.DataFrame()
            )
            dl_df.columns = (
                [
                    "Curva",
                    "Apex (m)",
                    "Ref. vel. min. (km/h)",
                    "Tu vel. min. (km/h)",
                    "Diferencia (km/h)",
                    "Tiempo ganado/perdido (s)",
                    "Avisos",
                ]
                if not dl_df.empty
                else dl_df.columns
            )
            csv_bytes = dl_df.to_csv(index=False).encode() if not dl_df.empty else b""

            ui.html("""<div class="panel-header">
              <span class="panel-title">Curvas</span>
              <div></div>
            </div>""")
            with ui.html('<div class="panel-body" style="padding:0">'):
                ui.html(_build_corners_table_html(rows))

            # Drill-down por curva
            ui.separator().classes("my-3 mx-4")
            with ui.column().classes("px-4 pb-4 w-full"):
                ui.label("Detalle de curva").classes("text-sm font-bold text-white mb-1")

                _ordered_rows = sorted(rows, key=lambda r: r.get("time_lost", 0), reverse=True)
                _labels = [
                    "%s · %+.3f s" % (r.get("name", r.get("id", "?")), r.get("time_lost", 0.0))
                    for r in _ordered_rows
                ]

                if _labels:
                    detail_area = ui.column().classes("w-full")

                    def _show_corner(label):
                        try:
                            idx = _labels.index(label)
                        except ValueError:
                            return
                        row = _ordered_rows[idx]
                        detail_area.clear()
                        with detail_area:
                            _render_corner_detail(row, trace)

                    corner_sel = ui.select(
                        options=_labels, value=_labels[0], label="Curva a atacar"
                    ).classes("w-full mb-2")
                    corner_sel.on("update:model-value", lambda e: _show_corner(e.value))
                    _show_corner(_labels[0])

                # Gráficas de curvas
                corners_charts = _charts_of("curva_")
                if corners_charts:
                    ui.label("Curvas con mayor perdida de tiempo").classes(
                        "text-sm font-bold text-white mt-4 mb-2"
                    )
                    with ui.row().classes("gap-2 flex-wrap"):
                        for p in corners_charts:
                            try:
                                with open(p, "rb") as f:
                                    ui.image(f.read()).classes("rounded").style("max-width:400px")
                            except Exception:
                                pass

                brakes = _charts_of("frenada_")
                if brakes:
                    ui.label("Detalle de zonas de frenada").classes(
                        "text-sm font-bold text-white mt-4 mb-2"
                    )
                    with ui.row().classes("gap-2 flex-wrap"):
                        for p in brakes:
                            try:
                                with open(p, "rb") as f:
                                    ui.image(f.read()).classes("rounded").style("max-width:400px")
                            except Exception:
                                pass

                # Descarga CSV
                if csv_bytes:
                    ui.download(csv_bytes, "corners_compare.csv").classes("mt-2")

        # COLUMNA DERECHA
        with ui.html('<div class="right-col">'):
            # Panel gráfica delta
            with ui.html('<div class="panel">'):
                ui.html(
                    '<div class="panel-header"><span class="panel-title">Delta acumulado</span></div>'
                )
                with ui.html('<div class="panel-body">'):
                    overview = _charts_of("delta_map") + _charts_of("time_loss_bar")
                    if overview:
                        with ui.html('<div class="chart-area" style="height:auto">'):
                            for p in overview:
                                try:
                                    with open(p, "rb") as f:
                                        ui.image(f.read()).classes("rounded w-full")
                                except Exception:
                                    pass
                    else:
                        ui.label("No hay gráfica de delta disponible.").classes("text-xs").style(
                            "color:var(--muted)"
                        )

                    gg = _charts_of("gg_diagram")
                    if gg:
                        ui.label("Circulo de friccion (G-G)").classes(
                            "text-sm font-bold text-white mt-3 mb-1"
                        )
                        try:
                            with open(gg[0], "rb") as f:
                                ui.image(f.read()).classes("rounded").style("max-width:300px")
                        except Exception:
                            pass

                    full = _charts_of("full_lap")
                    if full:
                        ui.label("Vista completa de la vuelta").classes(
                            "text-sm font-bold text-white mt-3 mb-1"
                        )
                        try:
                            with open(full[0], "rb") as f:
                                ui.image(f.read()).classes("rounded w-full")
                        except Exception:
                            pass

            # Panel Pace Notes
            def go_to_pacenotes():
                navigate(3)

            with ui.html('<div class="panel">'):
                ui.html(
                    '<div class="panel-header"><span class="panel-title">Pace Notes</span></div>'
                )
                with ui.html('<div class="panel-body">'):
                    ui.label(
                        "Genera tonos de guia para CrewChief con las perdidas detectadas."
                    ).classes("text-xs").style(
                        "color:var(--muted);margin-bottom:12px;display:block"
                    )
                    ui.button(
                        "🔔 Generar Pace Notes",
                        on_click=go_to_pacenotes,
                    ).classes("btn-secondary w-full").props("flat")

    # ── Franja de exportación ─────────────────────────────────────────────────
    with ui.html('<div class="export-strip">'):
        ui.html('<span style="font-size:11px;color:var(--muted)">Análisis completado</span>')
        with ui.html('<div style="display:flex;gap:8px;align-items:center">'):
            ui.button("← Volver", on_click=lambda: navigate(1)).props("flat").classes(
                "btn-secondary"
            )
            _render_next_btn(state, 2, navigate)


# ── funciones auxiliares ──────────────────────────────────────────────────────


def _render_corner_detail(row, trace):
    from fantasma.core.compare import corner_coaching

    coach = corner_coaching(row, trace)

    _color_map = {"gain": "text-green-400", "neutral": "text-blue-300", "loss": "text-yellow-400"}
    _bg_map = {"gain": "bg-green-950", "neutral": "bg-blue-950", "loss": "bg-yellow-950"}
    status = coach.get("status", "neutral")
    ui.label(coach.get("summary", "")).classes(
        f"{_color_map.get(status, 'text-gray-300')} {_bg_map.get(status, '')} px-3 py-2 rounded mb-2 text-sm"
    )

    with ui.row().classes("gap-6 mb-2"):
        with ui.column().classes("items-center"):
            ui.label("Curva").classes("text-xs text-gray-400")
            ui.label(str(coach.get("name", "—"))).classes("font-bold text-white")
        with ui.column().classes("items-center"):
            ui.label("Impacto").classes("text-xs text-gray-400")
            _tl = coach.get("time_lost") or 0.0
            ui.label("%+.3f s" % _tl).classes(
                "font-bold " + ("text-green-400" if _tl < 0 else "text-red-400")
            )
        with ui.column().classes("items-center"):
            ui.label("Apex").classes("text-xs text-gray-400")
            ui.label("%s m" % coach.get("apex", {}).get("ref_apex_m", "—")).classes(
                "font-bold text-white"
            )

    actions = coach.get("actions") or []
    if actions:
        ui.label("Plan de ataque").classes("text-sm font-bold text-white mb-1")
        for action in actions:
            ui.label(f"· {action}").classes("text-sm text-gray-300")

    detail_rows = []
    br = coach.get("braking") or {}
    if br.get("delta_start_m") is not None:
        detail_rows.append(
            {
                "Punto clave": "Frenada",
                "Referencia": "%s m" % br.get("ref_start_m", "—"),
                "Tu": "%s m" % br.get("drv_start_m", "—"),
                "Diferencia": "%+d m" % br["delta_start_m"],
            }
        )
    if br.get("delta_peak_pct") is not None:
        detail_rows.append(
            {
                "Punto clave": "Pico de freno",
                "Referencia": "%s%%" % br.get("ref_peak_pct", "—"),
                "Tu": "%s%%" % br.get("drv_peak_pct", "—"),
                "Diferencia": "%+d pp" % br["delta_peak_pct"],
            }
        )
    ap = coach.get("apex") or {}
    if ap.get("delta_vmin_kmh") is not None:
        detail_rows.append(
            {
                "Punto clave": "V-Min",
                "Referencia": "%s km/h" % ap.get("ref_vmin_kmh", "—"),
                "Tu": "%s km/h" % ap.get("drv_vmin_kmh", "—"),
                "Diferencia": "%+d km/h" % ap["delta_vmin_kmh"],
            }
        )
    th = coach.get("throttle") or {}
    if th.get("delta_gas100_m") is not None:
        detail_rows.append(
            {
                "Punto clave": "Gas 100%",
                "Referencia": "%s m" % th.get("ref_gas100_m", "—"),
                "Tu": "%s m" % th.get("drv_gas100_m", "—"),
                "Diferencia": "%+d m" % th["delta_gas100_m"],
            }
        )
    lat = coach.get("lateral") or {}
    if lat.get("delta_peak_g") is not None:
        detail_rows.append(
            {
                "Punto clave": "G lateral",
                "Referencia": "%.2f G" % lat.get("ref_peak_g", 0.0),
                "Tu": "%.2f G" % lat.get("drv_peak_g", 0.0),
                "Diferencia": "%+.2f G" % lat["delta_peak_g"],
            }
        )
    gear = coach.get("gear") or {}
    if gear.get("ref") or gear.get("drv"):
        detail_rows.append(
            {
                "Punto clave": "Marcha/RPM en apex",
                "Referencia": "%s · %s rpm"
                % (gear.get("ref", {}).get("gear", "—"), gear.get("ref", {}).get("rpm", "—")),
                "Tu": "%s · %s rpm"
                % (gear.get("drv", {}).get("gear", "—"), gear.get("drv", {}).get("rpm", "—")),
                "Diferencia": "%+d rpm" % gear["delta_rpm"]
                if gear.get("delta_rpm") is not None
                else "—",
            }
        )
    if detail_rows:
        cols = ["Punto clave", "Referencia", "Tu", "Diferencia"]
        ui.table(
            columns=[{"name": c, "label": c, "field": c, "align": "left"} for c in cols],
            rows=detail_rows,
        ).classes("w-full text-xs mt-2").props("flat dense")


def _render_next_btn(state, current_step, navigate):
    from .ng_helpers import _DEFAULT_FLOW, _FLOWS, _STEPS

    flow = _FLOWS.get(state.flow_key, _FLOWS[_DEFAULT_FLOW])
    if current_step not in flow["steps"]:
        remaining = sorted(s for s in flow["steps"] if s > current_step)
        if remaining:
            next_i = remaining[0]
            ui.button(
                "Continuar con tu flujo — Ir al Paso %d (%s) →" % (next_i, _STEPS[next_i]),
                on_click=lambda: navigate(next_i),
            ).props("color=primary unelevated")
        return
    next_i = flow["next"].get(current_step)
    if next_i is None:
        ui.label("Completaste todos los pasos de tu flujo!").classes("text-green-400 font-bold")
    else:
        ui.button(
            "Ir al Paso %d — %s →" % (next_i, _STEPS[next_i]),
            on_click=lambda: navigate(next_i),
        ).props("color=primary unelevated")
