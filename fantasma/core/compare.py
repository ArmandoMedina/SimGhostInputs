"""Comparacion piloto vs referencia, por distancia (no por tiempo)."""
from . import wear
from .corners import _samples, detect_corners, extract_milestones
from .normalize import resample


def delta_trace(ref, drv, step=5.0):
    """Remuestrea ambas vueltas a la misma rejilla y devuelve la traza de comparacion:
    lista de dicts con dist, delta_t (positivo = piloto pierde), y canales de ambos."""
    r = resample(ref, step)
    d = resample(drv, step)
    n = min(len(r.channels["dist"]), len(d.channels["dist"]))
    rows = []
    for i in range(n):
        row = {"dist": r.channels["dist"][i],
               "delta_t": d.channels["time"][i] - r.channels["time"][i]}
        for ch in ("speed", "throttle", "brake", "steering", "gear", "glat", "glong"):
            if ch in r.channels:
                row["ref_" + ch] = r.channels[ch][i]
            if ch in d.channels:
                row["drv_" + ch] = d.channels[ch][i]
        rows.append(row)
    return rows


def _segment(corner):
    return corner.get("segment_m") or corner.get("range_m")


def _corner_metrics(corner, lap_data):
    """Metricas del piloto dentro del segmento de una curva de la referencia."""
    lo, hi = _segment(corner)
    seg = [s for s in lap_data if lo <= s["dist"] <= hi]
    if not seg:
        return None
    out = {}
    vmin = min(seg, key=lambda s: s["speed"])
    out["vmin"] = round(vmin["speed"])
    out["vmin_d"] = round(vmin["dist"])
    if "gear" in vmin:
        out["vmin_gear"] = int(vmin["gear"])
    blocks, cur = [], None
    for s in seg:
        if s.get("brake", 0) > 10:
            if cur and s["time"] - cur[-1]["time"] < 0.3:
                cur.append(s)
            else:
                cur = [s]
                blocks.append(cur)
    strong = [b for b in blocks if max(x["brake"] for x in b) >= 50]
    blk = (strong or blocks or [None])[-1] if (strong or blocks) else None
    if blk:
        out["brake_d"] = round(blk[0]["dist"])
        out["brake_pct"] = round(max(x["brake"] for x in blk))
    g100 = next((s for s in seg if s["dist"] > vmin["dist"] and s.get("throttle", 0) >= 98), None)
    if g100:
        out["gas100_d"] = round(g100["dist"])
    return out


def compare(ref, drv, step=5.0, corners=None):
    """Comparacion completa. corners: lista estilo corners.json (si no, se detectan
    en la referencia). Devuelve (trace, corner_rows, summary)."""
    trace = delta_trace(ref, drv, step)
    if corners is None:
        events, _ = detect_corners(ref)
        corners = extract_milestones(ref, events)
    drv_data, _ = _samples(drv)

    def delta_at(dist):
        i = min(int(dist / step), len(trace) - 1)
        return trace[max(0, i)]["delta_t"]

    # series de slip (proxy de desgaste), si hay canales de rueda
    ref_ratios, drv_ratios = wear.calibrate(ref), wear.calibrate(drv)
    ref_slip = wear.slip_series(ref, ref_ratios) if ref_ratios else None
    drv_slip = wear.slip_series(drv, drv_ratios) if drv_ratios else None

    rows = []
    for c in corners:
        m = c["milestones"]
        drv_m = _corner_metrics(c, drv_data)
        if drv_m is None:
            continue
        lo, hi = _segment(c)
        row = {
            "id": c.get("id", "?"), "name": c.get("name", c.get("id", "?")),
            "apex_d": m["apex"]["d"],
            "ref_vmin": m["apex"]["v"], "drv_vmin": drv_m["vmin"],
            "d_vmin": drv_m["vmin"] - m["apex"]["v"],
            "time_lost": round(delta_at(hi) - delta_at(lo), 3),
        }
        if "brake_start" in m and "brake_d" in drv_m:
            row["ref_brake_d"] = m["brake_start"]["d"]
            row["drv_brake_d"] = drv_m["brake_d"]
            row["d_brake_m"] = drv_m["brake_d"] - m["brake_start"]["d"]
        if "full_throttle" in m and "gas100_d" in drv_m:
            row["d_gas100_m"] = drv_m["gas100_d"] - m["full_throttle"]["d"]
        if ref_slip is not None and drv_slip is not None:
            row["ref_slip"] = wear.slip_index(ref, lo, hi, slip=ref_slip)
            row["drv_slip"] = wear.slip_index(drv, lo, hi, slip=drv_slip)
        ra = wear.assist_count(ref, "abs", lo, hi)
        da = wear.assist_count(drv, "abs", lo, hi)
        if ra is not None and da is not None:
            row["ref_abs"], row["drv_abs"] = ra, da
        tol = c.get("tolerances", {})
        flags = []
        if abs(row["d_vmin"]) > tol.get("vmin_kmh", 5):
            flags.append("vmin")
        if "d_brake_m" in row and abs(row["d_brake_m"]) > tol.get("brake_start_m", 15):
            flags.append("frenada")
        row["flags"] = "+".join(flags)
        rows.append(row)

    summary = {
        "ref_laptime": round(ref.laptime, 3),
        "drv_laptime": round(drv.laptime, 3),
        "total_delta": round(trace[-1]["delta_t"], 3) if trace else 0.0,
        "corners": len(rows),
        "ref_wear": wear.wear_summary(ref),
        "drv_wear": wear.wear_summary(drv),
    }
    return trace, rows, summary
