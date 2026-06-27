"""Test sistemático de degradación graceful por canales ausentes — compare().

Cubre las 32 combinaciones (2^5) de los canales {glat, glong, gear, abs, tcs}
presentes o ausentes, ejercitando el pipeline completo:
  compare() -> delta_trace / detect_corners / extract_milestones / wear_summary

Para cada combinación verifica:
  (a) No crashea.
  (b) Se detectan curvas y el delta básico se calcula.
  (c) Los campos que dependen de un canal ausente NO aparecen (no se inventan).
  (d) Los campos que dependen de un canal presente SÍ aparecen.

Parcialmente cubierto por la suite: test_compare.py tiene casos unitarios de gear
y glat ausentes; aquí el cubrimiento es sistemático y cruza todos los canales.
"""

import itertools

import pytest
from conftest import make_lap

from fantasma.core.compare import compare

# ---------------------------------------------------------------------------
# Constantes de configuración del parametrize
# ---------------------------------------------------------------------------

# Canales degradables que make_lap sabe generar (parte de OPTIONAL)
_MAKE_LAP_OPT = frozenset({"glat", "glong", "gear"})

# Canales degradables que NO genera make_lap; se añaden manualmente si presentes
_MANUAL_CH = frozenset({"abs", "tcs"})

# Canales base que SIEMPRE están: necesarios para el perfil de velocidad,
# frenadas y turn-in (la lógica de corners los requiere para hitos de calidad).
_BASE = ("throttle", "brake", "steering", "rpm", "alt")

_ALL_DEGRADABLE = ("glat", "glong", "gear", "abs", "tcs")

# 32 subconjuntos: desde el conjunto vacío hasta los 5 canales juntos
_SUBSETS = [
    frozenset(combo)
    for r in range(len(_ALL_DEGRADABLE) + 1)
    for combo in itertools.combinations(_ALL_DEGRADABLE, r)
]


def _id(subset):
    """ID legible para pytest -v."""
    return "+".join(sorted(subset)) if subset else "ninguno"


# ---------------------------------------------------------------------------
# Test parametrizado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("present", _SUBSETS, ids=_id)
def test_compare_degradacion_graceful(present):
    """Para la combinación `present` de canales opcionales:
    compare() no crashea y los campos reflejan fielmente qué canales existen."""

    # --- construir vueltas sintéticas ---
    # canales de make_lap: base fija + los del subset que make_lap puede generar
    make_lap_channels = _BASE + tuple(c for c in _MAKE_LAP_OPT if c in present)

    ref = make_lap(channels=make_lap_channels)
    # drv siempre más lento (base_speed 160 vs 180 de ref) para que total_delta > 0
    drv = make_lap(channels=make_lap_channels, base_speed=160.0)

    # añadir abs/tcs como canal de ceros si están en el subset
    n = len(ref)
    for ch in _MANUAL_CH:
        if ch in present:
            ref.channels[ch] = [0.0] * n
            drv.channels[ch] = [0.0] * n

    # --- (a) no crashea ---
    trace, rows, summary = compare(ref, drv, step=5.0)

    # --- (b) campos base siempre presentes ---
    # el perfil de dos valles siempre genera curvas detectables
    assert rows, f"No se detectaron curvas con canales presentes: {present}"
    assert "ref_laptime" in summary
    assert "drv_laptime" in summary
    assert "total_delta" in summary
    # drv más lento -> delta acumulado positivo
    assert summary["total_delta"] > 0, "delta esperado positivo (drv más lento)"
    # la traza tiene puntos con dist y delta_t siempre
    assert len(trace) > 0
    assert all("dist" in pt and "delta_t" in pt for pt in trace)

    # --- (c/d) canales opcionales en la traza de delta ---
    # gear, glat y glong de ref/drv aparecen en cada punto de la traza si y solo si
    # el canal está presente en la vuelta (delta_trace itera sobre r.channels).
    # NOTA: vmin_gear se calcula en _corner_metrics pero compare() NO lo copia a las
    # rows de comparación por curva — es un campo interno que no aflora en la salida de
    # compare(). Por eso la verificación de gear se hace aquí en la traza, no en rows.
    first = trace[0]
    for ch in ("gear", "glat", "glong"):
        if ch in present:
            assert f"ref_{ch}" in first, f"ref_{ch} ausente en traza con canal {ch} presente"
        else:
            assert f"ref_{ch}" not in first, f"ref_{ch} apareció en traza sin canal {ch}"

    # --- (c/d) campos dependientes de 'abs' en rows de curva ---
    # ref_abs/drv_abs aparecen en la row solo si abs está en AMBAS vueltas;
    # assist_count devuelve 0 (no None) con canal presente y sin activaciones,
    # por lo que el campo SÍ aparece (con valor 0) cuando el canal existe.
    if "abs" not in present:
        for row in rows:
            assert "ref_abs" not in row, "ref_abs apareció sin canal abs"
            assert "drv_abs" not in row, "drv_abs apareció sin canal abs"
    else:
        assert any("ref_abs" in row for row in rows), (
            "ref_abs ausente aun con canal abs presente en ambas vueltas"
        )

    # --- (c/d) wear_summary: abs_count y tcs_count por canal ---
    for key in ("ref_wear", "drv_wear"):
        w = summary[key]
        if "abs" not in present:
            assert "abs_count" not in w, f"abs_count en {key} sin canal abs"
        else:
            # canal presente con ceros -> 0 activaciones, pero el campo existe
            assert "abs_count" in w, f"abs_count ausente en {key} con canal abs"
        if "tcs" not in present:
            assert "tcs_count" not in w, f"tcs_count en {key} sin canal tcs"
        else:
            assert "tcs_count" in w, f"tcs_count ausente en {key} con canal tcs"
