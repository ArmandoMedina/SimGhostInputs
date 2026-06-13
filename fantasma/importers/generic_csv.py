"""Importador de CSV generico: primera fila = encabezados, datos debajo.

column_map: dict encabezado_origen -> canal canonico, p. ej.
    {"LapDist": "dist", "SessionTime": "time", "Speed_kmh": "speed"}
Si no se da, intenta adivinar por nombres comunes (case-insensitive).
"""
import csv

from ..core.lap import Lap

GUESS = {
    "time": "time", "sessiontime": "time", "t": "time",
    "lap_time_s": "time", "laptime_s": "time", "laptime": "time", "lap_time": "time",
    "dist": "dist", "distance": "dist", "lapdist": "dist", "lap_distance": "dist",
    "dist_m": "dist", "dist_meters": "dist",
    "speed": "speed", "speed_kmh": "speed", "kmh": "speed", "groundspeed": "speed",
    "throttle": "throttle", "gas": "throttle",
    "throttle_pct": "throttle", "throttlepct": "throttle", "throttle_percent": "throttle",
    "brake": "brake", "freno": "brake",
    "brake_pct": "brake", "brakepct": "brake", "brake_percent": "brake",
    "steering": "steering", "steer": "steering", "steerangle": "steering",
    "steering_deg": "steering", "steering_angle": "steering",
    "gear": "gear", "marcha": "gear",
    "glat": "glat", "g_lat": "glat", "lateralg": "glat",
    "glong": "glong", "g_long": "glong",
    "rpm": "rpm", "enginerpm": "rpm",
    "alt": "alt", "altitude": "alt",
}


def load(path, column_map=None):
    lap = Lap(meta={"source_file": path, "beacons": []})
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        cols = []
        for i, name in enumerate(header):
            key = name.strip()
            canon = None
            if column_map and key in column_map:
                canon = column_map[key]
            elif key.lower().replace(" ", "") in GUESS:
                canon = GUESS[key.lower().replace(" ", "")]
            if canon:
                cols.append((i, canon))
                lap.channels.setdefault(canon, [])
        if not any(c == "dist" for _, c in cols) or not any(c == "time" for _, c in cols):
            raise ValueError(
                "El CSV necesita al menos columnas de tiempo y distancia. "
                "Usa --map para indicar cuales son (ej. --map LapDist=dist --map SessTime=time).")
        for row in reader:
            if not row:
                continue
            for i, cn in cols:
                try:
                    lap.channels[cn].append(float(row[i]))
                except (ValueError, IndexError):
                    lap.channels[cn].append(0.0)
    return lap
