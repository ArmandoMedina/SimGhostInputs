"""Overlay HUD animado — 3 paneles rodantes (gas / freno / volante) + franja de datos.

Diseño HUD-A: ventana deslizante de W_BEFORE metros antes y W_AFTER metros después
del cursor. Colores: ABS=ámbar, TCS=violeta, volante por G-lat (amarillo P75-P90,
naranja >P90). Fondo #0a0c10. Cursor amarillo.

Dependencias (extra `overlay`): Pillow>=10, matplotlib>=3.7, ffmpeg en PATH.
"""
import concurrent.futures
import os
import shutil
import subprocess

import numpy as np

# ── paleta ───────────────────────────────────────────────────────────────────
_BG    = "#0a0c10"
_FG    = "#e8eaed"
_DIM   = "#9aa0a6"
_REF   = "#9aa0a6"
_GAS   = "#00c853"
_FRENO = "#ff1744"
_VOL   = "#40c4ff"
_ABS   = "#ffab00"
_TCS   = "#e040fb"
_RABS  = "#b8860b"
_RTCS  = "#7b5ea7"
_GMED  = "#fdd835"
_GMAX  = "#ff6d00"
_RGMED = "#6b5e00"
_RGMAX = "#7a3300"
_YEL   = "#fdd835"

W_BEFORE = 320   # metros antes del cursor
W_AFTER  = 200   # metros después del cursor
_FIG_W   = 17    # pulgadas
_FIG_H   = 5.2
_DPI     = 110   # → ~1870 × 572 px


# ── utilidades de enmascarado ─────────────────────────────────────────────────

def _masked(vals, flags, active):
    """NaN donde el flag no coincide con active (corta la línea en matplotlib)."""
    return np.where((np.asarray(flags) > 0.5) == active, vals, np.nan)


def _masked_g(vals, glat, lo, hi=None):
    """NaN fuera del rango |G-lat| ∈ [lo, hi)."""
    cond = np.abs(glat) >= lo
    if hi is not None:
        cond &= np.abs(glat) < hi
    return np.where(cond, vals, np.nan)


# ── interpolación ─────────────────────────────────────────────────────────────

def _interp_lap(lap, ds):
    """Interpola todos los canales del Lap en la rejilla uniforme ds (1 m)."""
    d_orig = np.array(lap.col("dist"), dtype=float)
    out = {}
    for ch in ("throttle", "brake", "steering", "speed", "glat", "abs", "tcs"):
        raw = lap.col(ch)
        if raw:
            out[ch] = np.interp(ds, d_orig, np.array(raw, dtype=float))
        else:
            out[ch] = np.zeros_like(ds, dtype=float)
    return out


# ── métricas por ventana ──────────────────────────────────────────────────────

def _count_events(d_orig, flag_orig, lo, hi):
    """Flancos de subida (0→1) de flag_orig en el tramo [lo, hi]."""
    mask = (d_orig >= lo) & (d_orig <= hi)
    f = (flag_orig[mask] > 0.5).astype(np.int8)
    return int(np.sum(np.diff(f) > 0)) if len(f) >= 2 else 0


def _slip_window(slip_grid, ds, lo, hi):
    """Índice de slip en la ventana visible; None si no hay serie."""
    if slip_grid is None:
        return None
    mask = (ds >= lo) & (ds <= hi)
    excess = np.maximum(0.0, np.abs(slip_grid[mask]) - 2.0)   # DEADBAND_PCT = 2
    return round(float(np.mean(excess)), 2) if excess.size else None


def _corner_at(corners_by_seg, dist):
    """Nombre y texto de V-Min de la curva que contiene dist."""
    for (lo, hi), c in corners_by_seg:
        if lo <= dist <= hi:
            name = c.get("name", c.get("id", ""))
            ap = (c.get("milestones") or {}).get("apex", {})
            v = ap.get("v")
            txt2 = "V-Min objetivo %d km/h" % v if v else ""
            return name, txt2
    return "", ""


