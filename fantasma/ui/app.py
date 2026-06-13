"""UI local de SimGhostInputs — corre con: fantasma ui (o streamlit run app.py).

Flujo de 4 pasos:
  1. Importar  — cargar archivos de referencia y piloto
  2. Comparar  — delta por metro, tabla por curva, gráficas
  3. Overlay   — generar el HUD animado (webm con alfa)
  4. Componer  — superponer el overlay sobre el video de grabación
"""
import json
import os
import tempfile

import streamlit as st

# ── configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="SimGhostInputs",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo ────────────────────────────────────────────────────────────────
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
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read())
    tmp.flush()
    return tmp.name


def _load_laps(path, column_map=None):
    from fantasma import importers
    from fantasma.core.normalize import split_laps
    return split_laps(importers.load(path, column_map))


def _fmt_lap(seconds):
    m, s = divmod(int(seconds), 60)
    return "%d:%05.2f" % (m, seconds - m * 60)


def _corners_from_json(uploaded):
    data = json.load(uploaded)
    return data.get("corners", data) if isinstance(data, dict) else data


def _lap_table(laps, editor_key, single=False):
    """Muestra tabla de selección de vueltas; devuelve lista de índices marcados."""
    import pandas as _pd
    _best_i, _best_t = 0, float("inf")
    for i, l in enumerate(laps):
        if l.meta.get("is_complete") and l.laptime < _best_t:
            _best_t, _best_i = l.laptime, i

    rows = []
    for i, l in enumerate(laps):
        _c = l.meta.get("is_complete", False)
        rows.append({
            "Sel":    i == _best_i,
            "#":      i,
            "Tiempo": _fmt_lap(l.laptime),
            "Metros": int(l.length),
            "Estado": "🏆 Más rápida" if i == _best_i else ("✓ Completa" if _c else "⚠️ Incompleta"),
        })

    if single:
        st.caption("Marca **solo una** vuelta — es la referencia contra la que te vas a comparar. 🏆 = más rápida completa · ⚠️ = vuelta incompleta (out/in lap)")
    else:
        st.info("Aquí **sí puedes marcar varias vueltas**. La primera marcada se usará en el análisis; las demás se incluyen si generas overlay de toda la sesión. 🏆 = más rápida · ⚠️ = incompleta (out/in lap)")

    edited = st.data_editor(
        _pd.DataFrame(rows),
        column_config={
            "Sel":    st.column_config.CheckboxColumn("Sel", width="small"),
            "#":      st.column_config.NumberColumn("#", disabled=True, width="small"),
            "Tiempo": st.column_config.TextColumn("Tiempo", disabled=True, width="medium"),
            "Metros": st.column_config.NumberColumn("Metros", disabled=True, width="small"),
            "Estado": st.column_config.TextColumn("Estado", disabled=True, width="medium"),
        },
        hide_index=True, use_container_width=True, key=editor_key,
    )
    return [int(r["#"]) for _, r in edited.iterrows() if r["Sel"]]


# ── posiciones del HUD (traducidas) ──────────────────────────────────────────
_POS_LABELS = {
    "Abajo derecha":   "bottom-right",
    "Abajo izquierda": "bottom-left",
    "Arriba derecha":  "top-right",
    "Arriba izquierda":"top-left",
    "Abajo centro":    "bottom-center",
    "Arriba centro":   "top-center",
    "Centro":          "center",
}


# ── estado de navegación ──────────────────────────────────────────────────────
if "nav_step" not in st.session_state:
    st.session_state["nav_step"] = 0

_STEP_LABELS = ["Importar", "Comparar", "Overlay", "Componer"]

def _step_done(i):
    return bool([
        "ref_lap" in st.session_state,
        "summary" in st.session_state,
        "last_overlay" in st.session_state,
        False,
    ][i])

def _step_unlocked(i):
    if i == 0: return True
    has_data = "ref_lap" in st.session_state
    if i in (1, 2): return has_data
    if i == 3: return has_data and "last_overlay" in st.session_state
    return False

