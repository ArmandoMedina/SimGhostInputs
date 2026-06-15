"""Importadores: cada uno devuelve un Lap (outing completo) con canales canonicos."""
import os


def load(path, column_map=None):
    """Carga un archivo de telemetria segun su extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv", ".xlsx"):
        from . import motec_csv
        try:
            return motec_csv.load(path)
        except motec_csv.NotMotecFormat:
            if ext == ".csv":
                from . import generic_csv
                return generic_csv.load(path, column_map)
            raise
    raise ValueError("Formato no soportado: %s" % ext)


def load_laps(path, column_map=None):
    """Carga un archivo y separa las vueltas. Devuelve lista de Lap."""
    from ..core.normalize import split_laps
    return split_laps(load(path, column_map))
