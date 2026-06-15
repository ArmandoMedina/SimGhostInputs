"""Modelo de datos interno: una vuelta (o outing) con canales canonicos.

Canales canonicos (todos opcionales salvo time y dist):
    time      s      tiempo desde el inicio del segmento
    dist      m      distancia desde el inicio del segmento
    speed     km/h
    throttle  %      0-100
    brake     %      0-100
    steering  deg    negativo = izquierda
    gear      -      entero
    glat      G      positivo = izquierda (convencion del logger)
    glong     G
    rpm       rpm
    alt       m      altitud
"""
from dataclasses import dataclass, field

CANONICAL = ["time", "dist", "speed", "throttle", "brake", "steering",
             "gear", "glat", "glong", "rpm", "alt"]


@dataclass
class Lap:
    """Serie de muestras por canal. Todas las listas tienen la misma longitud."""
    channels: dict = field(default_factory=dict)   # nombre canonico -> list[float]
    meta: dict = field(default_factory=dict)       # venue, vehicle, driver, beacons...

    def __len__(self):
        return len(self.channels.get("time", []))

    def col(self, name):
        return self.channels.get(name)

    def has(self, name):
        return name in self.channels

    def sample(self, i):
        return {k: v[i] for k, v in self.channels.items()}

    def slice_time(self, t0, t1):
        """Sub-vuelta con tiempo y distancia re-referenciados a su inicio."""
        t = self.channels["time"]
        idx = [i for i, x in enumerate(t) if t0 <= x < t1]
        if not idx:
            return Lap(meta=dict(self.meta))
        out = Lap(meta=dict(self.meta))
        for k, v in self.channels.items():
            out.channels[k] = [v[i] for i in idx]
        toff = out.channels["time"][0]
        out.channels["time"] = [x - toff for x in out.channels["time"]]
        if "dist" in out.channels:
            doff = out.channels["dist"][0]
            out.channels["dist"] = [x - doff for x in out.channels["dist"]]
        return out

    @property
    def laptime(self):
        t = self.channels.get("time")
        return (t[-1] - t[0]) if t else 0.0

    @property
    def length(self):
        d = self.channels.get("dist")
        return (d[-1] - d[0]) if d else 0.0
