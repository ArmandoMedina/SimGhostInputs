# Demo pedido por el PO (2026-07-06): video con un beep en cada cambio de
# marcha HACIA ARRIBA (solo upshift) de su propia vuelta, muxeado sobre el
# video real. Variante filtrada del demo de MARCHAS de la sesion anterior,
# que valido el mecanismo dist->tiempo con 33 beeps (up y down).
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

from fantasma.importers import load_laps
from fantasma.viz.compose import mux_pace_notes_into_video
from fantasma.viz.pacenotes import _metadata_entry, _write_metadata, generate_tone

DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
VIDEO = r"C:\Users\amedina\Downloads\0207\frames\2_composed.mp4"
PACK = Path(r"C:\Users\amedina\Downloads\0207\_pack_UPSHIFT")
OUT = r"C:\Users\amedina\Downloads\0207\_DEMO_UPSHIFT.mp4"

drv = min(
    (lap for lap in load_laps(DRV) if lap.has("dist") and lap.has("time") and lap.laptime > 60),
    key=lambda lap: abs(lap.laptime - 394.05),
)
print("vuelta: %.2f s" % drv.laptime)
if not drv.has("gear"):
    sys.exit("la vuelta no tiene canal gear")

gear = drv.col("gear")
dist = drv.col("dist")
ups = []
last_engaged = 0  # el canal pasa por 0 (neutral) durante cada cambio: 2 -> 0 -> 3
for i in range(len(gear)):
    g = int(gear[i])
    if g <= 0:
        continue
    # subida real: la marcha engranada supera a la ultima engranada
    if last_engaged >= 1 and g > last_engaged:
        if not ups or dist[i] - ups[-1][0] > 5:  # dedupe rebotes a <5 m
            ups.append((dist[i], g))
    last_engaged = g

print("upshifts detectados: %d" % len(ups))
PACK.mkdir(parents=True, exist_ok=True)
for old in PACK.glob("*.wav"):
    old.unlink()
entries = []
for d, g in ups:
    filename = "%d_0.wav" % int(d)
    # tono corto y agudo (1200 Hz), distinto de todos los cues de coaching
    (PACK / filename).write_bytes(generate_tone(1200, 0.09, volume=0.9))
    entries.append(_metadata_entry("subida a %da" % g, "upshift", int(d), filename))
_write_metadata(PACK, entries, track_name="Nordschleife")
print("pack: %d beeps en %s" % (len(entries), PACK))

out = mux_pace_notes_into_video(VIDEO, str(PACK), drv, OUT, volume=1.0)
print("demo:", out)
