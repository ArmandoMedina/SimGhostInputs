# Parte 2: que escucho el PO exactamente. Toma los packs reales de los demos
# (Downloads\0207) y calcula, cue por cue, en que segundo del video suena y que
# tan lejos cae del evento real equivalente en la vuelta del piloto.
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

from fantasma.core.corners import detect_corners, extract_milestones
from fantasma.importers import load_laps
from fantasma.viz.pacenotes import _dist_to_time

DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
PACKS = [
    r"C:\Users\amedina\Downloads\0207",  # pack raiz (56 curvas / tonos)
    r"C:\Users\amedina\Downloads\0207\_pack_LOGICA2",
    r"C:\Users\amedina\Downloads\0207\_pack_VOZ_ref",
]

drv_laps = load_laps(DRV)
drv = min(
    (lap for lap in drv_laps if lap.has("dist") and lap.has("time") and lap.laptime > 60),
    key=lambda lap: abs(lap.laptime - 394.05),
)
t = drv.col("time")
d = drv.col("dist")
print("drv laptime=%.2f  time[0]=%.3f  time[-1]=%.3f  dist[0]=%.1f" % (drv.laptime, t[0], t[-1], d[0]))
print("_dist_to_time(drv, 0)=%.2f  _dist_to_time(drv, %d)=%.2f" % (_dist_to_time(drv, 0), int(d[-1]), _dist_to_time(drv, d[-1])))

# Milestones reales del piloto (su propia vuelta) para comparar contra los cues
evs, _ = detect_corners(drv)
drv_corners = extract_milestones(drv, evs)


def drv_milestone_dists(kind):
    out = []
    for c in drv_corners:
        m = (c.get("milestones") or {}).get(kind)
        if m and m.get("d") is not None:
            out.append(float(m["d"]))
    return out


drv_brakes = drv_milestone_dists("brake")
drv_apexes = drv_milestone_dists("apex")

KIND_TO_DRV = {
    "contador de frenada": ("brake", drv_brakes),
    "punto de frenada": ("brake", drv_brakes),
    "apex": ("apex", drv_apexes),
}

for pack in PACKS:
    meta = Path(pack) / "metadata.json"
    if not meta.exists():
        print("\n== %s: sin metadata.json" % pack)
        continue
    entries = json.loads(meta.read_text(encoding="utf-8")).get("entries", [])
    print("\n== PACK %s  (%d cues)" % (pack, len(entries)))
    print("%-42s %7s %8s | %s" % ("cue", "d_m", "t_video", "vs evento real del piloto"))
    for e in entries:
        dist = float(e.get("distanceRoundTrack") or 0)
        t_cue = _dist_to_time(drv, dist)
        desc = (e.get("description") or "?")[:42]
        label = None
        for key, (kind, dists) in KIND_TO_DRV.items():
            if key in desc:
                near = min(dists, key=lambda x: abs(x - dist)) if dists else None
                if near is not None and abs(near - dist) <= 500:
                    dt = t_cue - _dist_to_time(drv, near)
                    label = "%s real a %dm -> cue %+.1f s" % (kind, near, dt)
                break
        print("%-42s %7.0f %8.1f | %s" % (desc, dist, t_cue, label or "-"))
