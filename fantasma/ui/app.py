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
    best_i = _best_lap_index(laps)
    options = []
    for i, l in enumerate(laps):
        _c = l.meta.get("is_complete", False)
        estado = "🏆 Más rápida" if i == best_i else ("✓ Completa" if _c else "⚠️ Incompleta")
        options.append("#%d  ·  %s  ·  %dm  ·  %s" % (i, _fmt_lap(l.laptime), int(l.length), estado))
    sel = st.radio("", options, index=best_i, key=editor_key, label_visibility="collapsed")
    return [options.index(sel)]


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
_FLOWS = {
    "📊 Solo análisis": {
        "desc": "Tabla por curva, gráficas ghost y reporte exportable. No necesitas video.",
        "requires": [
            "📄 CSV de la vuelta de referencia",
            "📄 CSV de tus vueltas",
        ],
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
        "desc": "Genera el HUD transparente para pegarlo tú mismo en tu editor de video.",
        "requires": [
            "📄 CSV de la vuelta de referencia",
            "📄 CSV de tus vueltas",
        ],
        "deliverables": [
            "🎬 `overlay.webm` — HUD transparente con alfa (velocímetro, gas, freno, delta)",
        ],
        "steps": [0, 1, 3],
        "next": {1: 3, 3: None},
    },
    "🎥 Video con HUD": {
        "desc": "El video final ya compuesto: tu grabación con el HUD integrado, listo para subir.",
        "requires": [
            "📄 CSV de la vuelta de referencia",
            "📄 CSV de tus vueltas",
            "🎬 Tu video de grabación (.mp4/.mov) **con audio del motor activado**",
        ],
        "deliverables": [
            "🎬 `overlay.webm` — HUD transparente con alfa",
            "🎥 `vuelta_composed.mp4` — tu grabación recortada a la vuelta, con el HUD ya integrado",
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

    st.info(
        "**Una vuelta por flujo.** Cada vez que usas la app procesas exactamente una vuelta. "
        "Si tienes varias vueltas para analizar, al terminar el flujo el botón "
        "**«Procesar otra vuelta»** te devuelve aquí sin tener que recargar archivos ni la referencia."
    )

    # ── cómo exportar telemetría ──────────────────────────────────────────────
    st.subheader("① Antes de empezar: exporta tu telemetría")
    st.markdown(
        "SimGhostInputs necesita **archivos CSV** con los datos de la sesión. "
        "Se exportan desde **MoTeC i2** después de cada tanda usando el plugin gratuito **Sim To MoTeC**."
    )

    with st.expander("📋 Ver guía de exportación paso a paso", expanded=False):
        st.markdown("### 1. Instalar y abrir Sim To MoTeC")
        st.markdown(
            "Descarga e instala **[Sim To MoTeC](https://github.com/GeekyDeaks/sim-to-motec/releases)** "
            "(compatible con AMS2, ACC, iRacing, rFactor 2 y más). "
            "Ábrelo **antes** de arrancar el sim — captura en segundo plano mientras corres."
        )
        _img_or_placeholder("docs/guide/s2m_01_install.png",
                            "AMS2 logger v1.8.6 — la app lista antes de iniciar la sesión")

        st.markdown("### 2. Configurar y arrancar la captura")
        st.markdown(
            "Ajusta **Sampling Frequency a 20 Hz** y haz clic en **Start**. "
            "Los campos Vehicle, Venue y Lap se rellenan solos cuando entras en pista."
        )
        _img_or_placeholder("docs/guide/s2m_02_config.png",
                            "Sampling Frequency: 20 Hz · Log File: Not Started · Start activado")

        st.markdown("### 3. Abrir MoTeC i2 después de la sesión")
        st.markdown(
            "Abre **MoTeC i2 Standard** (se instala junto con Sim To MoTeC). "
            "Ve a **File → Open Log File** y abre el `.ld` que generó el logger "
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
            "💡 Exporta **dos archivos**: uno con la vuelta de referencia "
            "(tu mejor tiempo anterior, o la de un coach) y otro con **tus vueltas de la sesión de hoy**."
        )

    st.divider()

    # ── ¿qué quieres obtener hoy? ─────────────────────────────────────────────
    st.subheader("② ¿Qué quieres obtener hoy?")
    st.caption(
        "Elige el flujo que mejor describe tu objetivo. "
        "La UI se adapta y solo te muestra los pasos que necesitas."
    )

    _flow_keys = list(_FLOWS.keys())
    _cols = st.columns(len(_flow_keys))
    for _ci, (_fk, _fv) in enumerate(_FLOWS.items()):
        with _cols[_ci]:
            _selected = st.session_state["flow_key"] == _fk
            _border   = "2px solid #00c853" if _selected else "1px solid #3d4450"
            st.markdown(
                "<div style='border:%s; border-radius:10px; padding:1rem; min-height:260px'>" % _border,
                unsafe_allow_html=True,
            )
            st.markdown("### %s" % _fk)
            st.caption(_fv["desc"])
            st.markdown("**Necesitas:**")
            for _r in _fv["requires"]:
                st.markdown("- %s" % _r)
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

    _ref_laps = _rc["laps"]
    _ref_path = _rc["path"]
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
            _ref_tbl = _lap_table(_ref_laps, editor_key="ref_lap_tbl")
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
            _drv_tbl = _lap_table(_drv_laps, editor_key="drv_lap_tbl")
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
    _flow_has_analysis = 2 in _flow["steps"]
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
            if st.button("Detectar curvas automáticamente", help="Analiza la vuelta de referencia y detecta dónde están las curvas."):
                with st.spinner("Analizando vuelta de referencia…"):
                    try:
                        from fantasma.core.normalize import fastest_lap as _fl
                        from fantasma.core.corners import detect_corners as _dc2, extract_milestones as _em
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


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 3:
    st.markdown('<div class="step-header">Paso 3 — Generar overlay HUD</div>', unsafe_allow_html=True)
    st.caption(
        "Genera el **HUD animado** sincronizado con tu vuelta. "
        "Es un archivo de video **transparente** (como un sticker animado) que en el Paso 4 "
        "se pega encima de tu grabación. Muestra: barras de gas y freno, delta acumulado, "
        "velocidad, marcha, volante y G-lateral."
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
        st.caption("Si quieres regenerarlo con distintos parámetros, usa las opciones de abajo.")
        _next_step_btn(3)
        st.divider()

    out_dir = st.text_input(
        "Carpeta donde guardar el overlay",
        value=os.path.join(os.path.expanduser("~"), "fantasma_salida"),
        help="Se crea automáticamente si no existe. Anota esta ruta — la necesitarás en el Paso 4.",
    )
    st.caption(
        "📌 Anota la ruta de arriba — la necesitarás en el Paso 4 para indicarle dónde está el overlay."
    )

    with st.expander("⚙️ Opciones de render"):
        _col_a, _col_b = st.columns(2)
        _fps = _col_a.selectbox(
            "FPS del overlay", [24, 30, 60], index=1,
            help=(
                "Usa el mismo valor que tiene tu video de grabación. "
                "Si no sabes, 30 fps es el estándar más común. "
                "Un overlay a 30 sobre un video a 60 funciona bien; lo contrario puede verse entrecortado."
            ),
        )
        _fmt = _col_b.selectbox(
            "Formato del overlay", ["webm", "prores", "png"], index=0,
            help=(
                "webm — Recomendado. Compatible con DaVinci Resolve, Kdenlive, Premiere y cualquier editor moderno.\n"
                "prores — Para Final Cut Pro en Mac o si necesitas máxima calidad sin compresión.\n"
                "png — Solo frames sueltos (una imagen por fotograma). Para uso avanzado."
            ),
        )

    st.info(
        "⏱️ **Tiempo estimado de render:** entre 5 y 30 minutos dependiendo de la duración de la vuelta "
        "y el número de cores de tu PC. El render usa todos los cores disponibles en paralelo. "
        "Tu PC seguirá disponible mientras renderiza, solo irá más lenta."
    )

    if st.button("Generar overlay", type="primary"):
        os.makedirs(out_dir, exist_ok=True)
        _bar = st.progress(0, text="Iniciando render…")

        def _progress(n, total, status=None):
            pct = min(n / total, 1.0) if total else 0
            label = status if status else "Frame %d / %d (%.0f%%)" % (n, total, pct * 100)
            _bar.progress(pct, text=label)

        try:
            from fantasma.viz.overlay import render_overlay
            _webms = [render_overlay(ref_lap, drv_lap, corners or [], out_dir,
                                     fps=_fps, fmt=_fmt, progress=_progress)]

            _bar.progress(1.0, text="Completado")
            st.success("✓ Overlay generado:")
            for _w in _webms:
                st.code(_w)
            st.caption(
                "Copia esa ruta — la necesitarás en el campo «Overlay» del Paso 4."
            )
            st.session_state["last_overlay"] = _webms[0]
            st.divider()
            _next_step_btn(3)
        except ImportError:
            st.error(
                "Faltan dependencias del render. Ejecuta en la terminal: "
                "`pip install 'fantasma-inputs[overlay]'`"
            )
        except Exception as _e:
            st.error("Error en el render: %s" % _e)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — COMPONER
# ══════════════════════════════════════════════════════════════════════════════
elif step_idx == 4:
    st.markdown('<div class="step-header">Paso 4 — Componer video final</div>', unsafe_allow_html=True)
    st.caption(
        "Junta el overlay del Paso 3 con tu video de grabación. "
        "El resultado es un **clip MP4 recortado exactamente a la duración de tu vuelta**, "
        "con el HUD ya integrado y listo para subir."
    )

    # ── dos hechos clave que el usuario debe saber antes de empezar ────────────
    _col_k1, _col_k2 = st.columns(2)
    _col_k1.warning(
        "🎙️ **El video debe tener audio del motor activado.**  \n"
        "La detección automática de sincronía analiza el sonido del motor para saber exactamente "
        "en qué segundo cruzaste la línea de meta. Sin audio del motor tendrás que calcular el "
        "offset manualmente y escribirlo a mano."
    )
    _col_k2.info(
        "✂️ **El output no es el video completo de tu sesión.**  \n"
        "Se genera un clip recortado: solo los segundos de tu vuelta, desde que cruzas la meta "
        "hasta que la terminas. Mucho más rápido de procesar y más fácil de compartir."
    )

    st.divider()
    st.markdown("**① Archivos de entrada**")
    st.caption(
        "Escribe las rutas completas de los archivos. "
        "Tip: en el Explorador de Windows, haz clic en la barra de dirección de la carpeta, "
        "copia la ruta y añade el nombre del archivo al final."
    )

    _col1, _col2 = st.columns(2)
    _video_path = _col1.text_input(
        "Tu video de grabación",
        value=st.session_state.get("last_compose_video", ""),
        placeholder=r"C:\Videos\mi_sesion_nordschleife.mp4",
        help=(
            "El video que grabaste mientras corrías. "
            "IMPORTANTE: debe tener el audio del sim activado (el sonido del motor). "
            "Sin audio la detección automática de sync no funciona."
        ),
    )
    _overlay_path = _col2.text_input(
        "El overlay del HUD (del Paso 3)",
        value=st.session_state.get("last_overlay", ""),
        placeholder=r"C:\Users\TuNombre\fantasma_salida\overlay.webm",
        help="El archivo .webm (o .mov) generado en el Paso 3.",
    )

    # ── auto-sync — protagonista, no opcional ────────────────────────────────
    st.divider()
    st.markdown("**② ¿En qué segundo del video empieza tu vuelta?**")
    st.caption(
        "La detección automática escucha el sonido del motor en tu video y lo compara con los "
        "datos de RPM de la telemetría para encontrar el segundo exacto en que cruzaste la meta. "
        "Precisión ~0.5 s. Tarda ~30 segundos."
    )

    with st.expander("🔍 Detectar sincronía automáticamente *(recomendado — requiere scipy)*", expanded=True):
        _drv_for_sync = st.session_state.get("drv_lap")
        _sc_col1, _sc_col2 = st.columns([2, 1])
        with _sc_col1:
            if _drv_for_sync is None:
                st.caption("No hay telemetría cargada del Paso 1. Sube aquí el CSV del piloto:")
                _sync_up = st.file_uploader(
                    "CSV del piloto para sync", type=["csv", "xlsx"],
                    key="sync_drv_upload",
                )
                if _sync_up:
                    _sc = _cache_file(_sync_up)
                    if _sc["ok"] and _sc["laps"]:
                        from fantasma.core.normalize import fastest_lap as _fl
                        _drv_for_sync = _fl(_sc["laps"])
                        st.success("✓ Telemetría cargada para sync.")
            else:
                st.success(
                    "✓ Usando la vuelta del Paso 1 (%s). "
                    "Pulsa «Detectar» cuando tengas el video cargado." %
                    _fmt_lap(_drv_for_sync.laptime)
                )
        with _sc_col2:
            _can_sync = bool(_video_path and _drv_for_sync)
            if not _can_sync:
                st.caption("Necesitas el video y la telemetría para detectar.")
            if st.button("Detectar", disabled=not _can_sync, key="btn_autosync", type="primary" if _can_sync else "secondary"):
                with st.spinner("Analizando audio del video… (~30 s)"):
                    try:
                        from fantasma.viz.sync import auto_sync
                        _det, _z = auto_sync(_video_path, _drv_for_sync)
                        st.session_state["_autosync_detected"] = _det
                        st.session_state["_autosync_z"]        = _z
                        st.session_state["compose_offset"]     = _det
                    except ImportError as _ie:
                        st.error(str(_ie))
                    except Exception as _se:
                        st.error("Error en auto-sync: %s" % _se)

        if "_autosync_detected" in st.session_state:
            _off = st.session_state["_autosync_detected"]
            _z_s = st.session_state.get("_autosync_z", 0.0)
            _qlbl = "Excelente" if _z_s > 10 else "Muy bueno" if _z_s > 6 else "Bueno" if _z_s > 4 else "Marginal"
            st.success(
                "✓ Offset detectado: **%.3f s** desde el inicio del video hasta el cruce de meta.  \n"
                "Sync quality: **%s** (z=%.1f σ) — pre-cargado en el campo de abajo." % (_off, _qlbl, _z_s)
            )

    # ── parámetros de composición ─────────────────────────────────────────────
    st.divider()
    st.markdown("**③ Parámetros del HUD**")
    _col3, _col4, _col5 = st.columns(3)
    _pos_sel  = _col3.selectbox(
        "Posición del HUD en pantalla",
        list(_POS_LABELS.keys()),
        help="Dónde se coloca el HUD dentro del frame del video.",
    )
    _position = _POS_LABELS[_pos_sel]
    _offset   = _col4.number_input(
        "Offset (segundos desde el inicio del video hasta la meta)",
        value=st.session_state.get("compose_offset", 0.0),
        step=0.1,
        key="compose_offset",
        help=(
            "El segundo del video en que tu auto cruza la línea de meta por primera vez. "
            "Ejemplo: si empiezas a grabar 12 segundos antes de cruzar la meta, escribe 12. "
            "Si usaste «Detectar sincronía» este campo se rellena solo — no necesitas tocarlo."
        ),
    )
    _scale = _col5.slider(
        "Tamaño del HUD",
        0.25, 1.5, 1.0, 0.05,
        help="1.0 = tamaño completo del render. 0.7 = más pequeño, si el HUD tapa algo importante.",
    )

    st.divider()
    st.markdown("**④ Archivo de salida** *(opcional)*")
    _out_path = st.text_input(
        "Ruta del video final",
        placeholder=r"C:\Videos\nordschleife_lap1_con_hud.mp4",
        help=(
            "Si lo dejas vacío, el archivo se guarda en la misma carpeta que el video "
            "original con el sufijo `_composed.mp4`."
        ),
    )

    # ── resumen pre-compose ───────────────────────────────────────────────────
    _drv_lap = st.session_state.get("drv_lap")
    if _video_path and _overlay_path and _drv_lap is not None:
        def _mss(s):
            return "%d:%02d" % (int(s) // 60, int(s) % 60)
        st.info(
            "**Resumen de lo que se va a generar:**  \n"
            "- Video fuente: `%s`  \n"
            "- Overlay: `%s`  \n"
            "- Clip de salida: desde **%s min** del video → duración **%s** (%.0f s)  \n"
            "- HUD posición: %s · escala: %.0f%%  \n"
            "- Codec: NVENC (GPU) si hay GPU NVIDIA disponible, libx264 (CPU) si no." % (
                os.path.basename(_video_path),
                os.path.basename(_overlay_path),
                _mss(float(st.session_state.get("compose_offset", 0.0))),
                _mss(_drv_lap.laptime),
                _drv_lap.laptime,
                _pos_sel,
                _scale * 100,
            )
        )

    st.divider()
    if not _video_path:
        st.caption("⬆️ Escribe la ruta de tu video para habilitar el botón.")
    elif not _overlay_path:
        st.caption("⬆️ Escribe la ruta del overlay del Paso 3 para habilitar el botón.")

    if st.button("Componer video", type="primary", disabled=not (_video_path and _overlay_path)):
        if not _out_path:
            _base     = os.path.splitext(os.path.basename(_video_path))[0]
            _out_path = os.path.join(os.path.dirname(_video_path), _base + "_composed.mp4")

        _bar = st.progress(0, text="Iniciando composición…")
        try:
            from fantasma.viz.compose import compose_video

            def _compose_progress(n, total):
                pct = min(n / total, 1.0) if total else 0
                _bar.progress(pct, text="Componiendo… frame %d / %d (%.0f%%)" % (n, total, pct * 100))

            _lap_duration = _drv_lap.laptime if _drv_lap is not None else None
            _result = compose_video(_video_path, _overlay_path, _out_path,
                                    position=_position, offset=_offset, scale=_scale,
                                    lap_duration=_lap_duration,
                                    progress=_compose_progress)
            _bar.progress(1.0, text="Completado")
            st.success("✓ Video guardado en:")
            st.code(_result)
            if _drv_lap is not None:
                def _mss(s):
                    return "%d:%02d" % (int(s) // 60, int(s) % 60)
                st.info(
                    "Clip recortado desde el minuto **%s** del video original · "
                    "duración: **%s** (%.1f s)." % (
                        _mss(_offset), _mss(_drv_lap.laptime), _drv_lap.laptime)
                )
            _z_score = st.session_state.get("_autosync_z")
            if _z_score is not None:
                _qlbl = "Excelente" if _z_score > 10 else "Muy bueno" if _z_score > 6 else "Bueno" if _z_score > 4 else "Marginal"
                st.info("Sync quality: **%s** (z=%.1f σ, offset=%.2f s) ✓" % (_qlbl, _z_score, float(_offset)))
            st.session_state["last_compose_video"] = _video_path
            st.balloons()
            _next_step_btn(4)
            st.divider()
            if st.button(
                "🔄 Procesar otra vuelta",
                help="Vuelve al Paso 1 para seleccionar otra vuelta. Mantiene la referencia y el video.",
            ):
                for _k in ["drv_lap", "drv_laps", "drv_path", "summary", "trace", "rows",
                           "charts_paths", "last_overlay", "_autosync_detected", "_autosync_z"]:
                    st.session_state.pop(_k, None)
                for _k in list(st.session_state.keys()):
                    if _k.startswith("drv_sel_") or _k == "drv_lap_tbl":
                        st.session_state.pop(_k, None)
                st.session_state["nav_step"] = 1
                st.rerun()
        except RuntimeError as _e:
            st.error(str(_e))
        except Exception as _e:
            st.error("Error: %s" % _e)
