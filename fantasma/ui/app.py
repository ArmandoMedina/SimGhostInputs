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
import streamlit as st

from fantasma.ui._helpers import _DEFAULT_FLOW, _FLOWS, _STEPS, _go
from fantasma.ui import step0, step1, step2, step3, step4

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


# ── estado de navegación ──────────────────────────────────────────────────────

if "nav_step" not in st.session_state:
    st.session_state["nav_step"] = 0
if "flow_key" not in st.session_state:
    st.session_state["flow_key"] = _DEFAULT_FLOW

_flow = _FLOWS[st.session_state["flow_key"]]


def _step_done(i):
    return bool([
        "flow_key"     in st.session_state,
        "ref_lap"      in st.session_state,
        "summary"      in st.session_state,
        "last_overlay" in st.session_state,
        False,
    ][i])


def _step_in_flow(i):
    return i in _flow["steps"]


def _step_unlocked(i):
    if i <= 1:  return True
    if i == 2:  return "ref_lap"      in st.session_state
    if i == 3:  return "ref_lap"      in st.session_state
    # Paso 4 (Componer) solo necesita video + overlay. La telemetría es
    # opcional: habilita el sync automático y el recorte a la vuelta, pero
    # sin ella se compone con offset manual y duración completa (modo legado
    # de compose_video). Siempre accesible — apunta a un overlay.webm existente
    # con «Explorar…».
    if i == 4:  return True
    return False


# ── cancelar render si el usuario navegó ─────────────────────────────────────

_render_active = st.session_state.get("_render_active", False)
if _render_active and st.session_state.get("_render_step") != st.session_state.get("nav_step"):
    _ev = st.session_state.get("_cancel_event")
    if _ev:
        _ev.set()
    st.session_state["_render_active"] = False
    _render_active = False
    st.warning("El render se canceló porque cambiaste de paso.")


# ── sidebar ───────────────────────────────────────────────────────────────────

# El sidebar se bloquea solo mientras el hilo de render sigue corriendo. El flag
# _render_active permanece True hasta que _render_widget reporta el resultado en
# el paso (orden: sidebar → routing), así que usar _render_active aquí dejaría el
# sidebar bloqueado un run de más al terminar/cancelar. _render_busy lo libera en
# cuanto el hilo marca done.
_pd_busy = st.session_state.get("_progress_data")
_render_busy = _render_active and not (_pd_busy and _pd_busy.get("done"))

with st.sidebar:
    st.title("👻 SimGhostInputs")
    st.caption("Análisis de inputs de simracing por distancia")
    st.divider()
    if _render_busy:
        st.warning("⏳ Render en curso…  \nNavega al terminar o presiona **Detener** en la pantalla principal.")
    for _i, _lbl in enumerate(_STEPS):
        _current  = st.session_state["nav_step"] == _i
        _done     = _step_done(_i)
        _in_flow  = _step_in_flow(_i)
        _unlocked = _step_unlocked(_i)
        _icon     = "▶️" if _current else ("✅" if _done else ("○" if _in_flow else "·"))
        _suffix   = "" if _in_flow else "  *(opcional)*"
        if st.button(
            "%s  %d · %s%s" % (_icon, _i, _lbl, _suffix),
            disabled=not _unlocked or _render_busy,
            use_container_width=True,
            key="nav_%d" % _i,
        ):
            _go(_i)
    st.divider()
    st.caption("Flujo: **%s**" % st.session_state["flow_key"])
    st.caption("Tus datos nunca salen de tu máquina.")


# ── routing ───────────────────────────────────────────────────────────────────

_step_idx = st.session_state["nav_step"]

if   _step_idx == 0:  step0.render()
elif _step_idx == 1:  step1.render(_flow)
elif _step_idx == 2:  step2.render()
elif _step_idx == 3:  step3.render()
elif _step_idx == 4:  step4.render()
