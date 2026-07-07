"""Deteccion de curvas e hitos sobre una vuelta.

Metodologia (validada contra telemetria real del Nordschleife):
- Una curva es un evento: frenada -> turn-in -> release -> apex (V-Min) -> gas -> gas 100%.
- Se detectan dos tipos: 'vmin' (minimo local de velocidad con prominencia) y
  'kink' (pico de G lateral sostenido sin caida de velocidad).
- Los hitos de cada curva se extraen SOLO dentro de su segmento (punto medio con
  las curvas vecinas) para no contaminarse con la frenada de la curva siguiente.
- La frenada real es el ultimo bloque de freno con pico >= 50%; los blips de
  trail-braking no cuentan como inicio de frenada.
- El gas real (`throttle_on`) exige throttle sostenido, igual que `full_throttle`;
  un roce fugaz de pedal no cuenta como inicio de aceleracion.
- Entre el fin de la frenada (o el lift) y el gas sostenido puede existir un
  tramo de coast (freno y gas ambos por debajo de su umbral): se marca con
  `coast_start`/`coast_end` cuando existe hueco (si el gas se solapa con el
  freno, no hay coast).
"""


def samples(lap):
    keys = [
        k
        for k in (
            "time",
            "dist",
            "speed",
            "throttle",
            "brake",
            "steering",
            "gear",
            "glat",
            "glong",
            "rpm",
            "alt",
        )
        if lap.has(k)
    ]
    n = len(lap)
    return [{k: lap.col(k)[i] for k in keys} for i in range(n)], keys


def detect_corners(
    lap, vmin_window_s=1.2, vmin_prominence_kmh=3.0, kink_glat=2.2, sample_rate_hint=None
):
    """Devuelve lista de eventos: [{'kind': 'vmin'|'kink', 'i': indice}] ordenada por distancia.

    sample_rate_hint: reservado para uso futuro; dt se calcula directamente de los datos.
    """
    data, keys = samples(lap)
    if "speed" not in keys:
        raise ValueError("La vuelta no tiene canal de velocidad")
    if "dist" not in keys:
        raise ValueError(
            "La vuelta no tiene canal de distancia. En MoTeC i2 re-exporta el CSV "
            "incluyendo el canal 'Distance': es el eje maestro de comparacion del que "
            "dependen detect, compare y overlay."
        )
    # frecuencia de muestreo aproximada
    dt = (data[-1]["time"] - data[0]["time"]) / max(1, len(data) - 1)
    W = max(3, int(round(vmin_window_s / dt)))
    events = []
    i = W
    while i < len(data) - W:
        v = data[i]["speed"]
        win = data[i - W : i + W + 1]
        if (
            v == min(s["speed"] for s in win)
            and data[i - W]["speed"] > v + vmin_prominence_kmh
            and data[i + W]["speed"] > v + vmin_prominence_kmh
        ):
            events.append(("vmin", i))
            i += W
        else:
            i += 1
    if "glat" in keys:
        Wk = max(3, int(round(0.5 / dt)))
        i = Wk
        while i < len(data) - Wk:
            g = abs(data[i]["glat"])
            if g > kink_glat and g == max(abs(s["glat"]) for s in data[i - Wk : i + Wk + 1]):
                d = data[i]["dist"]
                if not any(abs(data[j]["dist"] - d) < 80 for _, j in events):
                    events.append(("kink", i))
                i += Wk * 2
            else:
                i += 1
    events.sort(key=lambda e: data[e[1]]["dist"])
    return events, data


