"""Genera docs/icon.ico con un fantasma en la paleta dark del UI."""
import io
import struct

from PIL import Image, ImageDraw


def draw_ghost(size):
    s = size
    pad = s * 0.08
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    body = (220, 220, 235, 255)
    accent = (100, 180, 255, 255)
    bg = (8, 9, 13, 255)

    d.rectangle([0, 0, s, s], fill=bg)

    left, top = pad, pad * 1.2
    right, bottom = s - pad, s - pad * 0.5
    head_h = right - left

    d.ellipse([left, top, right, top + head_h * 0.85], fill=body)
    mid_y = top + head_h * 0.85 * 0.5
    d.rectangle([left, mid_y, right, bottom - s * 0.15], fill=body)

    wave_w = (right - left) / 3
    wave_h = s * 0.16
    for i in range(3):
        wx = left + i * wave_w
        d.ellipse([wx, bottom - wave_h * 2, wx + wave_w, bottom], fill=bg)

    eye_y = top + head_h * 0.32
    eye_r = s * 0.07
    eye_off = (right - left) * 0.22
    cx = (left + right) / 2
    for sign in (-1, 1):
        ex = cx + sign * eye_off
        d.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=accent)

    return img


def build_ico(frames):
    """Construye un ICO con PNG embebidos para soporte de 256x256."""
    images = []
    for sz in sorted(frames):
        buf = io.BytesIO()
        frames[sz].save(buf, format="PNG")
        images.append((sz, buf.getvalue()))

    n = len(images)
    header = struct.pack("<HHH", 0, 1, n)
    offset = 6 + n * 16
    entries = b""
    data = b""
    for sz, png_bytes in images:
        w = sz if sz < 256 else 0
        h = sz if sz < 256 else 0
        entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png_bytes), offset)
        entries += entry
        offset += len(png_bytes)
        data += png_bytes
    return header + entries + data


if __name__ == "__main__":
    sizes = [16, 32, 48, 64, 128, 256]
    frames = {s: draw_ghost(s) for s in sizes}

    ico_bytes = build_ico(frames)
    out = "docs/icon.ico"
    with open(out, "wb") as f:
        f.write(ico_bytes)

    frames[256].save("docs/icon_preview.png")
    print(f"ICO generado: {out}  ({len(ico_bytes)//1024} KB, {len(sizes)} tamanos)")
    print("Preview: docs/icon_preview.png")
