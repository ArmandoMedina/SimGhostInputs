# Subtitulos para la cinta de estudio (pedido del PO, 2026-07-06): cada sonido
# del pack aparece rotulado en pantalla en el segundo en que suena, para saber
# que significa sin memorizar la leyenda. El .srt se incrusta como pista de
# subtitulos mov_text SIN re-encodear (-c copy) y se puede prender/apagar en el
# reproductor (VLC/Windows los muestran solos).
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

from fantasma.importers import load_laps
from fantasma.viz.pacenotes import _dist_to_time

DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
PACK = Path(r"C:\Users\amedina\Downloads\0207\_pack_COMPLETO")
VIDEO = r"C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO.mp4"
SRT = Path(r"C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO.srt")
OUT = r"C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO_SUBS.mp4"

# rotulo por tipo de cue (descripcion del metadata: "<curva> — <label>")
ROTULOS = {
    "contador de frenada": "🔔 3-2-1 FRENA en ~3 s",
    "punto de frenada": "🛑 FRENA aquí",
    "soltar freno": "🌊 suelta el freno",
    "turn-in": "↪ gira",
    "apex": "🎯 apex",
    "inicio de acelerador": "🟢 gas progresivo",
    "gas completo": "🚀 gas a fondo",
}


def fmt(t):
    ms = int(round((t % 1) * 1000))
    s = int(t)
    return "%02d:%02d:%02d,%03d" % (s // 3600, (s % 3600) // 60, s % 60, ms)


drv = min(
    (lap for lap in load_laps(DRV) if lap.has("dist") and lap.has("time") and lap.laptime > 60),
    key=lambda lap: abs(lap.laptime - 394.05),
)
entries = json.loads((PACK / "metadata.json").read_text(encoding="utf-8"))["entries"]

subs = []
for e in entries:
    d = float(e.get("distanceRoundTrack") or 0)
    t = _dist_to_time(drv, d)
    desc = e.get("description") or "?"
    corner, _, label = desc.partition(" — ")
    if label == "upshift":
        text = "⬆ %s — así cambia el rápido" % corner.replace(" (referencia)", "")
    else:
        text = "%s — %s" % (ROTULOS.get(label, label), corner)
    subs.append((t, text))

subs.sort()
# agrupa sonidos a <1 s en un solo subtitulo (no encimar lineas ilegibles)
grouped = []
for t, text in subs:
    if grouped and t - grouped[-1][0] < 1.0:
        grouped[-1][1].append(text)
    else:
        grouped.append((t, [text]))

lines = []
for i, (t, texts) in enumerate(grouped, 1):
    end = min(t + 2.0, grouped[i][0] - 0.05) if i < len(grouped) else t + 2.0
    lines.append("%d\n%s --> %s\n%s\n" % (i, fmt(t), fmt(max(t, end - 0.01) if end <= t else end), "\n".join(texts)))
SRT.write_text("\n".join(lines), encoding="utf-8")
print("srt: %d rotulos (%d sonidos) -> %s" % (len(grouped), len(subs), SRT))

subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", VIDEO,
        "-i", str(SRT),
        "-map", "0", "-map", "1",
        "-c", "copy", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=spa",
        OUT,
    ],
    check=True,
    capture_output=True,
)
print("video con subtitulos:", OUT)
