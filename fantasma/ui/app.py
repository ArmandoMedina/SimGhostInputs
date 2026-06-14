"""UI local de SimGhostInputs — corre con: fantasma ui (o streamlit run app.py).

Pasos disponibles:
  0. Inicio    — guía de exportación y selector de flujo
  1. Importar  — cargar archivos de referencia y piloto
  2. Comparar  — delta por metro, tabla por curva, gráficas  (solo en flujos de análisis)
  3. Overlay   — generar el HUD animado (webm con alfa)
  4. Componer  — superponer el overlay sobre el video de grabación

Flujos predefinidos (el usuario elige en el Paso 0):
  📊 Solo análisis      → 0 → 1 → 2
  🎬 Solo overlay       → 0 → 1 → 3
  🎥 Video con HUD      → 0 → 1 → 3 → 4  (default)
  Los pasos fuera del flujo elegido quedan accesibles desde el sidebar como opcionales.
"""
import json
import os
import tempfile

import streamlit as st

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
    ck = "file_%s" % uploaded_file.file_id
    if ck not in st.session_state:
        with st.spinner("Leyendo archivo…"):
            try:
                path = _save_upload(uploaded_file, os.path.splitext(uploaded_file.name)[1])
                laps = _load_laps(path)
                st.session_state[ck] = {"path": path, "laps": laps, "ok": True}
            except Exception as _e:
                st.session_state[ck] = {"path": "", "laps": [], "ok": False, "err": str(_e)}
    return st.session_state[ck]


def _img_or_placeholder(rel_path, caption):
    """Muestra imagen si existe, si no un placeholder con la descripción."""
    full = os.path.join(os.path.dirname(__file__), "..", "..", rel_path)
    if os.path.exists(full):
        st.image(full, caption=caption, use_container_width=True)
    else:
        st.info("📷 **Imagen pendiente:** %s" % caption)


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

# ── flujos disponibles ────────────────────────────────────────────────────────
# Cada flujo define qué pasos son relevantes y qué entregables produce.
# Overlay (3) y Componer (4) no dependen de Comparar (2): se desbloquean desde Importar.
_FLOWS = {
    "📊 Solo análisis": {
        "desc": "Tabla por curva, gráficas ghost y reporte exportable. Sin video.",
        "deliverables": [
            "📄 `report.md` — resumen narrativo por curva",
            "📊 `corners_compare.csv` — datos por curva en CSV",
            "📈 `delta.csv` — delta continuo metro a metro",
            "🖼️ Gráficas PNG por curva",
        ],
        "steps": [0, 1, 2],
        "next": {1: 2, 2: None},
    },
    "🎬 Solo overlay": {
        "desc": "HUD animado (.webm con transparencia) para pegar tú mismo en tu editor de video.",
        "deliverables": [
            "🎬 `overlay.webm` — HUD transparente con alfa (velocímetro, gas, freno, delta)",
        ],
        "steps": [0, 1, 3],
        "next": {1: 3, 3: None},
    },
    "🎥 Video con HUD": {
        "desc": "El video final ya compuesto: tu grabación con el HUD integrado, listo para subir.",
        "deliverables": [
            "🎬 `overlay.webm` — HUD transparente con alfa",
            "🎥 `vuelta_composed.mp4` — tu grabación con el HUD ya integrado",
        ],
        "steps": [0, 1, 3, 4],
        "next": {1: 3, 3: 4, 4: None},
    },
}
_DEFAULT_FLOW = "🎥 Video con HUD"


# ── navegación ────────────────────────────────────────────────────────────────
if "nav_step" not in st.session_state:
    st.session_state["nav_step"] = 0
if "flow_key" not in st.session_state:
    st.session_state["flow_key"] = _DEFAULT_FLOW

_flow    = _FLOWS[st.session_state["flow_key"]]
_STEPS   = ["Inicio", "Importar", "Comparar", "Overlay", "Componer"]

