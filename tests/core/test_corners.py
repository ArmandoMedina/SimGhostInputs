"""Tier 1 — detección de curvas e hitos sobre trazados sintéticos de valles conocidos."""

import pytest

from conftest import make_lap
from fantasma.core.corners import detect_corners, detect_gear_shifts, extract_milestones
from fantasma.core.lap import Lap


def test_detects_one_event_per_valley():
    valleys = [
        {"center": 300.0, "vmin": 80.0, "half_width": 120.0, "direction": "right"},
        {"center": 800.0, "vmin": 60.0, "half_width": 120.0, "direction": "left"},
        {"center": 1300.0, "vmin": 70.0, "half_width": 120.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1700.0, valleys=valleys)
    events, _ = detect_corners(lap)
    assert len(events) == 3
    assert all(kind == "vmin" for kind, _ in events)


def test_detect_requires_speed_channel():
    lap = Lap()
    lap.channels = {"time": [0.0, 1.0], "dist": [0.0, 10.0]}  # sin 'speed'
    with pytest.raises(ValueError):
        detect_corners(lap)


def test_detect_requires_dist_channel():
    # Export real sin canal de distancia (ej. ORECA 07 vía sim-to-motec): debe
    # degradar con un ValueError claro, no propagar un KeyError('dist') desnudo.
    lap = Lap()
    lap.channels = {"time": [0.0, 1.0], "speed": [100.0, 90.0]}  # sin 'dist'
    with pytest.raises(ValueError):
        detect_corners(lap)


def test_milestones_have_apex_and_brake_start():
    lap = make_lap()
    corners = extract_milestones(lap)
    assert len(corners) == 2
    for c in corners:
        assert "apex" in c["milestones"]
        assert "brake_start" in c["milestones"]
        # el ápex es el punto más lento (V-Min)
        assert c["milestones"]["apex"]["v"] in (60, 80)


def test_corner_direction_matches_valley():
    valleys = [
        {"center": 400.0, "vmin": 80.0, "half_width": 120.0, "direction": "left"},
        {"center": 1000.0, "vmin": 70.0, "half_width": 120.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1500.0, valleys=valleys)
    corners = extract_milestones(lap)
    assert corners[0]["direction"] == "left"
    assert corners[1]["direction"] == "right"


def test_detection_without_glat_still_finds_vmin_corners():
    # degradación graceful: sin glat no hay kinks ni g_lat_max, pero las curvas V-Min siguen
    sin_glat = ("throttle", "brake", "steering", "gear")
    lap = make_lap(channels=sin_glat)
    corners = extract_milestones(lap)
    assert len(corners) == 2
    assert all("g_lat_max" not in c["milestones"] for c in corners)


def _lap_with_custom_pedals(brake_range, onset_d, blip_range=None):
    """Vuelta sintética de una curva con freno/gas artesanales (no derivados
    de la forma del valle de make_lap), para controlar con precisión el hueco
    entre frenada y gas: roces fugaces, coast y overlap.
    """
    lap = make_lap(
        length_m=900.0,
        valleys=[{"center": 310.0, "vmin": 80.0, "half_width": 250.0, "direction": "right"}],
        channels=("throttle", "brake"),
    )
    dist = lap.channels["dist"]
    throttle, brake = [], []
    for d in dist:
        b = 90.0 if brake_range[0] <= d <= brake_range[1] else 0.0
        t = 40.0 if d >= onset_d else 0.0
        if blip_range and blip_range[0] <= d <= blip_range[1]:
            t = 20.0
        throttle.append(t)
        brake.append(b)
    lap.channels["throttle"] = throttle
    lap.channels["brake"] = brake
    return lap


def test_throttle_on_ignores_fleeting_blip_and_anchors_on_sustained_gas():
    # roce fugaz de pedal en ~316-318 (freno-motor / ruido) durante el coast;
    # el gas real, sostenido, entra en 393 — el hito debe anclar ahí, no en el roce.
    lap = _lap_with_custom_pedals(
        brake_range=(150.0, 270.0), onset_d=393.0, blip_range=(316.0, 318.0)
    )
    corners = extract_milestones(lap)
    assert len(corners) == 1
    ms = corners[0]["milestones"]
    assert "throttle_on" in ms
    assert ms["throttle_on"]["d"] >= 390


def test_coast_detected_between_brake_release_and_sustained_throttle():
    lap = _lap_with_custom_pedals(brake_range=(150.0, 270.0), onset_d=393.0)
    corners = extract_milestones(lap)
    ms = corners[0]["milestones"]
    assert "coast_start" in ms
    assert "coast_end" in ms
    assert (
        ms["brake_release"]["d"]
        < ms["coast_start"]["d"]
        <= ms["coast_end"]["d"]
        < ms["throttle_on"]["d"]
    )


def test_throttle_on_ignores_blip_at_tail_of_segment():
    # blip corto (3 muestras >umbral) pegado al final del segmento (limite
    # `hi`): sin la guarda de longitud, seg[j:j+throttle_on_window] devuelve
    # menos de throttle_on_window muestras ahi y all() pasa trivialmente,
    # anclando throttle_on en un roce que nunca se sostuvo 15 muestras.
    lap = _lap_with_custom_pedals(brake_range=(150.0, 270.0), onset_d=10_000.0)
    dist = lap.channels["dist"]
    throttle = lap.channels["throttle"]
    for i, d in enumerate(dist):
        if 658.0 <= d <= 660.0:
            throttle[i] = 20.0
    corners = extract_milestones(lap)
    ms = corners[0]["milestones"]
    assert "throttle_on" not in ms


def _lap_with_sustained_pedal_dt(dt_s, onset_idx, sustain_count, threshold=40.0, tail=0):
    """Vuelta con `dt_s` (Hz explícito) y el pedal en `threshold` durante
    EXACTAMENTE `sustain_count` muestras desde `onset_idx` -- control por
    ÍNDICE (no por distancia) para probar el límite exacto de la ventana de
    sostenimiento (`throttle_on_window_s`) ya calibrada por tasa de muestreo
    real, no por conteo de muestras fijo.
    """
    lap = make_lap(
        dt_s=dt_s,
        length_m=900.0,
        valleys=[{"center": 310.0, "vmin": 80.0, "half_width": 250.0, "direction": "right"}],
        channels=("throttle", "brake"),
    )
    dist = lap.channels["dist"]
    n = len(dist)
    throttle = [0.0] * n
    brake = [90.0 if 150.0 <= d <= 270.0 else 0.0 for d in dist]
    end = min(onset_idx + sustain_count, n)
    for i in range(onset_idx, end):
        throttle[i] = threshold
    for i in range(end, min(end + tail, n)):
        throttle[i] = 0.0
    lap.channels["throttle"] = throttle
    lap.channels["brake"] = brake
    return lap


def test_throttle_on_window_matches_historical_15_samples_at_50hz():
    # Invariante no negociable: a 50Hz (dt=0.02s) la ventana calibrada por
    # tiempo (0.3s) debe dar exactamente 15 muestras, igual que el hardcode
    # historico -- 14 muestras sostenidas NO alcanzan, 15 SI.
    lap_14 = _lap_with_sustained_pedal_dt(dt_s=0.02, onset_idx=580, sustain_count=14)
    lap_15 = _lap_with_sustained_pedal_dt(dt_s=0.02, onset_idx=580, sustain_count=15)

    ms_14 = extract_milestones(lap_14)[0]["milestones"]
    ms_15 = extract_milestones(lap_15)[0]["milestones"]

    assert "throttle_on" not in ms_14
    assert ms_15["throttle_on"]["d"] == 392


def test_full_throttle_window_matches_historical_15_samples_at_50hz():
    # Mismo invariante que arriba, pero para full_throttle -- que hasta este
    # fix tenia su PROPIO hardcode de 15 independiente de throttle_on_window.
    lap_14 = _lap_with_sustained_pedal_dt(
        dt_s=0.02, onset_idx=580, sustain_count=14, threshold=100.0, tail=60
    )
    lap_15 = _lap_with_sustained_pedal_dt(
        dt_s=0.02, onset_idx=580, sustain_count=15, threshold=100.0, tail=60
    )

    ms_14 = extract_milestones(lap_14)[0]["milestones"]
    ms_15 = extract_milestones(lap_15)[0]["milestones"]

    assert "full_throttle" not in ms_14
    assert ms_15["full_throttle"]["d"] == 392


def test_throttle_on_window_calibrates_to_sample_rate_at_20hz():
    # A 20Hz (dt=0.05s) la misma ventana de 0.3s exige 6 muestras (no 15):
    # el bug de fondo era exigir 0.75s de sostenimiento a esta tasa en vez de
    # los 0.3s reales. 5 muestras NO alcanzan, 6 SI.
    lap_5 = _lap_with_sustained_pedal_dt(dt_s=0.05, onset_idx=232, sustain_count=5)
    lap_6 = _lap_with_sustained_pedal_dt(dt_s=0.05, onset_idx=232, sustain_count=6)

    ms_5 = extract_milestones(lap_5)[0]["milestones"]
    ms_6 = extract_milestones(lap_6)[0]["milestones"]

    assert "throttle_on" not in ms_5
    assert ms_6["throttle_on"]["d"] == 393


def test_no_coast_when_gas_overlaps_brake():
    # gas pegado al freno (overlap, dentro de la ventana de busqueda de 0.6s
    # antes del apex): no hay hueco, no hay coast.
    lap = _lap_with_custom_pedals(brake_range=(150.0, 306.0), onset_d=300.0)
    corners = extract_milestones(lap)
    c = corners[0]
    assert c.get("overlap_m", 0) > 0
    assert "coast_start" not in c["milestones"]
    assert "coast_end" not in c["milestones"]


# ── brake_start: fases de frenada y frontera entre curvas vecinas ─────────────


def _lap_brake_blocks(dt_s, blocks, throttle_blocks=None):
    """Vuelta de UNA curva (vmin en ~310 m) con bloques de freno artesanales por
    ÍNDICE, para controlar con precisión el hueco TEMPORAL entre bloques (la
    fusión de fases se decide por tiempo, no por distancia). `blocks` es una
    lista de (i0, i1, peak): brake=peak en los índices [i0, i1).

    `throttle_blocks` (opcional) inyecta gas por ÍNDICE sobre el default (para
    probar la readministración en el hueco que separa dos frenadas, ADR 0033):
    lista de (i0, i1, pct) que sobrescribe throttle=pct en [i0, i1). Sin él, el
    throttle queda como siempre (100 en dist>320, 0 antes)."""
    lap = make_lap(
        dt_s=dt_s,
        length_m=900.0,
        valleys=[{"center": 310.0, "vmin": 80.0, "half_width": 250.0, "direction": "right"}],
        channels=("throttle", "brake"),
    )
    dist = lap.channels["dist"]
    n = len(dist)
    brake = [0.0] * n
    for i0, i1, pk in blocks:
        for i in range(i0, min(i1, n)):
            brake[i] = pk
    lap.channels["brake"] = brake
    throttle = [100.0 if d > 320 else 0.0 for d in dist]
    for i0, i1, pct in throttle_blocks or []:
        for i in range(i0, min(i1, n)):
            throttle[i] = pct
    lap.channels["throttle"] = throttle
    return lap


def test_brake_start_en_la_primera_de_una_doble_pisada_fuerte():
    # dos bloques al 90% separados 0.45 s (< phase_gap 0.5) con el coche aún
    # desacelerando: son la MISMA frenada partida (una suelta breve para rotar).
    # El hito ancla donde EMPIEZA a cargarse el pedal, no en la segunda pisada
    # (que es lo que elegía el antiguo strong[-1]).
    lap = _lap_brake_blocks(0.05, [(100, 120, 90.0), (128, 165, 90.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[100])
    assert ms["brake_start"]["d"] != round(dist[128])


def test_brake_start_ignora_blip_debil_y_lejano_previo():
    # un blip débil (30%) y lejano (>0.5 s antes) NO adelanta el hito: queda en su
    # propia fase, con pico menor que la frenada real; gana la fase de pico máximo.
    # Preserva la intención original de strong[-1] (un roce previo no cuenta).
    lap = _lap_brake_blocks(0.05, [(60, 68, 30.0), (130, 165, 90.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[130])
    assert ms["brake_start"]["d"] != round(dist[60])


def test_brake_start_frenada_simple_de_un_bloque_no_regresa():
    # no-regresión: una frenada continua de un solo bloque ancla en su inicio.
    lap = _lap_brake_blocks(0.05, [(110, 165, 90.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[110])


def test_brake_start_no_lo_trunca_el_segmento_tras_un_kink():
    # kink (apex ~400, sin frenada) seguido de curva con frenada (apex ~700) cuya
    # frenada REAL empieza en 520, ANTES del punto medio entre ápices (550). El
    # hito debe caer en la frenada real (~520), no pegado al borde del segmento
    # (550). Sin el fix, brake_start = 550 y este test falla. El kink no absorbe
    # la frenada de la curva siguiente (cae tras su ápice) y viceversa.
    valleys = [
        {"center": 400.0, "vmin": 178.0, "half_width": 70.0, "direction": "left"},
        {"center": 700.0, "vmin": 80.0, "half_width": 150.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1100.0, base_speed=180.0, valleys=valleys)
    dist = lap.channels["dist"]
    lap.channels["brake"] = [90.0 if 520.0 <= d <= 700.0 else 0.0 for d in dist]
    lap.channels["throttle"] = [0.0 if 500.0 <= d <= 700.0 else 100.0 for d in dist]
    corners = extract_milestones(lap)
    kink = next(c for c in corners if c["kind"] == "kink")
    braking = next(c for c in corners if c["kind"] == "vmin")
    assert kink["no_brake"] is True
    assert braking["segment_m"][0] == 550
    assert 515 <= braking["milestones"]["brake_start"]["d"] <= 525


def test_brake_start_todas_las_fases_debiles_ancla_en_la_tardia():
    # Piso de intensidad: dos fases separadas (> phase_gap), NINGUNA alcanza
    # brake_strong (temprana 35%, tardia 20%). El hito debe anclar en la fase
    # TARDIA (recencia: la que entra al apex), como hacia strong[-1] con los
    # bloques viejos. HEAD elige la de pico maximo (la temprana, 35%) y adelanta
    # el cue ~metros a un roce debil; este test lo atrapa.
    lap = _lap_brake_blocks(0.05, [(60, 80, 35.0), (140, 165, 20.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[140])
    assert ms["brake_start"]["d"] != round(dist[60])


def test_brake_start_desempate_de_picos_iguales_gana_la_fase_mas_tardia():
    # Dos fases FUERTES (pico 90%) separadas por el gap y con pico identico:
    # gana la mas tardia (la que entra al apex). Regla documentada en
    # formato-datos.md que ningun test cubria. (No discrimina contra HEAD: HEAD
    # ya rompia el empate hacia la fase mas tardia; es blindaje de la regla.)
    lap = _lap_brake_blocks(0.05, [(60, 80, 90.0), (140, 165, 90.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[140])
    assert ms["brake_start"]["d"] != round(dist[60])


def test_brake_start_dos_fases_fuertes_gana_la_temprana_de_pico_mayor():
    # Dos fases FUERTES separadas (> phase_gap), la TEMPRANA con pico mayor
    # (100%) que la tardia (90%). brake_start debe anclar en la TEMPRANA: el cue
    # marca donde empezar a cargar el pedal hacia el maximo freno, y ese maximo
    # esta en la primera pisada. Es la regresion de C05 sobre la vuelta real de
    # Nordschleife (100% en d~1042, 90% en d~1117) capturada como test unitario.
    # HEAD (534fdae, "ultima fase fuerte") elige la tardia y llega tarde; el fix
    # ("fase de pico maximo") elige la temprana.
    lap = _lap_brake_blocks(0.05, [(60, 90, 100.0), (140, 165, 90.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[60])
    assert ms["brake_start"]["d"] != round(dist[140])


def test_brake_release_cae_despues_de_una_reaplicacion_suave():
    # Fase A fuerte (pico 60%) -> release -> fase B suave (pico 20%) separada
    # por el gap. brake_release debe caer DESPUES de B (el piloto solto el freno
    # de verdad al final de la ultima aplicacion), no en el hueco entre A y B.
    # HEAD ancla el release al final de la fase GANADORA (A, la de pico maximo)
    # y lo marca en el hueco, borrando B del analisis.
    lap = _lap_brake_blocks(0.05, [(60, 90, 60.0), (130, 150, 20.0)])
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert "brake_release" in ms
    assert ms["brake_release"]["d"] > round(dist[149])


def test_brake_starts_dos_frenadas_con_gas_en_hueco():
    # ADR 0033 (C05): dos bloques FUERTES separados, con el coche re-acelerando
    # (~26%) en el hueco -> son DOS frenadas reales que deben sonar. El escalar
    # `brake_start` sigue anclado en la PRIMERA (pico máximo 100%), no salta a la
    # tardía; `brake_starts` lista AMBAS cronológicamente.
    lap = _lap_brake_blocks(
        0.05,
        [(60, 90, 100.0), (140, 165, 90.0)],
        throttle_blocks=[(95, 135, 26.0)],
    )
    dist = lap.channels["dist"]
    ms = extract_milestones(lap)[0]["milestones"]
    assert ms["brake_start"]["d"] == round(dist[60])
    assert "brake_starts" in ms
    assert len(ms["brake_starts"]) == 2
    assert ms["brake_starts"][0]["d"] == round(dist[60])
    assert ms["brake_starts"][1]["d"] == round(dist[140])
    assert ms["brake_starts"][0]["brake_pct"] == 100
    assert ms["brake_starts"][1]["brake_pct"] == 90


def test_brake_starts_ausente_si_suelta_sin_gas():
    # Mismos dos bloques que arriba pero con throttle ~0 en el hueco (el piloto
    # suelta el freno sin volver a acelerar): se funden en UNA frenada -> NO se
    # publica `brake_starts` (el escalar sigue igual).
    lap = _lap_brake_blocks(0.05, [(60, 90, 100.0), (140, 165, 90.0)])
    ms = extract_milestones(lap)[0]["milestones"]
    assert "brake_start" in ms
    assert "brake_starts" not in ms


def test_brake_starts_ausente_en_trail_braking():
    # Un solo bloque MODULADO (freno baja de 90% a 30% pero nunca < brake_on=10),
    # con gas simultáneo en el tramo suave: es UN solo bloque, la fusión ni se
    # evalúa -> 1 frenada, sin `brake_starts`. El arrastre continuo no se parte.
    lap = _lap_brake_blocks(
        0.05,
        [(60, 100, 90.0), (100, 150, 30.0)],
        throttle_blocks=[(100, 150, 26.0)],
    )
    ms = extract_milestones(lap)[0]["milestones"]
    assert "brake_start" in ms
    assert "brake_starts" not in ms


def _lap_encadenada_mismo_sentido():
    """Dos curvas del MISMO sentido (derecha) con volante residual alto a la
    salida de la primera que entra a `pre` de la segunda por encima del umbral,
    una breve enderezada y el giro real hacia la segunda. Freno de la segunda
    arranca antes del punto medio del segmento (brake_start precede a `pre`)."""
    valleys = [
        {"center": 300.0, "vmin": 90.0, "half_width": 120.0, "direction": "right"},
        {"center": 900.0, "vmin": 80.0, "half_width": 120.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1300.0, base_speed=180.0, valleys=valleys)
    dist = lap.channels["dist"]
    steering, brake, throttle = [], [], []
    for d in dist:
        if d < 300:
            st = 20.0
        elif d < 620:
            st = 15.0  # residual > turn_in_deg al entrar a `pre` (lo = 600)
        elif d < 700:
            st = 0.0  # enderezada breve entre las dos curvas
        elif d <= 900:
            st = 25.0 * (d - 700) / 200.0  # giro real: cruza 8 grados en ~764 m
        else:
            st = 25.0 * max(0.0, (1100 - d) / 200.0)
        b = 90.0 if 500.0 <= d <= 890.0 else 0.0
        steering.append(st)
        brake.append(b)
        throttle.append(0.0 if b > 0 else 100.0)
    lap.channels["steering"] = steering
    lap.channels["brake"] = brake
    lap.channels["throttle"] = throttle
    return lap


def test_turn_in_no_se_adelanta_con_volante_residual_encadenado():
    # El volante residual de la salida de C1 entra a `pre` de C2 ya por encima
    # de turn_in_deg. Con brake_start anclando antes de `pre`, HEAD aceptaba la
    # PRIMERA muestra de `pre` como turn_in (~600 m, cientos de metros antes).
    # Exigir CRUCE ASCENDENTE del umbral lo evita: el residual no cruza.
    lap = _lap_encadenada_mismo_sentido()
    corners = extract_milestones(lap)
    ms = corners[1]["milestones"]
    assert ms["brake_start"]["d"] < 600  # frena antes del punto medio del segmento
    assert "turn_in" in ms
    assert ms["turn_in"]["d"] > 700  # el giro real, no el volante residual (~600)


def test_turn_in_recupera_cruce_entre_brake_start_y_segment_m0():
    # Curva tras un kink: la frenada arranca en ~520, ANTES del punto medio del
    # segmento (seg0 = 550). El volante cruza 8 grados (ascendente) en ~532, en
    # la tierra de nadie entre brake_start (~520) y seg0 (550). HEAD (534fdae)
    # busca turn_in solo dentro de `pre` (dist >= seg0) y pierde ese cruce -- es
    # la perdida de C14. El fix busca desde brake_start (t0) y lo recupera.
    valleys = [
        {"center": 400.0, "vmin": 178.0, "half_width": 70.0, "direction": "left"},
        {"center": 700.0, "vmin": 80.0, "half_width": 150.0, "direction": "right"},
    ]
    lap = make_lap(length_m=1100.0, base_speed=180.0, valleys=valleys)
    dist = lap.channels["dist"]
    lap.channels["brake"] = [90.0 if 520.0 <= d <= 700.0 else 0.0 for d in dist]
    lap.channels["throttle"] = [0.0 if 500.0 <= d <= 700.0 else 100.0 for d in dist]
    # volante a la derecha (positivo) que cruza 8 grados ascendente en ~532 y
    # sigue subiendo hasta el apex (nunca vuelve a bajar del umbral).
    lap.channels["steering"] = [min(25.0, 0.8 * (d - 522.0)) if d >= 522.0 else 0.0 for d in dist]
    braking = next(c for c in extract_milestones(lap) if c["kind"] == "vmin")
    ms = braking["milestones"]
    assert braking["segment_m"][0] == 550
    assert ms["brake_start"]["d"] < 550
    assert "turn_in" in ms
    assert 525 <= ms["turn_in"]["d"] < 550


def test_turn_in_normal_con_volante_en_cero_se_detecta():
    # No-regresion: con el volante en cero antes de girar, el cruce ascendente
    # normal detecta el turn_in (el nuevo filtro no rompe el caso comun).
    lap = make_lap(
        length_m=900.0,
        valleys=[{"center": 400.0, "vmin": 80.0, "half_width": 150.0, "direction": "right"}],
    )
    ms = extract_milestones(lap)[0]["milestones"]
    assert "turn_in" in ms
    assert ms["turn_in"]["d"] < ms["apex"]["d"]


# ── detect_gear_shifts: cambio de marcha lap-wide (cue "gear", solo subtitulo) ─


def _gear_lap(gear_sequence, dt=0.05, step_m=10.0):
    """Lap sintetico con time/dist/gear controlados muestra a muestra -- para
    scriptar blips exactos, make_lap() no sirve (deriva `gear` de la forma del
    valle de velocidad, sin control por muestra)."""
    n = len(gear_sequence)
    lap = Lap()
    lap.channels = {
        "time": [i * dt for i in range(n)],
        "dist": [i * step_m for i in range(n)],
        "gear": [float(g) for g in gear_sequence],
    }
    return lap


def test_detect_gear_shifts_ignora_blip_de_una_muestra():
    """Dos cambios reales (3->4, 4->5) sostenidos, mas un blip de 1 muestra
    (3->4->3) que el debounce de min_hold_s debe ignorar por completo -- no
    debe aparecer como un cambio ni desplazar la marcha "actual" que se
    compara contra el siguiente cambio real."""
    # indice 3: blip de 1 muestra (3->4->3); indice 8: cambio real 3->4
    # sostenido; indice 12: cambio real 4->5 sostenido. Un par de muestras de
    # cola extra en el ultimo grupo evitan que la confirmacion dependa de un
    # empate flotante exacto contra hold_until (time[i] acumula error de
    # redondeo con dt=0.05).
    gear_sequence = [3, 3, 3, 4, 3, 3, 3, 3] + [4, 4, 4, 4] + [5, 5, 5, 5, 5, 5]
    lap = _gear_lap(gear_sequence)

    shifts = detect_gear_shifts(lap, min_hold_s=0.15)

    assert shifts == [
        {"distance": 80, "gear_from": 3, "gear_to": 4},
        {"distance": 120, "gear_from": 4, "gear_to": 5},
    ]


def test_detect_gear_shifts_debounce_filtra_blip_con_muestreo_lento():
    """Regresion: con dt de muestreo >= min_hold_s, el bucle de verificacion
    viejo arrancaba en j=i (comparandose contra si mismo, siempre True) y la
    condicion `time[j] < hold_until` nunca volvia a cumplirse -- CUALQUIER
    blip de 1 muestra se aceptaba como cambio real. Con dt=0.2s (> 0.15s de
    min_hold_s) un blip 3->4->3 debe seguir descartandose: la muestra
    siguiente (revierte a 3) SI debe consultarse."""
    gear_sequence = [3, 3, 4, 3, 3, 3]
    lap = _gear_lap(gear_sequence, dt=0.2)

    shifts = detect_gear_shifts(lap, min_hold_s=0.15)

    assert shifts == []


def test_detect_gear_shifts_cambio_real_con_muestreo_lento_si_se_detecta():
    """Sanity del fix: un cambio REAL y sostenido tambien se detecta con
    dt >= min_hold_s -- el fix no rechaza todo por sistema, solo exige que la
    muestra siguiente confirme (no contradiga) la marcha nueva."""
    gear_sequence = [3, 3, 4, 4, 4, 4]
    lap = _gear_lap(gear_sequence, dt=0.2)

    shifts = detect_gear_shifts(lap, min_hold_s=0.15)

    assert shifts == [{"distance": 20, "gear_from": 3, "gear_to": 4}]


def test_detect_gear_shifts_sin_canal_gear_no_crashea():
    """Una vuelta sin canal 'gear' (export sin ese canal) devuelve lista
    vacia, no un KeyError."""
    lap = make_lap(channels=("throttle", "brake"))
    assert detect_gear_shifts(lap) == []
