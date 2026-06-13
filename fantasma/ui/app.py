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


def _best_lap_index(laps):
    best_i, best_t = 0, float("inf")
    for i, l in enumerate(laps):
        if l.meta.get("is_complete") and l.laptime < best_t:
            best_t, best_i = l.laptime, i
    return best_i


def _lap_table(laps, editor_key):
    """Tabla de selección de vueltas con checkboxes. Devuelve lista de índices marcados."""
    import pandas as _pd
    best_i = _best_lap_index(laps)
    rows = []
    for i, l in enumerate(laps):
        _c = l.meta.get("is_complete", False)
        rows.append({
            "Sel":    i == best_i,
            "#":      i,
            "Tiempo": _fmt_lap(l.laptime),
            "Metros": int(l.length),
            "Estado": "🏆 Más rápida" if i == best_i else ("✓ Completa" if _c else "⚠️ Incompleta"),
        })
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


def _cache_file(uploaded_file):
    """Carga y cachea un archivo subido por file_id. Devuelve dict con path y laps."""
    ck = "file_%s" % uploaded_file.file_id
    if ck not in st.session_state:
        with st.spinner("Leyendo archivo…"):
            try:
                path  = _save_upload(uploaded_file, os.path.splitext(uploaded_file.name)[1])
                laps  = _load_laps(path)
                st.session_state[ck] = {"path": path, "laps": laps, "ok": True}
            except Exception as _e:
                st.session_state[ck] = {"path": "", "laps": [], "ok": False, "err": str(_e)}
    return st.session_state[ck]


# ── posiciones del HUD ────────────────────────────────────────────────────────
_POS_LABELS = {
    "Abajo derecha":    "bottom-right",
    "Abajo izquierda":  "bottom-left",
    "Arriba derecha":   "top-right",
    "Arriba izquierda": "top-left",
    "Abajo centro":     "bottom-center",
    "Arriba centro":    "top-center",
    "Centro":           "center",
}


# ── navegación ────────────────────────────────────────────────────────────────
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
    has = "ref_lap" in st.session_state
    if i in (1, 2): return has
    if i == 3: return has and "last_overlay" in st.session_state
    return False

