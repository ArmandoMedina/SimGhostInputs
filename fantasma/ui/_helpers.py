"""Helpers y constantes compartidas para la UI de SimGhostInputs."""

import json
import os
import tempfile
import threading
import time

import streamlit as st

_POS_LABELS = {
    "Abajo derecha": "bottom-right",
    "Abajo izquierda": "bottom-left",
    "Arriba derecha": "top-right",
    "Arriba izquierda": "top-left",
    "Abajo centro": "bottom-center",
    "Arriba centro": "top-center",
    "Centro": "center",
}

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
_STEPS = ["Inicio", "Importar", "Comparar", "Overlay", "Componer"]


# ── navegación ────────────────────────────────────────────────────────────────


def _go(i):
    st.session_state["nav_step"] = i
    st.rerun()


def _next_step_btn(current_step_idx):
    flow = _FLOWS[st.session_state.get("flow_key", _DEFAULT_FLOW)]
    next_i = flow["next"].get(current_step_idx)
    if next_i is None:
        st.success("✅ ¡Completaste todos los pasos de tu flujo!")
    else:
        label = "Ir al Paso %d — %s →" % (next_i, _STEPS[next_i])
        if st.button(label, type="primary"):
            _go(next_i)


# ── archivos ──────────────────────────────────────────────────────────────────


def _save_upload(uploaded, suffix):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read())
    tmp.flush()
    return tmp.name


def _load_laps(path, column_map=None):
    from fantasma import importers

    return importers.load_laps(path, column_map)


def _cache_file(uploaded_file):
    ck = "file_%s" % uploaded_file.file_id
    if ck not in st.session_state:
        with st.spinner("Leyendo archivo…"):
            try:
                path = _save_upload(uploaded_file, os.path.splitext(uploaded_file.name)[1])
                laps = _load_laps(path)
                st.session_state[ck] = {
                    "path": path,
                    "name": uploaded_file.name,
                    "laps": laps,
                    "ok": True,
                }
            except Exception as _e:
                st.session_state[ck] = {"path": "", "laps": [], "ok": False, "err": str(_e)}
    return st.session_state[ck]


def _corners_from_json(uploaded):
    data = json.load(uploaded)
    return data.get("corners", data) if isinstance(data, dict) else data


# ── formato ───────────────────────────────────────────────────────────────────


def _fmt_lap(seconds):
    m, s = divmod(int(seconds), 60)
    return "%d:%05.2f" % (m, seconds - m * 60)


def _sync_quality_label(z):
    if z > 8:
        return "Excelente"
    if z > 5:
        return "Muy bueno"
    if z > 3:
        return "Bueno"
    return "Marginal"


# ── tabla de vueltas ──────────────────────────────────────────────────────────


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
        options.append(
            "#%d  ·  %s  ·  %dm  ·  %s" % (i, _fmt_lap(l.laptime), int(l.length), estado)
        )
    sel = st.radio("", options, index=best_i, key=editor_key, label_visibility="collapsed")
    return [options.index(sel)]


# ── selectores de archivo/carpeta nativos ─────────────────────────────────────


def _pick_file(title="Seleccionar archivo", filetypes=None):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        path = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes or [("Todos los archivos", "*.*")],
        )
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _pick_folder(title="Seleccionar carpeta", initialdir=None):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        path = filedialog.askdirectory(
            title=title,
            initialdir=initialdir or os.path.expanduser("~"),
        )
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _img_or_placeholder(rel_path, caption):
    full = os.path.join(os.path.dirname(__file__), "..", "..", rel_path)
    if os.path.exists(full):
        st.image(full, caption=caption, use_container_width=True)
    else:
        st.info("📷 **Imagen pendiente:** %s" % caption)


# ── render en background ──────────────────────────────────────────────────────


def _start_bg_render(step_idx, fn, progress_kw="progress", **kwargs):
    cancel = threading.Event()
    pd = {"n": 0, "total": 0, "status": "Iniciando…", "done": False, "error": None, "result": None}

    def _cb(n, total, status=None):
        if cancel.is_set():
            raise RuntimeError("__CANCELLED__")
        pd["n"] = n
        pd["total"] = total
        if status:
            pd["status"] = status

    def _run():
        try:
            pd["result"] = fn(**{progress_kw: _cb}, **kwargs)
        except RuntimeError as _e:
            pd["error"] = "__CANCELLED__" if "__CANCELLED__" in str(_e) else str(_e)
        except Exception as _e:
            pd["error"] = str(_e)
        finally:
            pd["done"] = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    st.session_state.update(
        {
            "_render_active": True,
            "_render_step": step_idx,
            "_cancel_event": cancel,
            "_progress_data": pd,
            "_render_thread": t,
        }
    )


def _render_widget(step_idx):
    if not st.session_state.get("_render_active"):
        return False, None, None
    if st.session_state.get("_render_step") != step_idx:
        return False, None, None

    pd = st.session_state["_progress_data"]

    if not pd["done"]:
        n, total = pd["n"], pd["total"]
        pct = min(n / total, 1.0) if total > 0 else 0.0
        label = pd["status"] or ("Frame %d / %d (%.0f%%)" % (n, total, pct * 100))
        st.progress(pct, text=label)
        if st.button("Detener render", type="secondary", key="_btn_cancel_%d" % step_idx):
            st.session_state["_cancel_event"].set()
            st.warning("Cancelando… espera un momento.")
        time.sleep(0.4)
        st.rerun()

    st.session_state["_render_active"] = False
    return True, pd["error"], pd["result"]
