"""Deteccion de curvas e hitos sobre una vuelta.

Metodologia (validada contra telemetria real del Nordschleife):
- Una curva es un evento: frenada -> turn-in -> release -> apex (V-Min) -> gas -> gas 100%.
- Se detectan dos tipos: 'vmin' (minimo local de velocidad con prominencia) y
  'kink' (pico de G lateral sostenido sin caida de velocidad).
- Los hitos de cada curva se extraen SOLO dentro de su segmento (punto medio con
  las curvas vecinas) para no contaminarse con la frenada de la curva siguiente.
- EXCEPCION (frenada): la deteccion de frenada usa una ventana propia, mas ancha,
  que arranca justo despues del apice de la curva PREVIA (no en el punto medio
  entre apices). El punto medio caia dentro de la zona de frenado cuando la curva
  anterior es un kink sin frenada, y truncaba el inicio real de la frenada de esta
  curva. Regla de propiedad: cada curva es DUENA de toda fase de frenada posterior
  al apice de su vecina previa; nada antes de ese apice se le atribuye (no se roba
  la frenada de la anterior), y un kink sin frenada nunca absorbe la frenada de la
  curva siguiente (esa frenada cae despues del apice del kink, no antes).
- Los bloques de freno se agrupan en FASES: bloques consecutivos separados por
  menos de `phase_gap_s` y con el coche aun desacelerando en el hueco se funden
  (una suelta breve para rotar, no una accion distinta). El piso de intensidad
  `brake_strong` es un FILTRO: descarta las fases que no lo alcanzan (el freno
  de verdad, el que evita pasarse de curva). Entre las fases que sobreviven al
  filtro, el inicio ancla en la PRIMERA muestra de la de PICO MAXIMO -- el cue
  marca donde empezar a cargar el pedal hacia el maximo freno aprovechando la
  transferencia de peso; ante empate de pico, la mas tardia (la que entra al
  apex). Si ninguna fase alcanza el piso, la ultima fase cronologica. Un blip
  de trail-braking debil y previo queda en su propia fase, por debajo del piso,
  y no adelanta el hito.
- El gas real (`throttle_on`) exige throttle sostenido, igual que `full_throttle`;
  un roce fugaz de pedal no cuenta como inicio de aceleracion.
- Entre el fin de la frenada (o el lift) y el gas sostenido puede existir un
  tramo de coast (freno y gas ambos por debajo de su umbral): se marca con
  `coast_start`/`coast_end` cuando existe hueco (si el gas se solapa con el
  freno, no hay coast).
"""

# Umbrales de frenada, fuente unica compartida por `extract_milestones` (mide la
# referencia) y `compare._corner_metrics` (mide al piloto). Estan aqui, en un solo
# sitio, para que ambos lados se midan con la MISMA vara: si un lado usara otros
# valores, `d_brake_m` saldria asimetrico (ver ADR 0031). `BRAKE_LOOKBACK_M` es el
# tope de look-back de la ventana de frenada (y de la propiedad por apice previo).
BRAKE_ON = 10
BRAKE_STRONG = 50
PHASE_GAP_S = 0.5
BRAKE_LOOKBACK_M = 450


def samples(lap):
    keys = [
        k
        for k in (
            "time",
            "dist",
            "speed",
            "throttle",
            "brake",
            "steering",
            "gear",
            "glat",
            "glong",
            "rpm",
            "alt",
        )
        if lap.has(k)
    ]
    n = len(lap)
    return [{k: lap.col(k)[i] for k in keys} for i in range(n)], keys


def _window_samples(dt, seconds, floor=3):
    """Convierte una ventana de tiempo (segundos) a conteo de muestras usando
    el `dt` real de la vuelta -- nunca asume una tasa de muestreo fija (p.ej.
    50Hz). `floor` evita ventanas degeneradas en vueltas con pocas muestras o
    con `dt` invalido (<=0: timestamps duplicados o fuera de orden)."""
    if dt <= 0:
        return floor
    return max(floor, int(round(seconds / dt)))