def _go(i):
    st.session_state["nav_step"] = i
    st.rerun()


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("👻 SimGhostInputs")
    st.caption("Análisis de inputs de simracing por distancia")
    st.divider()
    for _i, _lbl in enumerate(_STEP_LABELS):
        _current  = st.session_state["nav_step"] == _i
        _icon     = "▶️" if _current else ("✅" if _step_done(_i) else "○")
        if st.button(
            "%s  %d · %s" % (_icon, _i + 1, _lbl),
            disabled=not _step_unlocked(_i),
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
    st.caption("Sube dos archivos: la vuelta de referencia y la tuya. El resto es automático.")

    # ── ① Referencia ─────────────────────────────────────────────────────────
    st.subheader("① Vuelta de referencia")
    st.caption(
        "La vuelta contra la que te comparas — tu mejor tiempo anterior, "
        "la de un coach, o cualquier referencia que quieras superar."
    )

    ref_file = st.file_uploader("Archivo de referencia (CSV o XLSX)", type=["csv", "xlsx"], key="ref_upload")

    if not ref_file:
        st.info("⬆️ Sube la vuelta de referencia para continuar.")
        st.stop()

    _rc = _cache_file(ref_file)
    if not _rc["ok"]:
        st.error("No se pudo leer el archivo: %s" % _rc.get("err", ""))
        st.stop()

    _ref_laps = _rc["laps"]
    _ref_path = _rc["path"]

    # auto-selección: la más rápida completa
    _ref_auto_i = _best_lap_index(_ref_laps)
    _ref_sel_i  = st.session_state.get("ref_sel_override_%s" % ref_file.file_id, _ref_auto_i)
    _ref_sel_i  = min(_ref_sel_i, len(_ref_laps) - 1)

    st.success("✓ **Referencia:** %s" % _fmt_lap(_ref_laps[_ref_sel_i].laptime))

    if len(_ref_laps) > 1:
        with st.expander("Cambiar vuelta de referencia (%d vueltas en el archivo)" % len(_ref_laps)):
            st.caption("Marca **solo una** — la que quieres usar como referencia. 🏆 = más rápida · ⚠️ = incompleta")
            _ref_tbl = _lap_table(_ref_laps, editor_key="ref_lap_tbl")
            if len(_ref_tbl) == 0:
                st.warning("Marca una vuelta.")
            elif len(_ref_tbl) > 1:
                st.error("Solo puedes marcar **una** vuelta como referencia.")
            else:
                _ref_sel_i = _ref_tbl[0]
                st.session_state["ref_sel_override_%s" % ref_file.file_id] = _ref_sel_i
                if _ref_tbl[0] != _ref_auto_i:
                    st.info("Usando Vuelta #%d — %s" % (_ref_tbl[0], _fmt_lap(_ref_laps[_ref_tbl[0]].laptime)))

    # ── ② Tu telemetría ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("② Tu archivo de telemetría")
    st.caption(
        "Tus vueltas de la sesión. Se pre-selecciona la más rápida; "
        "puedes marcar varias si quieres generar overlay de toda la sesión."
    )

    drv_file = st.file_uploader("Tu archivo de telemetría (CSV o XLSX)", type=["csv", "xlsx"], key="drv_upload")

    if not drv_file:
        st.info("⬆️ Sube tu archivo de telemetría para continuar.")
        st.stop()

    _dc = _cache_file(drv_file)
    if not _dc["ok"]:
        st.error("No se pudo leer el archivo: %s" % _dc.get("err", ""))
        st.stop()

    _drv_laps = _dc["laps"]

    if not _drv_laps:
        st.warning("No se detectaron vueltas en el archivo.")
        st.stop()

    st.info(
        "Aquí **sí puedes marcar varias vueltas**. "
        "La primera marcada se usa en el análisis; las demás se incluyen si generas overlay de toda la sesión. "
        "🏆 = más rápida · ⚠️ = incompleta (out/in lap)"
    )
    _drv_sel = _lap_table(_drv_laps, editor_key="drv_lap_tbl")

    if not _drv_sel:
        st.warning("Marca al menos una vuelta para continuar.")
        st.stop()

    _drv_times = [_fmt_lap(_drv_laps[i].laptime) for i in _drv_sel if i < len(_drv_laps)]
    if len(_drv_sel) == 1:
        st.success("✓ **Tu vuelta:** %s" % _drv_times[0])
    else:
        st.success("✓ **%d vueltas seleccionadas:** %s" % (len(_drv_sel), " · ".join(_drv_times)))

    # ── Opciones avanzadas (curvas + mapeo de columnas) ───────────────────────
    _ref_col_map  = None
    _corners_file = None
    with st.expander("⚙️ Opciones avanzadas"):
        st.markdown("**Nombres de curvas** *(opcional)*")
        st.caption(
            "Si tienes un corners.json o quieres detectar las curvas automáticamente, "
            "el reporte mostrará nombres reales en lugar de C01, C02…"
        )
        _col_cj, _col_cd = st.columns(2)
        with _col_cj:
            _corners_file = st.file_uploader("Subir corners.json", type=["json"], key="corners_upload")
        with _col_cd:
            st.write(" ")
            if st.button("Detectar curvas automáticamente"):
                with st.spinner("Analizando vuelta de referencia…"):
                    try:
                        from fantasma.core.normalize import fastest_lap as _fl
                        from fantasma.core.corners import detect_corners as _dc2, extract_milestones as _em
                        _evs, _ = _dc2(_fl(_ref_laps))
                        _cdet   = _em(_fl(_ref_laps), _evs)
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
            st.caption("Edita los nombres directamente en la tabla:")
            _edited = st.data_editor(
                _pd2.DataFrame(_c_data),
                column_config={
                    "ID":     st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "Metro":  st.column_config.NumberColumn("Metro", disabled=True, width="small"),
                    "Nombre": st.column_config.TextColumn("Nombre de la curva", width="medium"),
                },
                hide_index=True, use_container_width=True, key="corners_editor",
            )
            for _i2, _row in _edited.iterrows():
                if _row["Nombre"]:
                    st.session_state["corners"][_i2]["name"] = _row["Nombre"]

        st.divider()
        st.markdown("**Mapeo de columnas** *(solo si el archivo dio error al cargar)*")
        st.caption("Formato: `nombre_en_tu_archivo = significado`, una por línea.")
        _pairs = st.text_area(
            "Columnas",
            placeholder="Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time\n  velocidad = speed",
            key="ref_map",
        )
        if _pairs.strip():
            _ref_col_map = dict(p.partition("=")[::2] for p in _pairs.splitlines() if "=" in p)

    # ── Cargar y ver análisis ─────────────────────────────────────────────────
    st.divider()
    if st.button("Cargar y ver análisis →", type="primary"):
        with st.spinner("Procesando…"):
            try:
                ref_lap      = _ref_laps[_ref_sel_i]
                drv_lap      = _drv_laps[_drv_sel[0]]
                drv_selected = [_drv_laps[i] for i in _drv_sel if i < len(_drv_laps)]
                corners      = st.session_state.get("corners")
                if _corners_file:
                    corners = _corners_from_json(_corners_file)

                st.session_state.update({
                    "ref_path":          _ref_path,
                    "drv_path":          _dc["path"],
                    "ref_laps":          _ref_laps,
                    "drv_laps":          _drv_laps,
                    "ref_lap":           ref_lap,
                    "drv_lap":           drv_lap,
                    "drv_selected_laps": drv_selected,
                    "corners":           corners,
                    "ref_col_map":       _ref_col_map,
                    "needs_compare":     True,   # dispara auto-compare en paso 2
                })
                _go(1)
            except Exception as _e:
                st.error("Error al cargar: %s" % _e)

    # resumen si ya hay datos cargados
    if "ref_lap" in st.session_state:
        _rl    = st.session_state["ref_lap"]
        _dl    = st.session_state["drv_lap"]
        _delta = _dl.laptime - _rl.laptime
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Referencia",  _fmt_lap(_rl.laptime))
        c2.metric("Longitud",    "%.0f m" % _rl.length)
        c3.metric("Tu vuelta",   _fmt_lap(_dl.laptime))
        c4.metric("Delta",       "%+.3f s" % _delta,
                  delta=round(-_delta, 3), delta_color="normal")
        if st.button("Ver análisis →", type="primary"):
            _go(1)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — COMPARAR
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 1:
    st.markdown('<div class="step-header">Paso 2 — Análisis por curva</div>', unsafe_allow_html=True)

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(0)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    # ── auto-compare al llegar desde el paso 1 ────────────────────────────────
    if st.session_state.pop("needs_compare", False) and "summary" not in st.session_state:
        with st.spinner("Comparando vuelta metro a metro…"):
            try:
                from fantasma.core.compare import compare
                _t, _r, _s = compare(ref_lap, drv_lap, step=10.0, corners=corners)
                st.session_state.update({"trace": _t, "rows": _r, "summary": _s})
            except Exception as _e:
                st.error("Error en comparación: %s" % _e)

    # ── resumen de laps comparados ────────────────────────────────────────────
    _c1, _c2 = st.columns(2)
    _c1.info("🏁 **Referencia:** %s · %s" % (
        os.path.basename(st.session_state.get("ref_path", "—")),
        _fmt_lap(ref_lap.laptime),
    ))
    _c2.info("🧑‍💻 **Tu vuelta:** %s · %s" % (
        os.path.basename(st.session_state.get("drv_path", "—")),
        _fmt_lap(drv_lap.laptime),
    ))

    # ── ajustes avanzados (recalcular) ────────────────────────────────────────
    with st.expander("⚙️ Recalcular con otros ajustes"):
        st.caption("Por defecto el análisis usa 10 m entre puntos y genera gráficas de las 5 peores curvas.")
        _gen_charts = st.checkbox("Generar gráficas por curva", value=True,
                                   help="Velocidad, gas y freno superpuestos en las curvas donde más pierdes.")
        if not _gen_charts:
            st.caption("Sin gráficas — solo verás la tabla resumen.")
        _col_sl, _col_n = st.columns(2)
        _track_m = int(ref_lap.length)
        _step_m  = _col_sl.slider(
            "Metros entre puntos", 1, 20, 10,
            help=(
                "Menos metros = más detalle, más tiempo. "
                "A 150 km/h, 10 m = una medición cada ~0.24 s. "
                "💡 Prueba primero con una vuelta para estimar cuánto tarda en tu PC."
            ),
        )
        _frames = max(1, _track_m // int(_step_m))
        _rel    = _frames / max(1, _track_m // 10)
        _col_sl.caption(
            "Esta pista: **~%s puntos** (%.1f× %s que con 10 m)"
            % ("{:,}".format(_frames), _rel, "más" if _rel > 1 else "menos")
        )
        _charts_top = _col_n.number_input("Curvas en gráficas", 1, 20, 5,
                                           help="Las N donde más tiempo pierdes.")
        if st.button("Recalcular", type="primary"):
            with st.spinner("Comparando…"):
                try:
                    from fantasma.core.compare import compare
                    _t, _r, _s = compare(ref_lap, drv_lap, step=float(_step_m), corners=corners)
                    st.session_state.update({"trace": _t, "rows": _r, "summary": _s,
                                             "charts_top": int(_charts_top),
                                             "gen_charts": _gen_charts})
                except Exception as _e:
                    st.error("Error: %s" % _e)
    else:
        _gen_charts = st.session_state.get("gen_charts", True)
        _charts_top = st.session_state.get("charts_top", 5)

    # ── resultados ────────────────────────────────────────────────────────────
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
        "**Vel. mínima** = velocidad en el ápex de la curva. "
        "**Diferencia km/h** = cuánto más rápido/lento vs referencia. "
        "**Tiempo ganado/perdido** = impacto en el tiempo de vuelta."
    )
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)[["name", "apex_d", "ref_vmin", "drv_vmin", "d_vmin", "time_lost", "flags"]]
        df.columns = ["Curva", "Ápex (m)", "Vel. mín. ref. (km/h)", "Tu vel. mín. (km/h)",
                      "Diferencia (km/h)", "Tiempo ganado/perdido (s)", "Avisos"]
        st.dataframe(df.style.format({
            "Tiempo ganado/perdido (s)": "{:+.3f}",
            "Diferencia (km/h)":         "{:+.0f}",
        }), use_container_width=True, hide_index=True)

    if _gen_charts:
        st.divider()
        st.subheader("Gráficas por curva")
        with st.spinner("Generando gráficas…"):
            try:
                _out = tempfile.mkdtemp()
                from fantasma.viz.charts import render_charts
                _charts = render_charts(trace, rows, corners or [], _out, top=int(_charts_top))
                _nc = min(len(_charts), 2)
                if _nc:
                    _cols = st.columns(_nc)
                    for _i, _p in enumerate(_charts):
                        _cols[_i % _nc].image(_p, use_container_width=True)
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
        "Genera un video transparente con el HUD animado (velocímetro, barras de gas/freno, delta). "
        "En el Paso 4 lo pegas encima de tu grabación."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(0)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    all_laps = st.checkbox(
        "Generar overlay para TODAS las vueltas seleccionadas en el Paso 1",
        help="Genera un overlay por cada vuelta que marcaste. Útil para revisar una sesión entera.",
    )
    _ndrv = len(st.session_state.get("drv_selected_laps", [drv_lap]))
    if all_laps and _ndrv > 1:
        st.info("Se generarán %d overlays. Tiempo estimado: %d–%d min." % (_ndrv, _ndrv * 15, _ndrv * 30))

    out_dir = st.text_input(
        "Carpeta de salida",
        value=os.path.join(os.path.expanduser("~"), "fantasma_salida"),
        help="El overlay se guardará aquí. Se crea automáticamente si no existe.",
    )

    with st.expander("⚙️ Opciones avanzadas"):
        _col_a, _col_b = st.columns(2)
        _fps = _col_a.selectbox(
            "Fotogramas por segundo (FPS)", [24, 30, 60], index=1,
            help="Usa el mismo valor que tiene tu grabación. La mayoría de cámaras graban a 30 o 60 fps.",
        )
        _fmt = _col_b.selectbox(
            "Formato del overlay", ["webm", "prores", "png"], index=0,
            help=(
                "webm — Recomendado: compatible con cualquier editor.\n"
                "prores — Para Final Cut Pro o DaVinci Resolve en Mac.\n"
                "png — Solo fotogramas, sin codificar (uso avanzado)."
            ),
        )

    st.info("El render puede tardar 15–30 min por vuelta. Tu PC seguirá disponible, solo más lenta.")

    if st.button("Generar overlay", type="primary"):
        os.makedirs(out_dir, exist_ok=True)
        _bar = st.progress(0, text="Iniciando…")

        def _progress(n, total):
            pct = n / total if total else 0
            _bar.progress(pct, text="Frame %d / %d (%.0f%%)" % (n, total, pct * 100))

        try:
            from fantasma.viz.overlay import render_overlay
            if all_laps:
                _laps_r = st.session_state.get("drv_selected_laps") or [drv_lap]
                _webms  = []
                for _i, _lap in enumerate(_laps_r):
                    st.write("Vuelta %d/%d — %s" % (_i + 1, len(_laps_r), _fmt_lap(_lap.laptime)))
                    _ld = os.path.join(out_dir, "lap_%02d" % _i)
                    os.makedirs(_ld, exist_ok=True)
                    _webms.append(render_overlay(ref_lap, _lap, corners or [], _ld,
                                                 fps=_fps, fmt=_fmt, progress=_progress))
            else:
                _webms = [render_overlay(ref_lap, drv_lap, corners or [], out_dir,
                                         fps=_fps, fmt=_fmt, progress=_progress)]

            _bar.progress(1.0, text="Completado")
            st.success("✓ Overlay generado en:")
            for _w in _webms:
                st.code(_w)
            st.session_state["last_overlay"] = _webms[0]
            st.divider()
            if st.button("Ir al Paso 4 — Componer video →", type="primary"):
                _go(3)
        except ImportError:
            st.error("Faltan dependencias. Ejecuta: pip install 'fantasma-inputs[overlay]'")
        except Exception as _e:
            st.error("Error: %s" % _e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — COMPONER
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 3:
    st.markdown('<div class="step-header">Paso 4 — Componer video final</div>', unsafe_allow_html=True)
    st.caption(
        "Junta el overlay del Paso 3 con tu video de grabación. "
        "El resultado es un MP4 con el HUD ya integrado."
    )
    st.info(
        "📂 Escribe la ruta completa de cada archivo. "
        "Si no sabes la ruta, abre la carpeta en el Explorador de Windows, "
        "haz clic en la barra de dirección y copia el texto."
    )

    _col1, _col2 = st.columns(2)
    _video_path   = _col1.text_input(
        "Tu video de grabación",
        placeholder=r"C:\Videos\mi_vuelta.mp4",
        help="El video que grabaste mientras corrías.",
    )
    _overlay_path = _col2.text_input(
        "El overlay generado en el Paso 3",
        value=st.session_state.get("last_overlay", ""),
        placeholder=r"C:\Users\TuNombre\fantasma_salida\overlay.webm",
    )

    st.divider()
    _col3, _col4, _col5 = st.columns(3)
    _pos_sel  = _col3.selectbox("Posición del HUD en pantalla", list(_POS_LABELS.keys()),
                                 help="Esquina donde aparecerá el HUD.")
    _position = _POS_LABELS[_pos_sel]
    _offset   = _col4.number_input(
        "Retraso del HUD (segundos)", value=0.0, step=0.5,
        help=(
            "Cuántos segundos pasan desde el inicio del video hasta que empieza la vuelta. "
            "Ejemplo: si empiezas a grabar 10 s antes de cruzar la meta, pon 10."
        ),
    )
    _scale = _col5.slider("Tamaño del HUD", 0.25, 1.5, 1.0, 0.05,
                           help="1.0 = tamaño original. Reduce si tapa demasiado.")

    _out_path = st.text_input(
        "Archivo de salida *(opcional — si lo dejas vacío se guarda junto al video)*",
        placeholder=r"C:\Videos\mi_vuelta_con_hud.mp4",
    )

    st.divider()
    if st.button("Componer video", type="primary", disabled=not (_video_path and _overlay_path)):
        if not _out_path:
            _base     = os.path.splitext(os.path.basename(_video_path))[0]
            _out_path = os.path.join(os.path.dirname(_video_path), _base + "_composed.mp4")

        with st.spinner("Composiendo con ffmpeg… (puede tardar unos minutos)"):
            try:
                from fantasma.viz.compose import compose_video
                _result = compose_video(_video_path, _overlay_path, _out_path,
                                        position=_position, offset=_offset, scale=_scale)
                st.success("✓ Video guardado en:")
                st.code(_result)
                st.balloons()
            except RuntimeError as _e:
                st.error(str(_e))
            except Exception as _e:
                st.error("Error: %s" % _e)
