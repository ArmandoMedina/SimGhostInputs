"""Fixtures compartidas para la suite.

La pieza central es `make_lap`: construye una `Lap` sintética y determinista a
partir de un perfil de velocidad controlado. No se versiona telemetría real
(principio "motor sin datos"): los casos límite se expresan como parámetros.

Convenciones de dominio horneadas aquí (confirmadas con el producto):
- `steering` negativo = izquierda; positivo = derecha.
- `glat` positivo = izquierda (convención MoTeC/AMS2).
- El tiempo se **integra** a partir de distancia/velocidad: ir más lento cuesta
  más tiempo, igual que en pista. Esto es lo que hace válidos los tests de delta.
"""
import pytest

from fantasma.core.lap import Lap

# canales opcionales que make_lap sabe generar (además de time/dist/speed,
# que siempre están)
OPTIONAL = ("throttle", "brake", "steering", "gear", "glat", "glong", "rpm", "alt")


def _speed_at(d, base, valleys):
    """Velocidad (km/h) en la distancia d: base menos el valle más profundo."""
    dip = 0.0
    for v in valleys:
        c, vmin, hw = v["center"], v["vmin"], v["half_width"]
        if abs(d - c) <= hw:
            depth = (base - vmin) * (1.0 - abs(d - c) / hw)
            dip = max(dip, depth)
    return base - dip


def _active_valley(d, valleys):
    """El valle cuyo segmento contiene d (o None), para derivar inputs."""
    for v in valleys:
        if abs(d - v["center"]) <= v["half_width"]:
            return v
    return None


def make_lap(length_m=1500.0, step_m=1.0, base_speed=180.0,
             valleys=None, channels=OPTIONAL, meta=None):
    """Construye una `Lap` sintética.

    Args:
        length_m:   longitud de la vuelta en metros.
        step_m:     separación entre muestras (en distancia).
        base_speed: velocidad en recta (km/h).
        valleys:    lista de dicts {center, vmin, half_width, direction} — cada
                    uno es una "curva" (un valle de velocidad con frenada/ápex/gas).
                    direction: "left" | "right". Por defecto, dos curvas.
        channels:   qué canales OPCIONALES incluir. Quitar uno prueba la
                    degradación graceful (p. ej. channels sin "gear").
        meta:       dict de metadatos a fusionar.

    Returns:
        Lap con time/dist/speed + los canales opcionales pedidos.
    """
    if valleys is None:
        valleys = [
            {"center": 400.0, "vmin": 80.0, "half_width": 120.0, "direction": "right"},
            {"center": 1000.0, "vmin": 60.0, "half_width": 140.0, "direction": "left"},
        ]
    chans = set(channels)

    dist, speed = [], []
    d = 0.0
    while d <= length_m:
        dist.append(d)
        speed.append(_speed_at(d, base_speed, valleys))
        d += step_m

    n = len(dist)

    # tiempo integrado a partir de distancia / velocidad media del tramo
    time = [0.0]
    for i in range(1, n):
        dd = dist[i] - dist[i - 1]
        v_avg = (speed[i] + speed[i - 1]) / 2.0 / 3.6  # km/h -> m/s
        time.append(time[-1] + dd / max(v_avg, 0.5))

    lap = Lap(meta=dict(meta or {}))
    lap.channels["time"] = time
    lap.channels["dist"] = dist
    lap.channels["speed"] = speed

    # --- canales opcionales derivados del perfil ---
    throttle, brake, steering, gear, glat, glong, rpm, alt = ([] for _ in range(8))
    for i in range(n):
        di, vi = dist[i], speed[i]
        val = _active_valley(di, valleys)
        # zona de frenada: antes del ápex dentro del valle; gas: después
        if val is not None:
            before_apex = di <= val["center"]
            t = 0.0 if before_apex else min(100.0, (di - val["center"]) / val["half_width"] * 100.0)
            b = 90.0 if before_apex and di >= val["center"] - val["half_width"] else 0.0
            sgn_steer = -1.0 if val["direction"] == "left" else 1.0
            sgn_glat = 1.0 if val["direction"] == "left" else -1.0
            shape = 1.0 - abs(di - val["center"]) / val["half_width"]
            st = sgn_steer * 30.0 * shape
            gl = sgn_glat * 2.5 * shape
            gln = -1.2 if before_apex else 0.6
        else:
            t, b, st, gl, gln = 100.0, 0.0, 0.0, 0.0, 0.0
        throttle.append(t)
        brake.append(b)
        steering.append(st)
        glat.append(gl)
        glong.append(gln)
        gear.append(float(max(1, min(6, int(vi // 35) + 1))))
        rpm.append(3000.0 + vi * 30.0)
        alt.append(100.0)

    derived = {"throttle": throttle, "brake": brake, "steering": steering,
               "gear": gear, "glat": glat, "glong": glong, "rpm": rpm, "alt": alt}
    for name in OPTIONAL:
        if name in chans:
            lap.channels[name] = derived[name]

    return lap


@pytest.fixture
def lap_factory():
    """Expone make_lap como fixture para tests que quieran construir variantes."""
    return make_lap
