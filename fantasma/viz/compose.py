"""Compositor: superpone el overlay (canal alfa) sobre el video de grabación con ffmpeg."""
import os
import re
import shutil
import subprocess

POSITIONS = {
    "top-left":      ("0",        "0"),
    "top-right":     ("W-w",      "0"),
    "bottom-left":   ("0",        "H-h"),
    "bottom-right":  ("W-w",      "H-h"),
    "top-center":    ("(W-w)/2",  "0"),
    "bottom-center": ("(W-w)/2",  "H-h"),
    "center":        ("(W-w)/2",  "(H-h)/2"),
}


def _ffprobe_path(ffmpeg_path):
    probe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
    return probe if shutil.which(probe) else (shutil.which("ffprobe") or "")


def _video_fps(ffprobe, video_path):
    """Devuelve los fps del video como float, o 0 si no se puede obtener."""
    try:
        r = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True,
        )
        line = r.stdout.strip()
        num, _, den = line.partition("/")
        return float(num) / float(den) if den else float(num)
    except Exception:
        return 0.0


def _total_frames(ffmpeg_path, video_path, lap_duration=None):
    """Estima frames totales para la barra de progreso.

    Si lap_duration está disponible calcula fps * lap_duration (más preciso
    para el modelo de recorte). Sin él cae al conteo completo del video.
    """
    ffprobe = _ffprobe_path(ffmpeg_path)
    if not ffprobe:
        return 0
    if lap_duration:
        fps = _video_fps(ffprobe, video_path)
        return int(lap_duration * fps) if fps else 0
    try:
        r = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=nb_frames,r_frame_rate",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True,
        )
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        for line in lines:
            if line.isdigit():
                return int(line)
        fps_line = next((l for l in lines if "/" in l), None)
        dur_line = next((l for l in lines if "." in l), None)
        if fps_line and dur_line:
            num, _, den = fps_line.partition("/")
            fps = float(num) / float(den) if den else float(num)
            return int(float(dur_line) * fps)
    except Exception:
        pass
    return 0


def _nvenc_available(ffmpeg_path):
    """Devuelve True si h264_nvenc está disponible en este ffmpeg."""
    try:
        r = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True, text=True,
        )
        return "h264_nvenc" in r.stdout
    except Exception:
        return False


def _build_filter(position, scale, offset=0.0):
    """Construye el filtro ffmpeg para superponer el overlay.

    offset solo se usa en modo legacy (sin recorte). En modo recorte el seek
    ya posicionó el video y el overlay empieza en t=0.
    """
    px, py = POSITIONS.get(position, POSITIONS["bottom-right"])
    steps = []
    cur = "1:v"

    if scale != 1.0:
        steps.append("[%s]scale=iw*%.6f:ih*%.6f[ov_s]" % (cur, scale, scale))
        cur = "ov_s"

    if offset != 0.0:
        steps.append("[%s]setpts=PTS+%.6f/TB[ov_d]" % (cur, offset))
        cur = "ov_d"

    steps.append("[0:v][%s]overlay=x=%s:y=%s[out]" % (cur, px, py))
    return ";".join(steps)


def compose_video(video, overlay, output, position="bottom-right",
                  offset=0.0, scale=1.0, lap_duration=None, progress=None):
    """Superpone overlay con canal alfa sobre el video de grabación.

    Cuando lap_duration está disponible (recomendado) el output es un clip
    recortado que empieza en `offset` y dura exactamente `lap_duration`
    segundos — sin importar la duración del video original. Esto garantiza
    tiempos de compose consistentes independientemente del largo de la sesión.

    Sin lap_duration el comportamiento es el legado: offset demora el overlay
    via setpts y el output tiene la duración completa del video.

    Args:
        video:        Ruta al video de grabación (mp4, mov, mkv…).
        overlay:      Ruta al overlay con canal alfa (.webm VP9 o .mov ProRes).
        output:       Ruta del archivo de salida.
        position:     Posición del HUD en pantalla.
        offset:       Segundos desde el inicio del video hasta la vuelta.
        scale:        Factor de escala del HUD (1.0 = tamaño original).
        lap_duration: Duración de la vuelta en segundos. Si se provee, el
                      output se recorta a exactamente esa duración.
        progress:     Callback progress(n_frames, total_frames) para UI.

    Returns:
        Ruta del archivo de salida.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg no encontrado en PATH — instálalo con: winget install Gyan.FFmpeg"
        )

    out_dir = os.path.dirname(output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    use_nvenc = _nvenc_available(ffmpeg)
    if use_nvenc:
        video_enc = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "18", "-b:v", "0"]
    else:
        video_enc = ["-c:v", "libx264", "-crf", "18", "-preset", "fast"]

    n_frames = _total_frames(ffmpeg, video, lap_duration) if progress else 0

    if lap_duration:
        # Modo recorte: seek rápido al offset, output limitado a la vuelta.
        # El overlay empieza en t=0 del clip resultante (no necesita setpts).
        fc = _build_filter(position, scale, offset=0.0)
        cmd = [
            ffmpeg, "-y",
            "-ss", "%.3f" % offset,
            "-i", video,
            "-i", overlay,
            "-filter_complex", fc,
            "-map", "[out]",
            "-map", "0:a?",
            *video_enc,
            "-c:a", "aac", "-b:a", "192k",
            "-t", "%.3f" % lap_duration,
            output,
        ]
    else:
        # Modo legado: overlay demora via setpts, video completo.
        fc = _build_filter(position, scale, offset)
        cmd = [
            ffmpeg, "-y",
            "-i", video,
            "-i", overlay,
            "-filter_complex", fc,
            "-map", "[out]",
            "-map", "0:a?",
            *video_enc,
            "-c:a", "aac", "-b:a", "192k",
            output,
        ]

    if progress:
        cmd_p = [cmd[0], "-progress", "pipe:1", "-nostats"] + cmd[1:]
        pat = re.compile(r"^frame=(\d+)")
        proc = subprocess.Popen(cmd_p, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
        try:
            for line in proc.stdout:
                m = pat.match(line.strip())
                if m and n_frames > 0:
                    f = int(m.group(1))
                    progress(f, n_frames)
        finally:
            proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
    else:
        subprocess.run(cmd, check=True)

    return output