# ── figura matplotlib reutilizable ────────────────────────────────────────────

class _HUDFigure:
    """Crea la figura una sola vez; update() cambia datos sin recrear artistas."""

    def __init__(self):
        import matplotlib.pyplot as plt
        self._plt = plt

        fig, axes = plt.subplots(3, 1, figsize=(_FIG_W, _FIG_H), sharex=True)
        fig.patch.set_facecolor(_BG)
        self.fig   = fig
        self.axes  = axes

        # ── franja de datos (textos dinámicos) ───────────────────────────────
        kw = dict(transform=fig.transFigure, va="top")
        self.t_gap_val = fig.text(0.045, 0.985, "",  color=_FRENO, fontsize=17, weight="bold", **kw)
        self.t_dv_val  = fig.text(0.158, 0.985, "",  color=_FG,    fontsize=17, weight="bold", **kw)
        self.t_sl_val  = fig.text(0.272, 0.985, "—", color=_FG,    fontsize=17, weight="bold", **kw)
        self.t_sl_ref  = fig.text(0.305, 0.978, "",  color=_DIM,   fontsize=10, **kw)
        self.t_ab_val  = fig.text(0.405, 0.985, "",  color=_ABS,   fontsize=14, **kw)
        self.t_ab_ref  = fig.text(0.450, 0.978, "",  color=_DIM,   fontsize=10, **kw)
        self.t_corner  = fig.text(0.988, 0.985, "",  color=_YEL,   fontsize=15,
                                  weight="bold", va="top", ha="right", transform=fig.transFigure)
        self.t_corner2 = fig.text(0.988, 0.948, "",  color=_DIM,   fontsize=10,
                                  va="top", ha="right", transform=fig.transFigure)

        # labels fijos
        fig.text(0.012, 0.97,  "GAP",       color=_DIM,  fontsize=10, **kw)
        fig.text(0.135, 0.97,  "ΔV",        color=_DIM,  fontsize=10, **kw)
        fig.text(0.225, 0.97,  "DESLIZ",    color=_DIM,  fontsize=10, **kw)
        fig.text(0.375, 0.97,  "ABS",       color=_DIM,  fontsize=10, **kw)
        fig.text(0.520, 0.97,  "freno+ABS", color=_ABS,  fontsize=9,  **kw)
        fig.text(0.585, 0.97,  "gas+TCS",   color=_TCS,  fontsize=9,  **kw)

        # ── estilo de paneles ─────────────────────────────────────────────────
        specs = [("gas %", -5, 105), ("freno %", -5, 105), ("volante °", -38, 38)]
        for ax, (ylabel, ylo, yhi) in zip(axes, specs):
            ax.set_facecolor((0, 0, 0, 0))
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.tick_params(colors=_DIM, labelsize=8, length=0, labelbottom=False)
            ax.grid(color="#2a2e33", linewidth=0.5, alpha=0.6)
            ax.set_ylabel(ylabel, color=_FG, fontsize=9)
            ax.set_ylim(ylo, yhi)

        axes[2].axhline(0, color="#444", lw=0.7)

        lw   = 1.8
        nil  = ([], [])
        l    = {}

        # panel gas (índice 0)
        ax0 = axes[0]
        l["rthr"]   = ax0.plot(*nil, color=_REF,  lw=lw)[0]
        l["rtcs"]   = ax0.plot(*nil, color=_RTCS, lw=lw)[0]
        l["dthr"]   = ax0.plot(*nil, color=_GAS,  lw=lw)[0]
        l["dtcs"]   = ax0.plot(*nil, color=_TCS,  lw=lw)[0]
        self.cur0   = ax0.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        # panel freno (índice 1)
        ax1 = axes[1]
        l["rbrk"]   = ax1.plot(*nil, color=_REF,   lw=lw)[0]
        l["rabs"]   = ax1.plot(*nil, color=_RABS,  lw=lw)[0]
        l["dbrk"]   = ax1.plot(*nil, color=_FRENO, lw=lw)[0]
        l["dabs"]   = ax1.plot(*nil, color=_ABS,   lw=lw)[0]
        self.cur1   = ax1.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        # panel volante (índice 2)
        ax2 = axes[2]
        l["rsteer"] = ax2.plot(*nil, color=_REF,   lw=lw)[0]
        l["rgmed"]  = ax2.plot(*nil, color=_RGMED, lw=lw)[0]
        l["rgmax"]  = ax2.plot(*nil, color=_RGMAX, lw=lw)[0]
        l["dsteer"] = ax2.plot(*nil, color=_VOL,   lw=lw)[0]
        l["dgmed"]  = ax2.plot(*nil, color=_GMED,  lw=lw)[0]
        l["dgmax"]  = ax2.plot(*nil, color=_GMAX,  lw=lw)[0]
        self.cur2   = ax2.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        self.l = l
        fig.tight_layout(rect=(0, 0, 1, 0.90))

    def update(self, cur_d, win_d, rw, dw, p75, p90,
               gap, dv, slip_val, ref_slip_val, abs_n, ref_abs_n,
               corner_name, corner_txt):
        """Actualiza datos y texto para el frame actual."""
        l = self.l

        # gas
        l["rthr"].set_data(win_d, rw["throttle"])
        l["rtcs"].set_data(win_d, _masked(rw["throttle"], rw["tcs"], True))
        l["dthr"].set_data(win_d, dw["throttle"])
        l["dtcs"].set_data(win_d, _masked(dw["throttle"], dw["tcs"], True))

        # freno
        l["rbrk"].set_data(win_d, rw["brake"])
        l["rabs"].set_data(win_d, _masked(rw["brake"], rw["abs"], True))
        l["dbrk"].set_data(win_d, dw["brake"])
        l["dabs"].set_data(win_d, _masked(dw["brake"], dw["abs"], True))

        # volante
        l["rsteer"].set_data(win_d, rw["steering"])
        l["rgmed"].set_data(win_d, _masked_g(rw["steering"], rw["glat"], p75, p90))
        l["rgmax"].set_data(win_d, _masked_g(rw["steering"], rw["glat"], p90))
        l["dsteer"].set_data(win_d, dw["steering"])
        l["dgmed"].set_data(win_d, _masked_g(dw["steering"], dw["glat"], p75, p90))
        l["dgmax"].set_data(win_d, _masked_g(dw["steering"], dw["glat"], p90))

        # cursor y límites de ventana
        for cur in (self.cur0, self.cur1, self.cur2):
            cur.set_xdata([cur_d, cur_d])
        x0 = float(win_d[0]) if win_d.size else 0.0
        x1 = float(win_d[-1]) if win_d.size else 1.0
        self.axes[0].set_xlim(x0, x1)   # se propaga a sharex

        # franja de datos
        self.t_gap_val.set_text("%+.2f s" % gap)
        self.t_gap_val.set_color(_FRENO if gap > 0 else _GAS)
        self.t_dv_val.set_text("%+d" % dv)
        self.t_dv_val.set_color(_FRENO if dv < -8 else _FG)
        if slip_val is not None:
            self.t_sl_val.set_text("%.1f" % slip_val)
            self.t_sl_ref.set_text("ref %.1f" % ref_slip_val if ref_slip_val is not None else "")
        else:
            self.t_sl_val.set_text("—")
            self.t_sl_ref.set_text("")
        self.t_ab_val.set_text("●" * min(abs_n, 5))
        self.t_ab_ref.set_text("ref %d✕" % ref_abs_n)
        self.t_corner.set_text(corner_name)
        self.t_corner2.set_text(corner_txt)

    def to_pil(self):
        """Renderiza y devuelve imagen PIL RGBA."""
        from PIL import Image
        self.fig.canvas.draw()
        buf = self.fig.canvas.buffer_rgba()
        w, h = self.fig.canvas.get_width_height()
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4).copy()
        return Image.fromarray(arr, "RGBA")

    def close(self):
        self._plt.close(self.fig)


