"""Genera un pack de Pace Notes para CrewChief desde el analisis de SimGhostInputs."""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from pathlib import Path


def crewchief_pacenotes_dir(track_name: str) -> str:
    """Devuelve el directorio estándar de CrewChief para pace notes de AMS2."""
    return os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "CrewChiefV4",
        "pace_notes",
        "ams2",
        track_name,
    )


DEFAULT_MILESTONES = ["brake", "apex", "gas"]
# Anticipo del countdown en segundos (ADR 0024). Fuente unica: la UI (leyenda
# del Paso 5) y las firmas de este modulo lo leen de aqui — no lo dupliques.
DEFAULT_COUNTDOWN_S = 3.5
# Escala de los tics de AVISO del countdown (fracciones de la frecuencia base).
# El "¡ya!" no esta aqui: es el tono de frenada (DEFAULT_FREQS["brake"]) y suena
# EXACTO en el punto de frenada de la referencia — el PO: "el 3er bip tiene que
# coincidir con el inicio de la frenada, el 3 debe ser el ya" (QA 2026-07-06).
# La leyenda de la UI la deriva de aqui; _render_cue la consume por `step`.
COUNTDOWN_SCALE = (0.75, 0.875)
# Gap minimo global entre cues (metros). Fuente unica: plan_tone_events y la
# expansion del countdown en build_tone_pack lo comparten.
DEFAULT_MIN_GAP_M = 50
DEFAULT_FREQS = {
    "brake_countdown": 880,
    # brake a 1000 Hz, NO 880: el countdown termina su escala en 880 y con la
    # misma frecuencia eran indistinguibles al oido (QA 2026-07-05, ADR 0024).
    "brake": 1000,
    "brake_release": 720,
    "turn_in": 660,
    "apex": 440,
    "throttle_on": 260,
    "gas": 220,
    "gas_100": 180,
    "full_throttle": 180,
    "coast": 340,
}
MILESTONE_ALIASES = {
    "brake": ["brake", "brake_start"],
    "brake_release": ["brake_release", "release"],
    "apex": ["apex"],
    "gas": ["throttle_on", "gas", "full_throttle"],
    "throttle_on": ["throttle_on", "gas"],
    "gas_100": ["gas_100", "full_throttle"],
    "full_throttle": ["full_throttle", "gas_100"],
    "turn_in": ["turn_in"],
}
MILESTONE_LABELS = {
    "brake_countdown": "contador de frenada",
    "brake_tic": "contador de frenada",
    "brake": "punto de frenada",
    "brake_release": "soltar freno",
    "apex": "apex",
    "throttle_on": "inicio de acelerador",
    "gas": "inicio de acelerador",
    "gas_100": "gas completo",
    "full_throttle": "gas completo",
    "turn_in": "turn-in",
    "coast": "inercia",
}
PLAN_CUES = [
    "brake_countdown",
    "brake",
    "brake_release",
    "turn_in",
    "throttle_on",
    "full_throttle",
]
# Catalogo COMPLETO de tipos de cue con su configuracion por defecto (enabled +
# priority). PLAN_CUES arriba sigue siendo la lista que consume la leyenda de
# la UI (Paso 5, WS-4) y NO se toca aqui: enumera solo los tipos que suenan
# HOY por defecto. DEFAULT_CONFIG es el catalogo mas amplio (incluye tipos
# apagados por defecto) que se threadea por el pipeline via cue_config. Con
# DEFAULT_CONFIG el pack es identico al de hoy (no-regresion): mismos tipos
# activos, mismas prioridades que antes vivian hardcodeadas en
# _corner_candidates.
DEFAULT_CONFIG = {
    # Tics de aviso del countdown de frenada (ADR 0024/0026). Su enabled y
    # priority NO estan conectados todavia al mecanismo de tics en
    # plan_tone_events (esta atado al milestone "brake" protegido y no pasa
    # por _corner_candidates); se documenta aqui por catalogo completo.
    # Conectarlo (apagar el countdown por separado) es follow-up.
    "brake_countdown": {"enabled": True, "priority": 100},
    "brake": {"enabled": True, "priority": 80},
    "brake_release": {"enabled": True, "priority": 70},
    "turn_in": {"enabled": True, "priority": 60},
    "throttle_on": {"enabled": True, "priority": 85},
    "full_throttle": {"enabled": True, "priority": 75},
    # Reincorporado al catalogo (ADR 0026 lo apago, no lo borro). Apagado por
    # defecto: no-regresion con el pack de hoy, que no suena en el apex.
    "apex": {"enabled": False, "priority": 90},
    # Coast/inercia (WS-1: milestones coast_start/coast_end en corners.py). Un
    # solo cue en coast_start, no dos: coast_end no marca una accion del
    # piloto, solo el fin del hueco de inercia — un cue de entrada basta para
    # avisar "aqui no hay ni freno ni gas". solo_sin_frenada=True: en curvas
    # CON frenada el freno-turn_in-release ya cubre esa fase; el coast se
    # reserva para curvas sin freno, donde es la unica pista de que hay que
    # soltar el pedal antes de dar gas. Apagado por defecto.
    "coast": {"enabled": False, "priority": 50, "solo_sin_frenada": True},
    # Cambio de marcha: slot reservado, SIN IMPLEMENTAR. TODO: la deteccion de
    # marcha (leer "gear" del milestone, decidir el umbral del cue) es
    # follow-up; no se generan candidatos para este tipo todavia.
    "gear": {"enabled": False, "priority": 65},
}


