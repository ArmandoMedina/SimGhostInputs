"""Utilidades compartidas de importación de CSV."""


def detect_delimiter(path):
    """Detecta el separador de un CSV: coma (por defecto) o punto y coma.

    Algunos exports europeos de MoTeC i2 usan ';' como separador (y coma decimal).
    Se decide por la primera línea no vacía: gana el separador más frecuente.
    """
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            if line.strip():
                return ";" if line.count(";") > line.count(",") else ","
    return ","


def pfloat(s):
    """float tolerante a coma decimal europea: '100,5' -> 100.5.

    Solo trata la coma como separador decimal cuando no hay punto en el valor
    (en un CSV separado por comas los campos numéricos nunca contienen coma,
    así que es seguro aplicarlo siempre).
    """
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s)