# ── worker de proceso (nivel de módulo — requerido por spawn en Windows) ──────

def _render_chunk(args):
    """Renderiza el rango de frames [frame_start, frame_end) en un proceso separado."""
    import matplotlib
    matplotlib.use("Agg")

    (frame_start, frame_end,
     ds, ref_ch, drv_ch, p75, p90,
     ref_slip, drv_slip,
     ref_d_o, ref_abs_o, drv_d_o, drv_abs_o,
     trace, n_tr, step,
     t_arr, d_arr, corners_by_seg,
     frames_dir, fps, t_start) = args

    hud      = _HUDFigure()
    last_png = None
    try:
        for n in range(frame_start, frame_end):
            t     = t_start + n / fps
            i_t   = max(0, min(int(np.searchsorted(t_arr, t, "right")) - 1, len(d_arr) - 1))
            cur_d = float(d_arr[i_t])

            w0    = max(0.0, cur_d - W_BEFORE)
            w1    = min(float(ds[-1]), cur_d + W_AFTER)
            mask  = (ds >= w0) & (ds <= w1)
            win_d = ds[mask]

            out_path = os.path.join(frames_dir, "f%06d.png" % n)
            if win_d.size < 2:
                if last_png is not None:
                    shutil.copy(last_png, out_path)
                continue

            rw = {k: v[mask] for k, v in ref_ch.items()}
            dw = {k: v[mask] for k, v in drv_ch.items()}

            gap          = trace[max(0, min(int(cur_d / step), n_tr - 1))]["delta_t"]
            ref_v        = float(np.interp(cur_d, ds, ref_ch["speed"]))
            drv_v        = float(np.interp(cur_d, ds, drv_ch["speed"]))
            dv           = int(drv_v - ref_v)
            slip_val     = _slip_window(drv_slip, ds, w0, w1)
            ref_slip_val = _slip_window(ref_slip, ds, w0, w1)
            abs_n        = _count_events(drv_d_o, drv_abs_o, w0, w1)
            ref_abs_n    = _count_events(ref_d_o, ref_abs_o, w0, w1)
            corner_name, corner_txt = _corner_at(corners_by_seg, cur_d)

            hud.update(cur_d, win_d, rw, dw, p75, p90,
                       gap, dv, slip_val, ref_slip_val, abs_n, ref_abs_n,
                       corner_name, corner_txt)
            hud.to_pil().save(out_path)
            last_png = out_path
    finally:
        hud.close()

    return frame_end - frame_start