def generate_tone(freq_hz, duration_s, volume=0.8, sample_rate=24000) -> bytes:
    import numpy as np

    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    fade = min(int(sample_rate * 0.01), len(t) // 2)
    envelope = np.ones(len(t))
    if fade > 0:
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
    samples = (np.sin(2 * np.pi * freq_hz * t) * envelope * volume * 32767).astype(np.int16)
    return _make_wav_bytes(samples, sample_rate=sample_rate)


def _make_wav_bytes(samples_int16, sample_rate=24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples_int16.tobytes())
    return buf.getvalue()


def build_tone_pack(
    rows,
    corners,
    outdir,
    top=5,
    milestones=None,
    freqs=None,
    duration=0.12,
    volume=0.8,
    smart=True,
    track_name=None,
    countdown_s=DEFAULT_COUNTDOWN_S,
    cue_config=None,
) -> dict:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    milestones = milestones or DEFAULT_MILESTONES
    freqs = {**DEFAULT_FREQS, **(freqs or {})}
    entries = []
    files = []
    plan = (
        plan_tone_events(rows, corners, top=top, countdown_s=countdown_s, cue_config=cue_config)
        if smart
        else _legacy_tone_events(rows, corners, top, milestones)
    )
    variants = {}

    for event in plan["events"]:
        distance = int(event["distance"])
        cue = event["cue"]
        data = _render_cue(event, freqs, duration, volume)
        variant = variants.get(distance, 0)
        variants[distance] = variant + 1
        filename = "%d_%d.wav" % (distance, variant)
        path = out / filename
        path.write_bytes(data)
        files.append(str(path))
        entries.append(_metadata_entry(event["corner_name"], cue, distance, filename))

    metadata_path = _write_metadata(out, entries, track_name=track_name)
    plan_path = _write_plan(out, plan)
    files.append(str(metadata_path))
    files.append(str(plan_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


def plan_tone_events(
    rows,
    corners,
    top=5,
    min_gap_m=DEFAULT_MIN_GAP_M,
    max_events_per_corner=3,
    countdown_m=120,
    countdown_s=DEFAULT_COUNTDOWN_S,
    cue_config=None,
) -> dict:
    cue_config = cue_config or DEFAULT_CONFIG
    events = []
    corners_plan = []

    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        candidates = _corner_candidates(row, corner, countdown_m, countdown_s, cue_config)
        selected = []
        skipped = []
        for candidate in sorted(candidates, key=lambda c: (-c["priority"], c["distance"])):
            if candidate["distance"] <= 0:
                # El anticipo cayo antes de la meta (curva pegada al inicio de
                # vuelta): descartar, no clampear a 0 — un cue en t=0 del video
                # suena aleatorio (QA 2026-07-05).
                skipped.append({**candidate, "reason": "antes_de_la_meta"})
                continue
            if candidate.get("protected"):
                # El tono de frenada nunca cede a un gap (R1): entra siempre.
                selected.append(candidate)
                continue
            if len(selected) >= max_events_per_corner:
                skipped.append({**candidate, "reason": "max_events_per_corner"})
                continue
            if any(abs(candidate["distance"] - s["distance"]) < min_gap_m for s in selected):
                skipped.append({**candidate, "reason": "too_close_in_corner"})
                continue
            selected.append(candidate)

        selected.sort(key=lambda c: c["distance"])
        for candidate in selected:
            events.append(candidate)
        corners_plan.append(
            {
                "id": row.get("id", corner.get("id")),
                "name": _corner_name(row, corner),
                "time_lost": _as_float(row.get("time_lost", 0)),
                "selected": [_plan_public(c) for c in selected],
                "skipped": [_plan_public(c) for c in skipped],
            }
        )

    events.sort(key=lambda c: c["distance"])
    # Gap minimo GLOBAL: el de arriba solo separa cues DENTRO de una curva; en
    # curvas encadenadas quedaban cues de curvas vecinas a <1 s (sopa de tonos,
    # QA 2026-07-05). Un tono de frenada PROTEGIDO nunca se descarta (R1):
    # protegido vs no-protegido cae el no-protegido; protegido vs protegido se
    # quedan ambos (dos frenadas reales pegadas siguen sonando ambas). Entre
    # no-protegidos gana el de mayor prioridad. Nota: al reemplazar al vecino
    # anterior no hace falta re-verificar hacia atras — el reemplazado ya
    # respetaba el gap con su predecesor y el nuevo esta aun mas adelante.
    kept = []
    skipped_global = []
    for event in events:
        if kept and event["distance"] - kept[-1]["distance"] < min_gap_m:
            prev = kept[-1]
            ev_prot = event.get("protected")
            prev_prot = prev.get("protected")
            if ev_prot and prev_prot:
                kept.append(event)
            elif ev_prot and not prev_prot:
                skipped_global.append({**kept.pop(), "reason": "too_close_global"})
                kept.append(event)
            elif prev_prot and not ev_prot:
                skipped_global.append({**event, "reason": "too_close_global"})
            elif event["priority"] > prev["priority"]:
                skipped_global.append({**kept.pop(), "reason": "too_close_global"})
                kept.append(event)
            else:
                skipped_global.append({**event, "reason": "too_close_global"})
        else:
            kept.append(event)

    # Reconciliar el plan por curva: un cue descartado globalmente NO puede
    # seguir en "selected" (plan.json es la auditoria de que suena y que no).
    # Nota: los brake_tic se agregan despues, a plan["events"] pero NO a los
    # "selected" por-curva; la fuente de verdad de lo que se renderiza es
    # plan["events"], no la suma de los "selected".
    dropped = {(e["corner_id"], e["cue"], e["distance"]) for e in skipped_global}
    for corner_plan in corners_plan:
        still = []
        for sel in corner_plan["selected"]:
            if (sel["corner_id"], sel["cue"], sel["distance"]) in dropped:
                corner_plan["skipped"].append({**sel, "reason": "too_close_global"})
            else:
                still.append(sel)
        corner_plan["selected"] = still

    # Countdown OPORTUNISTA: por cada frenada protegida con lead_m, 2 tics de
    # aviso antes de la frenada (en brake_d - lead_m y brake_d - lead_m/2). Cada
    # tic entra SOLO si cabe a >=min_gap de TODO sonido de OTRO grupo ya en la
    # linea de tiempo (frenadas y tics de OTRAS curvas). El tono de frenada de
    # SU MISMA curva y su tic hermano quedan fuera de la comparacion: son un
    # solo grupo cohesivo (2 tics + el "ya" en brake_d, ADR 0026) y un tic no
    # puede auto-rechazarse contra el evento que anuncia. Sin esta exclusion,
    # lead_m < 2*min_gap_m (curvas por debajo de ~103 km/h con el default de
    # 3.5 s) tiraba el tic step=1 contra su propia frenada. Se recorren en
    # orden de distancia (greedy) para resolver tic-vs-tic entre curvas.
    timeline = [(idx, e["distance"]) for idx, e in enumerate(kept)]
    tic_candidates = []
    for idx, e in enumerate(kept):
        if e.get("protected") and e.get("lead_m"):
            for step, frac in ((0, 1.0), (1, 0.5)):
                d = int(round(e["distance"] - e["lead_m"] * frac))
                tic_candidates.append((d, step, idx, e))
    tics = []
    for d, step, own_idx, e in sorted(tic_candidates, key=lambda x: x[0]):
        if d <= 0:
            continue
        if any(abs(d - t) < min_gap_m for t_idx, t in timeline if t_idx != own_idx):
            continue
        timeline.append((own_idx, d))
        tics.append(
            {
                "corner_id": e["corner_id"],
                "corner_name": e["corner_name"],
                "cue": "brake_tic",
                "distance": d,
                "priority": 100,
                "reason": "aviso de frenada",
                "step": step,
            }
        )

    all_events = sorted(kept + tics, key=lambda c: c["distance"])
    return {
        "events": [_plan_public(e) for e in all_events],
        "corners": corners_plan,
        "skipped_global": [_plan_public(e) for e in skipped_global],
    }


def _run_async_in_thread(coro):
    """Ejecuta una corutina en un thread con su propio event-loop.

    Seguro si hay un loop activo (p.ej. NiceGUI/uvicorn), donde
    asyncio.run() lanzaria RuntimeError: This event loop is already running.
    """
    import asyncio

    exc: list = []

    def _target():
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        except Exception as e:  # noqa: BLE001
            exc.append(e)
        finally:
            loop.close()

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if exc:
        raise exc[0]


def build_voice_pack(rows, corners, outdir, top=5, lang="es-MX", track_name=None) -> dict:
    if importlib.util.find_spec("edge_tts") is None:
        raise RuntimeError("edge-tts no instalado: ejecuta pip install 'fantasma-inputs[voice]'")

    import edge_tts

    ffmpeg = shutil.which("ffmpeg")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    files = []
    voice = _voice_for_lang(lang)

    if not ffmpeg:
        print("aviso: ffmpeg no disponible; se omiten las pace notes de voz", file=sys.stderr)
        metadata_path = _write_metadata(out, entries, track_name=track_name)
        return {"outdir": str(out), "files": [str(metadata_path)], "entries": 0}

    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        brake = _milestone(corner, "brake") or _milestone(row, "brake")
        if not brake or brake.get("d") is None:
            continue
        raw_distance = _as_float(brake["d"]) - 200
        if raw_distance <= 0:
            # La nota caeria antes de la meta (curva pegada al inicio): saltarla,
            # no clampear a 0 — una voz en t=0 del video suena aleatoria. Con
            # aviso: un descarte silencioso hace creer que edge-tts fallo.
            print(
                "aviso: nota de voz de %s descartada (caeria antes de la meta)"
                % _corner_name(row, corner),
                file=sys.stderr,
            )
            continue
        distance = int(round(raw_distance))
        name = _corner_name(row, corner)
        filename = "%d_0.wav" % distance
        text = _voice_text(row, name)
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = os.path.join(tmp, "note.mp3")
            wav = out / filename
            _run_async_in_thread(edge_tts.Communicate(text, voice=voice).save(mp3))
            try:
                subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-i",
                        mp3,
                        "-ar",
                        "24000",
                        "-ac",
                        "1",
                        "-sample_fmt",
                        "s16",
                        str(wav),
                    ],
                    check=True,
                    capture_output=True,
                )
            except (OSError, subprocess.CalledProcessError) as e:
                print("aviso: no se pudo convertir voz para %s: %s" % (name, e), file=sys.stderr)
                continue
        files.append(str(out / filename))
        entries.append(_metadata_entry(name, "voice", distance, filename))

    metadata_path = _write_metadata(out, entries, track_name=track_name)
    files.append(str(metadata_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


def build_pack(rows, corners, outdir, mode="tones", top=5, cue_config=None, **kwargs) -> dict:
    track_name = kwargs.pop("track_name", None)
    if mode == "tones":
        tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang"}
        return build_tone_pack(
            rows,
            corners,
            outdir,
            top=top,
            track_name=track_name,
            cue_config=cue_config,
            **tone_kwargs,
        )
    if mode == "voice":
        return build_voice_pack(
            rows, corners, outdir, top=top, lang=kwargs.get("lang", "es-MX"), track_name=track_name
        )
    if mode != "both":
        raise ValueError("modo invalido: %s" % mode)

    tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang"}
    tones = build_tone_pack(
        rows, corners, outdir, top=top, track_name=track_name, cue_config=cue_config, **tone_kwargs
    )
    tone_entries = _read_entries(Path(outdir) / "metadata.json")
    voice = build_voice_pack(
        rows, corners, outdir, top=top, lang=kwargs.get("lang", "es-MX"), track_name=track_name
    )
    voice_entries = _read_entries(Path(outdir) / "metadata.json")
    _write_metadata(Path(outdir), tone_entries + voice_entries, track_name=track_name)
    files = list(dict.fromkeys(tones["files"] + voice["files"]))
    return {
        "outdir": str(Path(outdir)),
        "files": files,
        "entries": len(tone_entries) + len(voice_entries),
    }


def render_pace_notes_track(pace_notes_dir, lap, output, sample_rate=24000, volume=1.0) -> str:
    import numpy as np

    metadata_path = Path(pace_notes_dir) / "metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("no existe metadata.json en %s" % pace_notes_dir)
    if not lap.has("dist") or not lap.has("time"):
        raise RuntimeError("la telemetria necesita canales time y dist para sincronizar sonidos")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    total_frames = int((lap.laptime + 1.0) * sample_rate)
    mixed = np.zeros(total_frames, dtype=np.float32)
    for entry in metadata.get("entries", []):
        t = _dist_to_time(lap, _as_float(entry.get("distanceRoundTrack")))
        start = max(0, int(t * sample_rate))
        for filename in entry.get("fileNames", []):
            wav_path = Path(pace_notes_dir) / filename
            if not wav_path.exists():
                continue
            samples, rate = _read_wav_int16(wav_path)
            if rate != sample_rate:
                continue
            end = min(len(mixed), start + len(samples))
            if end > start:
                mixed[start:end] += samples[: end - start] * volume

    mixed = (mixed.clip(-1.0, 1.0) * 32767).astype(np.int16)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_bytes(_make_wav_bytes(mixed, sample_rate=sample_rate))
    return str(output)


def _top_rows(rows, top):
    if not top:
        # top=0 (o None): TODAS las curvas detectadas, tambien donde no se
        # pierde tiempo — el cue de frenada actua como pace note de ritmo,
        # estilo rally (pedido del PO, ADR 0024).
        return list(rows)
    losses = [r for r in rows if _as_float(r.get("time_lost", 0)) > 0]
    losses.sort(key=lambda r: _as_float(r.get("time_lost", 0)), reverse=True)
    return losses[:top]


def _legacy_tone_events(rows, corners, top, milestones):
    events = []
    corners_plan = []
    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        selected = []
        for milestone in milestones:
            m = _milestone(corner, milestone) or _milestone(row, milestone)
            if not m or m.get("d") is None:
                continue
            selected.append(
                _event(row, corner, milestone, _as_float(m["d"]), 0, "legacy:%s" % milestone)
            )
        events.extend(selected)
        corners_plan.append(
            {
                "id": row.get("id", corner.get("id")),
                "name": _corner_name(row, corner),
                "time_lost": _as_float(row.get("time_lost", 0)),
                "selected": [_plan_public(e) for e in selected],
                "skipped": [],
            }
        )
    # skipped_global vacio para que el esquema del plan sea el mismo que el smart
    return {
        "events": [_plan_public(e) for e in events],
        "corners": corners_plan,
        "skipped_global": [],
    }


def _countdown_lead_m(brake, countdown_m, countdown_s, min_lead_m=60, max_lead_m=350):
    """Distancia de anticipo del countdown de frenada.

    Por tiempo: countdown_s segundos a la velocidad de llegada a la frenada
    (v del milestone, km/h), acotada a [min_lead_m, max_lead_m]. Los 120 m
    fijos daban ~2 s a velocidad GT3 — insuficiente para reaccionar (el PO
    pidio 3-4 s; ADR 0024). Fallback al countdown_m fijo si el milestone no
    trae v (corners JSON viejos, tests sinteticos).
    """
    v = brake.get("v")
    if not v:
        return countdown_m
    lead = _as_float(v) / 3.6 * countdown_s
    return max(min_lead_m, min(max_lead_m, lead))


def _cue_cfg(cue_config, cue):
    """Config de un tipo de cue con fallback a DEFAULT_CONFIG.

    Un cue_config parcial (solo algunas claves, p.ej. en un test que solo
    quiere subir una prioridad) no debe dejar sin enabled/priority a los tipos
    que no menciono explicitamente.
    """
    cfg = (cue_config or {}).get(cue)
    if cfg is None:
        cfg = DEFAULT_CONFIG.get(cue, {"enabled": True, "priority": 50})
    return cfg


def _corner_candidates(row, corner, countdown_m, countdown_s=DEFAULT_COUNTDOWN_S, cue_config=None):
    cue_config = cue_config or DEFAULT_CONFIG
    loss = _as_float(row.get("time_lost", 0))
    flags = str(row.get("flags", ""))
    d_brake = _as_float(row.get("d_brake_m", 0)) if row.get("d_brake_m") not in (None, "") else 0
    d_gas = _as_float(row.get("d_gas100_m", 0)) if row.get("d_gas100_m") not in (None, "") else 0
    braking_issue = "frenada" in flags or d_brake > 15
    exit_issue = abs(d_gas) > 20 or (loss >= 0.25 and "vmin" not in flags)
    apex_issue = "vmin" in flags or loss >= 0.25
    candidates = []

    brake_cfg = _cue_cfg(cue_config, "brake")
    brake = _milestone(corner, "brake")
    if brake_cfg.get("enabled", True) and brake and brake.get("d") is not None:
        brake_d = _as_float(brake["d"])
        lead_m = _countdown_lead_m(brake, countdown_m, countdown_s)
        # Tono de frenada UNIVERSAL: toda curva con milestone de frenada suena,
        # sin importar severidad. Es PROTEGIDO — ningun gap lo descarta (R1), sin
        # importar su prioridad en config. El countdown (tics de aviso) se
        # coloca aparte y de forma oportunista en plan_tone_events usando lead_m.
        candidates.append(
            _event(
                row,
                corner,
                "brake",
                brake_d,
                brake_cfg.get("priority", 80),
                "marca frenada",
                lead_m=lead_m,
                protected=True,
            )
        )

    release_cfg = _cue_cfg(cue_config, "brake_release")
    release = _milestone(corner, "brake_release")
    if (
        release_cfg.get("enabled", True)
        and release
        and release.get("d") is not None
        and braking_issue
    ):
        candidates.append(
            _event(
                row,
                corner,
                "brake_release",
                _as_float(release["d"]),
                release_cfg.get("priority", 70),
                "salida de freno",
            )
        )

    turn_cfg = _cue_cfg(cue_config, "turn_in")
    turn = _milestone(corner, "turn_in")
    if turn_cfg.get("enabled", True) and turn and turn.get("d") is not None and loss >= 0.25:
        candidates.append(
            _event(
                row,
                corner,
                "turn_in",
                _as_float(turn["d"]),
                turn_cfg.get("priority", 60),
                "inicio de giro",
            )
        )

    throttle_cfg = _cue_cfg(cue_config, "throttle_on")
    throttle = _milestone(corner, "throttle_on")
    if (
        throttle_cfg.get("enabled", True)
        and throttle
        and throttle.get("d") is not None
        and exit_issue
    ):
        candidates.append(
            _event(
                row,
                corner,
                "throttle_on",
                _as_float(throttle["d"]),
                throttle_cfg.get("priority", 85),
                "inicio de gas",
            )
        )

    full_cfg = _cue_cfg(cue_config, "full_throttle")
    full = _milestone(corner, "full_throttle")
    if (
        full_cfg.get("enabled", True)
        and full
        and full.get("d") is not None
        and (exit_issue or loss >= 0.25)
    ):
        candidates.append(
            _event(
                row,
                corner,
                "full_throttle",
                _as_float(full["d"]),
                full_cfg.get("priority", 75),
                "gas a fondo",
            )
        )

    apex_cfg = _cue_cfg(cue_config, "apex")
    apex = _milestone(corner, "apex")
    if apex_cfg.get("enabled", False) and apex and apex.get("d") is not None and apex_issue:
        candidates.append(
            _event(
                row,
                corner,
                "apex",
                _as_float(apex["d"]),
                apex_cfg.get("priority", 90),
                "corrige V-Min/apex",
            )
        )

    coast_cfg = _cue_cfg(cue_config, "coast")
    coast = _milestone(corner, "coast_start")
    if coast_cfg.get("enabled", False) and coast and coast.get("d") is not None:
        # Sin frenada: no hay milestone "brake" en esta curva (turn_in +
        # release ya cubren la fase de freno cuando si la hay).
        sin_frenada = _milestone(corner, "brake") is None
        if not coast_cfg.get("solo_sin_frenada", True) or sin_frenada:
            candidates.append(
                _event(
                    row,
                    corner,
                    "coast",
                    _as_float(coast["d"]),
                    coast_cfg.get("priority", 50),
                    "inercia",
                )
            )

    return candidates


def _event(row, corner, cue, distance, priority, reason, lead_m=None, protected=False):
    event = {
        "corner_id": str(row.get("id") or corner.get("id") or "?"),
        "corner_name": _corner_name(row, corner),
        "cue": cue,
        "distance": int(round(distance)),
        "priority": priority,
        "reason": reason,
    }
    if lead_m is not None:
        event["lead_m"] = int(round(lead_m))
    if protected:
        event["protected"] = True
    return event


def _plan_public(event):
    keys = (
        "corner_id",
        "corner_name",
        "cue",
        "distance",
        "priority",
        "reason",
        "lead_m",
        "protected",
        "step",
    )
    return {k: event[k] for k in keys if k in event}


def _find_corner(row, corners):
    by_key = {}
    for corner in corners:
        for key in (corner.get("id"), corner.get("name")):
            if key:
                by_key[str(key)] = corner
    for key in (row.get("id"), row.get("name")):
        if key and str(key) in by_key:
            return by_key[str(key)]
    row_apex = row.get("apex_d")
    if row_apex is not None:
        row_apex = _as_float(row_apex)
        for corner in corners:
            apex = _milestone(corner, "apex")
            if apex and apex.get("d") is not None and abs(_as_float(apex["d"]) - row_apex) <= 1:
                return corner
    return None


def _milestone(corner, name):
    milestones = corner.get("milestones") or {}
    for key in MILESTONE_ALIASES.get(name, [name]):
        if key in milestones:
            return milestones[key]
    return None


def _metadata_entry(name, milestone, distance, filename):
    label = MILESTONE_LABELS.get(milestone, milestone)
    return {
        "description": "%s — %s" % (name, label),
        "distanceRoundTrack": distance,
        "lapNumber": None,
        "minimumSpeed": None,
        "maximumSpeed": None,
        "minimumYawAngle": None,
        "maximumYawAngle": None,
        "recordingNames": [filename],
        "fileNames": [filename],
        "playAllInOrder": False,
    }


def _render_cue(event, freqs, duration, volume):
    """Sintetiza el WAV de un evento del plan segun su cue.

    Cada evento del plan ya trae su distancia final (los tics del countdown y
    el tono de frenada son eventos independientes, colocados en plan_tone_events).
    El tic asciende en frecuencia por su `step` (COUNTDOWN_SCALE); el tono de
    frenada suena mas largo y a otra frecuencia para no confundirlo con el tic.
    """
    cue = event["cue"]
    if cue == "brake_tic":
        base = freqs.get("brake_countdown", 880)
        scale = COUNTDOWN_SCALE[event.get("step", 0)]
        return generate_tone(base * scale, 0.08, volume=volume)
    if cue == "brake":
        return generate_tone(freqs.get("brake", 1000), duration, volume=volume)
    return generate_tone(freqs.get(cue, 440), duration, volume=volume)


def _write_metadata(outdir, entries, track_name=None):
    metadata = {
        "description": "Generado por SimGhostInputs",
        "gameEnumName": "AMS2",
        "carClassName": None,
        "trackName": track_name,
        "entries": entries,
    }
    path = outdir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_plan(outdir, plan):
    path = outdir / "plan.json"
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _read_entries(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("entries", [])


def _corner_name(row, corner):
    return str(row.get("name") or corner.get("name") or corner.get("id") or "?")


def _as_float(value):
    if value in (None, ""):
        return 0.0
    return float(value)


def _dist_to_time(lap, dist):
    d = lap.col("dist")
    t = lap.col("time")
    if not d or not t:
        return 0.0
    if dist <= d[0]:
        return t[0]
    for i in range(1, len(d)):
        if d[i] >= dist:
            span = d[i] - d[i - 1]
            if span <= 0:
                return t[i]
            ratio = (dist - d[i - 1]) / span
            return t[i - 1] + ratio * (t[i] - t[i - 1])
    return t[-1]


def _read_wav_int16(path):
    import numpy as np

    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise RuntimeError("WAV no soportado para preview: %s" % path)
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0, rate


def _voice_text(row, name):
    loss = _as_float(row.get("time_lost", 0))
    flags = str(row.get("flags", ""))
    has_brake = "frenada" in flags
    has_vmin = "vmin" in flags
    if has_brake and has_vmin:
        return "%s. Frena mas tarde y sube el apex. Pierdes %.1f segundos." % (name, loss)
    if has_brake:
        return "%s. Frena mas tarde. Pierdes %.1f segundos." % (name, loss)
    if has_vmin:
        return "%s. Sube la velocidad en el apex. Pierdes %.1f segundos." % (name, loss)
    return "%s. Pierdes %.1f segundos." % (name, loss)


def _voice_for_lang(lang):
    voices = {
        "es-MX": "es-MX-JorgeNeural",
        "es-ES": "es-ES-AlvaroNeural",
        "en-US": "en-US-GuyNeural",
    }
    return voices.get(lang, lang)
