"""Preview de un frame del HUD para el Paso 4 de la UI NiceGUI."""

import os
import subprocess
import tempfile


def compose_preview_frame(overlay_path: str, position: str, scale: float):
    """Extrae el primer frame del overlay .webm y lo compone sobre un fondo oscuro.

    Devuelve un PIL Image (RGB) listo para serializar a base64.
    """
    from PIL import Image

    # Extraer frame 0 del overlay con ffmpeg
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
    os.close(tmp_fd)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", overlay_path, "-vframes", "1", "-q:v", "2", tmp_path],
            capture_output=True,
            check=True,
        )
        hud = Image.open(tmp_path).convert("RGBA")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # Fondo representativo (1280x720, gris oscuro como asfalto)
    W, H = 1280, 720
    bg = Image.new("RGBA", (W, H), (30, 30, 35, 255))

    # Escalar el HUD
    new_w = int(hud.width * scale)
    new_h = int(hud.height * scale)
    if new_w < 1:
        new_w = 1
    if new_h < 1:
        new_h = 1
    hud_scaled = hud.resize((new_w, new_h), Image.LANCZOS)

    # Posicionar
    margin = 20
    _positions = {
        "bottom-right": (W - new_w - margin, H - new_h - margin),
        "bottom-left": (margin, H - new_h - margin),
        "top-right": (W - new_w - margin, margin),
        "top-left": (margin, margin),
        "bottom-center": ((W - new_w) // 2, H - new_h - margin),
        "top-center": ((W - new_w) // 2, margin),
        "center": ((W - new_w) // 2, (H - new_h) // 2),
    }
    x, y = _positions.get(position, _positions["bottom-right"])
    bg.paste(hud_scaled, (x, y), hud_scaled)

    return bg.convert("RGB")
