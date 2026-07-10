"""Comparacion piloto vs referencia, por distancia (no por tiempo)."""

from . import wear
from .corners import (
    BRAKE_LOOKBACK_M,
    BRAKE_ON,
    BRAKE_STRONG,
    PHASE_GAP_S,
    detect_corners,
    extract_milestones,
    samples,
    select_brake_phase,
)
from .normalize import resample


def delta_trace(ref, drv, step=5.0):
    """Remuestrea ambas vueltas a la misma rejilla y devuelve la traza de comparacion:
    lista de dicts con dist, delta_t (positivo = piloto pierde), y canales de ambos."""
    r = resample(ref, step)
    d = resample(drv, step)
    n = min(len(r.channels["dist"]), len(d.channels["dist"]))
    rows = []
    for i in range(n):
        row = {
            "dist": r.channels["dist"][i],
            "delta_t": d.channels["time"][i] - r.channels["time"][i],
        }
        for ch in ("speed", "throttle", "brake", "steering", "gear", "glat", "glong", "rpm"):
            if ch in r.channels:
                row["ref_" + ch] = r.channels[ch][i]
            if ch in d.channels:
                row["drv_" + ch] = d.channels[ch][i]
        rows.append(row)
    return rows


def _is_num(value):
    return isinstance(value, (int, float))


def _round_or_none(value, ndigits=1):
    return round(value, ndigits) if _is_num(value) else None


def _near_sample(seg, dist):
    if not seg:
        return None
    return min(seg, key=lambda s: abs(s["dist"] - dist))


def _first_at_or_above(seg, channel, threshold):
    return next((s for s in seg if s.get(channel, 0) >= threshold), None)


def _peak_abs(seg, channel):
    vals = [abs(s[channel]) for s in seg if channel in s]
    return max(vals) if vals else None


def _brake_profile(seg, prefix):
    brake = prefix + "_brake"
    if not seg or brake not in seg[0]:
        return {}
    active = [s for s in seg if s.get(brake, 0) > 10]
    if not active:
        return {}
    peak = max(active, key=lambda s: s.get(brake, 0))
    return {
        "start_m": round(active[0]["dist"]),
        "peak_m": round(peak["dist"]),
        "peak_pct": round(peak[brake]),
        "ramp_m": round(max(0, peak["dist"] - active[0]["dist"])),
    }


def _gear_rpm_at(sample, prefix):
    if not sample:
        return {}
    out = {}
    gear = sample.get(prefix + "_gear")
    rpm = sample.get(prefix + "_rpm")
    if _is_num(gear):
        out["gear"] = int(gear)
    if _is_num(rpm):
        out["rpm"] = round(rpm)
    return out