def _go(i):
    st.session_state["nav_step"] = i
    st.rerun()


# ── sidebar: breadcrumbs ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("👻 SimGhostInputs")
    st.caption("Análisis de inputs de simracing por distancia")
    st.divider()
    for _i, _lbl in enumerate(_STEP_LABELS):
        _current  = st.session_state["nav_step"] == _i
        _icon     = "▶️" if _current else ("✅" if _step_done(_i) else "○")
        _disabled = not _step_unlocked(_i)
        if st.button(
            "%s  %d · %s" % (_icon, _i + 1, _lbl),
            disabled=_disabled,
            use_container_width=True,
            key="nav_%d" % _i,
        ):
            _go(_i)
    st.divider()
    st.caption("Tus datos nunca salen de tu máquina.")

step_idx = st.session_state["nav_step"]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — IMPORTAR
# ══════════════════════════════════════════════════════════════════════════════
if step_idx == 0:
    st.markdown('<div class="step-header">Paso 1 — Importar telemetría</div>', unsafe_allow_html=True)

    # ── 1A: vuelta de referencia ──────────────────────────────────────────────
    st.subheader("① Vuelta de referencia")
    st.caption(
        "La vuelta contra la que te vas a comparar — tu mejor tiempo anterior, "
        "la de un coach, o cualquier referencia que quieras superar. "
        "Exporta desde MoTeC i2 como CSV o XLSX."
    )
    ref_file = st.file_uploader(
        "Selecciona el archivo de referencia (CSV o XLSX)",
        type=["csv", "xlsx"], key="ref_upload",
    )
    ref_col_map = None

    if not ref_file:
        st.info("⬆️ Sube la vuelta de referencia para continuar.")
        st.stop()

    # cargar y detectar vueltas (cachear por file_id)
    _ref_ck = "ref_%s" % ref_file.file_id
    if _ref_ck not in st.session_state:
        with st.spinner("Leyendo archivo de referencia…"):
            try:
                _rpath = _save_upload(ref_file, os.path.splitext(ref_file.name)[1])
                ref_file.seek(0)
                _rlaps = _load_laps(_rpath)
                st.session_state[_ref_ck] = {"path": _rpath, "ok": True, "laps": _rlaps}
            except ValueError as _e:
                _rpath = _save_upload(ref_file, os.path.splitext(ref_file.name)[1])
                st.session_state[_ref_ck] = {"path": _rpath, "ok": False, "err": str(_e), "laps": []}
            except Exception as _e:
                st.session_state[_ref_ck] = {"path": "", "ok": False, "err": str(_e), "laps": []}

    _rc       = st.session_state[_ref_ck]
    _ref_path = _rc["path"]
    _ref_laps = _rc["laps"]

    if not _rc["ok"]:
        st.warning("No pudimos detectar las columnas automáticamente. Indica cuáles son:")
        with st.expander("Configurar columnas del archivo", expanded=True):
            st.caption(
                "Escribe cómo se llaman en tu archivo y qué significan, "
                "una por línea con el formato:  nombre_en_tu_archivo = significado"
            )
            pairs = st.text_area(
                "Columnas",
                placeholder="Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time\n  velocidad = speed",
                key="ref_map",
            )
            if pairs.strip():
                ref_col_map = dict(p.partition("=")[::2] for p in pairs.splitlines() if "=" in p)

    # selección de vuelta de referencia — exactamente 1
    if _ref_laps:
        _ref_sel = _lap_table(_ref_laps, editor_key="ref_lap_sel", single=True)
        if len(_ref_sel) == 0:
            st.warning("Selecciona una vuelta de referencia para continuar.")
            st.stop()
        if len(_ref_sel) > 1:
            st.error("Solo puedes marcar **una** vuelta como referencia. Desmarca las demás.")
            st.stop()
        st.session_state["ref_lap_index"] = _ref_sel[0]

    # ── 1B: vuelta del piloto ─────────────────────────────────────────────────
    st.divider()
    st.subheader("② Tu archivo de telemetría")
    st.caption(
        "El archivo con tus vueltas de la sesión. "
        "Puedes marcar una o varias vueltas — la primera marcada se usará en el análisis, "
        "el resto se incluirán si generas overlay de todas las vueltas."
    )
    drv_file = st.file_uploader(
        "Selecciona tu archivo de telemetría (CSV o XLSX)",
        type=["csv", "xlsx"], key="drv_upload",
    )

    if not drv_file:
        st.info("⬆️ Sube tu archivo de telemetría para continuar.")
        st.stop()

    _drv_ck = "drv_%s" % drv_file.file_id
    if _drv_ck not in st.session_state:
        with st.spinner("Leyendo vueltas de tu archivo…"):
            try:
                _dpath = _save_upload(drv_file, os.path.splitext(drv_file.name)[1])
                drv_file.seek(0)
                _dlaps = _load_laps(_dpath)
                st.session_state[_drv_ck] = {"path": _dpath, "laps": _dlaps}
            except Exception as _e:
                st.error("No se pudo leer el archivo: %s" % _e)
                st.stop()

    _dc       = st.session_state[_drv_ck]
    _drv_laps = _dc["laps"]

    if not _drv_laps:
        st.warning("No se detectaron vueltas en el archivo.")
        st.stop()

    _drv_sel = _lap_table(_drv_laps, editor_key="drv_lap_sel", single=False)
    if not _drv_sel:
        st.warning("Marca al menos una vuelta para continuar.")
        st.stop()
    st.session_state["drv_lap_indices"] = _drv_sel

    # ── 1C: curvas del circuito ───────────────────────────────────────────────
    st.divider()
    st.subheader("③ Nombres de curvas (opcional)")
    st.caption(
        "Si agregas nombres, el reporte mostrará 'Hatzenbach', 'Karussell', etc. "
        "en lugar de C01, C02… Puedes saltarte este paso."
    )

    col_cj, col_cd = st.columns([1, 1])
    corners_file = None
    with col_cj:
        corners_file = st.file_uploader(
            "Sube un corners.json que ya tengas",
            type=["json"], key="corners_upload",
        )
    with col_cd:
        st.write("¿Primera vez? Detéctalas automáticamente:")
        if st.button("Detectar curvas"):
            with st.spinner("Analizando vuelta de referencia…"):
                try:
                    from fantasma.core.normalize import fastest_lap as _fl
                    from fantasma.core.corners import detect_corners as _dc2, extract_milestones as _em
                    _best_ref = _fl(_ref_laps)
                    _evs, _   = _dc2(_best_ref)
                    _cdet     = _em(_best_ref, _evs)
                    st.session_state["corners"]          = _cdet
                    st.session_state["corners_editable"] = True
                    st.success("✓ %d curvas detectadas." % len(_cdet))
                except Exception as _e:
                    st.error("Error: %s" % _e)

    if st.session_state.get("corners_editable") and st.session_state.get("corners"):
        import pandas as _pd2
        _c_data = [
            {"ID": c["id"], "Nombre": c.get("name", ""), "Metro": c["milestones"]["apex"]["d"]}
            for c in st.session_state["corners"]
        ]
        st.caption("Escribe el nombre de cada curva (puedes dejar en blanco las que no conozcas):")
        _edited = st.data_editor(
            _pd2.DataFrame(_c_data),
            column_config={
                "ID":     st.column_config.TextColumn("ID", disabled=True, width="small"),
                "Metro":  st.column_config.NumberColumn("Metro", disabled=True, width="small"),
                "Nombre": st.column_config.TextColumn("Nombre de la curva", width="medium"),
            },
            hide_index=True, use_container_width=True, key="corners_editor",
        )
        for i, row in _edited.iterrows():
            if row["Nombre"]:
                st.session_state["corners"][i]["name"] = row["Nombre"]

    # ── 1D: cargar ────────────────────────────────────────────────────────────
    st.divider()
    if st.button("Cargar y continuar →", type="primary"):
        with st.spinner("Procesando archivos…"):
            try:
                _sel_ref = st.session_state.get("ref_lap_index", 0)
                _sel_drv = st.session_state.get("drv_lap_indices", [0])

                ref_lap      = _ref_laps[_sel_ref]
                drv_laps     = _dc["laps"]
                drv_lap      = drv_laps[_sel_drv[0]]
                drv_selected = [drv_laps[i] for i in _sel_drv if i < len(drv_laps)]

                corners = st.session_state.get("corners")
                if corners_file:
                    corners = _corners_from_json(corners_file)

                st.session_state.update({
                    "ref_path":          _ref_path,
                    "drv_path":          _dc["path"],
                    "ref_laps":          _ref_laps,
                    "drv_laps":          drv_laps,
                    "ref_lap":           ref_lap,
                    "drv_lap":           drv_lap,
                    "drv_selected_laps": drv_selected,
                    "corners":           corners,
                    "ref_col_map":       ref_col_map,
                })
                st.success("✓ Archivos cargados correctamente.")
            except Exception as _e:
                st.error("Error al cargar: %s" % _e)

    if "ref_lap" in st.session_state:
        _rl    = st.session_state["ref_lap"]
        _dl    = st.session_state["drv_lap"]
        _delta = _dl.laptime - _rl.laptime
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Referencia",      _fmt_lap(_rl.laptime))
        c2.metric("Ref. — longitud", "%.0f m" % _rl.length)
        c3.metric("Tu vuelta",       _fmt_lap(_dl.laptime))
        c4.metric("Delta", "%+.3f s" % _delta,
                  delta=round(-_delta, 3), delta_color="normal")
        _ndrv = len(st.session_state.get("drv_selected_laps", []))
        st.caption(
            "Vueltas de referencia disponibles: %d · Vueltas del piloto seleccionadas: %d"
            % (len(st.session_state["ref_laps"]), _ndrv)
        )
        st.divider()
        if st.button("Ir al Paso 2 — Comparar →", type="primary"):
            _go(1)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — COMPARAR
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 1:
    st.markdown('<div class="step-header">Paso 2 — Comparar</div>', unsafe_allow_html=True)
    st.caption(
        "Aquí el sistema compara tu vuelta contra la referencia metro a metro "
        "y te dice en qué curvas estás perdiendo tiempo, cuánto, y por qué "
        "(velocidad mínima baja, frenada tarde, gas tardío…)."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(0)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    # resumen de lo que se va a comparar
    _c1, _c2 = st.columns(2)
    _c1.info("🏁 **Referencia:** %s — %s" % (
        st.session_state.get("ref_path", "—").split(os.sep)[-1],
        _fmt_lap(ref_lap.laptime),
    ))
    _c2.info("🧑‍💻 **Tu vuelta:** %s — %s" % (
        st.session_state.get("drv_path", "—").split(os.sep)[-1],
        _fmt_lap(drv_lap.laptime),
    ))

    st.divider()
    gen_charts = st.checkbox(
        "Generar gráficas por curva",
        value=True,
        help="Muestra velocidad, gas y freno de ambas vueltas superpuestos en las curvas donde más tiempo pierdes.",
    )

    with st.expander("⚙️ Ajustes avanzados"):
        step_m     = st.slider(
            "Precisión del análisis (metros entre puntos)",
            1, 20, 5,
            help="Valor más bajo = análisis más fino pero más lento. 5 m es suficiente para la mayoría de pistas.",
        )
        charts_top = st.number_input(
            "Cuántas curvas mostrar en las gráficas",
            1, 20, 5,
            help="Muestra las N curvas donde más tiempo pierdes.",
        )

    if st.button("Comparar ahora", type="primary"):
        with st.spinner("Comparando vuelta metro a metro…"):
            try:
                from fantasma.core.compare import compare
                trace, rows, summary = compare(ref_lap, drv_lap,
                                               step=float(step_m), corners=corners)
                st.session_state.update({"trace": trace, "rows": rows, "summary": summary})
            except Exception as _e:
                st.error("Error en comparación: %s" % _e)

    if "summary" in st.session_state:
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
            "**Vel. mínima** = velocidad más baja en el ápex de la curva. "
            "**Diferencia km/h** = cuánto más rápido/lento vas en el ápex vs la referencia. "
            "**Tiempo ganado/perdido** = impacto en el tiempo de vuelta (negativo = ganas tiempo)."
        )
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)[["name", "apex_d", "ref_vmin", "drv_vmin",
                                     "d_vmin", "time_lost", "flags"]]
            df.columns = [
                "Curva", "Ápex (metro)", "Vel. mín. referencia (km/h)",
                "Tu vel. mínima (km/h)", "Diferencia km/h",
                "Tiempo ganado/perdido (s)", "Avisos",
            ]
            st.dataframe(df.style.format({
                "Tiempo ganado/perdido (s)": "{:+.3f}",
                "Diferencia km/h":           "{:+.0f}",
            }), use_container_width=True, hide_index=True)

        if gen_charts:
            st.divider()
            st.subheader("Gráficas por curva")
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
                    st.info("matplotlib no instalado — ejecuta: pip install 'fantasma-inputs[charts]'")
                except Exception as _e:
                    st.error("Error en gráficas: %s" % _e)

        st.divider()
        if st.button("Ir al Paso 3 — Generar overlay →", type="primary"):
            _go(2)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 2:
    st.markdown('<div class="step-header">Paso 3 — Generar overlay HUD</div>', unsafe_allow_html=True)
    st.caption(
        "El overlay es un video transparente con el HUD animado (velocímetro, barras de gas/freno, "
        "delta de tiempo vs la referencia). En el Paso 4 lo pegas encima de tu grabación."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(0)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    col_a, col_b = st.columns(2)
    fps = col_a.selectbox(
        "Fotogramas por segundo (FPS)",
        [24, 30, 60], index=1,
        help="Usa el mismo valor que tiene tu grabación. La mayoría de cámaras graban a 30 o 60 fps.",
    )
    fmt = col_b.selectbox(
        "Formato del overlay",
        ["webm", "prores", "png"],
        index=0,
        help=(
            "webm — Recomendado: compatible con cualquier editor, archivo más pequeño.\n"
            "prores — Para Final Cut Pro o DaVinci Resolve en Mac.\n"
            "png — Solo los fotogramas sin codificar (uso avanzado)."
        ),
    )

    all_laps = st.checkbox(
        "Generar overlay para TODAS las vueltas seleccionadas en el Paso 1",
        help="Genera un overlay por cada vuelta que marcaste. Útil para revisar varias vueltas de una sesión.",
    )

    out_dir = st.text_input(
        "Carpeta donde guardar el overlay",
        value=os.path.join(os.path.expanduser("~"), "fantasma_salida"),
        help="El overlay se guardará aquí. La carpeta se crea automáticamente si no existe.",
    )

    _ndrv = len(st.session_state.get("drv_selected_laps", [drv_lap]))
    if all_laps and _ndrv > 1:
        st.info(
            "Se generarán %d overlays (uno por vuelta). "
            "Tiempo estimado: %d–%d minutos." % (_ndrv, _ndrv * 15, _ndrv * 30)
        )
    else:
        st.info("El render puede tardar 15–30 min para una vuelta completa del Nordschleife.")

    if st.button("Generar overlay", type="primary"):
        os.makedirs(out_dir, exist_ok=True)
        progress_bar = st.progress(0, text="Iniciando…")

        def _progress(n, total):
            pct = n / total if total else 0
            progress_bar.progress(pct, text="Frame %d / %d (%.0f%%)" % (n, total, pct * 100))

        try:
            from fantasma.viz.overlay import render_overlay
            if all_laps:
                laps_to_render = st.session_state.get("drv_selected_laps") or [drv_lap]
                webms = []
                for i, lap in enumerate(laps_to_render):
                    st.write("Vuelta %d/%d — %s" % (i + 1, len(laps_to_render), _fmt_lap(lap.laptime)))
                    lap_dir = os.path.join(out_dir, "lap_%02d" % i)
                    os.makedirs(lap_dir, exist_ok=True)
                    webms.append(render_overlay(ref_lap, lap, corners or [], lap_dir,
                                                fps=fps, fmt=fmt, progress=_progress))
            else:
                webms = [render_overlay(ref_lap, drv_lap, corners or [], out_dir,
                                        fps=fps, fmt=fmt, progress=_progress)]

            progress_bar.progress(1.0, text="Completado")
            st.success("✓ Overlay generado en:")
            for w in webms:
                st.code(w)
            st.session_state["last_overlay"] = webms[0]
            st.divider()
            if st.button("Ir al Paso 4 — Componer video →", type="primary"):
                _go(3)
        except ImportError:
            st.error("Faltan dependencias. Ejecuta en la terminal: pip install 'fantasma-inputs[overlay]'")
        except Exception as _e:
            st.error("Error: %s" % _e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — COMPONER
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 3:
    st.markdown('<div class="step-header">Paso 4 — Componer video final</div>', unsafe_allow_html=True)
    st.caption(
        "Aquí juntas el overlay del Paso 3 con tu video de grabación. "
        "El resultado es un MP4 con el HUD ya integrado, listo para subir o compartir."
    )

    st.info(
        "📂 Escribe la ruta completa de cada archivo. "
        "Si no sabes la ruta, abre la carpeta en el Explorador de Windows, "
        "haz clic en la barra de dirección y copia el texto.",
        icon="ℹ️",
    )

    col1, col2 = st.columns(2)
    video_path   = col1.text_input(
        "Tu video de grabación",
        placeholder=r"C:\Videos\mi_vuelta.mp4",
        help="El video que grabaste mientras corrías (OBS, ShadowPlay, cámara de cabina…).",
    )
    overlay_path = col2.text_input(
        "El overlay generado en el Paso 3",
        value=st.session_state.get("last_overlay", ""),
        placeholder=r"C:\Users\TuNombre\fantasma_salida\overlay.webm",
        help="El archivo .webm o .mov que generó SimGhostInputs.",
    )

    st.divider()
    col3, col4, col5 = st.columns(3)
    _pos_display = list(_POS_LABELS.keys())
    _pos_sel = col3.selectbox(
        "Posición del HUD en pantalla",
        _pos_display,
        index=0,
        help="Esquina donde aparecerá el HUD sobre tu video.",
    )
    position = _POS_LABELS[_pos_sel]

    offset = col4.number_input(
        "Retraso del HUD (segundos)",
        value=0.0, step=0.5,
        help=(
            "Si tu grabación empieza antes de cruzar la meta, pon aquí cuántos segundos "
            "pasan desde el inicio del video hasta que comienza la vuelta. "
            "Ejemplo: si empiezas a grabar 10 s antes de cruzar la línea, pon 10."
        ),
    )
    scale = col5.slider(
        "Tamaño del HUD",
        0.25, 1.5, 1.0, 0.05,
        help="1.0 = tamaño original. Reduce si el HUD tapa demasiado, aumenta si se ve pequeño.",
    )

    out_path = st.text_input(
        "Archivo de salida (opcional)",
        placeholder=r"C:\Videos\mi_vuelta_con_hud.mp4",
        help="Si lo dejas vacío, el archivo se guarda en la misma carpeta que tu video con el sufijo _composed.",
    )

    st.divider()
    if st.button(
        "Componer video",
        type="primary",
        disabled=not (video_path and overlay_path),
    ):
        if not out_path:
            base     = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(os.path.dirname(video_path), base + "_composed.mp4")

        with st.spinner("Componiendo con ffmpeg… (puede tardar unos minutos)"):
            try:
                from fantasma.viz.compose import compose_video
                result = compose_video(video_path, overlay_path, out_path,
                                       position=position, offset=offset, scale=scale)
                st.success("✓ Video compuesto guardado en:")
                st.code(result)
                st.balloons()
            except RuntimeError as _e:
                st.error(str(_e))
            except Exception as _e:
                st.error("Error al componer: %s" % _e)
