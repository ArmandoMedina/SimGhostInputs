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

from ..core.lap import Lap, MOTEC_MAP


class NotMotecFormat(Exception):
    pass


def _rows_from_csv(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.reader(f):
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
                float(first)
                data_started = True
            except ValueError:
                continue
        if data_started:
            vals = {}
            bad = False
            for i, cn in cols:
                try:
                    vals[cn] = float(row[i]) if i < len(row) and str(row[i]).strip() != "" else 0.0
                except (ValueError, TypeError):
                    vals[cn] = 0.0
                    if cn in ("time", "dist"):
                        bad = True
            # descartar filas de cierre sin tiempo/distancia validos
            if bad or (("dist" in vals) and str(row[[i for i, c in cols if c == "dist"][0]]).strip() in ("", "None")):
                continue
            for _, cn in cols:
                lap.channels[cn].append(vals[cn])

    if header is None:
        raise NotMotecFormat("No se encontro la fila de canales 'Time' (¿es un export de MoTeC i2?)")
    if "beacon markers" in {k.lower() for k in meta}:
        pass
    lap.meta = meta
    # beacons del outing, si existen
    bm = meta.get("Beacon Markers", "")
    try:
        lap.meta["beacons"] = [float(x) for x in bm.split()]
    except ValueError:
        lap.meta["beacons"] = []
    lap.meta["source_file"] = os.path.basename(path)
    return lap
