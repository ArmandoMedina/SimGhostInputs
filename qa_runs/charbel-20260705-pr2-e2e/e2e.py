# E2E del PR 2 (ADR 0024) con datos reales: regenera el pack con el motor nuevo
# (countdown por tiempo 3.5 s, top=0 todas las curvas, gap global, sin cues en
# d<=0) y lo muxea sobre el video real -> _DEMO_FIXED.mp4 para el oido del PO.
# Verifica de forma determinista las propiedades que el ADR promete.
import sys

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

import json
from pathlib import Path

from fantasma.core.compare import compare
from fantasma.core.corners import detect_corners, extract_milestones
from fantasma.importers import load_laps
from fantasma.viz.pacenotes import _dist_to_time, build_tone_pack

REF = r"C:\Repositorio personal\Paterial para test (no es un repo)\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
OUTDIR = r"C:\Users\amedina\Downloads\0207\_pack_FIXED"

ref = min(
    (lap for lap in load_laps(REF) if lap.has("dist") and lap.has("time") and lap.laptime > 60),
    key=lambda lap: lap.laptime,
)
drv = min(
    (lap for lap in load_laps(DRV) if lap.has("dist") and lap.has("time") and lap.laptime > 60),
    key=lambda lap: abs(lap.laptime - 394.05),
)
print("ref=%.2f s  drv=%.2f s" % (ref.laptime, drv.laptime))

evs, _ = detect_corners(ref)
corners = extract_milestones(ref, evs)
_, rows, _ = compare(ref, drv, step=1.0, corners=corners)
print("curvas=%d  rows=%d" % (len(corners), len(rows)))

res = build_tone_pack(rows, corners, OUTDIR, top=0, countdown_s=3.5, track_name="Nordschleife")
print("pack: %d entradas en %s" % (res["entries"], res["outdir"]))

plan = json.loads((Path(OUTDIR) / "plan.json").read_text(encoding="utf-8"))
events = plan["events"]
fails = []

# 1) ningun cue en d<=0 (y por tanto ninguno suena en t=0 del video)
bad = [e for e in events if e["distance"] <= 0]
if bad:
    fails.append("cues en d<=0: %r" % bad)

# 2) gap global: eventos consecutivos separados >= 50 m
dists = [e["distance"] for e in events]
close = [
    (a, b) for a, b in zip(dists, dists[1:]) if b - a < 50
]
if close:
    fails.append("pares a <50 m: %r" % close)

# 3) countdown ~3.5 s antes de la frenada de la referencia (medido en el
#    tiempo de la REF, que es cuya velocidad define el anticipo; clamp 60-350 m)
cd = [e for e in events if e["cue"] == "brake_countdown"]
lead_times = []
for e in cd:
    corner = next((c for c in corners if str(c.get("id")) == e["corner_id"]), None)
    if not corner:
        continue
    ms = corner.get("milestones") or {}
    brake = ms.get("brake") or ms.get("brake_start")
    if not brake or brake.get("d") is None:
        continue
    dt = _dist_to_time(ref, float(brake["d"])) - _dist_to_time(ref, e["distance"])
    lead_times.append(dt)
if lead_times:
    import statistics

    print(
        "countdowns=%d  anticipo en ref: mediana %.2f s  min %.2f  max %.2f"
        % (len(cd), statistics.median(lead_times), min(lead_times), max(lead_times))
    )
    # con clamp [60,350] m el anticipo real queda entre ~1 s (curva lenta) y ~5 s
    if statistics.median(lead_times) < 2.5 or statistics.median(lead_times) > 5.0:
        fails.append("mediana de anticipo fuera de 2.5-5.0 s: %.2f" % statistics.median(lead_times))

# 4) resumen de descartes del plan
skipped_global = plan.get("skipped_global", [])
n_meta = sum(
    1 for c in plan["corners"] for s in c["skipped"] if s["reason"] == "antes_de_la_meta"
)
print(
    "eventos=%d  descartados_gap_global=%d  descartados_antes_de_meta=%d"
    % (len(events), len(skipped_global), n_meta)
)

if fails:
    print("\nFALLAS:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("\nOK: todas las propiedades del ADR 0024 se cumplen en datos reales")