def _step_done(i):
    return bool([
        "flow_key" in st.session_state,
        "ref_lap"  in st.session_state,
        "summary"  in st.session_state,
        "last_overlay" in st.session_state,
        False,
    ][i])

def _step_in_flow(i):
    return i in _flow["steps"]

def _step_unlocked(i):
    if i == 0: return True
    if i == 1: return True
    if i == 2: return "ref_lap" in st.session_state
    if i == 3: return "ref_lap" in st.session_state
    if i == 4: return "last_overlay" in st.session_state
    return False

def _go(i):
    st.session_state["nav_step"] = i
    st.rerun()

def _next_step_btn(current_step_idx):
    """Botón 'siguiente paso' adaptado al flujo elegido."""
    next_i = _flow["next"].get(current_step_idx)
    if next_i is None:
        st.success("✅ ¡Completaste todos los pasos de tu flujo!")
    else:
        label = "Ir al Paso %d — %s →" % (next_i, _STEPS[next_i])
        if st.button(label, type="primary"):
            _go(next_i)


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("👻 SimGhostInputs")
    st.caption("Análisis de inputs de simracing por distancia")
    st.divider()
    for _i, _lbl in enumerate(_STEPS):
        _current    = st.session_state["nav_step"] == _i
        _done       = _step_done(_i)
        _in_flow    = _step_in_flow(_i)
        _unlocked   = _step_unlocked(_i)
        _icon       = "▶️" if _current else ("✅" if _done else ("○" if _in_flow else "·"))
        _suffix     = "" if _in_flow else "  *(opcional)*"
        if st.button(
            "%s  %d · %s%s" % (_icon, _i, _lbl, _suffix),
            disabled=not _unlocked,
            use_container_width=True,
            key="nav_%d" % _i,
        ):
            _go(_i)
    st.divider()
    st.caption("Flujo: **%s**" % st.session_state["flow_key"])
    st.caption("Tus datos nunca salen de tu máquina.")

