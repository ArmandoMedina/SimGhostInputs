"""Tier 1 — comparación piloto vs referencia.

Aquí viven las afirmaciones que SON la promesa del producto:
- piloto más lento => delta_t POSITIVO (= "pierdes tiempo");
- ápex más rápido => d_vmin POSITIVO;
- faltar un canal opcional (gear/glat) NO rompe la comparación (degradación graceful).
"""

from conftest import make_lap
from fantasma.core.compare import compare, delta_trace


def test_identical_laps_have_zero_delta():
    ref = make_lap()
    drv = make_lap()
    trace = delta_trace(ref, drv, step=5.0)
    # vueltas idénticas -> delta nulo en todo punto
    assert max(abs(row["delta_t"]) for row in trace) < 1e-6


def test_slower_driver_loses_time_positive_delta():
    ref = make_lap(base_speed=200.0)
    drv = make_lap(base_speed=150.0)  # más lento en todas partes
    trace = delta_trace(ref, drv, step=5.0)
    # convención confirmada: piloto más lento => delta acumulado POSITIVO
    assert trace[-1]["delta_t"] > 0.0


def test_faster_apex_gives_positive_d_vmin():
    ref = make_lap(
        valleys=[{"center": 700.0, "vmin": 70.0, "half_width": 150.0, "direction": "right"}],
        length_m=1500.0,
    )
    drv = make_lap(
        valleys=[{"center": 700.0, "vmin": 90.0, "half_width": 150.0, "direction": "right"}],
        length_m=1500.0,
    )
    _, rows, _ = compare(ref, drv, step=5.0)
    assert rows  # se detectó la curva
    # piloto pasa más rápido por el ápex (90 vs 70) => d_vmin positivo
    assert rows[0]["d_vmin"] > 0


def test_summary_counts_corners_and_laptimes():
    ref = make_lap()  # dos valles por defecto
    drv = make_lap(base_speed=160.0)
    _, rows, summary = compare(ref, drv, step=5.0)
    assert summary["corners"] == len(rows) == 2
    assert summary["drv_laptime"] > summary["ref_laptime"]  # drv más lento
    assert summary["total_delta"] > 0


def test_compare_without_gear_channel_does_not_crash():
    # degradación graceful: sin canal de marcha la comparación sigue funcionando
    sin_gear = tuple(c for c in ("throttle", "brake", "steering", "glat", "glong") if c != "gear")
    ref = make_lap(channels=sin_gear)
    drv = make_lap(channels=sin_gear, base_speed=160.0)
    _, rows, _ = compare(ref, drv, step=5.0)
    assert rows
    # no debe haberse inventado una marcha
    assert "vmin_gear" not in rows[0]


def test_compare_without_glat_channel_does_not_crash():
    sin_glat = tuple(c for c in ("throttle", "brake", "steering", "gear", "glong") if c != "glat")
    ref = make_lap(channels=sin_glat)
    drv = make_lap(channels=sin_glat, base_speed=160.0)
    _, rows, summary = compare(ref, drv, step=5.0)
    assert rows
    assert summary["corners"] == 2


# ---------------------------------------------------------------------------
# FIX 2 — aviso de delta sospechosamente grande (posible circuito distinto)
# ---------------------------------------------------------------------------


