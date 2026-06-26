"""Separacion de vueltas y remuestreo por distancia."""

import bisect

from .lap import Lap


def split_laps(outing):
    """Divide un outing en vueltas. Estrategia, en orden:
    1. beacons del log (MoTeC 'Beacon Markers')
    2. cambios en el canal lap_number
    3. reinicios del canal de distancia
    Devuelve lista de Lap con time/dist re-referenciados a 0.
    """
    t = outing.col("time")
    cuts = []
    beacons = outing.meta.get("beacons") or []
    if beacons:
        cuts = [b for b in beacons if t[0] < b < t[-1]]
    elif outing.has("lap_number"):
        ln = outing.col("lap_number")
        cuts = [t[i] for i in range(1, len(ln)) if ln[i] != ln[i - 1]]
    else:
        d = outing.col("dist")
        cuts = [t[i] for i in range(1, len(d)) if d[i] < d[i - 1] - 100]

    bounds = [t[0]] + cuts + [t[-1] + 0.01]
    laps = []
    for i in range(len(bounds) - 1):
        seg = outing.slice_time(bounds[i], bounds[i + 1])
        if len(seg) > 10:
            seg.meta["lap_index"] = i
            seg.meta["is_complete"] = i not in (0, len(bounds) - 2) or not cuts
            laps.append(seg)
    # con beacons, la primera y ultima son out-lap / in-lap parciales
    if cuts:
        for lap_ in laps:
            lap_.meta["is_complete"] = 0 < lap_.meta["lap_index"] < len(bounds) - 2
    return laps


def fastest_lap(laps, min_length_ratio=0.9):
    """La vuelta completa mas rapida; si ninguna esta marcada completa, la mas larga."""
    maxlen = max(l.length for l in laps)
    full = [l for l in laps if l.length >= maxlen * min_length_ratio]
    candidates = [l for l in full if l.meta.get("is_complete")] or full
    return min(candidates, key=lambda l: l.laptime)


def resample(lap, step=5.0):
    """Remuestrea todos los canales a una rejilla de distancia uniforme (interp lineal;
    canales discretos como gear, por el valor anterior)."""
    d = lap.col("dist")
    out = Lap(meta=dict(lap.meta))
    out.meta["resample_step_m"] = step
    grid = []
    x = 0.0
    while x <= d[-1]:
        grid.append(x)
        x += step
    out.channels["dist"] = grid
    discrete = {"gear", "lap_number", "beacon"}
    for name, vals in lap.channels.items():
        if name == "dist":
            continue
        res = []
        for g in grid:
            i = bisect.bisect_right(d, g) - 1
            i = max(0, min(i, len(d) - 2))
            if name in discrete:
                res.append(vals[i])
                continue
            d0, d1 = d[i], d[i + 1]
            if d1 <= d0:
                res.append(vals[i])
            else:
                f = (g - d0) / (d1 - d0)
                f = max(0.0, min(1.0, f))
                res.append(vals[i] + (vals[i + 1] - vals[i]) * f)
        out.channels[name] = res
    return out
