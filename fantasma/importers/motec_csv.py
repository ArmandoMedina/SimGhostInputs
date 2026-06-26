"""Importador de CSV exportado por MoTeC i2 (y el mismo layout guardado como .xlsx).

Estructura del export de i2:
    filas 1-~13 : metadatos en pares clave/valor (col A/B y col E/F)
    una fila con los nombres de canal (empieza con 'Time')
    la fila siguiente con las unidades
    filas en blanco
    datos
"""

import csv
import os

from ..core.lap import Lap
from ._util import detect_delimiter, pfloat

MOTEC_MAP = {
    "Time": "time",
    "Distance": "dist",
    "Ground Speed": "speed",
    "Throttle Pos": "throttle",
    "Brake Pos": "brake",
    "Steering Pos": "steering",
    "Gear": "gear",
    "G Force Lat": "glat",
    "G Force Long": "glong",
    "Engine RPM": "rpm",
    "Altitude": "alt",
    "Lap Number": "lap_number",
    "BR2 Beacon Number": "beacon",
    "Speed": "speed",
    "THROTTLE": "throttle",
    "BRAKE": "brake",
    "STEERANGLE": "steering",
    "Tyre Speed FL": "ts_fl",
    "Tyre Speed FR": "ts_fr",
    "Tyre Speed RL": "ts_rl",
    "Tyre Speed RR": "ts_rr",
    "Tyre Temp FL": "tt_fl",
    "Tyre Temp FR": "tt_fr",
    "Tyre Temp RL": "tt_rl",
    "Tyre Temp RR": "tt_rr",
    "Brake Temp FL": "bt_fl",
    "Brake Temp FR": "bt_fr",
    "Brake Temp RL": "bt_rl",
    "Brake Temp RR": "bt_rr",
    "ABS Active": "abs",
    "TCS Active": "tcs",
    "Fuel Level": "fuel",
    "Clutch Pos": "clutch",
    "Brake Bias Setting": "bias",
    "Track Temp": "track_temp",
    "Ambient Temp": "ambient_temp",
}


class NotMotecFormat(Exception):
    pass


def _rows_from_csv(path):
    delimiter = detect_delimiter(path)
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.reader(f, delimiter=delimiter):
            yield row


def _rows_from_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        raise ImportError("Para leer .xlsx instala openpyxl: pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True)
    for row in wb.active.iter_rows(values_only=True):
        yield ["" if c is None else c for c in row]


def load(path):
    rows = _rows_from_xlsx(path) if path.lower().endswith(".xlsx") else _rows_from_csv(path)
    meta = {}
    header = None
    data_started = False
    lap = Lap()
    cols = []  # [(indice, nombre_canonico)]
    extra = {}

    for row in rows:
        if not row or all(str(c).strip() == "" for c in row):
            continue
        first = str(row[0]).strip()
        if header is None:
            if first == "Time":
                header = [str(c).strip() for c in row]
                for i, name in enumerate(header):
                    if name in MOTEC_MAP:
                        cols.append((i, MOTEC_MAP[name]))
                    elif name:
                        extra[i] = name
                for _, cn in cols:
                    lap.channels[cn] = []
                continue
            # metadatos en pares clave/valor
            if len(row) > 1 and first:
                meta[first] = str(row[1]).strip() if row[1] is not None else ""
            if len(row) > 5 and str(row[4]).strip():
                meta[str(row[4]).strip()] = str(row[5]).strip()
            continue
        # tras el header: la fila de unidades y filas vacias hasta el primer dato
        if not data_started:
            try:
                pfloat(first)
                data_started = True
            except ValueError:
                continue
        if data_started:
            vals = {}
            bad = False
            for i, cn in cols:
                try:
                    vals[cn] = pfloat(row[i]) if i < len(row) and str(row[i]).strip() != "" else 0.0
                except (ValueError, TypeError):
                    vals[cn] = 0.0
                    if cn in ("time", "dist"):
                        bad = True
            # descartar filas de cierre sin tiempo/distancia validos
            if bad or (
                ("dist" in vals)
                and str(row[[i for i, c in cols if c == "dist"][0]]).strip() in ("", "None")
            ):
                continue
            for _, cn in cols:
                lap.channels[cn].append(vals[cn])

    if header is None:
        raise NotMotecFormat(
            "No se encontro la fila de canales 'Time' (¿es un export de MoTeC i2?)"
        )
    lap.meta = meta
    # beacons del outing, si existen
    bm = meta.get("Beacon Markers", "")
    try:
        lap.meta["beacons"] = [float(x) for x in bm.split()]
    except ValueError:
        lap.meta["beacons"] = []
    lap.meta["source_file"] = os.path.basename(path)
    return lap
