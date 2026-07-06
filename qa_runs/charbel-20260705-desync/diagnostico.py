# Diagnostico del desync de pace notes (hipotesis final de la sesion 1d56f67f):
# la referencia (Nordschleife 2025 MoTeC) y la vuelta del piloto (Nordschleife 2020)
# miden la pista con distinta calibracion de distancia -> los cues (metros de la
# referencia) mapeados a tiempo con la vuelta del piloto caen en otro punto fisico.
#
# Corre desde la raiz del repo: python qa_runs/charbel-20260705-desync/diagnostico.py
import sys

sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")

from fantasma.core.corners import detect_corners, extract_milestones
from fantasma.importers import load_laps
from fantasma.viz.pacenotes import _dist_to_time

REF = r"C:\Repositorio personal\Paterial para test (no es un repo)\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
DRV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
DRV_LAPTIME = 394.05  # lap del video 2_composed.mp4 (394.07 s)


def pick_lap(laps, target=None):
    valid = [lap for lap in laps if lap.has("dist") and lap.has("time") and lap.laptime > 60]
    if target is None:
        return min(valid, key=lambda lap: lap.laptime)
    return min(valid, key=lambda lap: abs(lap.laptime - target))


def describe(tag, lap):
    d = lap.col("dist")
    print(
        "%s: laptime=%.2f s  dist=[%.1f .. %.1f]  largo=%.1f m  muestras=%d"
        % (tag, lap.laptime, d[0], d[-1], d[-1] - d[0], len(d))
    )
    return d


def apexes(lap):
    evs, _ = detect_corners(lap)
    corners = extract_milestones(lap, evs)
    out = []
    for c in corners:
        m = c.get("milestones") or {}
        apex = m.get("apex")
        if apex and apex.get("d") is not None:
            out.append((float(apex["d"]), float(apex.get("v") or 0)))
    return corners, out


ref_laps = load_laps(REF)
drv_laps = load_laps(DRV)
print("vueltas ref=%d  drv=%d" % (len(ref_laps), len(drv_laps)))
ref = pick_lap(ref_laps)
drv = pick_lap(drv_laps, DRV_LAPTIME)

d_ref = describe("REF (2025 MoTeC)", ref)
d_drv = describe("DRV (2020 race) ", drv)

len_ref = d_ref[-1] - d_ref[0]
len_drv = d_drv[-1] - d_drv[0]
print("\nlargo drv/ref = %.5f  (diferencia %.1f m)" % (len_drv / len_ref, len_drv - len_ref))

ref_corners, ref_apex = apexes(ref)
drv_corners, drv_apex = apexes(drv)
print("curvas detectadas: ref=%d  drv=%d" % (len(ref_apex), len(drv_apex)))

# Empareja cada apex de la referencia con el apex del piloto mas cercano (+-400 m)
print("\n%8s %10s %8s | %s" % ("d_ref", "d_drv", "delta_m", "error de tiempo al mapear d_ref sobre drv"))
pairs = []
for dr, vr in ref_apex:
    cand = [(abs(dd - dr), dd) for dd, vv in drv_apex if abs(dd - dr) <= 400]
    if not cand:
        continue
    _, dd = min(cand)
    t_cue = _dist_to_time(drv, dr)  # donde SUENA el cue en el video (mapeo actual)
    t_true = _dist_to_time(drv, dd)  # donde el piloto pasa de verdad por esa curva
    pairs.append((dr, dd))
    print("%8.0f %10.0f %8.0f | cue suena %+.2f s respecto al paso real" % (dr, dd, dd - dr, t_cue - t_true))

if len(pairs) >= 2:
    import numpy as np

    x = np.array([p[0] for p in pairs])
    y = np.array([p[1] for p in pairs])
    a, b = np.polyfit(x, y, 1)
    resid = y - (a * x + b)
    print(
        "\najuste lineal d_drv = %.5f * d_ref %+.1f  (residuo max %.1f m)"
        % (a, b, float(abs(resid).max()))
    )
    print("=> si a difiere de 1.0, la calibracion de distancia NO coincide entre archivos")
