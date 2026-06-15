"""Paso 2 — Comparar: análisis curva a curva."""
import os
import tempfile

import streamlit as st

from ._helpers import _fmt_lap, _go, _next_step_btn


def render():
    st.markdown('<div class="step-header">Paso 2 — Análisis por curva</div>', unsafe_allow_html=True)
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

    _c1, _c2 = st.columns(2)
    _c1.info("🏁 **Referencia:** %s · %s" % (
        os.path.basename(st.session_state.get("ref_path", "—")), _fmt_lap(ref_lap.laptime)))
    _c2.info("🧑‍💻 **Tu vuelta:** %s · %s" % (
        os.path.basename(st.session_state.get("drv_path", "—")), _fmt_lap(drv_lap.laptime)))

    if "summary" not in st.session_state:
        st.info("Los resultados aparecerán aquí una vez completado el análisis.")
        st.stop()

    summary = st.session_state["summary"]
    rows    = st.session_state["rows"]
    trace   = st.session_state["trace"]

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tiempo referencia", _fmt_lap(summary["ref_laptime"]))
    c2.metric("Tu tiempo",         _fmt_lap(summary["drv_laptime"]))
    c3.metric("Diferencia total",  "%+.3f s" % summary["total_delta"],
              delta=round(-summary["total_delta"], 3), delta_color="normal")

    st.divider()
    st.subheader("¿Dónde estás perdiendo tiempo?")
    st.caption(
        "**Vel. mínima en ápex** = la velocidad más baja que alcanzas en el punto más cerrado de la curva. "
        "**Diferencia km/h** = cuánto más rápido (+) o más lento (−) que la referencia en ese ápex. "
        "**Tiempo ganado/perdido**: positivo = pierdes tiempo, negativo = ganas tiempo. "
        "Las curvas están ordenadas por impacto en el crono."
    )
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)[["name", "apex_d", "ref_vmin", "drv_vmin", "d_vmin", "time_lost", "flags"]]
        df.columns = ["Curva", "Ápex (m)", "Ref. vel. mín. (km/h)", "Tu vel. mín. (km/h)",
                      "Diferencia (km/h)", "Tiempo ganado/perdido (s)", "Avisos"]
        st.dataframe(df.style.format({
            "Tiempo ganado/perdido (s)": "{:+.3f}",
            "Diferencia (km/h)":         "{:+.0f}",
        }), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Gráficas de análisis")
    st.caption(
        "**delta_map** = mapa de la vuelta coloreado por dónde ganas y pierdes tiempo. "
        "**time_loss_bar** = barras por curva ordenadas de mayor a menor pérdida. "
        "**curva_*** = detalle de gas / freno / volante / delta en cada curva con pérdida."
    )

    if "charts_paths" not in st.session_state:
        _charts_import_err = False
        _charts_gen_err    = None
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

    if _charts:
        def _show(container, path):
            try:
                with open(path, "rb") as _f:
                    container.image(_f.read(), use_container_width=True)
            except Exception as _ie:
                container.error("No se pudo cargar: %s\n%s" % (os.path.basename(path), _ie))

        def _charts_of(prefix):
            return [p for p in _charts if os.path.basename(p).startswith(prefix)]

        _overview = _charts_of("delta_map") + _charts_of("time_loss_bar")
        if _overview:
            st.markdown("**Resumen de vuelta**")
            _ov_cols = st.columns(len(_overview))
            for _i, _p in enumerate(_overview):
                _show(_ov_cols[_i], _p)

        _gg = _charts_of("gg_diagram")
        if _gg:
            st.markdown("**Círculo de fricción (G-G)**")
            _, _gc, _ = st.columns([1, 2, 1])
            _show(_gc, _gg[0])

        _full = _charts_of("full_lap")
        if _full:
            st.markdown("**Vista completa de la vuelta — todos los canales**")
            _show(st, _full[0])

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

    st.divider()
    _next_step_btn(2)
