"""UI local de SimGhostInputs — corre con: fantasma ui (o streamlit run app.py).

Flujo de 4 pasos:
  1. Importar  — cargar archivos de referencia y piloto
  2. Comparar  — delta por metro, tabla por curva, gráficas
  3. Overlay   — generar el HUD animado (webm con alfa)
  4. Componer  — superponer el overlay sobre el video de grabación
"""
import json
import os
import sys
import tempfile
import threading

import streamlit as st

# ── configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="SimGhostInputs",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo: fondo oscuro coherente con el HUD ────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0e1117; }
.step-header { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; }
.metric-ok  { color: #00c853; }
.metric-bad { color: #ff1744; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def _save_upload(uploaded, suffix):
    """Guarda un UploadedFile en un archivo temporal y devuelve la ruta."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read())
    tmp.flush()
    return tmp.name


def _load_lap_cached(path, column_map=None):
    from fantasma import importers
    from fantasma.core.normalize import split_laps, fastest_lap
    outing = importers.load(path, column_map)
    laps   = split_laps(outing)
    best   = fastest_lap(laps)
    return outing, laps, best


def _fmt_lap(seconds):
    m, s = divmod(int(seconds), 60)
    return "%d:%05.2f" % (m, seconds - m * 60)


def _corners_from_json(uploaded):
    data = json.load(uploaded)
    return data.get("corners", data) if isinstance(data, dict) else data


# ── sidebar: navegación ───────────────────────────────────────────────────────
STEPS = ["1 · Importar", "2 · Comparar", "3 · Overlay", "4 · Componer"]
with st.sidebar:
    st.image("https://raw.githubusercontent.com/ArmandoMedina/SimGhostInputs/master/docs/logo.png",
             use_container_width=True, output_format="auto",
             caption=None) if False else None   # logo futuro
    st.title("👻 SimGhostInputs")
    st.caption("Análisis de inputs de simracing por distancia")
    st.divider()
    step = st.radio("Flujo de trabajo", STEPS, label_visibility="collapsed")
    st.divider()
    st.caption("Tus datos nunca salen de tu máquina.")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — IMPORTAR
# ══════════════════════════════════════════════════════════════════════════════
if step == STEPS[0]:
    st.markdown('<div class="step-header">Paso 1 — Importar telemetría</div>', unsafe_allow_html=True)

    # ── 1A: vuelta de referencia ──────────────────────────────────────────────
    st.subheader("① Vuelta de referencia")
    st.caption(
        "Es la vuelta contra la que te vas a comparar — puede ser tu mejor tiempo anterior, "
        "la de un coach, o cualquier lap de referencia que quieras superar. "
        "Exporta el archivo desde MoTeC i2 como CSV o XLSX."
    )
    ref_file = st.file_uploader("Selecciona el archivo de referencia (un solo archivo CSV o XLSX)",
                                type=["csv", "xlsx"], key="ref_upload")
    ref_col_map = None

    if not ref_file:
        st.info("⬆️ Sube la vuelta de referencia para continuar.")
        st.stop()

    # intentar cargar para detectar si necesita mapeo de columnas (solo la primera vez)
    _ref_cache_key = "ref_loaded_%s" % ref_file.file_id
    if _ref_cache_key not in st.session_state:
        with st.spinner("Leyendo archivo de referencia…"):
            try:
                _ref_path_tmp = _save_upload(ref_file, os.path.splitext(ref_file.name)[1])
                ref_file.seek(0)
                from fantasma import importers as _imp_ref
                _imp_ref.load(_ref_path_tmp)
                st.session_state[_ref_cache_key] = {"path": _ref_path_tmp, "ok": True}
            except ValueError as _e:
                st.session_state[_ref_cache_key] = {"path": _ref_path_tmp, "ok": False, "err": str(_e)}
    _ref_cache = st.session_state[_ref_cache_key]
    _ref_path_tmp = _ref_cache["path"]
    _ref_load_ok  = _ref_cache["ok"]
    if not _ref_load_ok:
        _ref_err = _ref_cache.get("err", "")

    if not _ref_load_ok:
        st.warning("No pudimos detectar las columnas automáticamente. Indica cuáles son:")
        with st.expander("Configurar columnas del archivo", expanded=True):
            st.caption(
                "Tu archivo tiene nombres de columnas que no reconocemos. "
                "Escribe abajo cómo se llaman en tu archivo y qué significan, "
                "una por línea con el formato  nombre_en_tu_archivo = significado"
            )
            _ejemplo = "Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time\n  velocidad = speed"
            pairs = st.text_area("Columnas", placeholder=_ejemplo, key="ref_map")
            if pairs.strip():
                ref_col_map = dict(p.partition("=")[::2] for p in pairs.splitlines() if "=" in p)

    # ── 1B: vuelta del piloto ─────────────────────────────────────────────────
    st.divider()
    st.subheader("② Tu archivo de telemetría")
    st.caption(
        "El archivo con tus vueltas de la sesión. "
        "Si tiene varias vueltas podrás elegir cuál analizar en el siguiente paso."
    )
    drv_file = st.file_uploader("Selecciona tu archivo de telemetría (un solo archivo CSV o XLSX)",
                                type=["csv", "xlsx"], key="drv_upload")

    if not drv_file:
        st.info("⬆️ Sube tu archivo de telemetría para continuar.")
        st.stop()

    # detectar vueltas automáticamente (solo la primera vez; cachear en session_state)
    lap_index = None
    _drv_cache_key = "drv_laps_%s" % drv_file.file_id
    if _drv_cache_key not in st.session_state:
        with st.spinner("Leyendo vueltas de tu archivo…"):
            try:
                import tempfile as _tf
                from fantasma import importers as _imp
                from fantasma.core.normalize import split_laps as _sl
                _tmp = _tf.NamedTemporaryFile(delete=False, suffix=os.path.splitext(drv_file.name)[1])
                _tmp.write(drv_file.read()); _tmp.flush(); drv_file.seek(0)
                st.session_state[_drv_cache_key] = {"laps": _sl(_imp.load(_tmp.name)), "path": _tmp.name}
            except Exception as _e:
                st.error("No se pudo leer el archivo: %s" % _e)
                st.stop()
    _detected_laps = st.session_state[_drv_cache_key]["laps"]

    if _detected_laps:
        import pandas as _pd
        _best_i = 0
        _best_t = float("inf")
        for i, l in enumerate(_detected_laps):
            if l.meta.get("is_complete") and l.laptime < _best_t:
                _best_t = l.laptime
                _best_i = i

        _lap_rows = []
        for i, l in enumerate(_detected_laps):
            _complete = l.meta.get("is_complete", False)
            _lap_rows.append({
                "Analizar": i == _best_i,
                "#": i,
                "Tiempo": _fmt_lap(l.laptime),
                "Metros": int(l.length),
                "Completa": "✓" if _complete else "—",
            })

        st.caption("Marca las vueltas que quieres analizar. La vuelta completa más rápida está pre-seleccionada.")
        _edited_laps = st.data_editor(
            _pd.DataFrame(_lap_rows),
            column_config={
                "Analizar": st.column_config.CheckboxColumn("Analizar", width="small"),
                "#":        st.column_config.NumberColumn("#", disabled=True, width="small"),
                "Tiempo":   st.column_config.TextColumn("Tiempo", disabled=True, width="medium"),
                "Metros":   st.column_config.NumberColumn("Metros", disabled=True, width="small"),
                "Completa": st.column_config.TextColumn("✓", disabled=True, width="small"),
            },
            hide_index=True,
            use_container_width=True,
            key="lap_selector",
        )

        _selected_indices = [int(row["#"]) for _, row in _edited_laps.iterrows() if row["Analizar"]]
        if not _selected_indices:
            st.warning("Marca al menos una vuelta para continuar.")
            st.stop()

        lap_index = _selected_indices[0]
        st.session_state["selected_lap_indices"] = _selected_indices
    else:
        st.warning("No se detectaron vueltas en el archivo.")
        st.stop()

    # ── 1C: curvas del circuito ───────────────────────────────────────────────
    st.divider()
    st.subheader("③ Nombres de curvas (opcional)")
    st.caption(
        "Si agregas nombres, el reporte mostrará 'Hatzenbach', 'Karussell', etc. "
        "en lugar de C01, C02… Puedes saltarte este paso y añadirlos después."
    )

    _corners_in_state = "corners" in st.session_state and st.session_state["corners"]
    col_cj, col_cd = st.columns([1, 1])
    corners_file = None
    with col_cj:
        corners_file = st.file_uploader(
            "Sube un corners.json que ya tengas",
            type=["json"], key="corners_upload")
    with col_cd:
        st.write("¿Primera vez? Detéctalas automáticamente:")
        if st.button("Detectar curvas"):
            with st.spinner("Analizando vuelta de referencia…"):
                try:
                    from fantasma import importers as _imp2
                    from fantasma.core.normalize import split_laps as _sl2, fastest_lap as _fl2
                    from fantasma.core.corners import detect_corners as _dc, extract_milestones as _em
                    _ref_lap2 = _fl2(_sl2(_imp2.load(_ref_path_tmp)))
                    _evs, _ = _dc(_ref_lap2)
                    _corners_det = _em(_ref_lap2, _evs)
                    st.session_state["corners"] = _corners_det
                    st.session_state["corners_editable"] = True
                    st.success("✓ %d curvas detectadas. Puedes ponerles nombre abajo." % len(_corners_det))
                except Exception as e:
                    st.error("Error: %s" % e)

    if st.session_state.get("corners_editable") and st.session_state.get("corners"):
        import pandas as _pd2
        _c_data = [{"ID": c["id"], "Nombre": c.get("name", ""), "Metro": c["milestones"]["apex"]["d"]}
                   for c in st.session_state["corners"]]
        st.caption("Escribe el nombre de cada curva (puedes dejar en blanco las que no conozcas):")
        _edited = st.data_editor(
            _pd2.DataFrame(_c_data),
            column_config={
                "ID":     st.column_config.TextColumn("ID", disabled=True, width="small"),
                "Metro":  st.column_config.NumberColumn("Metro", disabled=True, width="small"),
                "Nombre": st.column_config.TextColumn("Nombre de la curva", width="medium"),
            },
            hide_index=True, use_container_width=True, key="corners_editor"
        )
        for i, row in _edited.iterrows():
            if row["Nombre"]:
                st.session_state["corners"][i]["name"] = row["Nombre"]

    # ── 1D: cargar ───────────────────────────────────────────────────────────
    st.divider()
    if st.button("Cargar y continuar →", type="primary"):
        with st.spinner("Procesando archivos…"):
            try:
                ref_path = _ref_path_tmp
                drv_path = st.session_state[_drv_cache_key]["path"]

                _, ref_laps, ref_lap = _load_lap_cached(ref_path, ref_col_map)
                drv_laps = st.session_state[_drv_cache_key]["laps"]
                _sel_idxs = st.session_state.get("selected_lap_indices", [lap_index])
                drv_lap   = drv_laps[_sel_idxs[0]] if _sel_idxs else drv_laps[lap_index]

                corners = st.session_state.get("corners")
                if corners_file:
                    corners = _corners_from_json(corners_file)

                _drv_selected = [drv_laps[i] for i in _sel_idxs if i < len(drv_laps)]
                st.session_state.update({
                    "ref_path": ref_path, "drv_path": drv_path,
                    "ref_laps": ref_laps, "drv_laps": drv_laps,
                    "ref_lap": ref_lap,   "drv_lap": drv_lap,
                    "drv_selected_laps": _drv_selected,
                    "corners": corners,
                    "ref_col_map": ref_col_map,
                    "lap_index": lap_index,
                })
                st.success("✓ Archivos cargados. Ve al Paso 2 para comparar.")
            except Exception as e:
                st.error("Error al cargar: %s" % e)

    if "ref_lap" in st.session_state:
        ref_lap = st.session_state["ref_lap"]
        drv_lap = st.session_state["drv_lap"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ref. — tiempo de vuelta", "%.3f s" % ref_lap.laptime)
        c2.metric("Ref. — longitud",          "%.0f m" % ref_lap.length)
        c3.metric("Piloto — tiempo de vuelta", "%.3f s" % drv_lap.laptime)
        delta = drv_lap.laptime - ref_lap.laptime
        c4.metric("Delta",
                  "%+.3f s" % delta,
                  delta=round(-delta, 3),   # positivo si el piloto es más rápido
                  delta_color="normal")
        st.caption("Vueltas referencia: %d · Vueltas piloto: %d" % (
            len(st.session_state["ref_laps"]), len(st.session_state["drv_laps"])))


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — COMPARAR
# ══════════════════════════════════════════════════════════════════════════════
elif step == STEPS[1]:
    st.markdown('<div class="step-header">Paso 2 — Comparar</div>', unsafe_allow_html=True)

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    col_cfg, col_run = st.columns([2, 1])
    with col_cfg:
        step_m = st.slider("Resolución de rejilla (metros)", 1, 20, 5)
        gen_charts = st.checkbox("Generar gráficas por curva", value=True)
        charts_top = st.number_input("Top N curvas con mayor pérdida", 1, 20, 5)

    if col_run.button("Comparar ahora", type="primary"):
        with st.spinner("Comparando…"):
            try:
                from fantasma.core.compare import compare
                trace, rows, summary = compare(ref_lap, drv_lap,
                                               step=float(step_m), corners=corners)
                st.session_state.update({
                    "trace": trace, "rows": rows, "summary": summary,
                })
            except Exception as e:
                st.error("Error en comparación: %s" % e)

    if "summary" in st.session_state:
        summary = st.session_state["summary"]
        rows    = st.session_state["rows"]
        trace   = st.session_state["trace"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Tiempo referencia", "%.3f s" % summary["ref_laptime"])
        c2.metric("Tiempo piloto",     "%.3f s" % summary["drv_laptime"])
        c3.metric("Delta total",       "%+.3f s" % summary["total_delta"],
                  delta=round(-summary["total_delta"], 3), delta_color="normal")

        st.divider()
        st.subheader("Tabla por curva")
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)[["name", "apex_d", "ref_vmin", "drv_vmin",
                                     "d_vmin", "time_lost", "flags"]]
            df.columns = ["Curva", "Ápex m", "V-Min ref", "V-Min tú", "ΔV-Min", "Tiempo perdido", "Avisos"]
            st.dataframe(df.style.format({
                "Tiempo perdido": "{:+.3f}",
                "ΔV-Min":         "{:+.0f}",
            }), use_container_width=True, hide_index=True)

        if gen_charts:
            st.divider()
            st.subheader("Gráficas de curvas")
            with st.spinner("Generando gráficas…"):
                try:
                    out_dir = tempfile.mkdtemp()
                    from fantasma.viz.charts import render_charts
                    charts = render_charts(trace, rows, corners or [], out_dir, top=int(charts_top))
                    n_cols = min(len(charts), 2)
                    if n_cols:
                        cols = st.columns(n_cols)
                        for i, path in enumerate(charts):
                            cols[i % n_cols].image(path, use_container_width=True)
                except ImportError:
                    st.info("matplotlib no instalado — instala `fantasma-inputs[charts]` para gráficas.")
                except Exception as e:
                    st.error("Error en gráficas: %s" % e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
elif step == STEPS[2]:
    st.markdown('<div class="step-header">Paso 3 — Generar overlay HUD</div>', unsafe_allow_html=True)

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    col_a, col_b, col_c = st.columns(3)
    fps    = col_a.selectbox("FPS", [24, 30, 60], index=1)
    fmt    = col_b.selectbox("Formato", ["webm", "prores", "png"], index=0)
    all_laps = col_c.checkbox("Todas las vueltas (--all-laps)",
                               help="Renderiza cada vuelta completa del piloto por separado.")

    out_dir = st.text_input("Carpeta de salida",
                             value=os.path.join(os.path.expanduser("~"), "fantasma_salida"))

    st.info("El render puede tardar 15-30 min para una vuelta completa del Nordschleife. "
            "La barra de progreso se actualiza cada 10 segundos de video.")

    if st.button("Generar overlay", type="primary"):
        os.makedirs(out_dir, exist_ok=True)
        progress_bar = st.progress(0, text="Iniciando…")
        status_text  = st.empty()

        def _progress(n, total):
            pct = n / total if total else 0
            progress_bar.progress(pct, text="Frame %d / %d (%.0f%%)" % (n, total, pct * 100))
            status_text.caption("Renderizando…")

        try:
            from fantasma.viz.overlay import render_overlay

            if all_laps:
                complete = st.session_state.get("drv_selected_laps") or st.session_state["drv_laps"]
                webms = []
                for i, lap in enumerate(complete):
                    st.write("Vuelta %d/%d — %.2f s" % (i + 1, len(complete), lap.laptime))
                    lap_dir = os.path.join(out_dir, "lap_%02d" % i)
                    os.makedirs(lap_dir, exist_ok=True)
                    out = render_overlay(ref_lap, lap, corners or [], lap_dir,
                                         fps=fps, fmt=fmt, progress=_progress)
                    webms.append(out)
            else:
                out = render_overlay(ref_lap, drv_lap, corners or [], out_dir,
                                     fps=fps, fmt=fmt, progress=_progress)
                webms = [out]

            progress_bar.progress(1.0, text="Completado")
            st.success("Overlay generado:")
            for w in webms:
                st.code(w)
            st.session_state["last_overlay"] = webms[0] if len(webms) == 1 else os.path.join(out_dir, "overlay_all.webm")
        except ImportError:
            st.error("matplotlib y/o Pillow no instalados. Ejecuta: pip install 'fantasma-inputs[overlay]'")
        except Exception as e:
            st.error("Error: %s" % e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — COMPONER
# ══════════════════════════════════════════════════════════════════════════════
elif step == STEPS[3]:
    st.markdown('<div class="step-header">Paso 4 — Componer video final</div>', unsafe_allow_html=True)
    st.caption("Superpone el overlay sobre tu grabación. Solo necesitas ffmpeg instalado.")

    col1, col2 = st.columns(2)
    video_path   = col1.text_input("Ruta del video de grabación",
                                    placeholder=r"C:\Videos\mi_vuelta.mp4")
    overlay_path = col2.text_input("Ruta del overlay (.webm/.mov)",
                                    value=st.session_state.get("last_overlay", ""),
                                    placeholder=r"C:\fantasma_salida\overlay.webm")

    col3, col4, col5 = st.columns(3)
    position = col3.selectbox("Posición del HUD", [
        "bottom-right", "bottom-left", "top-right", "top-left",
        "bottom-center", "top-center", "center",
    ])
    offset = col4.number_input("Delay del overlay (s)", value=0.0, step=0.5,
                                help="Segundos desde el inicio del video hasta que empieza el overlay.")
    scale  = col5.slider("Escala del HUD", 0.25, 1.5, 1.0, 0.05)

    out_path = st.text_input("Archivo de salida",
                              placeholder=r"C:\Videos\mi_vuelta_hud.mp4")

    if st.button("Componer video", type="primary",
                 disabled=not (video_path and overlay_path)):
        if not out_path:
            base = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(os.path.dirname(video_path), base + "_composed.mp4")

        with st.spinner("Composiendo con ffmpeg…"):
            try:
                from fantasma.viz.compose import compose_video
                result = compose_video(video_path, overlay_path, out_path,
                                       position=position, offset=offset, scale=scale)
                st.success("Video compuesto:")
                st.code(result)
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error("Error al componer: %s" % e)
