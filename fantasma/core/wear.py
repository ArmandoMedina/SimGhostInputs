"""Indicadores de maltrato de goma (proxy de desgaste).

No existe canal de desgaste directo en los exports tipicos; se estima con:
- **Indice de deslizamiento**: la velocidad de rueda (`Tyre Speed`, angular) se
  calibra contra la velocidad real en tramos de rodadura libre, y la desviacion
  posterior es slip: negativo = bloqueo en frenada, positivo = patinaje en traccion.
  El deslizamiento es lo que gasta la goma.
- **Temperatura de goma**: media de las cuatro ruedas (sobrecalentar = gastar).
- **Activaciones de ABS/TCS**: cada una es un casi-bloqueo / casi-derrape.
"""

WHEELS = ("fl", "fr", "rl", "rr")
DEADBAND_PCT = 2.0   # slip menor a esto es ruido de medicion


def calibrate(lap):
    """Razon rueda/velocidad por rueda, calibrada en rodadura libre
    (sin freno, sin G longitudinal, velocidad alta). Devuelve dict o None."""
    if not lap.has("ts_fl") or not lap.has("speed"):
        return None
    n = len(lap)
    spd = lap.col("speed")
    brk = lap.col("brake") or [0.0] * n
    glong = lap.col("glong") or [0.0] * n
    ratios = {}
    for w in WHEELS:
        ts = lap.col("ts_" + w)
        if ts is None:
            return None
        vals = [ts[i] / spd[i] for i in range(n)
                if spd[i] > 80 and brk[i] < 1 and abs(glong[i]) < 0.2 and ts[i] > 0]
        if len(vals) < 50:
            return None
        vals.sort()
        ratios[w] = vals[len(vals) // 2]  # mediana
    return ratios


def slip_series(lap, ratios=None):
    """Serie de slip (%) por muestra: el peor de las 4 ruedas, con signo
    (negativo = bloqueo, positivo = patinaje). None si faltan canales."""
    ratios = ratios or calibrate(lap)
    if ratios is None:
        return None
    n = len(lap)
    spd = lap.col("speed")
    out = []
    cols = {w: lap.col("ts_" + w) for w in WHEELS}
    for i in range(n):
        v = spd[i]
        if v < 30:
            out.append(0.0)
            continue
        worst = 0.0
        for w in WHEELS:
            est = cols[w][i] / ratios[w]
            s = (est - v) / v * 100.0
            if abs(s) > abs(worst):
                worst = s
        out.append(worst)
    return out


def slip_index(lap, d0=None, d1=None, slip=None, ratios=None):
    """Indice de deslizamiento de un tramo: media del exceso de |slip| sobre la
    banda muerta, ponderada por muestra. 0 = limpio; >5 = goma sufriendo."""
    slip = slip if slip is not None else slip_series(lap, ratios)
    if slip is None:
        return None
    d = lap.col("dist")
    vals = [max(0.0, abs(slip[i]) - DEADBAND_PCT) for i in range(len(slip))
            if (d0 is None or d0 <= d[i]) and (d1 is None or d[i] <= d1)]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


def assist_count(lap, channel, d0=None, d1=None):
    """Numero de activaciones (flancos de subida) de abs/tcs en un tramo."""
    c = lap.col(channel)
    if c is None:
        return None
    d = lap.col("dist")
    count = 0
    prev = 0.0
    for i in range(len(c)):
        if (d0 is None or d0 <= d[i]) and (d1 is None or d[i] <= d1):
            if c[i] > 0.5 and prev <= 0.5:
                count += 1
            prev = c[i]
    return count


def tyre_temp_avg(lap, d0=None, d1=None):
    """Temperatura media de las 4 gomas en un tramo (°C)."""
    cols = [lap.col("tt_" + w) for w in WHEELS]
    if any(c is None for c in cols):
        return None
    d = lap.col("dist")
    vals = [sum(c[i] for c in cols) / 4.0 for i in range(len(d))
            if (d0 is None or d0 <= d[i]) and (d1 is None or d[i] <= d1)]
    return round(sum(vals) / len(vals), 1) if vals else None


def wear_summary(lap):
    """Resumen de vuelta: indice de slip, conteos ABS/TCS, temps, combustible usado."""
    ratios = calibrate(lap)
    slip = slip_series(lap, ratios) if ratios else None
    out = {}
    if slip is not None:
        out["slip_index"] = slip_index(lap, slip=slip)
    for ch in ("abs", "tcs"):
        n = assist_count(lap, ch)
        if n is not None:
            out[ch + "_count"] = n
    t = tyre_temp_avg(lap)
    if t is not None:
        out["tyre_temp_avg"] = t
    fuel = lap.col("fuel")
    if fuel and fuel[0] > 0:
        out["fuel_used"] = round(fuel[0] - fuel[-1], 2)
    return out