def detect_corners(lap, vmin_window_s=1.2, vmin_prominence_kmh=3.0, kink_glat=2.2):
    """Devuelve lista de eventos: [{'kind': 'vmin'|'kink', 'i': indice}] ordenada por distancia."""
    data, keys = samples(lap)
    if "speed" not in keys:
        raise ValueError("La vuelta no tiene canal de velocidad")
    if "dist" not in keys:
        raise ValueError(
            "La vuelta no tiene canal de distancia. En MoTeC i2 re-exporta el CSV "
            "incluyendo el canal 'Distance': es el eje maestro de comparacion del que "
            "dependen detect, compare y overlay."
        )
    # frecuencia de muestreo aproximada
    dt = (data[-1]["time"] - data[0]["time"]) / max(1, len(data) - 1)
    W = _window_samples(dt, vmin_window_s)
    events = []
    i = W
    while i < len(data) - W:
        v = data[i]["speed"]
        win = data[i - W : i + W + 1]
        if (
            v == min(s["speed"] for s in win)
            and data[i - W]["speed"] > v + vmin_prominence_kmh
            and data[i + W]["speed"] > v + vmin_prominence_kmh
        ):
            events.append(("vmin", i))
            i += W
        else:
            i += 1
    if "glat" in keys:
        Wk = _window_samples(dt, 0.5)
        i = Wk
        while i < len(data) - Wk:
            g = abs(data[i]["glat"])
            if g > kink_glat and g == max(abs(s["glat"]) for s in data[i - Wk : i + Wk + 1]):
                d = data[i]["dist"]
                if not any(abs(data[j]["dist"] - d) < 80 for _, j in events):
                    events.append(("kink", i))
                i += Wk * 2
            else:
                i += 1
    events.sort(key=lambda e: data[e[1]]["dist"])
    return events, data


def select_brake_phase(
    lap_samples, window_m, brake_on=BRAKE_ON, brake_strong=BRAKE_STRONG, phase_gap_s=PHASE_GAP_S
):
    """Elige la fase de frenada dentro de una ventana de busqueda.

    Helper COMPARTIDO por `extract_milestones` (mide la referencia) y
    `compare._corner_metrics` (mide al piloto). Vive aqui, en un solo sitio, a
    proposito: cuando cada lado tenia su propia copia del algoritmo y su propia
    ventana, `d_brake_m` salia asimetrico y levantaba banderas `"frenada"`
    espurias incluso comparando una vuelta contra si misma. Con este helper
    ambos lados se miden con la MISMA vara.

    `window_m` = [lo, hi]: se consideran las muestras con `lo < dist <= hi`
    (misma semantica excl-incl que la ventana de frenada ampliada
    `brake_lo < dist <= apex`). Los puntos con `brake` > `brake_on` se agrupan
    en bloques (hueco temporal intra-bloque < 0.3 s) y los bloques consecutivos
    se funden en FASES cuando el hueco es < `phase_gap_s` y el coche sigue
    desacelerando en el hueco (una suelta breve para rotar). El piso
    `brake_strong` FILTRA las fases; entre las que quedan gana la de PICO
    MAXIMO (desempate a la mas tardia); si ninguna alcanza el piso, la ultima
    fase cronologica.

    Devuelve `(chosen, phases)`: `chosen` es la fase elegida (lista de muestras)
    o `None` si no hubo frenada; `phases` es la lista completa de fases -- la
    necesita `brake_release`, que se ancla tras la ULTIMA fase cronologica.
    """
    lo, hi = window_m
    win = [s for s in lap_samples if lo < s["dist"] <= hi]
    blocks, cur = [], None
    for s in win:
        if s.get("brake", 0) > brake_on:
            if cur and s["time"] - cur[-1]["time"] < 0.3:
                cur.append(s)
            else:
                cur = [s]
                blocks.append(cur)
    if not blocks:
        return None, []
    phases = [list(blocks[0])]
    for b in blocks[1:]:
        prev_last = phases[-1][-1]
        gap_s = b[0]["time"] - prev_last["time"]
        still_braking = b[0]["speed"] <= prev_last["speed"] + 2.0
        if gap_s < phase_gap_s and still_braking:
            phases[-1].extend(b)
        else:
            phases.append(list(b))
    peaks = [max(s["brake"] for s in ph) for ph in phases]
    strong = [i for i, pk in enumerate(peaks) if pk >= brake_strong]
    if strong:
        top = max(peaks[i] for i in strong)
        chosen = phases[max(i for i in strong if peaks[i] == top)]
    else:
        chosen = phases[-1]
    return chosen, phases