def test_compare_avisa_delta_sospechoso():
    """Delta > 50 % del tiempo de vuelta de referencia dispara el aviso.

    Caso tipico de bug silencioso: ref de un circuito, piloto de otro.
    La comparacion produce un numero pero el aviso lo delata.
    """
    ref = make_lap(base_speed=180.0)
    # piloto tan lento que el delta supera con creces el 50 % del laptime de ref
    drv = make_lap(base_speed=20.0)
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("sospechosamente grande" in a for a in avisos), (
        "Se esperaba aviso de delta grande; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_delta_normal():
    """Delta normal (diferencia de segundos) NO dispara el aviso."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=175.0)  # ligeramente mas lento
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("sospechosamente grande" in a for a in avisos), (
        "Aviso inesperado de delta grande: %r" % avisos
    )


# ---------------------------------------------------------------------------
# FIX 3 — aviso informativo de autos distintos
# ---------------------------------------------------------------------------


def test_compare_avisa_autos_distintos():
    """Metadata de Vehicle distinta en ref y piloto genera aviso informativo."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap(meta={"Vehicle": "Ferrari 296 GT3"})
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("autos distintos" in a for a in avisos), (
        "Se esperaba aviso de autos distintos; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_autos_iguales():
    """Mismo auto en ref y piloto -> sin aviso de autos."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


def test_compare_sin_aviso_vehicle_ausente():
    """Si la metadata de Vehicle no esta disponible, NO avisa ni crashea."""
    ref = make_lap()  # sin meta -> meta={}
    drv = make_lap()
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


def test_compare_sin_aviso_vehicle_solo_en_ref():
    """Vehicle solo en ref (no en piloto) -> degradacion graciosa, sin aviso."""
    ref = make_lap(meta={"Vehicle": "BMW M4 GT3"})
    drv = make_lap()
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("autos distintos" in a for a in avisos)


# ---------------------------------------------------------------------------
# FIX 4 — aviso cuando piloto es más rápido que referencia (posible inversión)
# ---------------------------------------------------------------------------


def test_compare_avisa_piloto_mas_rapido():
    """Delta muy negativo (piloto mucho más rápido) dispara aviso de inversión.

    Caso típico: usuario subió los archivos al revés — referencia lenta, piloto rápido.
    """
    ref = make_lap(base_speed=100.0)  # vuelta lenta como "referencia"
    drv = make_lap(base_speed=200.0)  # piloto claramente más rápido
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert any("piloto más rápido" in a for a in avisos), (
        "Se esperaba aviso de piloto invertido; avisos actuales: %r" % avisos
    )


def test_compare_sin_aviso_piloto_ligeramente_mas_rapido():
    """Un piloto ligeramente más rápido (delta < -1 s) NO dispara el aviso."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=182.0)  # mínimamente más rápido
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("piloto más rápido" in a for a in avisos), (
        "Aviso inesperado de inversión: %r" % avisos
    )


def test_compare_sin_aviso_piloto_mas_lento():
    """Piloto más lento (delta positivo) -> no hay aviso de inversión."""
    ref = make_lap(base_speed=180.0)
    drv = make_lap(base_speed=150.0)
    _, _, summary = compare(ref, drv, step=5.0)
    avisos = summary.get("avisos", [])
    assert not any("piloto más rápido" in a for a in avisos)


# ---------------------------------------------------------------------------
# Frenada simétrica — referencia y piloto se miden con la MISMA vara
#
# El punto de frenada se detectaba en DOS sitios que divergieron: la referencia
# en corners.extract_milestones (ventana ampliada + fases por pico máximo) y el
# piloto en compare._corner_metrics (ventana del segmento + "último bloque
# fuerte"). Esa asimetría inflaba `d_brake_m` y levantaba banderas "frenada"
# espurias. El helper compartido `select_brake_phase` las mide igual.
# ---------------------------------------------------------------------------


def _single_corner_lap(brake_blocks, apex=400.0, length_m=900.0, base_speed=180.0):
    """Vuelta de UNA curva (V-Min en `apex`) con el canal de freno escrito a mano
    a partir de `brake_blocks` = [(d0, d1, peak), ...]; el resto de canales sale
    de la forma del valle de make_lap. Controla con precisión dos fases fuertes
    de freno (doble pisada) para provocar la divergencia de algoritmos."""
    lap = make_lap(
        length_m=length_m,
        base_speed=base_speed,
        valleys=[{"center": apex, "vmin": 80.0, "half_width": 200.0, "direction": "right"}],
        channels=("throttle", "brake", "steering", "gear", "glat", "glong"),
    )
    dist = lap.channels["dist"]
    brake, throttle = [], []
    for d in dist:
        pk = 0.0
        for d0, d1, p in brake_blocks:
            if d0 <= d <= d1:
                pk = max(pk, p)
        brake.append(pk)
        throttle.append(0.0 if (pk > 0 or d <= apex) else 100.0)
    lap.channels["brake"] = brake
    lap.channels["throttle"] = throttle
    return lap


def test_compare_same_lap_has_zero_d_brake_in_every_corner():
    """Invariante: si el piloto y la referencia son la MISMA vuelta, entonces
    `d_brake_m == 0` en TODAS las curvas. Con la asimetría de HEAD (la
    referencia elige la fase de pico máximo, el piloto el último bloque fuerte)
    una doble pisada da `d_brake_m != 0` comparando la vuelta contra sí misma:
    la prueba más limpia de que la asimetría estaba viva. FALLA con HEAD."""
    lap = _single_corner_lap([(200.0, 260.0, 95.0), (300.0, 360.0, 80.0)])
    _, rows, _ = compare(lap, lap, step=5.0)
    braked = [r for r in rows if "d_brake_m" in r]
    assert braked, "se esperaba al menos una curva con frenada detectada"
    assert all(r["d_brake_m"] == 0 for r in braked), (
        "misma vuelta debe dar d_brake_m == 0; filas: %r"
        % [(r["id"], r["d_brake_m"]) for r in braked]
    )


def test_driver_brake_anchors_on_first_of_double_pedal():
    """El piloto también se beneficia del arreglo: ante una doble pisada fuerte
    con el pico mayor en la PRIMERA, `drv_brake_d` ancla en la primera pisada,
    no en la segunda. Con HEAD el piloto usaba "último bloque fuerte" y anclaba
    en la segunda (~300); el helper compartido ancla en la de pico máximo
    (~200). FALLA con HEAD."""
    ref = _single_corner_lap([(210.0, 360.0, 95.0)])  # frenada limpia de un bloque
    drv = _single_corner_lap([(200.0, 260.0, 95.0), (300.0, 360.0, 80.0)])  # doble pisada
    _, rows, _ = compare(ref, drv, step=5.0)
    braked = [r for r in rows if "drv_brake_d" in r]
    assert braked, "se esperaba una curva con frenada del piloto"
    assert braked[0]["drv_brake_d"] <= 260, (
        "drv_brake_d debe anclar en la primera pisada (~200), no en la segunda (~300); valor: %r"
        % braked[0]["drv_brake_d"]
    )


def test_compare_umbrales_no_default_fluyen_a_ambos_lados():
    """Los umbrales de frenada salen de UNA fuente (los parametros de `compare`)
    y llegan por igual a la referencia (`extract_milestones`) y al piloto
    (`_corner_metrics`). Con la asimetria latente de antes -- la referencia
    tomaba el umbral del config y el piloto usaba el default del helper -- pasar
    un `brake_strong` no-default rompia el invariante `d_brake_m == 0` de la
    vuelta contra si misma. Este test lo cubre: `test_compare_same_lap...` usa
    defaults en ambos lados y por eso no probaba su propia premisa.

    Diseno: dos fases fuertes, la temprana (~150, pico 60) mayor que la tardia
    (~280, pico 45). Con `brake_strong=50` ambos lados eligen la de pico maximo
    (150). Con `brake_strong=70` (por ENCIMA de los dos picos) ninguna fase
    supera el filtro y ambos lados caen a la ultima fase cronologica (280). Que
    el metro elegido cambie de 150 a 280 prueba que el umbral llega al lado de la
    REFERENCIA; que `d_brake_m` siga en 0 prueba que llega identico al del
    PILOTO. Si fluyera a un solo lado, con 70 un lado quedaria en 150 y el otro
    en 280 y el invariante se romperia."""
    lap = _single_corner_lap([(150.0, 200.0, 60.0), (280.0, 340.0, 45.0)])

    _, rows_def, _ = compare(lap, lap, step=5.0, brake_strong=50)
    braked_def = [r for r in rows_def if "d_brake_m" in r]
    assert braked_def, "se esperaba una curva con frenada"
    assert all(r["d_brake_m"] == 0 for r in braked_def)
    assert braked_def[0]["ref_brake_d"] == braked_def[0]["drv_brake_d"] == 150

    _, rows_hi, _ = compare(lap, lap, step=5.0, brake_strong=70)
    braked_hi = [r for r in rows_hi if "d_brake_m" in r]
    assert braked_hi, "se esperaba una curva con frenada"
    assert all(r["d_brake_m"] == 0 for r in braked_hi), (
        "umbral no-default debe llegar identico a referencia y piloto; filas: %r"
        % [(r["id"], r["ref_brake_d"], r["drv_brake_d"], r["d_brake_m"]) for r in braked_hi]
    )
    assert braked_hi[0]["ref_brake_d"] == braked_hi[0]["drv_brake_d"] == 280