# ── función principal ─────────────────────────────────────────────────────────

def render_overlay(ref, drv, corners, outdir, fps=30, fmt="webm",
                   t_start=0.0, t_end=None, progress=None):
    """Renderiza el overlay HUD-A. Devuelve ruta del video o carpeta de frames."""
    try:
        import matplotlib
        matplotlib.use("Agg")
    except ImportError:
        raise ImportError(
            "matplotlib requerido para el overlay: "
            "pip install 'fantasma-inputs[overlay]'"
        )

    from ..core.compare import delta_trace
    from ..core import wear

    # ── rejilla uniforme de distancias (1 m) ─────────────────────────────────
    d_max = max(ref.col("dist")[-1], drv.col("dist")[-1])
    ds = np.arange(0.0, d_max + 1.0, 1.0)

    ref_ch = _interp_lap(ref, ds)
    drv_ch = _interp_lap(drv, ds)

    # percentiles G-lat de referencia
    glat_raw = ref.col("glat") or []
    glat_sorted = sorted(abs(x) for x in glat_raw) if glat_raw else [0.0]
    n_gl = len(glat_sorted)
    p75 = glat_sorted[int(n_gl * 0.75)]
    p90 = glat_sorted[int(n_gl * 0.90)]

    # slip en rejilla (None si faltan canales de velocidad de rueda)
    def _to_grid(lap):
        cal = wear.calibrate(lap)
        if cal is None:
            return None
        s = wear.slip_series(lap, cal)
        if s is None:
            return None
        return np.interp(ds, np.array(lap.col("dist"), dtype=float), np.array(s, dtype=float))

    ref_slip = _to_grid(ref)
    drv_slip = _to_grid(drv)

    # ABS originales (sin interpolar) para conteo de flancos preciso
    def _orig_flags(lap, ch):
        d = np.array(lap.col("dist"), dtype=float)
        raw = lap.col(ch)
        f = np.array(raw, dtype=float) if raw else np.zeros(len(d))
        return d, f

    ref_d_o, ref_abs_o = _orig_flags(ref, "abs")
    drv_d_o, drv_abs_o = _orig_flags(drv, "abs")

    # delta en tiempo (5 m de resolución)
    step  = 5.0
    trace = delta_trace(ref, drv, step)
    n_tr  = len(trace)

    # tiempo → distancia del piloto
    t_arr = np.array(drv.col("time"), dtype=float)
    d_arr = np.array(drv.col("dist"), dtype=float)

    # corners: ((lo, hi), dict)
    def _seg(c):
        return c.get("segment_m") or c.get("range_m") or [0.0, 0.0]
    corners_by_seg = [((_seg(c)[0], _seg(c)[1]), c) for c in corners]

    # ── render paralelo de frames ─────────────────────────────────────────────
    frames_dir = os.path.join(outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    t_end    = t_end if t_end is not None else float(t_arr[-1])
    n_frames = int((t_end - t_start) * fps)

    n_workers = max(1, (os.cpu_count() or 1) - 1)

    base = (ds, ref_ch, drv_ch, p75, p90,
            ref_slip, drv_slip,
            ref_d_o, ref_abs_o, drv_d_o, drv_abs_o,
            trace, n_tr, step,
            t_arr, d_arr, corners_by_seg,
            frames_dir, fps, t_start)

    if n_workers <= 1:
        # 1 o 2 cores: spawn overhead > ganancia; loop secuencial
        _render_chunk((0, n_frames, *base))
        if progress:
            progress(n_frames, n_frames)
    else:
        # mp_context="spawn" fuerza el mismo comportamiento en Linux/Mac que en Windows.
        # fork (default en Linux) + matplotlib puede deadlockear o lanzar UserWarning.
        # PENDIENTE: probar en Linux y macOS antes de quitar este comentario.
        import multiprocessing
        mp_ctx = multiprocessing.get_context("spawn")
        chunk_sz = max(1, (n_frames + n_workers - 1) // n_workers)
        chunks   = [(i, min(n_frames, i + chunk_sz)) for i in range(0, n_frames, chunk_sz)]
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=n_workers, mp_context=mp_ctx
        ) as executor:
            futs = [executor.submit(_render_chunk, (s, e, *base)) for s, e in chunks]
            done = 0
            for fut in concurrent.futures.as_completed(futs):
                done += fut.result()
                if progress:
                    progress(done, n_frames)

    if fmt == "png":
        return frames_dir

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("aviso: ffmpeg no encontrado — frames en %s" % frames_dir)
        return frames_dir

    if fmt == "webm":
        out = os.path.join(outdir, "overlay.webm")
        cmd = [ffmpeg, "-y", "-framerate", str(fps),
               "-i", os.path.join(frames_dir, "f%06d.png"),
               "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2M", out]
    else:
        out = os.path.join(outdir, "overlay.mov")
        cmd = [ffmpeg, "-y", "-framerate", str(fps),
               "-i", os.path.join(frames_dir, "f%06d.png"),
               "-c:v", "prores_ks", "-profile:v", "4444",
               "-pix_fmt", "yuva444p10le", out]

    subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(frames_dir, ignore_errors=True)
    return out
