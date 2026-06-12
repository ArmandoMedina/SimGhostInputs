"""Overlay HUD animado con transparencia, para superponer sobre el video real.

Genera una secuencia de frames PNG (RGBA) sincronizada con el TIEMPO de la vuelta
del piloto, y opcionalmente la codifica con ffmpeg a un video con canal alfa:
  - prores  -> .mov ProRes 4444 (alfa, compatible con Premiere/DaVinci/CapCut)
  - webm    -> .webm VP9 con alfa (mas ligero, editores modernos y OBS)
  - png     -> solo la secuencia de frames

El HUD muestra: barras de freno y gas (tu vs referencia en el mismo metro),
velocidades, delta acumulado, nombre de curva y franja de velocidad (ultimos metros).
"""
import bisect
import os
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 300
REF = (154, 160, 166, 230)
DRV_BRAKE = (255, 23, 68, 255)
DRV_GAS = (0, 200, 83, 255)
DRV_SPEED = (255, 109, 0, 255)
FG = (232, 234, 237, 255)
DIM = (232, 234, 237, 140)
PANEL = (10, 12, 16, 150)
YELLOW = (253, 216, 53, 255)


def _font(size):
    for name in ("arialbd.ttf", "arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class _LapIndex:
    """Acceso por tiempo y por distancia a una vuelta (canales crudos)."""

    def __init__(self, lap):
        self.t = lap.col("time")
        self.d = lap.col("dist")
        self.ch = lap.channels

    def at_time(self, t):
        i = bisect.bisect_right(self.t, t) - 1
        return max(0, min(i, len(self.t) - 1))

    def at_dist(self, d):
        i = bisect.bisect_right(self.d, d) - 1
        return max(0, min(i, len(self.d) - 1))

    def val(self, name, i, default=0.0):
        c = self.ch.get(name)
        return c[i] if c else default


def _bar(draw, x, y, h, w, pct, color, label, font):
    """Barra vertical 0-100 con fondo."""
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255, 28))
    fill_h = int(h * max(0, min(100, pct)) / 100.0)
    draw.rectangle([x, y + h - fill_h, x + w, y + h], fill=color)
    draw.text((x + w / 2, y + h + 6), label, font=font, fill=DIM, anchor="ma")