step_idx = st.session_state["nav_step"]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 0 — INICIO
# ══════════════════════════════════════════════════════════════════════════════
if step_idx == 0:
    st.markdown('<div class="step-header">👻 Bienvenido a SimGhostInputs</div>', unsafe_allow_html=True)
    st.caption("Compara tus inputs de simracing contra una vuelta de referencia, curva a curva.")

    # ── cómo exportar telemetría ──────────────────────────────────────────────
    st.subheader("① Cómo exportar tu telemetría")
    st.markdown(
        "SimGhostInputs lee archivos **CSV o XLSX** exportados desde **Sim To MoTeC** "
        "(un plugin gratuito que captura telemetría mientras corres en el sim)."
    )

    with st.expander("Ver guía de exportación paso a paso", expanded=False):
        st.markdown("### 1. Instalar y abrir Sim To MoTeC")
        st.markdown(
            "Descarga e instala **[Sim To MoTeC](https://github.com/GeekyDeaks/sim-to-motec/releases)** "
            "(AMS2 logger). Compatible con AMS2, ACC, iRacing, rFactor 2 y más. "
            "Una vez instalado, ábrelo antes de arrancar el sim."
        )
        _img_or_placeholder("docs/guide/s2m_01_install.png",
                            "AMS2 logger v1.8.6 — la app lista antes de iniciar la sesión")

        st.markdown("### 2. Configurar y arrancar la captura")
        st.markdown(
            "Ajusta **Sampling Frequency a 20 Hz** y haz clic en **Start**. "
            "El logger queda en espera hasta que AMS2 arranque — "
            "verás los campos Vehicle, Venue y Lap rellenarse automáticamente al entrar en pista."
        )
        _img_or_placeholder("docs/guide/s2m_02_config.png",
                            "Sampling Frequency: 20 Hz · Log File: Not Started · Start activado")

        st.markdown("### 3. Después de la sesión: abrir MoTeC i2")
        st.markdown(
            "Abre **MoTeC i2 Standard** (se instala junto con Sim To MoTeC). "
            "Ve a **File → Open Log File** y abre el `.ld` generado por el logger "
            "(normalmente en `Documentos/MoTeC/`)."
        )
        _img_or_placeholder("docs/guide/s2m_03_i2_main.png",
                            "MoTeC i2 — File → Export Data...")

        st.markdown("### 4. Exportar como CSV")
        st.markdown(
            "En MoTeC i2: **File → Export Data...**  \n"
            "Opciones recomendadas:  \n"
            "- **Data Extent:** Entire Outing  \n"
            "- **Output File Format:** CSV File  \n"
            "- **Output Sample Rate:** Auto  \n"
            "- ✅ Include Time Stamp  \n"
            "- ✅ Include Distance Data  \n\n"
            "Haz clic en **Export** y guarda el archivo."
        )
        _img_or_placeholder("docs/guide/s2m_04_export.gif",
                            "File → Export Data → opciones recomendadas → Export")

        st.info(
            "💡 Exporta dos archivos: uno con la **vuelta de referencia** "
            "(tu mejor tiempo, o la de un coach) y otro con **tus vueltas de la sesión**."
        )

    st.divider()

    # ── ¿qué quieres obtener hoy? ─────────────────────────────────────────────
    st.subheader("② ¿Qué quieres obtener hoy?")
    st.caption("Elige tu objetivo y la UI te guiará solo por los pasos que necesitas.")

    _flow_keys = list(_FLOWS.keys())
    _cols = st.columns(len(_flow_keys))
    for _ci, (_fk, _fv) in enumerate(_FLOWS.items()):
        with _cols[_ci]:
            _selected = st.session_state["flow_key"] == _fk
            _border   = "2px solid #00c853" if _selected else "1px solid #3d4450"
            st.markdown(
                "<div style='border:%s; border-radius:10px; padding:1rem; min-height:200px'>" % _border,
                unsafe_allow_html=True,
            )
            st.markdown("### %s" % _fk)
            st.caption(_fv["desc"])
            st.markdown("**Obtienes:**")
            for _d in _fv["deliverables"]:
                st.markdown("- %s" % _d)
            st.markdown("</div>", unsafe_allow_html=True)
            if not _selected:
                if st.button("Elegir este", key="flow_%d" % _ci, use_container_width=True):
                    st.session_state["flow_key"] = _fk
                    _flow = _FLOWS[_fk]
                    st.rerun()
            else:
                st.success("✓ Seleccionado")

    st.divider()
    if st.button("Empezar — Ir a Importar →", type="primary"):
        _go(1)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — IMPORTAR
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 1:
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
    _ref_auto_i = _best_lap_index(_ref_laps)
    _ref_sel_i  = st.session_state.get("ref_sel_%s" % ref_file.file_id, _ref_auto_i)
    _ref_sel_i  = min(_ref_sel_i, len(_ref_laps) - 1)

    st.success("✓ **Referencia:** %s" % _fmt_lap(_ref_laps[_ref_sel_i].laptime))

    if len(_ref_laps) > 1:
        with st.expander("Cambiar vuelta de referencia (%d vueltas en el archivo)" % len(_ref_laps)):
            st.caption("Marca **solo una**. 🏆 = más rápida · ⚠️ = incompleta")
            _ref_tbl = _lap_table(_ref_laps, editor_key="ref_lap_tbl")
            if len(_ref_tbl) == 0:
                st.warning("Marca una vuelta.")
            elif len(_ref_tbl) > 1:
                st.error("Solo puedes marcar **una** vuelta como referencia.")
            else:
                _ref_sel_i = _ref_tbl[0]
                st.session_state["ref_sel_%s" % ref_file.file_id] = _ref_sel_i
                if _ref_tbl[0] != _ref_auto_i:
                    st.info("Usando Vuelta #%d — %s" % (_ref_tbl[0], _fmt_lap(_ref_laps[_ref_tbl[0]].laptime)))

    # ── ② Tu telemetría ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("② Tu archivo de telemetría")
    st.caption("Tus vueltas de la sesión. Se usa automáticamente la más rápida.")
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

    _drv_auto_i = _best_lap_index(_drv_laps)
    _drv_sel_i  = st.session_state.get("drv_sel_%s" % drv_file.file_id, _drv_auto_i)
    _drv_sel_i  = min(_drv_sel_i, len(_drv_laps) - 1)

    st.success("✓ **Tu vuelta:** %s" % _fmt_lap(_drv_laps[_drv_sel_i].laptime))

    if len(_drv_laps) > 1:
        with st.expander("Cambiar vuelta (%d vueltas en el archivo)" % len(_drv_laps)):
            st.caption("Marca **solo una**. 🏆 = más rápida · ⚠️ = incompleta")
            _drv_tbl = _lap_table(_drv_laps, editor_key="drv_lap_tbl")
            if len(_drv_tbl) == 0:
                st.warning("Marca una vuelta.")
            elif len(_drv_tbl) > 1:
                st.error("Solo puedes marcar **una** vuelta aquí.")
            else:
                _drv_sel_i = _drv_tbl[0]
                st.session_state["drv_sel_%s" % drv_file.file_id] = _drv_sel_i
                if _drv_tbl[0] != _drv_auto_i:
                    st.info("Usando Vuelta #%d — %s" % (_drv_tbl[0], _fmt_lap(_drv_laps[_drv_tbl[0]].laptime)))

    # ── Opciones avanzadas ────────────────────────────────────────────────────
    _ref_col_map  = None
    _corners_file = None
    _flow_has_analysis = 2 in _flow["steps"]
    with st.expander("⚙️ Opciones avanzadas — curvas y mapeo de columnas"):
        st.markdown("**Nombres de curvas** *(opcional)*")
        if _flow_has_analysis:
            st.caption("Si tienes un corners.json o quieres detectarlos, el reporte y el HUD mostrarán los nombres reales.")
        else:
            st.caption("Si tienes un corners.json o quieres detectarlos, los nombres aparecerán en los paneles del HUD.")
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
            st.caption("Edita los nombres directamente:")
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
        st.markdown("**Mapeo de columnas** *(solo si el archivo no se leyó correctamente)*")
        _pairs = st.text_area(
            "Columnas", key="ref_map",
            placeholder="Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time\n  velocidad = speed",
        )
        if _pairs.strip():
            _ref_col_map = dict(p.partition("=")[::2] for p in _pairs.splitlines() if "=" in p)

    # ── Cargar ────────────────────────────────────────────────────────────────
    _next_1 = _flow["next"].get(1)
    _load_labels = {2: "Cargar y ver análisis →", 3: "Cargar y generar overlay →"}
    _load_label  = _load_labels.get(_next_1, "Cargar →")

    st.divider()
    if st.button(_load_label, type="primary"):
        with st.spinner("Procesando…"):
            try:
                ref_lap = _ref_laps[_ref_sel_i]
                drv_lap = _drv_laps[_drv_sel_i]
                corners = st.session_state.get("corners")
                if _corners_file:
                    corners = _corners_from_json(_corners_file)
                st.session_state.update({
                    "ref_path":      _ref_path,
                    "drv_path":      _dc["path"],
                    "ref_laps":      _ref_laps,
                    "drv_laps":      _drv_laps,
                    "ref_lap":       ref_lap,
                    "drv_lap":       drv_lap,
                    "corners":       corners,
                    "ref_col_map":   _ref_col_map,
                    "needs_compare": _next_1 == 2,
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


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — COMPARAR
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 2:
    st.markdown('<div class="step-header">Paso 2 — Análisis por curva</div>', unsafe_allow_html=True)

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(1)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    if st.session_state.pop("needs_compare", False) and "summary" not in st.session_state:
        with st.spinner("Comparando vuelta metro a metro…"):
            try:
                from fantasma.core.compare import compare
                _t, _r, _s = compare(ref_lap, drv_lap, step=10.0, corners=corners)
                st.session_state.update({"trace": _t, "rows": _r, "summary": _s})
                st.session_state.pop("charts_paths", None)
            except Exception as _e:
                st.error("Error en comparación: %s" % _e)

    _c1, _c2 = st.columns(2)
    _c1.info("🏁 **Referencia:** %s · %s" % (
        os.path.basename(st.session_state.get("ref_path", "—")), _fmt_lap(ref_lap.laptime)))
    _c2.info("🧑‍💻 **Tu vuelta:** %s · %s" % (
        os.path.basename(st.session_state.get("drv_path", "—")), _fmt_lap(drv_lap.laptime)))

    with st.expander("⚙️ Recalcular con otros ajustes"):
        st.caption("Ajusta la resolución y las gráficas del **reporte de análisis**. No afecta el overlay (que usa su propia resolución interna).")
        _gen_charts = st.checkbox("Generar gráficas por curva", value=True)
        if not _gen_charts:
            st.caption("Sin gráficas — solo la tabla resumen.")
        _col_sl, _col_n = st.columns(2)
        _track_m = int(ref_lap.length)
        _step_m  = _col_sl.slider(
            "Metros entre puntos (resolución del análisis)", 1, 20, 10,
            help=(
                "Controla la granularidad del reporte y la tabla por curva. "
                "No afecta el overlay (usa 5 m fijos internamente). "
                "A 150 km/h, 10 m = una medición cada ~0.24 s. "
                "💡 Prueba con una vuelta primero para estimar cuánto tarda en tu PC."
            ),
        )
        _frames = max(1, _track_m // int(_step_m))
        _rel    = _frames / max(1, _track_m // 10)
        _col_sl.caption(
            "Esta pista: **~%s puntos** (%.1f× %s que con 10 m)"
            % ("{:,}".format(_frames), _rel, "más" if _rel > 1 else "menos")
        )
        _charts_top = _col_n.number_input("Curvas en gráficas", 1, 20, 5)
        if st.button("Recalcular", type="primary"):
            with st.spinner("Comparando…"):
                try:
                    from fantasma.core.compare import compare
                    _t, _r, _s = compare(ref_lap, drv_lap, step=float(_step_m), corners=corners)
                    st.session_state.update({"trace": _t, "rows": _r, "summary": _s,
                                             "charts_top": int(_charts_top),
                                             "gen_charts": _gen_charts})
                    st.session_state.pop("charts_paths", None)
                except Exception as _e:
                    st.error("Error: %s" % _e)

    _gen_charts = st.session_state.get("gen_charts", True)
    _charts_top = st.session_state.get("charts_top", 5)

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
        "**Vel. mínima** = velocidad en el ápex. "
        "**Diferencia km/h** = cuánto más rápido/lento vs referencia. "
        "**Tiempo ganado/perdido** = impacto en el crono."
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
        st.subheader("Gráficas de análisis")

        # Generate once per comparison; cache invalidated by compare/recalculate.
        # Error messages are set outside the spinner so they survive the rerun cycle.
        if "charts_paths" not in st.session_state:
            _charts_import_err = False
            _charts_gen_err = None
            with st.spinner("Generando gráficas…"):
                try:
                    _out = tempfile.mkdtemp()
                    from fantasma.viz.charts import render_charts
                    st.session_state["charts_paths"] = render_charts(
                        trace, rows, corners or [], _out, top=int(_charts_top)
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

            # -- Resumen de vuelta: delta map + time loss bar (side by side)
            _overview = _charts_of("delta_map") + _charts_of("time_loss_bar")
            if _overview:
                st.markdown("**Resumen de vuelta**")
                _ov_cols = st.columns(len(_overview))
                for _i, _p in enumerate(_overview):
                    _show(_ov_cols[_i], _p)

            # -- Círculo de fricción G-G (centrado)
            _gg = _charts_of("gg_diagram")
            if _gg:
                st.markdown("**Círculo de fricción (G-G)**")
                _, _gc, _ = st.columns([1, 2, 1])
                _show(_gc, _gg[0])

            # -- Vista multi-canal de vuelta completa (ancho completo)
            _full = _charts_of("full_lap")
            if _full:
                st.markdown("**Vista completa de la vuelta — todos los canales**")
                _show(st, _full[0])

            # -- Curvas: grid 2 columnas
            _corners_charts = _charts_of("curva_")
            if _corners_charts:
                st.markdown("**Curvas con mayor pérdida de tiempo**")
                _cc = st.columns(2)
                for _i, _p in enumerate(_corners_charts):
                    _show(_cc[_i % 2], _p)

            # -- Zonas de frenada: grid 2 columnas
            _brakes = _charts_of("frenada_")
            if _brakes:
                st.markdown("**Detalle de zonas de frenada**")
                _bc = st.columns(2)
                for _i, _p in enumerate(_brakes):
                    _show(_bc[_i % 2], _p)

    st.divider()
    _next_step_btn(2)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 3:
    st.markdown('<div class="step-header">Paso 3 — Generar overlay HUD</div>', unsafe_allow_html=True)
    st.caption(
        "Genera un video transparente con el HUD animado (velocímetro, barras de gas/freno, delta). "
        "En el Paso 4 lo pegas encima de tu grabación."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(1)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners")

    if "last_overlay" in st.session_state:
        st.success("✓ Ya tienes un overlay generado: `%s`" % st.session_state["last_overlay"])
        _next_step_btn(3)
        st.divider()

    _all_drv_laps    = st.session_state.get("drv_laps", [drv_lap])
    _complete_laps   = [l for l in _all_drv_laps if l.meta.get("is_complete")]
    _has_multi       = len(_complete_laps) > 1
    all_laps = False
    if _has_multi:
        all_laps = st.checkbox(
            "Generar overlay para TODAS las vueltas completas del archivo (%d vueltas)" % len(_complete_laps),
            help="Genera un overlay por cada vuelta completa detectada en tu archivo, sin necesidad de seleccionarlas antes.",
        )
        if all_laps:
            st.info("Se generarán %d overlays. Tiempo estimado: %d–%d min." % (
                len(_complete_laps), len(_complete_laps) * 15, len(_complete_laps) * 30))

    out_dir = st.text_input(
        "Carpeta de salida",
        value=os.path.join(os.path.expanduser("~"), "fantasma_salida"),
        help="Se crea automáticamente si no existe.",
    )

    with st.expander("⚙️ Opciones avanzadas"):
        _col_a, _col_b = st.columns(2)
        _fps = _col_a.selectbox(
            "Fotogramas por segundo (FPS)", [24, 30, 60], index=1,
            help="Usa el mismo valor que tiene tu grabación.",
        )
        _fmt = _col_b.selectbox(
            "Formato del overlay", ["webm", "prores", "png"], index=0,
            help=(
                "webm — Recomendado: compatible con cualquier editor.\n"
                "prores — Para Final Cut Pro o DaVinci Resolve en Mac.\n"
                "png — Solo fotogramas sin codificar (uso avanzado)."
            ),
        )

    st.info("El render puede tardar 15–30 min por vuelta. Tu PC seguirá disponible, solo más lenta.")

    if st.button("Generar overlay", type="primary"):
        os.makedirs(out_dir, exist_ok=True)
        _bar = st.progress(0, text="Iniciando…")

        def _progress(n, total, status=None):
            pct = min(n / total, 1.0) if total else 0
            label = status if status else "Frame %d / %d (%.0f%%)" % (n, total, pct * 100)
            _bar.progress(pct, text=label)

        try:
            from fantasma.viz.overlay import render_overlay
            if all_laps:
                _webms = []
                for _i, _lap in enumerate(_complete_laps):
                    st.write("Vuelta %d/%d — %s" % (_i + 1, len(_complete_laps), _fmt_lap(_lap.laptime)))
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
            _next_step_btn(3)
        except ImportError:
            st.error("Faltan dependencias. Ejecuta: pip install 'fantasma-inputs[overlay]'")
        except Exception as _e:
            st.error("Error: %s" % _e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — COMPONER
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 4:
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

    # ── auto-sync ─────────────────────────────────────────────────────────────
    st.divider()
    with st.expander("🔍 Detectar sincronía automáticamente *(opcional — requiere scipy)*"):
        st.caption(
            "Compara el audio del video con los canales RPM/velocidad de la telemetría "
            "para calcular el offset exacto. Precisión ~0.5 s. "
            "Si ya cargaste telemetría en el Paso 1 se usa directamente."
        )
        _drv_for_sync = st.session_state.get("drv_lap")
        _sc_col1, _sc_col2 = st.columns([2, 1])
        with _sc_col1:
            if _drv_for_sync is None:
                _sync_up = st.file_uploader(
                    "Telemetría del piloto (CSV o XLSX)", type=["csv", "xlsx"],
                    key="sync_drv_upload",
                )
                if _sync_up:
                    _sc = _cache_file(_sync_up)
                    if _sc["ok"] and _sc["laps"]:
                        from fantasma.core.normalize import fastest_lap as _fl
                        _drv_for_sync = _fl(_sc["laps"])
            else:
                st.info("Usando vuelta cargada en el Paso 1.")
        with _sc_col2:
            _can_sync = bool(_video_path and _drv_for_sync)
            if st.button("Detectar offset", disabled=not _can_sync, key="btn_autosync"):
                with st.spinner("Analizando audio del video… (~30 s)"):
                    try:
                        from fantasma.viz.sync import auto_sync
                        _det = auto_sync(_video_path, _drv_for_sync)
                        st.session_state["_autosync_detected"] = _det
                        st.session_state["compose_offset"]     = _det
                    except ImportError as _ie:
                        st.error(str(_ie))
                    except Exception as _se:
                        st.error("Error en auto-sync: %s" % _se)

        if "_autosync_detected" in st.session_state:
            st.success(
                "Offset detectado: **%.3f s** — pre-cargado en «Retraso del HUD»." %
                st.session_state["_autosync_detected"]
            )

    # ── parametros de composicion ──────────────────────────────────────────────
    st.divider()
    _col3, _col4, _col5 = st.columns(3)
    _pos_sel  = _col3.selectbox("Posición del HUD en pantalla", list(_POS_LABELS.keys()))
    _position = _POS_LABELS[_pos_sel]
    _offset   = _col4.number_input(
        "Retraso del HUD (segundos)",
        value=st.session_state.get("compose_offset", 0.0),
        step=0.1,
        key="compose_offset",
        help=(
            "Cuántos segundos pasan desde el inicio del video hasta que empieza la vuelta. "
            "Ejemplo: si empiezas a grabar 10 s antes de cruzar la meta, pon 10. "
            "«Detectar offset» rellena este campo automáticamente."
        ),
    )
    _scale = _col5.slider("Tamaño del HUD", 0.25, 1.5, 1.0, 0.05,
                           help="1.0 = tamaño original.")

    _out_path = st.text_input(
        "Archivo de salida *(opcional)*",
        placeholder=r"C:\Videos\mi_vuelta_con_hud.mp4",
        help="Si lo dejas vacío se guarda junto al video con el sufijo _composed.",
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
                _next_step_btn(4)
            except RuntimeError as _e:
                st.error(str(_e))
            except Exception as _e:
                st.error("Error: %s" % _e)
