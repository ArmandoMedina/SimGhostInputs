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


def _total_frames(ffmpeg_path, video_path):
    """Estima el total de frames del video para calcular % de progreso."""
    ffprobe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
    if not shutil.which(ffprobe):
        ffprobe = shutil.which("ffprobe") or ""
    if not ffprobe:
        return 0
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


def _build_filter(position, scale, offset):
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
                  offset=0.0, scale=1.0, progress=None):
    """Superpone overlay con canal alfa sobre el video de grabación.

    Args:
        video:    Ruta al video de la grabación (mp4, mov, mkv…).
        overlay:  Ruta al overlay con canal alfa (.webm VP9 o .mov ProRes 4444).
        output:   Ruta del archivo de salida.
        position: Posición del HUD ('bottom-right', 'top-left', etc.).
        offset:   Segundos de delay del overlay (positivo = overlay empieza
                  después; útil si el video arranca antes de la vuelta).
        scale:    Factor de escala del overlay (1.0 = tamaño original).

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

    fc = _build_filter(position, scale, offset)

    use_nvenc = _nvenc_available(ffmpeg)
    if use_nvenc:
        video_enc = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "18", "-b:v", "0"]
    else:
        video_enc = ["-c:v", "libx264", "-crf", "18", "-preset", "fast"]

    n_frames = _total_frames(ffmpeg, video) if progress else 0

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
