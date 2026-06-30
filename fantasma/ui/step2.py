"""Paso 2 — Comparar: análisis curva a curva."""

import io
import os
import tempfile

import pandas as pd
import streamlit as st

from ._helpers import _fmt_lap, _go, _next_step_btn


def render():
    st.markdown(
        '<div class="step-header">Paso 2 — Análisis por curva</div>', unsafe_allow_html=True
    )
    st.caption(
        "Compara tu vuelta contra la referencia metro a metro. "
        "La tabla muestra cuánto tiempo pierdes o ganas en cada curva y por qué."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(1)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    if "summary" not in st.session_state:
        with st.spinner("Comparando vuelta metro a metro…"):
            try:
                from fantasma.core.compare import compare

                if not corners:
                    from fantasma.core.corners import detect_corners, extract_milestones

                    _evs, _ = detect_corners(ref_lap)
                    corners = extract_milestones(ref_lap, _evs)
                    st.session_state["corners"] = corners
                _t, _r, _s = compare(ref_lap, drv_lap, step=1.0, corners=corners)
                st.session_state.update({"trace": _t, "rows": _r, "summary": _s})
                st.session_state.pop("charts_paths", None)
            except Exception as _e:
                st.error("Error en comparación: %s" % _e)
                st.stop()

    _ref_name = st.session_state.get("ref_name") or os.path.basename(
        st.session_state.get("ref_path", "—")
    )
    _drv_name = st.session_state.get("drv_name") or os.path.basename(
        st.session_state.get("drv_path", "—")
    )
    _c1, _c2 = st.columns(2)
    _c1.info("🏁 **Referencia:** %s · %s" % (_ref_name, _fmt_lap(ref_lap.laptime)))
    _c2.info("🧑‍💻 **Tu vuelta:** %s · %s" % (_drv_name, _fmt_lap(drv_lap.laptime)))

    if "summary" not in st.session_state:
        st.info("Los resultados aparecerán aquí una vez completado el análisis.")
        st.stop()

    summary = st.session_state["summary"]
    rows = st.session_state["rows"]
    trace = st.session_state["trace"]

    # Avisos globales del motor (autos/circuitos distintos, delta sospechoso). Viven en
    # summary["avisos"] y antes solo se veian en el CLI / report.md; aqui se muestran para que
    # un usuario de la UI no interprete un reporte invalido como valido (caso C12).
    for _av in summary.get("avisos") or []:
        st.warning("⚠️ " + (_av[0].upper() + _av[1:] if _av else _av))

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tiempo referencia", _fmt_lap(summary["ref_laptime"]))
    c2.metric("Tu tiempo", _fmt_lap(summary["drv_laptime"]))
    c3.metric(
        "Diferencia total",
        "%+.3f s" % summary["total_delta"],
        delta=round(-summary["total_delta"], 3),
        delta_color="normal",
    )

    if "charts_paths" not in st.session_state:
        _charts_import_err = False
        _charts_gen_err = None
        with st.spinner("Generando gráficas…"):
            try:
                _out = tempfile.mkdtemp()
                from fantasma.viz.charts import render_charts

                st.session_state["charts_paths"] = render_charts(
                    trace, rows, corners or [], _out, top=None
                )
            except ImportError:
                st.session_state["charts_paths"] = []
                _charts_import_err = True
            except Exception as _e:
                st.session_state["charts_paths"] = []
                _charts_gen_err = str(_e)
        if _charts_import_err:
            st.info("matplotlib no instalado — ejecuta: pip install 'fantasma-inputs[charts]'")
        if _charts_gen_err:
            st.error("Error en gráficas: %s" % _charts_gen_err)

    _charts = st.session_state.get("charts_paths", [])
    _tab_curvas, _tab_resumen, _tab_vuelta = st.tabs(
        ["Curvas prioritarias", "Resumen de vuelta", "Vuelta completa"]
    )

    def _show(container, path):
        try:
            with open(path, "rb") as _f:
                container.image(_f.read(), use_container_width=True)
        except Exception as _ie:
            container.error("No se pudo cargar: %s\n%s" % (os.path.basename(path), _ie))

    def _charts_of(prefix):
        return [p for p in _charts if os.path.basename(p).startswith(prefix)]

    with _tab_curvas:
        st.subheader("¿Dónde estás perdiendo tiempo?")
        st.caption(
            "**Vel. mínima en ápex** = la velocidad más baja en el punto más cerrado de la curva.  "
            "**Diferencia km/h**: positivo (+) = más rápido que la referencia en ese ápex.  "
            "**Tiempo ganado/perdido**: positivo (+) = **pierdes** tiempo aquí; negativo (−) = **ganas** tiempo.  "
            "Curvas ordenadas por impacto en el crono."
        )
        if not rows:
            st.info(
                "No se detectaron curvas en esta vuelta. Verifica que el CSV incluye el canal de distancia "
                "y que la vuelta tiene longitud suficiente para detectar frenadas."
            )
        if rows:
            df = pd.DataFrame(rows)[
                ["name", "apex_d", "ref_vmin", "drv_vmin", "d_vmin", "time_lost", "flags"]
            ].sort_values("time_lost", ascending=False)
            df.columns = [
                "Curva",
                "Ápex (m)",
                "Ref. vel. mín. (km/h)",
                "Tu vel. mín. (km/h)",
                "Diferencia (km/h)",
                "Tiempo ganado/perdido (s)",
                "Avisos",
            ]
            st.dataframe(
                df.style.format(
                    {
                        "Tiempo ganado/perdido (s)": "{:+.3f}",
                        "Diferencia (km/h)": "{:+.0f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            from fantasma.core.compare import corner_coaching

            _ordered_rows = sorted(rows, key=lambda _r: _r.get("time_lost", 0), reverse=True)
            _labels = [
                "%s · %+.3f s" % (_r.get("name", _r.get("id", "?")), _r.get("time_lost", 0.0))
                for _r in _ordered_rows
            ]
            _selected = st.selectbox("Curva a atacar", _labels, key="selected_corner_label")
            _row = _ordered_rows[_labels.index(_selected)]
            _coach = corner_coaching(_row, trace)

            st.markdown("**Qué atacar primero**")
            if _coach["status"] == "gain":
                st.success(_coach["summary"])
            elif _coach["status"] == "neutral":
                st.info(_coach["summary"])
            else:
                st.warning(_coach["summary"])

            _a1, _a2, _a3 = st.columns(3)
            _a1.metric("Curva", _coach["name"])
            _a2.metric("Impacto", "%+.3f s" % (_coach.get("time_lost") or 0.0))
            _a3.metric("Ápex", "%s m" % _coach["apex"].get("ref_apex_m", "—"))

            _actions = _coach.get("actions") or []
            if _actions:
                st.markdown("**Plan de ataque**")
                for _action in _actions:
                    st.write("- %s" % _action)

            _detail_rows = []
            _br = _coach.get("braking") or {}
            if _br.get("delta_start_m") is not None:
                _detail_rows.append(
                    {
                        "Punto clave": "Frenada",
                        "Referencia": "%s m" % _br.get("ref_start_m", "—"),
                        "Tú": "%s m" % _br.get("drv_start_m", "—"),
                        "Diferencia": "%+d m" % _br["delta_start_m"],
                    }
                )
            if _br.get("delta_peak_pct") is not None:
                _detail_rows.append(
                    {
                        "Punto clave": "Pico de freno",
                        "Referencia": "%s%%" % _br.get("ref_peak_pct", "—"),
                        "Tú": "%s%%" % _br.get("drv_peak_pct", "—"),
                        "Diferencia": "%+d pp" % _br["delta_peak_pct"],
                    }
                )
            _ap = _coach.get("apex") or {}
            if _ap.get("delta_vmin_kmh") is not None:
                _detail_rows.append(
                    {
                        "Punto clave": "V-Min",
                        "Referencia": "%s km/h" % _ap.get("ref_vmin_kmh", "—"),
                        "Tú": "%s km/h" % _ap.get("drv_vmin_kmh", "—"),
                        "Diferencia": "%+d km/h" % _ap["delta_vmin_kmh"],
                    }
                )
            _th = _coach.get("throttle") or {}
            if _th.get("delta_gas100_m") is not None:
                _detail_rows.append(
                    {
                        "Punto clave": "Gas 100%",
                        "Referencia": "%s m" % _th.get("ref_gas100_m", "—"),
                        "Tú": "%s m" % _th.get("drv_gas100_m", "—"),
                        "Diferencia": "%+d m" % _th["delta_gas100_m"],
                    }
                )
            _lat = _coach.get("lateral") or {}
            if _lat.get("delta_peak_g") is not None:
                _detail_rows.append(
                    {
                        "Punto clave": "G lateral",
                        "Referencia": "%.2f G" % _lat.get("ref_peak_g", 0.0),
                        "Tú": "%.2f G" % _lat.get("drv_peak_g", 0.0),
                        "Diferencia": "%+.2f G" % _lat["delta_peak_g"],
                    }
                )
            _gear = _coach.get("gear") or {}
            if _gear.get("ref") or _gear.get("drv"):
                _detail_rows.append(
                    {
                        "Punto clave": "Marcha/RPM en ápex",
                        "Referencia": "%s · %s rpm"
                        % (
                            _gear.get("ref", {}).get("gear", "—"),
                            _gear.get("ref", {}).get("rpm", "—"),
                        ),
                        "Tú": "%s · %s rpm"
                        % (
                            _gear.get("drv", {}).get("gear", "—"),
                            _gear.get("drv", {}).get("rpm", "—"),
                        ),
                        "Diferencia": (
                            "%+d rpm" % _gear["delta_rpm"]
                            if _gear.get("delta_rpm") is not None
                            else "—"
                        ),
                    }
                )
            if _detail_rows:
                st.dataframe(pd.DataFrame(_detail_rows), use_container_width=True, hide_index=True)

        _corners_charts = _charts_of("curva_")
        if _corners_charts:
            st.markdown("**Curvas con mayor pérdida de tiempo**")
            _cc = st.columns(2)
            for _i, _p in enumerate(_corners_charts):
                _show(_cc[_i % 2], _p)

        _brakes = _charts_of("frenada_")
        if _brakes:
            st.markdown("**Detalle de zonas de frenada**")
            _bc = st.columns(2)
            for _i, _p in enumerate(_brakes):
                _show(_bc[_i % 2], _p)

        if rows:
            _dl_df = pd.DataFrame(rows)[
                ["name", "apex_d", "ref_vmin", "drv_vmin", "d_vmin", "time_lost", "flags"]
            ]
            _dl_df.columns = [
                "Curva",
                "Ápex (m)",
                "Ref. vel. mín. (km/h)",
                "Tu vel. mín. (km/h)",
                "Diferencia (km/h)",
                "Tiempo ganado/perdido (s)",
                "Avisos",
            ]
            _csv_buf = io.StringIO()
            _dl_df.to_csv(_csv_buf, index=False)
            st.download_button(
                "⬇️ Descargar tabla de curvas (CSV)",
                _csv_buf.getvalue(),
                file_name="corners_compare.csv",
                mime="text/csv",
            )

    with _tab_resumen:
        st.subheader("Resumen de vuelta")
        _overview = _charts_of("delta_map") + _charts_of("time_loss_bar")
        if _overview:
            _ov_cols = st.columns(len(_overview))
            for _i, _p in enumerate(_overview):
                _show(_ov_cols[_i], _p)

        _gg = _charts_of("gg_diagram")
        if _gg:
            st.markdown("**Círculo de fricción (G-G)**")
            _, _gc, _ = st.columns([1, 2, 1])
            _show(_gc, _gg[0])
        if not _overview and not _gg:
            st.info("No hay gráficas de resumen disponibles para esta comparación.")

    with _tab_vuelta:
        st.subheader("Vista completa de la vuelta — todos los canales")
        _full = _charts_of("full_lap")
        if _full:
            _show(st, _full[0])
        else:
            st.info("No hay vista completa disponible para esta comparación.")

    _next_step_btn(2)