def _corner_segment(row, trace):
    if row.get("segment_start_m") is not None and row.get("segment_end_m") is not None:
        return row["segment_start_m"], row["segment_end_m"]
    anchors = [
        row.get("ref_brake_d"),
        row.get("drv_brake_d"),
        row.get("apex_d"),
    ]
    if row.get("d_gas100_m") is not None and row.get("ref_gas100_d") is not None:
        anchors.append(row.get("ref_gas100_d"))
        anchors.append(row.get("drv_gas100_d"))
    nums = [x for x in anchors if _is_num(x)]
    if nums:
        return max(min(nums) - 80, trace[0]["dist"]), min(max(nums) + 120, trace[-1]["dist"])
    apex = row.get("apex_d", trace[len(trace) // 2]["dist"] if trace else 0)
    return apex - 200, apex + 200


def _fmt_signed(value, unit="", digits=0):
    if not _is_num(value):
        return "sin dato"
    return ("%+.*f%s" % (digits, value, unit)).replace("+", "+")


def _append_unique(items, value):
    if value and value not in items:
        items.append(value)


def corner_coaching(row, trace):
    """Devuelve coaching determinista para una curva.

    `row` es una fila de `corner_rows`/`corners_compare.csv` y `trace` es la salida
    de `delta_trace()`. No usa IA: solo resume señales ya calculadas por distancia.
    """
    if not trace:
        status = "gain" if row.get("time_lost", 0) < 0 else "loss"
        return {
            "id": row.get("id", "?"),
            "name": row.get("name", row.get("id", "?")),
            "status": status,
            "time_lost": row.get("time_lost"),
            "summary": "No hay traza metro a metro para explicar esta curva.",
            "actions": ["Revisa el CSV de salida; falta delta.csv para el drill-down."],
            "braking": {},
            "apex": {},
            "throttle": {},
            "lateral": {},
            "gear": {},
        }

    lo, hi = _corner_segment(row, trace)
    seg = [s for s in trace if lo <= s["dist"] <= hi]

    apex_d = row.get("apex_d")
    ref_apex = _near_sample(seg, apex_d)
    drv_apex = _near_sample(seg, row.get("drv_vmin_d", apex_d))

    time_lost = row.get("time_lost", 0.0)
    status = "gain" if _is_num(time_lost) and time_lost < -0.02 else "loss"
    if _is_num(time_lost) and abs(time_lost) <= 0.02:
        status = "neutral"

    braking = {}
    ref_brake = _brake_profile([s for s in seg if s["dist"] <= apex_d], "ref") if apex_d else {}
    drv_brake = _brake_profile([s for s in seg if s["dist"] <= apex_d], "drv") if apex_d else {}
    if row.get("d_brake_m") is not None:
        braking.update(
            {
                "ref_start_m": row.get("ref_brake_d"),
                "drv_start_m": row.get("drv_brake_d"),
                "delta_start_m": row.get("d_brake_m"),
            }
        )
    if ref_brake and drv_brake:
        braking.update(
            {
                "ref_peak_pct": ref_brake.get("peak_pct"),
                "drv_peak_pct": drv_brake.get("peak_pct"),
                "delta_peak_pct": drv_brake.get("peak_pct") - ref_brake.get("peak_pct"),
                "ref_ramp_m": ref_brake.get("ramp_m"),
                "drv_ramp_m": drv_brake.get("ramp_m"),
                "delta_ramp_m": drv_brake.get("ramp_m") - ref_brake.get("ramp_m"),
            }
        )

    apex = {
        "ref_vmin_kmh": row.get("ref_vmin"),
        "drv_vmin_kmh": row.get("drv_vmin"),
        "delta_vmin_kmh": row.get("d_vmin"),
        "ref_apex_m": row.get("apex_d"),
        "drv_apex_m": row.get("drv_vmin_d"),
    }

    throttle = {}
    if row.get("d_gas100_m") is not None:
        throttle.update(
            {
                "ref_gas100_m": row.get("ref_gas100_d"),
                "drv_gas100_m": row.get("drv_gas100_d"),
                "delta_gas100_m": row.get("d_gas100_m"),
            }
        )
    elif apex_d is not None:
        post = [s for s in seg if s["dist"] >= apex_d]
        ref_gas = _first_at_or_above(post, "ref_throttle", 98)
        drv_gas = _first_at_or_above(post, "drv_throttle", 98)
        if ref_gas and drv_gas:
            throttle.update(
                {
                    "ref_gas100_m": round(ref_gas["dist"]),
                    "drv_gas100_m": round(drv_gas["dist"]),
                    "delta_gas100_m": round(drv_gas["dist"] - ref_gas["dist"]),
                }
            )

    lateral = {}
    if seg and "ref_glat" in seg[0] and "drv_glat" in seg[0]:
        ref_g = _peak_abs(seg, "ref_glat")
        drv_g = _peak_abs(seg, "drv_glat")
        if ref_g is not None and drv_g is not None:
            lateral = {
                "ref_peak_g": _round_or_none(ref_g, 2),
                "drv_peak_g": _round_or_none(drv_g, 2),
                "delta_peak_g": _round_or_none(drv_g - ref_g, 2),
            }

    gear = {}
    ref_gr = _gear_rpm_at(ref_apex, "ref")
    drv_gr = _gear_rpm_at(drv_apex, "drv")
    if ref_gr or drv_gr:
        gear = {"ref": ref_gr, "drv": drv_gr}
        if "gear" in ref_gr and "gear" in drv_gr:
            gear["same_gear"] = ref_gr["gear"] == drv_gr["gear"]
            gear["delta_gear"] = drv_gr["gear"] - ref_gr["gear"]
        if "rpm" in ref_gr and "rpm" in drv_gr:
            gear["delta_rpm"] = drv_gr["rpm"] - ref_gr["rpm"]

    actions = []
    d_brake = braking.get("delta_start_m")
    d_peak = braking.get("delta_peak_pct")
    d_vmin = apex.get("delta_vmin_kmh")
    d_gas = throttle.get("delta_gas100_m")
    d_g = lateral.get("delta_peak_g")

    if status == "gain":
        _append_unique(
            actions,
            "Aqui ganas %.3f s: usa esta curva como referencia de ejecucion." % abs(time_lost),
        )
    elif status == "neutral":
        _append_unique(actions, "Curva casi neutra: no es la primera palanca de mejora.")
    else:
        if _is_num(d_gas) and d_gas > 10:
            _append_unique(actions, "Acelera antes: llegas a gas 100%% %d m despues." % d_gas)
        if _is_num(d_vmin) and d_vmin < -3:
            _append_unique(
                actions, "Sube la velocidad minima: pasas el apex %d km/h mas lento." % abs(d_vmin)
            )
        if _is_num(d_brake) and d_brake < -10:
            _append_unique(
                actions, "Frena menos pronto: empiezas %d m antes que la referencia." % abs(d_brake)
            )
        if _is_num(d_brake) and d_brake > 10:
            _append_unique(
                actions, "Anticipa la referencia visual: empiezas a frenar %d m tarde." % d_brake
            )
        if _is_num(d_peak) and d_peak < -10:
            _append_unique(
                actions, "Aumenta pico de freno: tu maximo es %d pp menor." % abs(d_peak)
            )
        if _is_num(d_peak) and d_peak > 10:
            _append_unique(actions, "Suaviza el pico de freno: tu maximo es %d pp mayor." % d_peak)
        if _is_num(d_vmin) and d_vmin > 3 and _is_num(time_lost) and time_lost > 0:
            _append_unique(
                actions,
                "Vas %d km/h mas rapido en el apex pero pierdes tiempo: prioriza salida, no entrada."
                % d_vmin,
            )
        if _is_num(d_g) and d_g < -0.15:
            _append_unique(
                actions,
                "Generas %.2f G menos de carga lateral: revisa linea y uso de pista." % abs(d_g),
            )
        if gear.get("same_gear") is False:
            _append_unique(
                actions,
                "Usas una marcha distinta en el apex: ref %s, tu %s."
                % (gear["ref"].get("gear", "?"), gear["drv"].get("gear", "?")),
            )
    if not actions:
        actions.append(
            "La perdida no apunta a una sola senal; revisa la grafica de velocidad/gas/freno."
        )

    signals = []
    if _is_num(d_brake):
        if d_brake < -5:
            signals.append("frenas %d m antes" % abs(d_brake))
        elif d_brake > 5:
            signals.append("frenas %d m tarde" % d_brake)
    if _is_num(d_peak) and abs(d_peak) >= 5:
        signals.append("pico de freno %s pp" % _fmt_signed(d_peak, digits=0))
    if _is_num(d_vmin) and abs(d_vmin) >= 3:
        signals.append("V-Min %s km/h" % _fmt_signed(d_vmin, digits=0))
    if _is_num(d_gas) and abs(d_gas) >= 8:
        signals.append("gas 100%% %s m" % _fmt_signed(d_gas, digits=0))
    if _is_num(d_g) and abs(d_g) >= 0.1:
        signals.append("G-lat %s G" % _fmt_signed(d_g, digits=2))

    name = row.get("name", row.get("id", "?"))
    if status == "gain":
        lead = "Ganas %.3f s en %s" % (abs(time_lost), name)
    elif status == "neutral":
        lead = "%s casi neutra en el crono" % name
    else:
        lead = "Pierdes %.3f s en %s" % (time_lost, name)
    summary = lead + (": " + "; ".join(signals[:4]) if signals else ".")

    return {
        "id": row.get("id", "?"),
        "name": name,
        "status": status,
        "time_lost": time_lost,
        "segment_m": [round(lo), round(hi)],
        "summary": summary,
        "actions": actions[:4],
        "braking": braking,
        "apex": apex,
        "throttle": throttle,
        "lateral": lateral,
        "gear": gear,
    }


def _segment(corner):
    return corner.get("segment_m") or corner.get("range_m")


def _corner_metrics(
    corner,
    lap_data,
    prev_apex_d=None,
    brake_on=BRAKE_ON,
    brake_strong=BRAKE_STRONG,
    phase_gap_s=PHASE_GAP_S,
):
    """Metricas del piloto en una curva de la referencia.

    La frenada se detecta con el helper compartido `select_brake_phase` sobre la
    MISMA ventana ampliada que uso la referencia -- no con el segmento por punto
    medio. La ventana se RECONSTRUYE aqui a partir de los hitos que la curva ya
    trae (su `apex` y el de la curva previa), no de un campo publicado: el
    ADR 0031 descarta exponer `brake_window_m` (Opcion C) y adopta la Opcion A,
    "cada consumidor deriva la ventana de frenada del contexto que ya tiene".
    Reproduce la formula de `corners.extract_milestones`:
    `brake_lo = max(apex_prev, apex - BRAKE_LOOKBACK_M)`, ventana
    `(brake_lo, apex]`, con los limites redondeados igual que la referencia para
    que `d_brake_m == 0` cuando piloto y referencia son la misma vuelta. Antes
    este metodo tenia su propia copia del algoritmo y su propia ventana (el
    segmento), asi que `d_brake_m` salia asimetrico y levantaba banderas
    `"frenada"` espurias aunque el piloto frenara en el mismo metro. El resto de
    metricas (vmin, gas100) sigue acotado al segmento.
    """
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
    apex_d = corner["milestones"]["apex"]["d"]
    if prev_apex_d is not None:
        brake_lo = max(prev_apex_d, apex_d - BRAKE_LOOKBACK_M)
    else:
        brake_lo = apex_d - BRAKE_LOOKBACK_M
    brake_window = [round(brake_lo), round(apex_d)]
    phase, _ = select_brake_phase(lap_data, brake_window, brake_on, brake_strong, phase_gap_s)
    if phase:
        out["brake_d"] = round(phase[0]["dist"])
        out["brake_pct"] = round(max(s["brake"] for s in phase))
    g100 = next((s for s in seg if s["dist"] > vmin["dist"] and s.get("throttle", 0) >= 98), None)
    if g100:
        out["gas100_d"] = round(g100["dist"])
    return out


def compare(
    ref,
    drv,
    step=5.0,
    corners=None,
    brake_on=BRAKE_ON,
    brake_strong=BRAKE_STRONG,
    phase_gap_s=PHASE_GAP_S,
):
    """Comparacion completa. corners: lista estilo corners.json (si no, se detectan
    en la referencia). Devuelve (trace, corner_rows, summary).

    Los umbrales de frenada (`brake_on`, `brake_strong`, `phase_gap_s`) fluyen
    desde una unica fuente hacia AMBOS lados: cuando `corners is None` se pasan a
    `extract_milestones` (referencia) y siempre se pasan a `_corner_metrics`
    (piloto). Asi la referencia y el piloto se miden con la MISMA vara y el
    invariante `d_brake_m == 0` se mantiene aunque se cambien los umbrales.
    """
    trace = delta_trace(ref, drv, step)
    if corners is None:
        events, _ = detect_corners(ref)
        corners = extract_milestones(
            ref, events, brake_on=brake_on, brake_strong=brake_strong, phase_gap_s=phase_gap_s
        )
    drv_data, _ = samples(drv)

    def delta_at(dist):
        i = min(int(dist / step), len(trace) - 1)
        return trace[max(0, i)]["delta_t"]

    # series de slip (proxy de desgaste), si hay canales de rueda
    ref_ratios, drv_ratios = wear.calibrate(ref), wear.calibrate(drv)
    ref_slip = wear.slip_series(ref, ref_ratios) if ref_ratios else None
    drv_slip = wear.slip_series(drv, drv_ratios) if drv_ratios else None

    rows = []
    # `prev_apex_d` reconstruye la ventana de frenada del piloto igual que la
    # referencia (frontera de propiedad = apice de la curva previa; ADR 0031).
    # Se actualiza para CADA curva de la lista, incluso si el piloto no tiene
    # datos en su segmento, para no desalinear el apice previo de la siguiente.
    prev_apex_d = None
    for c in corners:
        m = c["milestones"]
        drv_m = _corner_metrics(c, drv_data, prev_apex_d, brake_on, brake_strong, phase_gap_s)
        # `.get(...).get(...)`: un corner armado a mano puede traer `apex` sin `d`
        # (o sin `apex`). Antes esto era `m["apex"]["d"]` y, al evaluarse ANTES del
        # `continue`, tumbaba TODA la comparacion con KeyError aunque el piloto no
        # tuviera muestras en ese segmento. `None` se propaga como "sin tope
        # previo": `_corner_metrics` ya trata `prev_apex_d is None` como la primera
        # curva (sin `max`), asi que la ventana de la siguiente no revienta.
        prev_apex_d = m.get("apex", {}).get("d")
        if drv_m is None:
            continue
        lo, hi = _segment(c)
        row = {
            "id": c.get("id", "?"),
            "name": c.get("name", c.get("id", "?")),
            "segment_start_m": round(lo),
            "segment_end_m": round(hi),
            "apex_d": m["apex"]["d"],
            "ref_vmin": m["apex"]["v"],
            "drv_vmin": drv_m["vmin"],
            "drv_vmin_d": drv_m["vmin_d"],
            "d_vmin": drv_m["vmin"] - m["apex"]["v"],
            "time_lost": round(delta_at(hi) - delta_at(lo), 3),
        }
        if "brake_start" in m and "brake_d" in drv_m:
            row["ref_brake_d"] = m["brake_start"]["d"]
            row["drv_brake_d"] = drv_m["brake_d"]
            row["d_brake_m"] = drv_m["brake_d"] - m["brake_start"]["d"]
        if "full_throttle" in m and "gas100_d" in drv_m:
            row["ref_gas100_d"] = m["full_throttle"]["d"]
            row["drv_gas100_d"] = drv_m["gas100_d"]
            row["d_gas100_m"] = drv_m["gas100_d"] - m["full_throttle"]["d"]
        if ref_slip is not None and drv_slip is not None:
            row["ref_slip"] = wear._slip_index(ref, lo, hi, slip=ref_slip)
            row["drv_slip"] = wear._slip_index(drv, lo, hi, slip=drv_slip)
        ra = wear._assist_count(ref, "abs", lo, hi)
        da = wear._assist_count(drv, "abs", lo, hi)
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

    ref_lt = round(ref.laptime, 3)
    drv_lt = round(drv.laptime, 3)
    total_delta = round(trace[-1]["delta_t"], 3) if trace else 0.0

    avisos = []

    # FIX 2: delta sospechosamente grande indica posible circuito distinto
    if ref_lt > 0 and abs(total_delta) > ref_lt * 0.5:
        avisos.append(
            "delta sospechosamente grande (%.1f s sobre vuelta de %.1f s): "
            "¿la referencia y el piloto son del mismo circuito?" % (total_delta, ref_lt)
        )

    # FIX 3: autos distintos — solo cuando metadata disponible en ambos
    ref_car = ref.meta.get("Vehicle")
    drv_car = drv.meta.get("Vehicle")
    if ref_car and drv_car and ref_car != drv_car:
        avisos.append("autos distintos: %s (ref) vs %s (piloto)" % (ref_car, drv_car))

    # FIX 4: piloto más rápido que referencia — posible referencia y piloto invertidos
    if total_delta < -1.0:
        avisos.append(
            "piloto más rápido que la referencia (%.1f s de ventaja): "
            "¿tienes la referencia y el piloto al revés?" % abs(total_delta)
        )

    summary = {
        "ref_laptime": ref_lt,
        "drv_laptime": drv_lt,
        "total_delta": total_delta,
        "corners": len(rows),
        "ref_wear": wear.wear_summary(ref),
        "drv_wear": wear.wear_summary(drv),
        "avisos": avisos,
    }
    return trace, rows, summary