def extract_milestones(
    lap,
    events=None,
    brake_on=10,
    brake_strong=50,
    throttle_on=5,
    full_throttle=98,
    turn_in_deg=8,
    throttle_on_window=15,
):
    """Extrae los hitos de cada curva, con segmentacion por curva.
    Devuelve lista de dicts estilo corners.json."""
    if events is None:
        events, data = detect_corners(lap)
    else:
        data, _ = samples(lap)
    apex_ds = [data[i]["dist"] for _, i in events]
    corners = []
    for n, (kind, ai) in enumerate(events):
        ad = data[ai]["dist"]
        lo = (apex_ds[n - 1] + ad) / 2 if n > 0 else ad - 450
        hi = (ad + apex_ds[n + 1]) / 2 if n < len(events) - 1 else ad + 350
        lo, hi = max(lo, ad - 450), min(hi, ad + 350)
        seg = [s for s in data if lo <= s["dist"] <= hi]
        pre = [s for s in seg if s["dist"] <= ad]
        post = [s for s in seg if s["dist"] > ad]
        if not pre or len(seg) < 5:
            continue
        ap = min(pre[-20:] + post[:20], key=lambda s: s["speed"])
        ms = {}
        # bloques de frenada
        blocks, cur = [], None
        for s in pre:
            if s.get("brake", 0) > brake_on:
                if cur and s["time"] - cur[-1]["time"] < 0.3:
                    cur.append(s)
                else:
                    cur = [s]
                    blocks.append(cur)
        no_brake = not blocks
        overlap = None
        if blocks:
            strong = [b for b in blocks if max(s["brake"] for s in b) >= brake_strong]
            blk = strong[-1] if strong else blocks[-1]
            bs, bmax = blk[0], max(blk, key=lambda s: s["brake"])
            ms["brake_start"] = _pt(bs, brake_pct=round(bmax["brake"]))
            rel = next(
                (s for s in seg if s["time"] > blk[-1]["time"] - 0.02 and s.get("brake", 0) < 2),
                None,
            )
            if rel:
                ms["brake_release"] = _pt(rel)
        elif pre and "throttle" in pre[0]:
            lift = min(pre, key=lambda s: s["throttle"])
            if lift["throttle"] < 80:
                ms["lift"] = _pt(lift, throttle_pct=round(lift["throttle"]))
        # turn-in
        if "steering" in ap:
            sign = 1 if ap["steering"] > 0 else -1
            t0 = ms["brake_start"]["t"] if "brake_start" in ms else pre[0]["time"]
            ti = next(
                (s for s in pre if s["time"] >= t0 and s["steering"] * sign > turn_in_deg), None
            )
            if ti and ti["time"] < ap["time"]:
                ms["turn_in"] = _pt(ti)
        # gas: ancla en el throttle SOSTENIDO, no en el primer cruce del umbral
        # (mismo criterio que full_throttle: umbral + N muestras seguidas). Un
        # roce fugaz de pedal (freno-motor, ruido) cruza el umbral un instante
        # pero no se sostiene y no debe ganar el hito. throttle_on_window=15
        # reusa la ventana que ya usa full_throttle (~0.3s a 50Hz, coherente
        # con el gap de 0.3s que funde bloques de frenada en este mismo modulo).
        g0 = None
        for j, s in enumerate(seg):
            if s["time"] < ap["time"] - 0.6 or s.get("throttle", 0) <= throttle_on:
                continue
            window = seg[j : j + throttle_on_window]
            if len(window) == throttle_on_window and all(
                x.get("throttle", 0) > throttle_on for x in window
            ):
                g0 = s
                break
        if g0:
            ms["throttle_on"] = _pt(g0, throttle_pct=round(g0["throttle"]))
            if "brake_release" in ms and g0["dist"] < ms["brake_release"]["d"]:
                overlap = round(ms["brake_release"]["d"] - g0["dist"])
            # coast: freno y gas ambos por debajo de su umbral, entre el fin de
            # la frenada (o el lift, en curvas sin freno) y el gas sostenido. Si
            # el gas se solapa con el freno (overlap) no hay hueco y no se
            # emite coast.
            end_ref = ms.get("brake_release") or ms.get("lift")
            if end_ref and end_ref["t"] < g0["time"]:
                coast = [
                    s
                    for s in seg
                    if end_ref["t"] < s["time"] < g0["time"]
                    and s.get("brake", 0) < brake_on
                    and s.get("throttle", 0) < throttle_on
                ]
                if coast:
                    ms["coast_start"] = _pt(coast[0])
                    ms["coast_end"] = _pt(coast[-1])
        ms["apex"] = _pt(ap, g_lat=ap.get("glat"))
        g100 = None
        for j, s in enumerate(post):
            if s.get("throttle", 0) >= full_throttle and all(
                x.get("throttle", 0) >= 90 for x in post[j : j + 15]
            ):
                g100 = s
                break
        if g100:
            ms["full_throttle"] = _pt(g100)
        near = [s for s in seg if ap["time"] - 2.0 <= s["time"] <= ap["time"] + 1.5]
        c = {
            "id": "C%02d" % (n + 1),
            "kind": kind,
            "milestones": ms,
            "no_brake": no_brake,
            "segment_m": [round(lo), round(hi)],
            "delta_s": round(seg[-1]["time"] - seg[0]["time"], 2),
        }
        if "steering" in ap and near:
            mx = max(near, key=lambda s: abs(s.get("steering", 0)))
            c["max_steering_deg"] = round(abs(mx["steering"]), 1)
            # direccion: volante en el apex; si es ambiguo (<5 deg), ventana corta +-0.5s
            if abs(ap["steering"]) >= 5:
                c["direction"] = "left" if ap["steering"] < 0 else "right"
            else:
                close = [s for s in near if abs(s["time"] - ap["time"]) <= 0.5]
                mc = max(close, key=lambda s: abs(s.get("steering", 0))) if close else mx
                c["direction"] = "left" if mc["steering"] < 0 else "right"
        if "glat" in ap and near:
            mg = max(near, key=lambda s: abs(s.get("glat", 0)))
            ms["g_lat_max"] = {"d": round(mg["dist"]), "g_lat": mg["glat"]}
        if "alt" in ap and seg:
            a0 = min(seg, key=lambda s: abs(s["dist"] - (ad - 100)))["alt"]
            a1 = min(seg, key=lambda s: abs(s["dist"] - (ad + 100)))["alt"]
            pct = (a1 - a0) / 200.0 * 100.0
            c["slope_pct"] = round(pct, 1)
            c["slope"] = "subida" if pct > 1 else ("bajada" if pct < -1 else "plano")
        if overlap and overlap > 0:
            c["overlap_m"] = overlap
        corners.append(c)
    return corners


def _pt(s, **extra):
    p = {"d": round(s["dist"]), "t": round(s["time"], 2), "v": round(s["speed"])}
    if "gear" in s:
        p["gear"] = int(s["gear"])
    p.update({k: v for k, v in extra.items() if v is not None})
    return p