def extract_milestones(
    lap,
    events=None,
    brake_on=BRAKE_ON,
    brake_strong=BRAKE_STRONG,
    throttle_on=5,
    full_throttle=98,
    turn_in_deg=8,
    throttle_on_window_s=0.3,
    phase_gap_s=PHASE_GAP_S,
):
    """Extrae los hitos de cada curva, con segmentacion por curva. Devuelve
    lista de dicts estilo corners.json.

    Frenada (`brake_start`): los puntos con `brake` > `brake_on` se agrupan en
    bloques y los bloques se funden en FASES cuando el hueco temporal entre
    ellos es menor que `phase_gap_s` y el coche sigue desacelerando (una suelta
    breve para rotar). El piso `brake_strong` FILTRA las fases (solo cuentan las
    que lo alcanzan); entre las que quedan, `brake_start` ancla en la primera
    muestra de la de PICO MAXIMO -- el cue marca donde empezar a cargar el pedal
    hacia el maximo freno. Ante empate de pico gana la mas tardia; si ninguna
    fase alcanza el piso, la ultima fase cronologica. `brake_release` se ancla
    al final de la ULTIMA fase cronologica (no la ganadora), para que una
    reaplicacion suave de freno posterior a la fase fuerte no lo adelante al
    hueco intermedio; como consecuencia fisica esperada del trail-braking, el
    release puede caer pasado el apex (siempre dentro del segmento).

    Turn-in (`turn_in`): primer CRUCE ASCENDENTE del umbral `turn_in_deg` sobre
    las muestras de `data` con `time >= t0` (t0 = `brake_start`, o el inicio de
    `pre` si la curva no frena) y `dist <= ad` (el apex). La ventana arranca en
    la frenada, no en `segment_m[0]`: si la frenada precede al segmento (curva
    tras un kink), el turn-in que la sigue tambien puede caer antes de
    `segment_m[0]`, y acotarlo al segmento lo perderia. Ampliar la ventana hacia
    atras no reabre la puerta al volante residual de la curva previa del mismo
    sentido: ese volante entra ya POR ENCIMA del umbral y solo DECRECE, no
    produce cruce ascendente.

    Invariante de `segment_m`: `brake_start` PUEDE preceder a `segment_m[0]`
    cuando la curva anterior es un kink sin frenada (la ventana de frenada
    arranca tras el apex previo, mas atras que el punto medio del segmento). Los
    consumidores de `segment_m` NO deben asumir que los hitos caen dentro del
    segmento.
    """
    if events is None:
        events, data = detect_corners(lap)
    else:
        data, _ = samples(lap)
    # dt real de la vuelta (no asume 50Hz): misma formula que detect_corners,
    # recalculada aqui porque este metodo puede recibir `events` ya calculados
    # sin haber pasado por detect_corners (y por tanto sin su `dt` local).
    dt = (data[-1]["time"] - data[0]["time"]) / max(1, len(data) - 1)
    throttle_on_window = _window_samples(dt, throttle_on_window_s)
    apex_ds = [data[i]["dist"] for _, i in events]
    corners = []
    # Apice PUBLICADO (V-Min redondeado) del ultimo corner que se ANEXO: es la
    # misma ancla del borde bajo de la ventana de frenada que `compare` encadena
    # en `prev_apex_d`. Ver la nota extensa junto al calculo de `brake_window`.
    prev_pub_apex = None
    for n, (kind, ai) in enumerate(events):
        ad = data[ai]["dist"]
        lo = (apex_ds[n - 1] + ad) / 2 if n > 0 else ad - 450
        hi = (ad + apex_ds[n + 1]) / 2 if n < len(events) - 1 else ad + 350
        lo, hi = max(lo, ad - 450), min(hi, ad + 350)
        seg = [s for s in data if lo <= s["dist"] <= hi]
        pre = [s for s in seg if s["dist"] <= ad]
        post = [s for s in seg if s["dist"] > ad]
        if not pre or len(seg) < 5:
            continue
        ap = min(pre[-20:] + post[:20], key=lambda s: s["speed"])
        ms = {}
        # --- deteccion de frenada (ventana propia, ver docstring) --------
        # Ventana de frenada mas ancha que el segmento: desde justo despues del
        # apice de la curva previa hasta este apice. Asi no se trunca el inicio
        # real de la frenada cuando la curva anterior es un kink sin frenada
        # (su punto medio caia en mitad de la zona de frenado). `ad - 450` es el
        # mismo tope de look-back que `lo`; la frontera de propiedad es el apice
        # previo (no se roba la frenada de la vecina anterior).
        # Auto-consistencia (ADR 0031, Opcion A): la ventana de frenada se deriva
        # del apice PUBLICADO (el V-Min `ap`, no el apice de EVENTO `ad`) y del
        # apice publicado del corner previo ANEXADO -- exactamente las anclas que
        # `compare._corner_metrics` reconstruye a partir del contexto publicado.
        # Antes esta ventana usaba el apice de EVENTO (`ad` y `apex_ds[n-1]`),
        # mientras se PUBLICABA el V-Min como apice: cuando el corner previo es un
        # kink cuyo V-Min retrasa al pico de glat, ambas anclas divergian y una
        # misma frenada continua se atribuia empezando en metros distintos entre
        # referencia y piloto (d_brake_m espurio comparando una vuelta contra si
        # misma). Al derivar de lo PUBLICADO, productor y consumidor usan la misma
        # ancla por construccion.
        apex_pub_d = round(ap["dist"])
        brake_lo = (
            max(prev_pub_apex, apex_pub_d - BRAKE_LOOKBACK_M)
            if prev_pub_apex is not None
            else apex_pub_d - BRAKE_LOOKBACK_M
        )
        # Ventana de frenada INTERNA: NO se publica en el dict de la curva. El
        # ADR 0031 descarta la Opcion C (exponer `brake_window_m`) y adopta la
        # Opcion A. Se redondea a enteros antes de filtrar, de modo que referencia
        # y piloto usen limites byte-identicos: esa es la condicion para que
        # d_brake_m == 0 cuando son la misma vuelta.
        brake_window = [round(brake_lo), round(apex_pub_d)]
        # El corner ya no puede saltarse (el unico `continue` quedo arriba), asi
        # que este apice publicado sera el `prev_pub_apex` del siguiente anexado.
        prev_pub_apex = apex_pub_d
        phase, phases = select_brake_phase(data, brake_window, brake_on, brake_strong, phase_gap_s)
        no_brake = phase is None
        overlap = None
        if phase is not None:
            bs = phase[0]
            bmax = max(phase, key=lambda s: s["brake"])
            ms["brake_start"] = _pt(bs, brake_pct=round(bmax["brake"]))
            # brake_release: cuando el piloto solto el freno de verdad, tras la
            # ULTIMA fase cronologica (no la ganadora). Si tras la fase fuerte
            # hay una reaplicacion mas suave, el release cae despues de ella y no
            # en el hueco intermedio. Se busca sobre `data` (no `seg`) acotado
            # por `hi`, para no depender de donde arranca el segmento.
            last_end_t = phases[-1][-1]["time"]
            rel = next(
                (
                    s
                    for s in data
                    if s["time"] > last_end_t - 0.02 and s["dist"] <= hi and s.get("brake", 0) < 2
                ),
                None,
            )
            if rel:
                ms["brake_release"] = _pt(rel)
        elif pre and "throttle" in pre[0]:
            lift = min(pre, key=lambda s: s["throttle"])
            if lift["throttle"] < 80:
                ms["lift"] = _pt(lift, throttle_pct=round(lift["throttle"]))
        # turn-in: exige CRUCE ASCENDENTE del umbral (muestra previa
        # <= turn_in_deg, actual >). El volante residual de la curva anterior
        # del mismo sentido entra ya por encima del umbral y solo decrece, asi
        # que NO produce cruce y no dispara un turn-in espurio cientos de metros
        # antes. Se busca sobre `data` desde t0 (brake_start, o el inicio de
        # `pre` si no hay frenada) hasta el apex: cuando la frenada precede al
        # segmento (curva tras un kink), el turn-in tambien puede caer antes de
        # `segment_m[0]`, y acotarlo a `pre` lo perderia.
        if "steering" in ap:
            sign = 1 if ap["steering"] > 0 else -1
            t0 = ms["brake_start"]["t"] if "brake_start" in ms else pre[0]["time"]
            scan = [s for s in data if s["time"] >= t0 and s["dist"] <= ad]
            ti = None
            for k in range(1, len(scan)):
                if (
                    scan[k - 1]["steering"] * sign <= turn_in_deg
                    and scan[k]["steering"] * sign > turn_in_deg
                ):
                    ti = scan[k]
                    break
            if ti and ti["time"] < ap["time"]:
                ms["turn_in"] = _pt(ti)
        # gas: ancla en el throttle SOSTENIDO, no en el primer cruce del umbral
        # (mismo criterio que full_throttle: umbral + N muestras seguidas). Un
        # roce fugaz de pedal (freno-motor, ruido) cruza el umbral un instante
        # pero no se sostiene y no debe ganar el hito. throttle_on_window_s=0.3
        # (convertido a muestras via dt real, no asume 50Hz) es la misma
        # ventana que reusa full_throttle -- coherente con el gap de 0.3s que
        # funde bloques de frenada en este mismo modulo.
        g0 = None
        for j, s in enumerate(seg):
            if s["time"] < ap["time"] - 0.6 or s.get("throttle", 0) <= throttle_on:
                continue
            window = seg[j : j + throttle_on_window]
            if len(window) == throttle_on_window and all(
                x.get("throttle", 0) > throttle_on for x in window
            ):
                g0 = s
                break
        if g0:
            ms["throttle_on"] = _pt(g0, throttle_pct=round(g0["throttle"]))
            if "brake_release" in ms and g0["dist"] < ms["brake_release"]["d"]:
                overlap = round(ms["brake_release"]["d"] - g0["dist"])
            # coast: freno y gas ambos por debajo de su umbral, entre el fin de
            # la frenada (o el lift, en curvas sin freno) y el gas sostenido. Si
            # el gas se solapa con el freno (overlap) no hay hueco y no se
            # emite coast.
            end_ref = ms.get("brake_release") or ms.get("lift")
            if end_ref and end_ref["t"] < g0["time"]:
                coast = [
                    s
                    for s in seg
                    if end_ref["t"] < s["time"] < g0["time"]
                    and s.get("brake", 0) < brake_on
                    and s.get("throttle", 0) < throttle_on
                ]
                if coast:
                    ms["coast_start"] = _pt(coast[0])
                    ms["coast_end"] = _pt(coast[-1])
        ms["apex"] = _pt(ap, g_lat=ap.get("glat"))
        g100 = None
        for j, s in enumerate(post):
            if s.get("throttle", 0) >= full_throttle and all(
                x.get("throttle", 0) >= 90 for x in post[j : j + throttle_on_window]
            ):
                g100 = s
                break
        if g100:
            ms["full_throttle"] = _pt(g100)
        near = [s for s in seg if ap["time"] - 2.0 <= s["time"] <= ap["time"] + 1.5]
        c = {
            "id": "C%02d" % (n + 1),
            "kind": kind,
            "milestones": ms,
            "no_brake": no_brake,
            "segment_m": [round(lo), round(hi)],
            "delta_s": round(seg[-1]["time"] - seg[0]["time"], 2),
        }
        if "steering" in ap and near:
            mx = max(near, key=lambda s: abs(s.get("steering", 0)))
            c["max_steering_deg"] = round(abs(mx["steering"]), 1)
            # direccion: volante en el apex; si es ambiguo (<5 deg), ventana corta +-0.5s
            if abs(ap["steering"]) >= 5:
                c["direction"] = "left" if ap["steering"] < 0 else "right"
            else:
                close = [s for s in near if abs(s["time"] - ap["time"]) <= 0.5]
                mc = max(close, key=lambda s: abs(s.get("steering", 0))) if close else mx
                c["direction"] = "left" if mc["steering"] < 0 else "right"
        if "glat" in ap and near:
            mg = max(near, key=lambda s: abs(s.get("glat", 0)))
            ms["g_lat_max"] = {"d": round(mg["dist"]), "g_lat": mg["glat"]}
        if "alt" in ap and seg:
            a0 = min(seg, key=lambda s: abs(s["dist"] - (ad - 100)))["alt"]
            a1 = min(seg, key=lambda s: abs(s["dist"] - (ad + 100)))["alt"]
            pct = (a1 - a0) / 200.0 * 100.0
            c["slope_pct"] = round(pct, 1)
            c["slope"] = "subida" if pct > 1 else ("bajada" if pct < -1 else "plano")
        if overlap and overlap > 0:
            c["overlap_m"] = overlap
        corners.append(c)
    return corners


