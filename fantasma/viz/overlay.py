"""Overlay HUD animado — 3 paneles rodantes (gas / freno / volante) + franja de datos.

Diseño HUD-A: ventana deslizante de W_BEFORE metros antes y W_AFTER metros después
del cursor. Colores: ABS=ámbar, TCS=violeta, volante por G-lat (amarillo P75-P90,
naranja >P90). Fondo #0a0c10. Cursor amarillo.

Dependencias (extra `overlay`): Pillow>=10, matplotlib>=3.7, ffmpeg en PATH.
"""

import os
import pickle
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

# ── paleta ───────────────────────────────────────────────────────────────────
_BG = "#0a0c10"
_FG = "#e8eaed"
_DIM = "#9aa0a6"
_REF = "#9aa0a6"
_GAS = "#00c853"
_FRENO = "#ff1744"
_VOL = "#40c4ff"
_ABS = "#ffab00"
_TCS = "#e040fb"
_RABS = "#e0a526"  # ABS de la referencia: más visible que antes, aún por debajo del piloto
_RTCS = "#a87fd0"  # TCS de la referencia: idem
_GMED = "#fdd835"
_GMAX = "#ff6d00"
_RGMED = "#6b5e00"
_RGMAX = "#7a3300"
_YEL = "#fdd835"

W_BEFORE = 320  # metros antes del cursor
W_AFTER = 200  # metros después del cursor
HOLD_M = 8  # retención de las luces ABS/TC: siguen encendidas estos metros
# tras la última activación, para que no parpadeen a 30/60 fps
SLIP_WIN_M = 40  # ventana CORTA detrás del cursor para DESLIZ: el deslizamiento
# que la goma acaba de sufrir, no el promedio de toda la pantalla
_FIG_W = 17  # pulgadas
_FIG_H = 5.2
_DPI = 110  # → ~1870 × 572 px


# ── utilidades de enmascarado ─────────────────────────────────────────────────


def _masked(vals, flags, active):
    """NaN donde el flag no coincide con active (corta la línea en matplotlib)."""
    if flags is None:
        return np.full_like(vals, np.nan)
    return np.where((np.asarray(flags) > 0.5) == active, vals, np.nan)


def _masked_g(vals, glat, lo, hi=None):
    """NaN fuera del rango |G-lat| ∈ [lo, hi)."""
    if glat is None:
        return np.full_like(vals, np.nan)
    cond = np.abs(glat) >= lo
    if hi is not None:
        cond &= np.abs(glat) < hi
    return np.where(cond, vals, np.nan)


# ── interpolación ─────────────────────────────────────────────────────────────

_REQUIRED_CH = ("throttle", "brake", "steering", "speed")
_OPTIONAL_CH = ("glat", "abs", "tcs", "gear")


def _interp_lap(lap, ds):
    """Interpola canales del Lap en la rejilla uniforme ds (1 m).

    Canales requeridos ausentes → zeros (el HUD puede seguir dibujándose).
    Canales opcionales ausentes → None (el renderizador los omite limpiamente).
    """
    d_orig = np.array(lap.col("dist"), dtype=float)
    out = {}
    for ch in _REQUIRED_CH:
        raw = lap.col(ch)
        out[ch] = np.interp(ds, d_orig, np.array(raw, dtype=float)) if raw else np.zeros_like(ds)
    for ch in _OPTIONAL_CH:
        raw = lap.col(ch)
        out[ch] = np.interp(ds, d_orig, np.array(raw, dtype=float)) if raw else None
    return out


# ── métricas por ventana ──────────────────────────────────────────────────────


def _flag_recent_grid(grid, i, hold):
    """True si el flag (rejilla 1 m) estuvo activo en los últimos `hold` m hasta
    el cursor. Da una luz instantánea con retención corta, no un conteo de ventana."""
    if grid is None:
        return False
    i = max(0, min(int(i), len(grid) - 1))
    seg = grid[max(0, i - int(hold)) : i + 1]
    return bool(seg.size) and float(np.max(seg)) > 0.5


def _slip_window(slip_grid, ds, lo, hi):
    """Índice de slip en la ventana visible; None si no hay serie."""
    if slip_grid is None:
        return None
    mask = (ds >= lo) & (ds <= hi)
    excess = np.maximum(0.0, np.abs(slip_grid[mask]) - 2.0)  # DEADBAND_PCT = 2
    return round(float(np.mean(excess)), 2) if excess.size else None