def render_frame(img_draw, ref_ix, drv_ix, t, corners_by_seg, delta_at, fonts):
    draw = img_draw
    f_big, f_med, f_small = fonts
    di = drv_ix.at_time(t)
    dist = drv_ix.d[di]
    ri = ref_ix.at_dist(dist)

    # panel de fondo
    draw.rounded_rectangle([10, 10, W - 10, H - 10], radius=18, fill=PANEL)

    # --- barras freno / gas (ref gris al lado de las tuyas) ---
    bh, bw, y0 = 180, 34, 38
    x = 60
    _bar(draw, x, y0, bh, bw, ref_ix.val("brake", ri), REF, "", f_small)
    _bar(draw, x + 44, y0, bh, bw, drv_ix.val("brake", di), DRV_BRAKE, "", f_small)
    draw.text((x + 22 + bw / 2, y0 + bh + 6), "FRENO", font=f_small, fill=DIM, anchor="ma")
    x = 220
    _bar(draw, x, y0, bh, bw, ref_ix.val("throttle", ri), REF, "", f_small)
    _bar(draw, x + 44, y0, bh, bw, drv_ix.val("throttle", di), DRV_GAS, "", f_small)
    draw.text((x + 22 + bw / 2, y0 + bh + 6), "GAS", font=f_small, fill=DIM, anchor="ma")
    draw.text((60 + bw / 2, y0 - 26), "ref", font=f_small, fill=DIM, anchor="ma")

    # --- velocidad y marcha ---
    v_drv = drv_ix.val("speed", di)
    v_ref = ref_ix.val("speed", ri)
    g_drv = int(drv_ix.val("gear", di))
    draw.text((420, 60), "%3.0f" % v_drv, font=f_big, fill=DRV_SPEED)
    draw.text((420, 150), "ref %3.0f km/h" % v_ref, font=f_small, fill=DIM)
    draw.text((420, 185), "marcha %d" % g_drv, font=f_small, fill=DIM)
    dv = v_drv - v_ref
    if abs(dv) >= 8:
        draw.text((570, 185), "%+.0f" % dv, font=f_small,
                  fill=DRV_BRAKE if dv < 0 else DRV_GAS)

    # --- delta acumulado ---
    dt = delta_at(dist)
    color = DRV_BRAKE if dt > 0.05 else (DRV_GAS if dt < -0.05 else FG)
    draw.text((760, 60), "%+.2f s" % dt, font=f_big, fill=color)
    draw.text((760, 150), "delta vs referencia", font=f_small, fill=DIM)

    # --- curva actual ---
    name, flash = "", None
    for (lo, hi), c in corners_by_seg:
        if lo <= dist <= hi:
            name = c.get("name", c.get("id", ""))
            ap = c["milestones"]["apex"]
            flash = "ápex m%d · V-Min ref %d" % (ap["d"], ap["v"])
            break
    draw.text((1100, 60), name, font=f_med, fill=YELLOW)
    if flash:
        draw.text((1100, 120), flash, font=f_small, fill=DIM)
    draw.text((1100, 185), "m %s" % "{:,}".format(int(dist)), font=f_small, fill=DIM)

    # --- franja de velocidad (ultimos 500m, tu naranja sobre ref gris) ---
    fx0, fx1, fy0, fy1 = 1450, W - 50, 50, 230
    draw.rectangle([fx0, fy0, fx1, fy1], fill=(255, 255, 255, 18))
    span = 500.0
    vmax = 300.0
    pts_ref, pts_drv = [], []
    for k in range(60):
        dd = dist - span + span * k / 59.0
        if dd < 0:
            continue
        xr = fx0 + (fx1 - fx0) * k / 59.0
        rr = ref_ix.at_dist(dd)
        dr = drv_ix.at_dist(dd)
        pts_ref.append((xr, fy1 - (fy1 - fy0) * min(vmax, ref_ix.val("speed", rr)) / vmax))
        pts_drv.append((xr, fy1 - (fy1 - fy0) * min(vmax, drv_ix.val("speed", dr)) / vmax))
    if len(pts_ref) > 1:
        draw.line(pts_ref, fill=REF, width=3)
        draw.line(pts_drv, fill=DRV_SPEED, width=2)
    draw.text((fx0 + 4, fy1 + 6), "velocidad · últimos 500 m", font=f_small, fill=DIM)


def render_overlay(ref, drv, corners, outdir, fps=30, fmt="prores",
                   t_start=0.0, t_end=None, progress=None):
    """Renderiza el overlay de la vuelta del piloto. Devuelve la ruta del video o carpeta."""
    from ..core.compare import delta_trace
    trace = delta_trace(ref, drv, 5.0)
    step = 5.0

    def delta_at(dist):
        i = max(0, min(int(dist / step), len(trace) - 1))
        return trace[i]["delta_t"]

    ref_ix, drv_ix = _LapIndex(ref), _LapIndex(drv)
    corners_by_seg = [((c.get("segment_m") or c.get("range_m"))[0],
                       (c.get("segment_m") or c.get("range_m"))[1]) for c in corners]
    corners_by_seg = list(zip(corners_by_seg, corners))
    fonts = (_font(72), _font(44), _font(22))

    frames_dir = os.path.join(outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    t_end = t_end if t_end is not None else drv_ix.t[-1]
    n_frames = int((t_end - t_start) * fps)
    for n in range(n_frames):
        t = t_start + n / fps
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        render_frame(ImageDraw.Draw(img), ref_ix, drv_ix, t, corners_by_seg, delta_at, fonts)
        img.save(os.path.join(frames_dir, "f%06d.png" % n))
        if progress and n % (fps * 10) == 0:
            progress(n, n_frames)

    if fmt == "png":
        return frames_dir
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("aviso: ffmpeg no encontrado; quedan los frames PNG en %s" % frames_dir)
        return frames_dir
    if fmt == "webm":
        out = os.path.join(outdir, "overlay.webm")
        cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i",
               os.path.join(frames_dir, "f%06d.png"),
               "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2M", out]
    else:
        out = os.path.join(outdir, "overlay.mov")
        cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i",
               os.path.join(frames_dir, "f%06d.png"),
               "-c:v", "prores_ks", "-profile:v", "4444",
               "-pix_fmt", "yuva444p10le", out]
    subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(frames_dir, ignore_errors=True)
    return out
