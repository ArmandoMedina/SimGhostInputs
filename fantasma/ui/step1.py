"""Paso 1 — Importar: cargar archivos de referencia y piloto."""
import streamlit as st

from ._helpers import (
    _best_lap_index,
    _cache_file,
    _corners_from_json,
    _fmt_lap,
    _go,
    _lap_table,
    _next_step_btn,
)


def render(flow):
    st.markdown('<div class="step-header">Paso 1 — Importar telemetría</div>', unsafe_allow_html=True)
    st.caption(
        "Sube los dos archivos CSV. La app detecta automáticamente las vueltas y pre-selecciona "
        "la más rápida completa de cada archivo — puedes cambiarla en el desplegable si quieres otra."
    )

    # ── ① Referencia ─────────────────────────────────────────────────────────
    st.subheader("① Vuelta de referencia")
    st.caption(
        "La vuelta que quieres superar. Puede ser tu mejor tiempo anterior, "
        "la de un coach, o la de otro piloto. Este archivo se mantiene fijo durante todo el flujo."
    )
    ref_file = st.file_uploader(
        "Archivo CSV de la referencia",
        type=["csv", "xlsx"],
        key="ref_upload",
        help="El CSV exportado de MoTeC i2 con la vuelta de referencia.",
    )

    if not ref_file:
        st.info("⬆️ Sube el archivo de referencia para continuar.")
        st.stop()

    _rc = _cache_file(ref_file)
    if not _rc["ok"]:
        st.error("No se pudo leer el archivo: %s" % _rc.get("err", ""))
        st.stop()

    _ref_laps   = _rc["laps"]
    _ref_path   = _rc["path"]
    _ref_auto_i = _best_lap_index(_ref_laps)
    _ref_sel_i  = st.session_state.get("ref_sel_%s" % ref_file.file_id, _ref_auto_i)
    _ref_sel_i  = min(_ref_sel_i, len(_ref_laps) - 1)

    st.success("✓ **Referencia cargada:** %s  (%d vueltas en el archivo)" % (
        _fmt_lap(_ref_laps[_ref_sel_i].laptime), len(_ref_laps)))

    if len(_ref_laps) > 1:
        with st.expander("Cambiar vuelta de referencia — %d vueltas disponibles" % len(_ref_laps)):
            st.caption(
                "🏆 = la más rápida completa (pre-seleccionada)  ·  "
                "✓ = completa  ·  ⚠️ = incompleta (salida de pista, pit, etc.)"
            )
            _ref_tbl   = _lap_table(_ref_laps, editor_key="ref_lap_tbl")
            _ref_sel_i = _ref_tbl[0]
            st.session_state["ref_sel_%s" % ref_file.file_id] = _ref_sel_i
            if _ref_tbl[0] != _ref_auto_i:
                st.info("Usando Vuelta #%d — %s" % (_ref_tbl[0], _fmt_lap(_ref_laps[_ref_tbl[0]].laptime)))

    # ── ② Tu telemetría ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("② Tu vuelta de hoy")
    st.caption(
        "Tus vueltas de la sesión de hoy. Se pre-selecciona automáticamente la más rápida completa. "
        "Si quieres analizar otra vuelta del mismo archivo, cambia la selección abajo."
    )
    drv_file = st.file_uploader(
        "Tu archivo CSV de telemetría",
        type=["csv", "xlsx"],
        key="drv_upload",
        help="El CSV exportado de MoTeC i2 con tus vueltas de hoy.",
    )

    if not drv_file:
        st.info("⬆️ Sube tu archivo de telemetría para continuar.")
        st.stop()

    _dc = _cache_file(drv_file)
    if not _dc["ok"]:
        st.error("No se pudo leer el archivo: %s" % _dc.get("err", ""))
        st.stop()

    _drv_laps = _dc["laps"]
    if not _drv_laps:
        st.warning("No se detectaron vueltas en el archivo. Verifica que el CSV incluye distancia y tiempo.")
        st.stop()

    _drv_auto_i = _best_lap_index(_drv_laps)
    _drv_sel_i  = st.session_state.get("drv_sel_%s" % drv_file.file_id, _drv_auto_i)
    _drv_sel_i  = min(_drv_sel_i, len(_drv_laps) - 1)

    st.success("✓ **Tu vuelta cargada:** %s  (%d vueltas en el archivo)" % (
        _fmt_lap(_drv_laps[_drv_sel_i].laptime), len(_drv_laps)))

    if len(_drv_laps) > 1:
        with st.expander("Cambiar vuelta — %d vueltas disponibles" % len(_drv_laps)):
            st.caption(
                "🏆 = la más rápida completa (pre-seleccionada)  ·  "
                "✓ = completa  ·  ⚠️ = incompleta (salida de pista, pit, etc.)"
            )
            _drv_tbl   = _lap_table(_drv_laps, editor_key="drv_lap_tbl")
            _drv_sel_i = _drv_tbl[0]
            st.session_state["drv_sel_%s" % drv_file.file_id] = _drv_sel_i
            if _drv_tbl[0] != _drv_auto_i:
                st.info("Usando Vuelta #%d — %s" % (_drv_tbl[0], _fmt_lap(_drv_laps[_drv_tbl[0]].laptime)))

    if len(_drv_laps) > 1:
        st.caption(
            "💡 **¿Tienes más vueltas para analizar?** Procesa esta primero. "
            "Al final del flujo, el botón **«Procesar otra vuelta»** te devuelve aquí "
            "para elegir la siguiente — sin recargar nada."
        )

    # ── Opciones avanzadas ────────────────────────────────────────────────────
    _ref_col_map  = None
    _corners_file = None
    with st.expander("⚙️ Opciones avanzadas — nombres de curvas y mapeo de columnas"):
        st.markdown("**Nombres de curvas** *(opcional pero recomendado)*")
        st.caption(
            "Por defecto las curvas se llaman C01, C02… "
            "Si les das nombres reales (Karussell, Adenauer Forst…) aparecen en el reporte y en el HUD."
        )
        _col_cj, _col_cd = st.columns(2)
        with _col_cj:
            _corners_file = st.file_uploader(
                "Subir corners.json",
                type=["json"],
                key="corners_upload",
                help="Archivo JSON con los nombres de curvas que hayas definido antes.",
            )
        with _col_cd:
            st.write(" ")
            if st.button("Detectar curvas automáticamente",
                         help="Analiza la vuelta de referencia y detecta dónde están las curvas."):
                with st.spinner("Analizando vuelta de referencia…"):
                    try:
                        from fantasma.core.corners import detect_corners as _dc2
                        from fantasma.core.corners import extract_milestones as _em
                        from fantasma.core.normalize import fastest_lap as _fl
                        _evs, _ = _dc2(_fl(_ref_laps))
                        _cdet   = _em(_fl(_ref_laps), _evs)
                        st.session_state["corners"]          = _cdet
                        st.session_state["corners_editable"] = True
                        st.success("✓ %d curvas detectadas. Edita los nombres en la tabla de abajo." % len(_cdet))
                    except Exception as _e:
                        st.error("Error: %s" % _e)

        if st.session_state.get("corners_editable") and st.session_state.get("corners"):
            import pandas as _pd2
            _c_data = [
                {"ID": c["id"], "Nombre": c.get("name", ""), "Metro": c["milestones"]["apex"]["d"]}
                for c in st.session_state["corners"]
            ]
            st.caption("Haz clic en la celda «Nombre» para editar:")
            _edited = st.data_editor(
                _pd2.DataFrame(_c_data),
                column_config={
                    "ID":     st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "Metro":  st.column_config.NumberColumn("Metro ápex", disabled=True, width="small"),
                    "Nombre": st.column_config.TextColumn("Nombre de la curva", width="medium"),
                },
                hide_index=True, use_container_width=True, key="corners_editor",
            )
            for _i2, _row in _edited.iterrows():
                if _row["Nombre"]:
                    st.session_state["corners"][_i2]["name"] = _row["Nombre"]

        st.divider()
        st.markdown("**Mapeo de columnas** *(solo si el archivo no se leyó correctamente)*")
        st.caption(
            "Si el CSV viene de un logger diferente a MoTeC i2 y las columnas no tienen "
            "los nombres estándar, mapéalas aquí con el formato `columna_original = canal`."
        )
        _pairs = st.text_area(
            "Columnas", key="ref_map",
            placeholder="Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time\n  velocidad = speed",
        )
        if _pairs.strip():
            _ref_col_map = dict(p.partition("=")[::2] for p in _pairs.splitlines() if "=" in p)

    # ── Cargar ────────────────────────────────────────────────────────────────
    _next_1      = flow["next"].get(1)
    _load_labels = {2: "Cargar y ver análisis →", 3: "Cargar y generar overlay →"}
    _load_label  = _load_labels.get(_next_1, "Cargar →")

    st.divider()
    if st.button(_load_label, type="primary"):
        with st.spinner("Procesando…"):
            try:
                ref_lap = _ref_laps[_ref_sel_i]
                drv_lap = _drv_laps[_drv_sel_i]
                corners = st.session_state.get("corners") if st.session_state.get("corners_editable") else None
                if _corners_file:
                    corners = _corners_from_json(_corners_file)
                    st.session_state["corners_editable"] = True
                st.session_state.update({
                    "ref_path":    _ref_path,
                    "drv_path":    _dc["path"],
                    "ref_name":    _rc.get("name") or ref_file.name,
                    "drv_name":    _dc.get("name") or drv_file.name,
                    "ref_laps":    _ref_laps,
                    "drv_laps":    _drv_laps,
                    "ref_lap":     ref_lap,
                    "drv_lap":     drv_lap,
                    "corners":     corners,
                    "ref_col_map": _ref_col_map,
                })
                _go(_next_1 or 2)
            except Exception as _e:
                st.error("Error al cargar: %s" % _e)

    if "ref_lap" in st.session_state:
        _rl    = st.session_state["ref_lap"]
        _dl    = st.session_state["drv_lap"]
        _delta = _dl.laptime - _rl.laptime
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Referencia",  _fmt_lap(_rl.laptime))
        c2.metric("Longitud",    "%.0f m" % _rl.length)
        c3.metric("Tu vuelta",   _fmt_lap(_dl.laptime))
        c4.metric("Delta",       "%+.3f s" % _delta, delta=round(-_delta, 3), delta_color="normal")
        _next_step_btn(1)
