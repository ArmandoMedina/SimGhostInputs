# Cinta de estudio (pedido del PO, 2026-07-06): el video del PO con la banda
# sonora COMPLETA de la REFERENCIA — todos los cues de coaching (pack ADR 0024,
# top=0) MAS un beep en cada cambio de marcha HACIA ARRIBA de la referencia.
# Proposito: aprender que significa cada sonido y cuando llega, sin pista.
# Todo sale de la vuelta de REFERENCIA (donde maneja el rapido); la vuelta del
# PO solo mapea distancia->tiempo del video (calibracion verificada al 0.1%).
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

from fantasma.core.compare import compare
from fantasma.core.corners import detect_corners, extract_milestones
from fantasma.importers import load_laps
from fantasma.viz.compose import mux_pace_notes_into_video
from fantasma.viz.pacenotes import (
    _metadata_entry,
    build_tone_pack,
    generate_tone,
)

REF = r"C:\Repositorio personal\Paterial para test (no es un repo)\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
VIDEO = r"C:\Users\amedina\Downloads\0207\frames\2_composed.mp4"
PACK = Path(r"C:\Users\amedina\Downloads\0207\_pack_COMPLETO")
OUT = r"C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO.mp4"


def pick(laps, target=None):
    valid = [lap for lap in laps if lap.has("dist") and lap.has("time") and lap.laptime > 60]
    if target is None:
        return min(valid, key=lambda lap: lap.laptime)
    return min(valid, key=lambda lap: abs(lap.laptime - target))


ref = pick(load_laps(REF))
drv = pick(load_laps(DRV), 394.05)
print("ref=%.2f s (fuente de TODOS los sonidos)  drv=%.2f s (solo mapeo al video)" % (ref.laptime, drv.laptime))

# 1) Pack de coaching completo (top=0, motor ADR 0024) desde la referencia
if PACK.exists():
    shutil.rmtree(PACK)
evs, _ = detect_corners(ref)
corners = extract_milestones(ref, evs)
_, rows, _ = compare(ref, drv, step=1.0, corners=corners)
res = build_tone_pack(rows, corners, str(PACK), top=0, countdown_s=3.5, track_name="Nordschleife")
print("coaching: %d cues" % res["entries"])

# 2) Upshifts DE LA REFERENCIA (el canal gear pasa por 0 en cada cambio)
gear = ref.col("gear")
dist = ref.col("dist")
ups = []
last_engaged = 0
for i in range(len(gear)):
    g = int(gear[i])
    if g <= 0:
        continue
    if last_engaged >= 1 and g > last_engaged:
        if not ups or dist[i] - ups[-1][0] > 5:
            ups.append((dist[i], g))
    last_engaged = g
print("upshifts de la referencia: %d" % len(ups))

meta_path = PACK / "metadata.json"
meta = json.loads(meta_path.read_text(encoding="utf-8"))
for d, g in ups:
    filename = "u%d_0.wav" % int(d)
    # 1500 Hz, mas agudo que todos los cues de coaching (max 1000 Hz): se
    # distingue como "aqui sube marcha el rapido"
    (PACK / filename).write_bytes(generate_tone(1500, 0.07, volume=0.85))
    meta["entries"].append(_metadata_entry("subida a %da (referencia)" % g, "upshift", int(d), filename))
meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print("pack completo: %d sonidos (%d coaching + %d upshifts)" % (len(meta["entries"]), res["entries"], len(ups)))

out = mux_pace_notes_into_video(VIDEO, str(PACK), drv, OUT, volume=1.0)
print("cinta de estudio:", out)