def detect_gear_shifts(lap, min_hold_s=0.15):
    """Detecta cambios de marcha a lo largo de TODA la vuelta (no por curva).

    Diff entre muestras consecutivas del canal `gear`. Un cambio candidato en
    la muestra i solo se confirma si la marcha nueva se sostiene al menos
    `min_hold_s` antes de volver a cambiar -- descarta blips de una sola
    muestra (ruido de sensor durante el propio cambio de marcha). Un blip
    descartado NO mueve la marcha "actual": el siguiente cambio real se sigue
    comparando contra la marcha previa al ruido.

    Confirmacion: se recorren las muestras SIGUIENTES a la candidata (i+1,
    i+2, ...) -- nunca la propia candidata, que siempre "coincide consigo
    misma" y no prueba nada. Se confirma en cuanto una muestra coincide con
    la marcha nueva Y su tiempo ya alcanzo min_hold_s; se rechaza en cuanto
    una muestra difiere. Si la vuelta se acaba antes de alcanzar min_hold_s
    sin haber visto ninguna muestra que contradiga, el candidato se
    RECHAZA igual (evidencia insuficiente): mejor perder un cambio real
    pegado al final de la vuelta que aceptar un blip sin verificar -- este
    modulo prioriza no generar un cue erroneo. Esto tambien cubre, sin caso
    especial, el muestreo mas lento que min_hold_s (dt >= min_hold_s): la
    primera muestra siguiente decide sola, revierta o confirme.
    """
    if not (lap.has("gear") and lap.has("dist") and lap.has("time")):
        return []
    gear = lap.col("gear")
    dist = lap.col("dist")
    time = lap.col("time")
    n = len(gear)
    shifts = []
    prev_gear = gear[0] if n else None
    i = 1
    while i < n:
        g = gear[i]
        if g == prev_gear:
            i += 1
            continue
        hold_until = time[i] + min_hold_s
        j = i + 1
        held = False
        while j < n:
            if gear[j] != g:
                held = False
                break
            held = time[j] >= hold_until
            if held:
                break
            j += 1
        if held:
            shifts.append(
                {"distance": round(dist[i]), "gear_from": int(prev_gear), "gear_to": int(g)}
            )
            prev_gear = g
        i += 1
    return shifts


def _pt(s, **extra):
    p = {"d": round(s["dist"]), "t": round(s["time"], 2), "v": round(s["speed"])}
    if "gear" in s:
        p["gear"] = int(s["gear"])
    p.update({k: v for k, v in extra.items() if v is not None})
    return p