def _corner_lo(corner, seg_lo):
    """Borde inferior de la ventana de PROPIEDAD de la curva (ADR 0031, Opcion A).

    `segment_m` NO es contrato de contencion: `brake_start` puede caer FUERA del
    segmento que la curva declara suyo (curva cuya frenada empieza tras un kink,
    antes de `segment_m[0]`). La curva es duena de su frenada desde `brake_start`,
    asi que la frontera baja se deriva del HITO publicado, no de `segment_m` ni de
    un pad fijo: se extiende hasta `brake_start` cuando este precede al segmento.
    """
    bs = (corner.get("milestones") or {}).get("brake_start") or {}
    bd = bs.get("d")
    return min(seg_lo, bd) if bd is not None else seg_lo


def _corner_at(corners_by_seg, dist):
    """Nombre y texto de V-Min de la curva que contiene dist.

    Ante solape (una curva de frenada extendida cuya ventana de propiedad invade
    la cola del segmento de la anterior), gana la curva MAS TARDIA: es la duena de
    esos metros de frenada (ADR 0031). Por eso se conserva la ULTIMA coincidencia,
    no la primera; asi el HUD deja de etiquetar la curva anterior mientras el pace
    note ya pertenece a la siguiente.
    """
    found = None
    for (lo, hi), c in corners_by_seg:
        if _corner_lo(c, lo) <= dist <= hi:
            found = c
    if found is None:
        return "", ""
    name = found.get("name", found.get("id", ""))
    ap = (found.get("milestones") or {}).get("apex", {})
    v = ap.get("v")
    txt2 = "V-Min objetivo %d km/h" % v if v else ""
    return name, txt2


# ── figura matplotlib reutilizable ────────────────────────────────────────────


