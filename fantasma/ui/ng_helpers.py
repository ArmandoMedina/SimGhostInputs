"""Helpers y constantes compartidas para la UI NiceGUI de SimGhostInputs."""

import json
import os
import tempfile
import threading

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
    "analisis": {
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
    "overlay": {
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
    "compose": {
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
_DEFAULT_FLOW = "compose"
_STEPS = ["Inicio", "Importar", "Comparar", "Overlay", "Componer"]


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


def _best_lap_index(laps):
    best_i, best_t = 0, float("inf")
    for i, l in enumerate(laps):
        if l.meta.get("is_complete") and l.laptime < best_t:
            best_t, best_i = l.laptime, i
    return best_i


def _lap_options(laps):
    best_i = _best_lap_index(laps)
    options = []
    for i, l in enumerate(laps):
        _c = l.meta.get("is_complete", False)
        estado = "🏆 Más rápida" if i == best_i else ("✓ Completa" if _c else "⚠️ Incompleta")
        options.append(
            "#%d  ·  %s  ·  %dm  ·  %s" % (i, _fmt_lap(l.laptime), int(l.length), estado)
        )
    return options


# ── archivos ──────────────────────────────────────────────────────────────────


def _save_upload(content_bytes, suffix):
    """Guarda bytes en un archivo temporal y devuelve la ruta."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name


def _load_laps(path, column_map=None):
    from fantasma import importers

    return importers.load_laps(path, column_map)


def _missing_distance(laps):
    return bool(laps) and not any(l.has("dist") for l in laps)


def _corners_from_json(data_bytes):
    """Recibe bytes de un JSON con curvas y devuelve la lista de corners."""
    data = json.loads(data_bytes)
    return data.get("corners", data) if isinstance(data, dict) else data


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


# ── render en background ──────────────────────────────────────────────────────


class RenderJob:
    def __init__(self):
        self.n = 0
        self.total = 0
        self.status = "Iniciando..."
        self.done = False
        self.error = None
        self.result = None
        self._cancel = threading.Event()

    def progress_cb(self, n, total, status=None):
        if self._cancel.is_set():
            raise RuntimeError("__CANCELLED__")
        self.n = n
        self.total = total
        if status:
            self.status = status

    def cancel(self):
        self._cancel.set()


def start_bg_render(fn, progress_kw="progress", **kwargs):
    """Lanza fn en un thread daemon. Devuelve un RenderJob para polling."""
    job = RenderJob()

    def _run():
        try:
            job.result = fn(**{progress_kw: job.progress_cb}, **kwargs)
        except RuntimeError as _e:
            job.error = "__CANCELLED__" if "__CANCELLED__" in str(_e) else str(_e)
        except Exception as _e:
            job.error = str(_e)
        finally:
            job.done = True

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return job