class _HUDFigure:
    """Crea la figura una sola vez; update() cambia datos sin recrear artistas."""

    def __init__(self):
        import matplotlib.pyplot as plt

        self._plt = plt

        fig, axes = plt.subplots(3, 1, figsize=(_FIG_W, _FIG_H), sharex=True)
        fig.patch.set_facecolor(_BG)
        self.fig = fig
        self.axes = axes

        # ── franja de datos (textos dinámicos) ───────────────────────────────
        kw = dict(transform=fig.transFigure, va="top")
        self.t_gap_val = fig.text(0.045, 0.985, "", color=_FRENO, fontsize=17, weight="bold", **kw)
        self.t_dv_val = fig.text(0.158, 0.985, "", color=_FG, fontsize=17, weight="bold", **kw)
        self.t_sl_val = fig.text(0.272, 0.985, "—", color=_FG, fontsize=17, weight="bold", **kw)
        self.t_sl_ref = fig.text(0.305, 0.978, "", color=_DIM, fontsize=10, **kw)
        # GASTO = desgaste acumulado DE LA VUELTA (carga de deslizamiento, ADR 0009).
        # Es CANTIDAD, no intensidad: crece a lo largo de la vuelta, NO se reinicia por
        # curva como DESLIZ. Las dos coexisten a propósito (ADR 0005, enmienda).
        self.t_load_val = fig.text(0.515, 0.985, "—", color=_FG, fontsize=15, weight="bold", **kw)
        self.t_load_ref = fig.text(0.555, 0.978, "", color=_DIM, fontsize=10, **kw)
        # luces instantáneas ABS / TC: el propio texto se enciende (color vivo)
        # cuando el flag del piloto está activo en el cursor, y se atenúa si no.
        self.t_abs_light = fig.text(
            0.385, 0.985, "ABS", color=_DIM, fontsize=15, weight="bold", **kw
        )
        self.t_tc_light = fig.text(0.448, 0.985, "TC", color=_DIM, fontsize=15, weight="bold", **kw)
        self.t_gear_val = fig.text(0.690, 0.985, "", color=_FG, fontsize=17, weight="bold", **kw)
        self.t_dist_val = fig.text(0.755, 0.985, "", color=_DIM, fontsize=14, **kw)
        self.t_spd_val = fig.text(0.835, 0.985, "", color=_FG, fontsize=14, **kw)
        self.t_corner = fig.text(
            0.988,
            0.985,
            "",
            color=_YEL,
            fontsize=15,
            weight="bold",
            va="top",
            ha="right",
            transform=fig.transFigure,
        )
        self.t_corner2 = fig.text(
            0.988,
            0.948,
            "",
            color=_DIM,
            fontsize=10,
            va="top",
            ha="right",
            transform=fig.transFigure,
        )

        # labels fijos
        fig.text(0.012, 0.97, "GAP", color=_DIM, fontsize=10, **kw)
        fig.text(0.135, 0.97, "ΔV", color=_DIM, fontsize=10, **kw)
        fig.text(0.225, 0.97, "DESLIZ", color=_DIM, fontsize=10, **kw)
        fig.text(0.470, 0.97, "GASTO", color=_DIM, fontsize=9, **kw)
        fig.text(0.635, 0.97, "MARCHA", color=_DIM, fontsize=9, **kw)
        fig.text(0.730, 0.97, "m", color=_DIM, fontsize=9, **kw)
        fig.text(0.812, 0.97, "km/h", color=_DIM, fontsize=9, **kw)

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

        # volante: divisiones cada 10° para igualar la densidad de escala de los
        # paneles de gas/freno (que van 0..100 en pasos de 20), no solo -20/0/20.
        axes[2].set_yticks([-30, -20, -10, 0, 10, 20, 30])

        axes[2].axhline(0, color="#444", lw=0.7)

        lw = 1.8
        nil = ([], [])
        l = {}

        # panel gas (índice 0)
        ax0 = axes[0]
        l["rthr"] = ax0.plot(*nil, color=_REF, lw=lw)[0]
        l["rtcs"] = ax0.plot(*nil, color=_RTCS, lw=lw)[0]
        l["dthr"] = ax0.plot(*nil, color=_GAS, lw=lw)[0]
        l["dtcs"] = ax0.plot(*nil, color=_TCS, lw=lw)[0]
        self.cur0 = ax0.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        # panel freno (índice 1)
        ax1 = axes[1]
        l["rbrk"] = ax1.plot(*nil, color=_REF, lw=lw)[0]
        l["rabs"] = ax1.plot(*nil, color=_RABS, lw=lw)[0]
        l["dbrk"] = ax1.plot(*nil, color=_FRENO, lw=lw)[0]
        l["dabs"] = ax1.plot(*nil, color=_ABS, lw=lw)[0]
        self.cur1 = ax1.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        # panel volante (índice 2)
        ax2 = axes[2]
        l["rsteer"] = ax2.plot(*nil, color=_REF, lw=lw)[0]
        l["rgmed"] = ax2.plot(*nil, color=_RGMED, lw=lw)[0]
        l["rgmax"] = ax2.plot(*nil, color=_RGMAX, lw=lw)[0]
        l["dsteer"] = ax2.plot(*nil, color=_VOL, lw=lw)[0]
        l["dgmed"] = ax2.plot(*nil, color=_GMED, lw=lw)[0]
        l["dgmax"] = ax2.plot(*nil, color=_GMAX, lw=lw)[0]
        self.cur2 = ax2.axvline(0, color=_YEL, lw=1.5, alpha=0.9)

        self.l = l
        fig.tight_layout(rect=(0, 0, 1, 0.90))

    def update(
        self,
        cur_d,
        win_d,
        rw,
        dw,
        p75,
        p90,
        gap,
        dv,
        slip_val,
        ref_slip_val,
        abs_on,
        tcs_on,
        corner_name,
        corner_txt,
        gear=None,
        speed=None,
        load_val=None,
        ref_load_val=None,
    ):
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
        self.axes[0].set_xlim(x0, x1)  # se propaga a sharex

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
        self.t_abs_light.set_color(_ABS if abs_on else _DIM)
        self.t_tc_light.set_color(_TCS if tcs_on else _DIM)
        if gear is not None:
            g = int(round(gear))
            self.t_gear_val.set_text("N" if g == 0 else ("R" if g < 0 else str(g)))
        self.t_dist_val.set_text("%d" % int(cur_d))
        self.t_spd_val.set_text("%d" % int(speed) if speed is not None else "")
        if load_val is not None:
            self.t_load_val.set_text("%.0f" % load_val)
            self.t_load_ref.set_text("ref %.0f" % ref_load_val if ref_load_val is not None else "")
        else:
            self.t_load_val.set_text("—")
            self.t_load_ref.set_text("")
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

    (
        frame_start,
        frame_end,
        ds,
        ref_ch,
        drv_ch,
        p75,
        p90,
        ref_slip,
        drv_slip,
        trace,
        n_tr,
        step,
        t_arr,
        d_arr,
        corners_by_seg,
        frames_dir,
        fps,
        t_start,
        ref_load_cum,
        drv_load_cum,
        d_offset,
    ) = args

    hud = _HUDFigure()
    last_png = None
    try:
        for n in range(frame_start, frame_end):
            t = t_start + n / fps
            i_t = max(0, min(int(np.searchsorted(t_arr, t, "right")) - 1, len(d_arr) - 1))
            cur_d = float(d_arr[i_t])

            w0 = max(0.0, cur_d - W_BEFORE)
            w1 = min(float(ds[-1]), cur_d + W_AFTER)
            mask = (ds >= w0) & (ds <= w1)
            win_d = ds[mask]

            out_path = os.path.join(frames_dir, "f%06d.png" % n)
            if win_d.size < 2:
                if last_png is not None:
                    shutil.copy(last_png, out_path)
                continue

            rw = {k: v[mask] if v is not None else None for k, v in ref_ch.items()}
            dw = {k: v[mask] if v is not None else None for k, v in drv_ch.items()}

            gap = trace[max(0, min(int(cur_d / step), n_tr - 1))]["delta_t"]
            ref_v = float(np.interp(cur_d, ds, ref_ch["speed"]))
            drv_v = float(np.interp(cur_d, ds, drv_ch["speed"]))
            dv = int(drv_v - ref_v)
            slip_d0 = max(0.0, cur_d - SLIP_WIN_M)  # ventana corta detrás del cursor
            slip_val = _slip_window(drv_slip, ds, slip_d0, cur_d)
            ref_slip_val = _slip_window(ref_slip, ds, slip_d0, cur_d)
            abs_on = _flag_recent_grid(drv_ch.get("abs"), cur_d - d_offset, HOLD_M)
            tcs_on = _flag_recent_grid(drv_ch.get("tcs"), cur_d - d_offset, HOLD_M)
            corner_name, corner_txt = _corner_at(corners_by_seg, cur_d)

            gear = (
                float(np.interp(cur_d, ds, drv_ch["gear"]))
                if drv_ch.get("gear") is not None
                else None
            )

            def _load_at(cum):
                if cum is None:
                    return None
                j = max(0, min(int(cur_d) - d_offset, len(cum) - 1))
                return float(cum[j])

            load_val = _load_at(drv_load_cum)
            ref_load_val = _load_at(ref_load_cum)

            hud.update(
                cur_d,
                win_d,
                rw,
                dw,
                p75,
                p90,
                gap,
                dv,
                slip_val,
                ref_slip_val,
                abs_on,
                tcs_on,
                corner_name,
                corner_txt,
                gear=gear,
                speed=drv_v,
                load_val=load_val,
                ref_load_val=ref_load_val,
            )
            hud.to_pil().save(out_path)
            last_png = out_path
    finally:
        hud.close()

    return frame_end - frame_start


# ── render paralelo vía subprocess ───────────────────────────────────────────


def _kill_all(procs):
    for p in procs:
        try:
            p.kill()
        except OSError:
            pass
    for p in procs:
        try:
            p.wait()
        except OSError:
            pass


def _render_parallel(chunks, base, n_frames, progress):
    """Lanza un subprocess por chunk usando python -m fantasma.viz._overlay_worker.

    Evita el crash de ProcessPoolExecutor(spawn) bajo Streamlit: el proceso
    hijo intentaba reimportar __main__ del servidor de Streamlit y caía en
    cascada, forzando el fallback al render serial (1 core).

    Soporta cancelación: si progress() lanza cualquier excepción (ej.
    RuntimeError("__CANCELLED__")), mata todos los workers inmediatamente.

    Optimizaciones:
    - Collect round-robin: todos los workers se sondean en cada iteración;
      un worker lento no bloquea la recolección de los rápidos.
    - Pickle compacto: cada worker recibe solo el slice de arrays que cubre
      su rango de distancia (+ padding de ventana HUD y retención ABS/TC).
      En Nordschleife esto reduce el pkl de ~4-5 MB a ~1 MB por worker.
    """
    (
        ds,
        ref_ch,
        drv_ch,
        p75,
        p90,
        ref_slip,
        drv_slip,
        trace,
        n_tr,
        step,
        t_arr,
        d_arr,
        corners_by_seg,
        frames_dir,
        fps,
        t_start,
        ref_load_cum,
        drv_load_cum,
        _,
    ) = base

    worker_cmd = [sys.executable, "-m", "fantasma.viz._overlay_worker"]
    procs, tmp_files = [], []
    chunk_args_map: dict = {}

    for s, e in chunks:
        # Rango de tiempo de este chunk → rango de distancia recorrida.
        t_min = t_start + s / fps
        t_max = t_start + (e - 1) / fps
        i_s = max(0, int(np.searchsorted(t_arr, t_min, "right")) - 1)
        i_e = min(len(t_arr) - 1, int(np.searchsorted(t_arr, t_max, "right")))

        d_chunk = d_arr[i_s : i_e + 1]
        d_min = float(d_chunk.min()) if d_chunk.size else 0.0
        d_max = float(d_chunk.max()) if d_chunk.size else float(ds[-1])

        # Padding: ventana HUD (W_BEFORE/W_AFTER) + retención de luces ABS/TC.
        d_lo = max(0, int(d_min) - W_BEFORE - HOLD_M)
        d_hi = min(len(ds), int(d_max) + W_AFTER + 2)
        d_offset = d_lo

        ds_sl = ds[d_lo:d_hi].copy()
        ref_ch_sl = {k: (v[d_lo:d_hi].copy() if v is not None else None) for k, v in ref_ch.items()}
        drv_ch_sl = {k: (v[d_lo:d_hi].copy() if v is not None else None) for k, v in drv_ch.items()}
        ref_slip_sl = ref_slip[d_lo:d_hi].copy() if ref_slip is not None else None
        drv_slip_sl = drv_slip[d_lo:d_hi].copy() if drv_slip is not None else None
        ref_load_sl = ref_load_cum[d_lo:d_hi].copy() if ref_load_cum is not None else None
        drv_load_sl = drv_load_cum[d_lo:d_hi].copy() if drv_load_cum is not None else None
        t_arr_sl = t_arr[max(0, i_s - 1) : i_e + 2].copy()
        d_arr_sl = d_arr[max(0, i_s - 1) : i_e + 2].copy()

        chunk_args = (
            s,
            e,
            ds_sl,
            ref_ch_sl,
            drv_ch_sl,
            p75,
            p90,
            ref_slip_sl,
            drv_slip_sl,
            trace,
            n_tr,
            step,
            t_arr_sl,
            d_arr_sl,
            corners_by_seg,
            frames_dir,
            fps,
            t_start,
            ref_load_sl,
            drv_load_sl,
            d_offset,
        )

        chunk_args_map[(s, e)] = chunk_args
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
        pickle.dump(chunk_args, tmp)
        tmp.close()
        tmp_files.append(tmp.name)
        procs.append(
            subprocess.Popen(
                worker_cmd + [tmp.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )

    failed = []
    done = 0
    try:
        # Round-robin: todos los workers se sondean en cada pasada.
        # Un worker lento no bloquea la recolección de los que ya terminaron.
        pending = list(zip(procs, tmp_files, chunks))
        while pending:
            still_pending = []
            for p, tmp_f, (s, e) in pending:
                ret = p.poll()
                if ret is None:
                    still_pending.append((p, tmp_f, (s, e)))
                else:
                    try:
                        os.unlink(tmp_f)
                    except OSError:
                        pass
                    if ret != 0:
                        failed.append((s, e))
                    else:
                        done += e - s
                        if progress:
                            progress(done, n_frames)
            pending = still_pending
            if pending:
                time.sleep(0.5)
                if progress:
                    progress(done, n_frames)  # para que cancel_event se chequee
    except BaseException:
        _kill_all(procs)
        # limpiar pkls restantes
        for f in tmp_files:
            try:
                os.unlink(f)
            except OSError:
                pass
        raise

    # fallback serial para cualquier chunk que haya fallado (usa el mismo slice que el worker)
    for s, e in failed:
        _render_chunk(chunk_args_map[(s, e)])
        done += e - s
        if progress:
            progress(done, n_frames)


# ── función principal ─────────────────────────────────────────────────────────


def _run_ffmpeg(cmd, n_frames, progress):
    """Corre ffmpeg y alimenta el callback de progreso leyendo stdout en tiempo real."""
    cmd_p = [cmd[0], "-progress", "pipe:1", "-nostats"] + cmd[1:]
    pat = re.compile(r"^frame=(\d+)")
    err_f = tempfile.TemporaryFile(mode="w+b")
    proc = subprocess.Popen(cmd_p, stdout=subprocess.PIPE, stderr=err_f, text=True)
    try:
        for line in proc.stdout:
            if progress and n_frames > 0:
                m = pat.match(line.strip())
                if m:
                    enc = int(m.group(1))
                    progress(
                        enc, n_frames, status="Codificando video… frame %d / %d" % (enc, n_frames)
                    )
    except BaseException:
        proc.kill()
        proc.wait()
        err_f.close()
        raise
    else:
        proc.wait()
    if proc.returncode != 0:
        err_f.seek(0)
        tail = b"".join(err_f.readlines()[-15:]).decode("utf-8", errors="replace").strip()
        err_f.close()
        raise RuntimeError(
            "ffmpeg falló (código %d). Últimas líneas:\n%s" % (proc.returncode, tail)
        )
    err_f.close()


def render_overlay(
    ref, drv, corners, outdir, fps=30, fmt="webm", t_start=0.0, t_end=None, progress=None
):
    """Renderiza el overlay HUD-A. Devuelve ruta del video o carpeta de frames."""
    try:
        import matplotlib

        matplotlib.use("Agg")
    except ImportError:
        raise ImportError(
            "matplotlib requerido para el overlay: pip install 'fantasma-inputs[overlay]'"
        )

    from ..core import wear
    from ..core.compare import delta_trace

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

    # carga de deslizamiento acumulada DE LA VUELTA (ADR 0009): cantidad extensiva,
    # Σ (exceso de slip / 100) × Δdist. Como ds tiene paso de 1 m, es cumsum del exceso.
    def _load_cum(slip_grid):
        if slip_grid is None:
            return None
        excess = np.maximum(0.0, np.abs(slip_grid) - wear.DEADBAND_PCT) / 100.0
        return np.cumsum(excess)  # Δds = 1 m

    ref_load_cum = _load_cum(ref_slip)
    drv_load_cum = _load_cum(drv_slip)

    # delta en tiempo (5 m de resolución)
    step = 5.0
    trace = delta_trace(ref, drv, step)
    n_tr = len(trace)

    # tiempo → distancia del piloto
    t_arr = np.array(drv.col("time"), dtype=float)
    d_arr = np.array(drv.col("dist"), dtype=float)

    # corners: ((lo, hi), dict)
    def _seg(c):
        return c.get("segment_m") or c.get("range_m") or [0.0, 0.0]

    # El desempate "ULTIMA gana" de _corner_at (ADR 0031) solo es correcto si los
    # corners llegan ordenados ascendente por pista: la curva mas tardia que solapa
    # es la que debe ganar los metros de frenada. Auto-detect (detect_corners) y la
    # UI ya entregan ese orden, pero --corners fichero.json hace json.load SIN
    # reordenar; se blinda aqui. Es no-op para el input ya ordenado.
    corners_by_seg = sorted([((_seg(c)[0], _seg(c)[1]), c) for c in corners], key=lambda t: t[0][0])

    # ── render paralelo de frames ─────────────────────────────────────────────
    frames_dir = os.path.join(outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    t_end = t_end if t_end is not None else float(t_arr[-1])
    n_frames = int((t_end - t_start) * fps)

    n_workers = max(1, (os.cpu_count() or 1) - 1)

    base = (
        ds,
        ref_ch,
        drv_ch,
        p75,
        p90,
        ref_slip,
        drv_slip,
        trace,
        n_tr,
        step,
        t_arr,
        d_arr,
        corners_by_seg,
        frames_dir,
        fps,
        t_start,
        ref_load_cum,
        drv_load_cum,
        0,  # d_offset — 0 para el caso serial (arrays completos)
    )

    if n_workers <= 1:
        _render_chunk((0, n_frames, *base))
        if progress:
            progress(n_frames, n_frames)
    else:
        chunk_sz = max(1, (n_frames + n_workers - 1) // n_workers)
        chunks = [(i, min(n_frames, i + chunk_sz)) for i in range(0, n_frames, chunk_sz)]
        _render_parallel(chunks, base, n_frames, progress)

    if fmt == "png":
        return frames_dir

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("aviso: ffmpeg no encontrado — frames en %s" % frames_dir)
        return frames_dir

    n_cpu = os.cpu_count() or 4

    if fmt == "webm":
        out = os.path.join(outdir, "overlay.webm")
        # VP9 alpha no tiene encoder GPU disponible; row-mt aprovecha todos los cores
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            os.path.join(frames_dir, "f%06d.png"),
            "-c:v",
            "libvpx-vp9",
            "-pix_fmt",
            "yuva420p",
            "-b:v",
            "2M",
            "-row-mt",
            "1",
            "-threads",
            str(n_cpu),
            out,
        ]
    else:
        out = os.path.join(outdir, "overlay.mov")
        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            os.path.join(frames_dir, "f%06d.png"),
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4444",
            "-pix_fmt",
            "yuva444p10le",
            out,
        ]

    _run_ffmpeg(cmd, n_frames, progress)
    shutil.rmtree(frames_dir, ignore_errors=True)
    return out
