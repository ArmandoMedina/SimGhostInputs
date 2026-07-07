def test_crewchief_pacenotes_dir():
    """crewchief_pacenotes_dir devuelve la ruta estandar de CrewChief para AMS2."""
    import os

    from fantasma.viz.pacenotes import crewchief_pacenotes_dir

    result = crewchief_pacenotes_dir("Interlagos")
    # Debe terminar en .../CrewChiefV4/pace_notes/ams2/Interlagos
    parts = result.replace("\\", "/").split("/")
    assert parts[-1] == "Interlagos"
    assert parts[-2] == "ams2"
    assert parts[-3] == "pace_notes"
    assert parts[-4] == "CrewChiefV4"
    # Debe estar bajo el directorio home del usuario
    assert result.startswith(os.path.expanduser("~"))


def test_generate_tone_returns_wav_bytes():
    """generate_tone devuelve bytes WAV validos."""
    from fantasma.viz.pacenotes import generate_tone

    data = generate_tone(440, 0.1)
    assert data[:4] == b"RIFF"
    assert len(data) > 100


def test_generate_tone_duration():
    """La duracion del tono es aproximadamente la pedida."""
    import io
    import wave

    from fantasma.viz.pacenotes import generate_tone

    data = generate_tone(440, 0.5, sample_rate=24000)
    with wave.open(io.BytesIO(data)) as w:
        frames = w.getnframes()
        rate = w.getframerate()
    assert abs(frames / rate - 0.5) < 0.01


def test_build_tone_pack_creates_files(tmp_path):
    """build_tone_pack genera WAVs y metadata.json."""
    from fantasma.viz.pacenotes import build_tone_pack

    rows = [
        {
            "name": "C01",
            "apex_d": 500,
            "time_lost": 0.4,
            "milestones": {"brake": {"d": 450}, "apex": {"d": 500}, "gas": {"d": 550}},
        },
    ]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {"brake": {"d": 450}, "apex": {"d": 500}, "gas": {"d": 550}},
        },
    ]
    result = build_tone_pack(rows, corners, str(tmp_path), top=1)
    assert (tmp_path / "metadata.json").exists()
    assert result["entries"] >= 1
    wavs = list(tmp_path.glob("*.wav"))
    assert len(wavs) >= 1


def test_metadata_json_format(tmp_path):
    """metadata.json tiene el formato exacto que CrewChief espera."""
    import json

    from fantasma.viz.pacenotes import build_tone_pack

    rows = [
        {
            "name": "Hatzenbach",
            "apex_d": 1847,
            "time_lost": 0.4,
            "milestones": {"brake": {"d": 1800}, "apex": {"d": 1847}, "gas": {"d": 1900}},
        }
    ]
    corners = [
        {
            "id": "C01",
            "name": "Hatzenbach",
            "milestones": {"brake": {"d": 1800}, "apex": {"d": 1847}, "gas": {"d": 1900}},
        }
    ]
    build_tone_pack(rows, corners, str(tmp_path), top=1)
    meta = json.loads((tmp_path / "metadata.json").read_text())
    assert "entries" in meta
    assert len(meta["entries"]) >= 1
    entry = meta["entries"][0]
    assert "distanceRoundTrack" in entry
    assert "fileNames" in entry
    assert "recordingNames" in entry


def test_plan_tone_events_limits_dense_corner():
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "vmin+frenada"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {
                "brake_start": {"d": 1000},
                "turn_in": {"d": 1015},
                "apex": {"d": 1040},
                "throttle_on": {"d": 1060},
                "full_throttle": {"d": 1080},
            },
        }
    ]
    plan = plan_tone_events(rows, corners, top=1, min_gap_m=50, max_events_per_corner=3)
    selected = plan["corners"][0]["selected"]
    assert len(selected) <= 3
    assert any(e["cue"] == "brake" for e in selected)
    assert any(s["reason"] == "too_close_in_corner" for s in plan["corners"][0]["skipped"])


def test_voice_text_frenada_flag():
    """flags='frenada' -> texto incluye 'Frena mas tarde'."""
    from fantasma.viz.pacenotes import _voice_text

    row = {"time_lost": 0.5, "flags": "frenada"}
    text = _voice_text(row, "Hatzenbach")
    assert "Frena mas tarde" in text
    assert "Hatzenbach" in text
    assert "0.5" in text


def test_voice_text_vmin_flag():
    """flags='vmin' -> texto incluye 'Sube la velocidad'."""
    from fantasma.viz.pacenotes import _voice_text

    row = {"time_lost": 0.3, "flags": "vmin"}
    text = _voice_text(row, "Bergwerk")
    assert "Sube la velocidad" in text
    assert "Bergwerk" in text


def test_voice_text_both_flags():
    """flags='vmin+frenada' -> texto incluye ambas indicaciones."""
    from fantasma.viz.pacenotes import _voice_text

    row = {"time_lost": 0.8, "flags": "vmin+frenada"}
    text = _voice_text(row, "Brunnchen")
    assert "Frena mas tarde" in text
    assert "apex" in text.lower()
    assert "Brunnchen" in text


def test_voice_text_no_flags():
    """flags='' -> mensaje generico con 'Pierdes'."""
    from fantasma.viz.pacenotes import _voice_text

    row = {"time_lost": 0.2, "flags": ""}
    text = _voice_text(row, "Caracciola")
    assert "Pierdes" in text
    assert "Caracciola" in text
    assert "0.2" in text


def test_render_pace_notes_track_places_cues(tmp_path):
    import wave

    from fantasma.core.lap import Lap
    from fantasma.viz.pacenotes import build_tone_pack, render_pace_notes_track

    rows = [{"id": "C01", "name": "C01", "apex_d": 500, "time_lost": 0.4, "flags": "vmin"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {
                "brake_start": {"d": 450},
                "apex": {"d": 500},
                "full_throttle": {"d": 560},
            },
        }
    ]
    pack = tmp_path / "pack"
    build_tone_pack(rows, corners, str(pack), top=1)
    lap = Lap(channels={"time": [0.0, 1.0, 2.0], "dist": [0.0, 500.0, 1000.0]})
    out = tmp_path / "preview.wav"
    render_pace_notes_track(str(pack), lap, str(out))
    with wave.open(str(out), "rb") as wav:
        assert wav.getframerate() == 24000
        assert wav.getnchannels() == 1
        assert wav.getnframes() > 24000


# ── Edge cases: entradas vacias ────────────────────────────────────────────────


def test_plan_tone_events_empty_rows_no_crash():
    """plan_tone_events con rows=[] no lanza excepcion y devuelve estructura valida."""
    from fantasma.viz.pacenotes import plan_tone_events

    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {
                "brake_start": {"d": 450},
                "apex": {"d": 500},
                "full_throttle": {"d": 560},
            },
        }
    ]
    result = plan_tone_events(rows=[], corners=corners, top=5)
    # Sin filas no hay eventos ni corners planificados
    assert result["events"] == []
    assert result["corners"] == []


def test_build_tone_pack_empty_rows_no_crash(tmp_path):
    """build_tone_pack con rows=[] no lanza excepcion y retorna entries=0."""
    from fantasma.viz.pacenotes import build_tone_pack

    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {
                "brake_start": {"d": 450},
                "apex": {"d": 500},
                "full_throttle": {"d": 560},
            },
        }
    ]
    result = build_tone_pack(rows=[], corners=corners, outdir=str(tmp_path), top=5)
    # Sin filas con time_lost > 0 no se genera ningun tono
    assert result["entries"] == 0
    # El directorio de salida y metadata.json deben existir igual
    assert (tmp_path / "metadata.json").exists()


# ── _run_async_in_thread: seguridad de event-loop ─────────────────────────────


def test_run_async_in_thread_safe_inside_running_loop():
    """_run_async_in_thread no lanza RuntimeError si hay un loop activo (p.ej. NiceGUI).

    asyncio.run() dentro de un loop activo lanzaria:
        RuntimeError: This event loop is already running
    El helper debe ejecutar la corutina en un thread separado y completarla sin error.
    """
    import asyncio

    from fantasma.viz.pacenotes import _run_async_in_thread

    result: list = []

    async def my_coro():
        result.append(42)

    async def outer():
        # Aqui hay un loop activo; asyncio.run() crashearia.
        _run_async_in_thread(my_coro())

    asyncio.run(outer())
    assert result == [42]


# ── Plan de cues: sincronia percibida (ADR 0024) ──────────────────────────────


def test_countdown_antes_de_la_meta_omite_tic_pero_conserva_la_frenada():
    """Curva pegada a la meta: un tic de aviso que caeria en d<=0 se omite, pero
    la frenada (protegida) siempre suena en su punto real y ningun cue cae en el
    segundo 0 del video (Reviewer sobre ADR 0024)."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    # brake a 100 m sin v -> fallback countdown_m=120 -> tics en -20 (omitido) y 40
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 100}}}]
    plan = plan_tone_events(rows, corners, top=1)
    assert all(e["distance"] > 0 for e in plan["events"])
    brakes = [e for e in plan["events"] if e["cue"] == "brake"]
    assert brakes and brakes[0]["distance"] == 100
    # solo el tic que cabe (40) se coloca; el que caeria antes de la meta se omite
    tics = [e for e in plan["events"] if e["cue"] == "brake_tic"]
    assert [e["distance"] for e in tics] == [40]


def test_frenada_protegida_sobrevive_vecino_de_mayor_prioridad():
    """Regresion 819: el tono de frenada es PROTEGIDO — ningun gap global lo
    descarta, ni siquiera contra un vecino de MAYOR prioridad a <min_gap. Antes
    la frenada (80) perdia contra un cue vecino de mas prioridad y la curva se
    quedaba muda. Ahora cae el no-protegido; la frenada siempre suena (R1)."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.3, "flags": ""},
        {"id": "C02", "name": "C02", "time_lost": 0.3, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 1000}}},
        # throttle_on (prioridad 85 > 80) a 20 m de la frenada de C01
        {"id": "C02", "name": "C02", "milestones": {"throttle_on": {"d": 1020}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    brakes = [e for e in plan["events"] if e["cue"] == "brake"]
    assert [e["distance"] for e in brakes] == [1000]
    # el vecino de mayor prioridad cae por el gap global, no la frenada
    assert not any(e["cue"] == "throttle_on" for e in plan["events"])
    assert any(
        s["cue"] == "throttle_on" and s["reason"] == "too_close_global"
        for s in plan["skipped_global"]
    )


def test_dos_frenadas_pegadas_ambas_suenan():
    """Protegido vs protegido: dos frenadas reales a <min_gap se quedan AMBAS
    (R1) — el gap global nunca sacrifica un tono de frenada."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "A", "name": "A", "time_lost": 0.5, "flags": "frenada"},
        {"id": "B", "name": "B", "time_lost": 0.5, "flags": "frenada"},
    ]
    corners = [
        {"id": "A", "name": "A", "milestones": {"brake_start": {"d": 1000}}},
        {"id": "B", "name": "B", "milestones": {"brake_start": {"d": 1030}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    brakes = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake")
    assert brakes == [1000, 1030]


def test_dos_countdowns_encadenados_no_amontonan_tics():
    """Regresion 4463 (tic-vs-tic): dos frenadas encadenadas no apilan sus tics.
    Cada tic entra solo si cabe a >=min_gap de TODO sonido ya colocado, incluidos
    los tics de la OTRA curva; el que no cabe se omite. Ningun tic queda a
    <min_gap de otro sonido."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "A", "name": "A", "time_lost": 0.5, "flags": "frenada"},
        {"id": "B", "name": "B", "time_lost": 0.5, "flags": "frenada"},
    ]
    corners = [
        {"id": "A", "name": "A", "milestones": {"brake_start": {"d": 1000, "v": 216}}},
        {"id": "B", "name": "B", "milestones": {"brake_start": {"d": 1040, "v": 216}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    events = plan["events"]
    # las dos frenadas protegidas a 40 m suenan ambas (R1)
    assert sorted(e["distance"] for e in events if e["cue"] == "brake") == [1000, 1040]
    tics = [e for e in events if e["cue"] == "brake_tic"]
    dists = [e["distance"] for e in events]
    for tic in tics:
        others = [d for d in dists if d != tic["distance"]]
        assert all(abs(tic["distance"] - o) >= 50 for o in others)
    # se omitieron tics: los 4 (2 por curva) no caben sin encimarse
    assert len(tics) < 4


def test_countdown_tics_no_se_autorrechazan_contra_su_propia_frenada():
    """Regresion: con lead_m < 2*min_gap_m (curvas por debajo de ~103 km/h con
    el countdown_s default), el tic step=1 (brake_d - lead_m/2) caia a <min_gap_m
    de SU PROPIA frenada y se perdia aunque no compitiera con ningun otro
    sonido. El tono de frenada y sus 2 tics son un solo grupo cohesivo (ADR
    0026): la cabida se chequea contra OTROS sonidos, nunca contra el propio
    grupo."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    # v=90 km/h -> lead_m=87.5, redondeado a 88 (< 2*min_gap_m=100): antes del
    # fix el tic step=1 (2000-44=1956) caia a 44 m de la frenada (<50) y se
    # descartaba pese a no competir con nada mas.
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 90}}}]
    plan = plan_tone_events(rows, corners, top=1)
    brake = next(e for e in plan["events"] if e["cue"] == "brake")
    assert brake["distance"] == 2000
    assert brake["lead_m"] == 88
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1912, 1956]


def test_countdown_tic_de_otra_curva_si_se_descarta_por_cabida():
    """La exclusion del propio grupo no exime a un tic de respetar la cabida
    contra OTRAS curvas — eso reabriria el bug 4463 (ADR 0026): un tic que
    caeria a <min_gap_m de un evento ajeno se sigue descartando."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C00", "name": "C00", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 90}}},
        # throttle_on de C00 a 10 m del tic step=0 de C01 (1912): se descarta
        # por cabida contra OTRA curva; el step=1 (1956) si cabe y sobrevive.
        {"id": "C00", "name": "C00", "milestones": {"throttle_on": {"d": 1902}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1956]


def test_plan_legacy_tiene_mismo_esquema():
    """El plan legacy (smart=False) expone skipped_global vacio: mismo esquema."""
    from fantasma.viz.pacenotes import _legacy_tone_events

    plan = _legacy_tone_events([], [], 5, ["brake"])
    assert plan["skipped_global"] == []


def test_countdown_anticipa_por_tiempo_con_v():
    """Con v en el milestone, el anticipo es countdown_s segundos a esa velocidad
    (216 km/h = 60 m/s -> 3.5 s = 210 m), no los 120 m fijos. La frenada se ancla
    en su punto real (protegida) y lleva el anticipo en lead_m; los tics se
    colocan a lead_m y lead_m/2 antes."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]
    plan = plan_tone_events(rows, corners, top=1, countdown_s=3.5)
    brake = next(e for e in plan["events"] if e["cue"] == "brake")
    assert brake["distance"] == 2000
    assert brake["lead_m"] == 210
    assert brake.get("protected")
    # 2 tics de aviso antes de la frenada, en brake_d - lead_m y brake_d - lead_m/2
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1790, 1895]
    # el 3er (ultimo) sonido es la frenada; nada de un 4o "ya"
    assert max(e["distance"] for e in plan["events"]) == 2000


def test_pack_expande_countdown_y_el_tercer_bip_es_el_ya(tmp_path):
    """El countdown se expande en WAVs independientes mapeados por SU distancia:
    tics de aviso a lead_m y lead_m/2 antes, y el "¡ya!" = tono de FRENADA
    exacto en la distancia donde frena la referencia ("nada de 1,2,3, ya: el 3
    debe ser el ya", PO 2026-07-06)."""
    import json

    from fantasma.viz.pacenotes import build_tone_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]
    build_tone_pack(rows, corners, str(tmp_path), top=1)
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    cues = sorted(
        (e["distanceRoundTrack"], e["description"].split(" — ")[1])
        for e in entries
        if "frenada" in e["description"]
    )
    assert cues == [
        (1790, "contador de frenada"),
        (1895, "contador de frenada"),
        (2000, "punto de frenada"),
    ]
    for d, _ in cues:
        assert (tmp_path / ("%d_0.wav" % d)).exists()


def test_pack_omite_tic_encimado_pero_nunca_el_ya(tmp_path):
    """Un tic de aviso que caeria a <50 m de un cue de otra curva se omite (en
    encadenadas queda "2-ya" o solo "ya"), pero el "¡ya!" en la frenada nunca
    se pierde."""
    import json

    from fantasma.viz.pacenotes import build_tone_pack

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C00", "name": "C00", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}},
        # throttle_on de C00 a 30 m del tic 1 de C01 (1790): el tic se omite
        {"id": "C00", "name": "C00", "milestones": {"throttle_on": {"d": 1760}}},
    ]
    build_tone_pack(rows, corners, str(tmp_path), top=0)
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    dists = {e["distanceRoundTrack"]: e["description"] for e in entries}
    assert 1790 not in dists
    assert "contador de frenada" in dists[1895]
    assert "punto de frenada" in dists[2000]


def test_countdown_lead_clamps_y_fallback():
    from fantasma.viz.pacenotes import _countdown_lead_m

    # 36 km/h * 3.5 s = 35 m -> clamp al minimo de 60 m
    assert _countdown_lead_m({"v": 36}, 120, 3.5) == 60
    # 700 km/h * 3.5 s = 680 m -> clamp al maximo de 350 m
    assert _countdown_lead_m({"v": 700}, 120, 3.5) == 350
    # sin v (corners viejos, tests sinteticos) -> fallback al countdown_m fijo
    assert _countdown_lead_m({"d": 500}, 120, 3.5) == 120


def test_top_cero_incluye_curvas_sin_perdida():
    """top=0 = todas las curvas detectadas (pace notes de ritmo), incluidas
    aquellas donde no se pierde tiempo; top>0 conserva el filtro por perdida."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.0, "flags": ""},
        {"id": "C02", "name": "C02", "time_lost": 0.4, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 500}}},
        {"id": "C02", "name": "C02", "milestones": {"brake_start": {"d": 3000}}},
    ]
    todas = plan_tone_events(rows, corners, top=0)
    assert {c["id"] for c in todas["corners"]} == {"C01", "C02"}
    top5 = plan_tone_events(rows, corners, top=5)
    assert {c["id"] for c in top5["corners"]} == {"C02"}


def test_brake_y_countdown_frecuencias_distintas():
    """brake y brake_countdown eran ambos 880 Hz: indistinguibles al oido."""
    from fantasma.viz.pacenotes import DEFAULT_FREQS

    assert DEFAULT_FREQS["brake"] == 1000
    assert DEFAULT_FREQS["brake"] != DEFAULT_FREQS["brake_countdown"]


# ── cue_config: catalogo filtrable + prioridad configurable (WS-2) ────────────


def test_default_config_reproduce_comportamiento_actual():
    """Con DEFAULT_CONFIG (o sin pasar cue_config) el pack es identico al de
    hoy: mismos tipos activos con las mismas prioridades que antes vivian
    hardcodeadas en _corner_candidates."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            # Milestones espaciados >100 m entre si para que ninguno compita
            # por cabida (min_gap_m default=50) — el foco de este test es la
            # paridad DEFAULT_CONFIG vs sin cue_config, no la regla de cabida.
            "milestones": {
                "brake_start": {"d": 1000},
                "brake_release": {"d": 1100},
                "turn_in": {"d": 1200},
                "apex": {"d": 1300},
                "throttle_on": {"d": 1400},
                "full_throttle": {"d": 1500},
            },
        }
    ]
    sin_config = plan_tone_events(rows, corners, top=1, max_events_per_corner=10)
    con_default = plan_tone_events(
        rows, corners, top=1, max_events_per_corner=10, cue_config=DEFAULT_CONFIG
    )
    assert sin_config == con_default
    # brake_tic: los 2 tics de aviso del countdown, siempre presentes junto a
    # una frenada protegida con lead_m (mecanismo aparte, no gateado por
    # cue_config en este WS). apex NO aparece: apagado por defecto.
    cues = {e["cue"] for e in sin_config["events"]}
    assert cues == {
        "brake",
        "brake_tic",
        "brake_release",
        "turn_in",
        "throttle_on",
        "full_throttle",
    }
    priorities = {e["cue"]: e["priority"] for e in sin_config["events"]}
    assert priorities == {
        "brake": 80,
        "brake_tic": 100,
        "brake_release": 70,
        "turn_in": 60,
        "throttle_on": 85,
        "full_throttle": 75,
    }


def test_cue_deshabilitado_no_aparece_en_el_pack():
    """Un tipo con enabled=False no genera candidatos, aunque su milestone
    exista y sus condiciones de severidad se cumplan."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "vmin"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {"brake_start": {"d": 1000}, "turn_in": {"d": 1015}},
        }
    ]
    cue_config = {**DEFAULT_CONFIG, "turn_in": {"enabled": False, "priority": 60}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    assert not any(e["cue"] == "turn_in" for e in plan["events"])
    assert any(e["cue"] == "brake" for e in plan["events"])


def test_apex_off_por_defecto_y_aparece_al_habilitarlo():
    """apex esta apagado por defecto (ADR 0026); al habilitarlo en cue_config
    vuelve a sonar."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "vmin"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            # apex a 200 m de la frenada: fuera del min_gap_m default (50) para
            # que el cue quede aislado y la asercion sea sobre enabled, no
            # sobre la regla de cabida contra la frenada protegida.
            "milestones": {"brake_start": {"d": 1000}, "apex": {"d": 1200}},
        }
    ]
    plan_default = plan_tone_events(rows, corners, top=1)
    assert not any(e["cue"] == "apex" for e in plan_default["events"])

    cue_config = {**DEFAULT_CONFIG, "apex": {"enabled": True, "priority": 90}}
    plan_on = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    assert any(e["cue"] == "apex" for e in plan_on["events"])


def test_coast_off_por_defecto_y_aparece_en_curva_sin_frenada():
    """coast esta apagado por defecto; al habilitarlo en una curva SIN
    milestone de frenada, aparece."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {"coast_start": {"d": 900}, "coast_end": {"d": 950}},
        }
    ]
    plan_default = plan_tone_events(rows, corners, top=1)
    assert not any(e["cue"] == "coast" for e in plan_default["events"])

    cue_config = {**DEFAULT_CONFIG, "coast": {"enabled": True, "priority": 50}}
    plan_on = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    coast_events = [e for e in plan_on["events"] if e["cue"] == "coast"]
    assert coast_events and coast_events[0]["distance"] == 900


def test_coast_solo_sin_frenada_no_aparece_en_curva_con_frenada():
    """Con solo_sin_frenada=True (default), coast no suena en una curva que
    tambien tiene milestone de frenada."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {
                "brake_start": {"d": 800},
                "coast_start": {"d": 900},
                "coast_end": {"d": 950},
            },
        }
    ]
    cue_config = {
        **DEFAULT_CONFIG,
        "coast": {"enabled": True, "priority": 50, "solo_sin_frenada": True},
    }
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    assert not any(e["cue"] == "coast" for e in plan["events"])
    assert any(e["cue"] == "brake" for e in plan["events"])

    cue_config_sin_filtro = {
        **DEFAULT_CONFIG,
        "coast": {"enabled": True, "priority": 50, "solo_sin_frenada": False},
    }
    plan_sin_filtro = plan_tone_events(rows, corners, top=1, cue_config=cue_config_sin_filtro)
    assert any(e["cue"] == "coast" for e in plan_sin_filtro["events"])


def test_gear_es_solo_un_slot_reservado():
    """gear esta en el catalogo pero apagado y sin logica de deteccion: un
    milestone 'gear' en la curva no genera ningun candidato de tipo gear."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    assert DEFAULT_CONFIG["gear"]["enabled"] is False
    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""}]
    corners = [
        {
            "id": "C01",
            "name": "C01",
            "milestones": {"brake_start": {"d": 1000}, "gear": {"d": 1010}},
        }
    ]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 65}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    assert not any(e["cue"] == "gear" for e in plan["events"])


def test_prioridad_configurable_invierte_quien_sobrevive_la_colision():
    """La clave de la feature: cambiar la prioridad de un tipo en cue_config
    invierte quien gana una colision por cabida entre dos curvas distintas.

    C01 tiene un turn_in (prioridad default 60, no protegido) y C02 tiene un
    throttle_on (prioridad default 85, no protegido) a menos de min_gap_m de
    distancia. Con la config por defecto gana throttle_on (mayor prioridad).
    Al subir la prioridad de turn_in por encima de la de throttle_on, gana
    turn_in en su lugar."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""},
        {"id": "C02", "name": "C02", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"turn_in": {"d": 1000}}},
        {"id": "C02", "name": "C02", "milestones": {"throttle_on": {"d": 1020}}},
    ]

    plan_default = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    cues_default = {e["cue"] for e in plan_default["events"]}
    assert "throttle_on" in cues_default
    assert "turn_in" not in cues_default

    cue_config = {**DEFAULT_CONFIG, "turn_in": {"enabled": True, "priority": 999}}
    plan_invertido = plan_tone_events(rows, corners, top=2, min_gap_m=50, cue_config=cue_config)
    cues_invertidas = {e["cue"] for e in plan_invertido["events"]}
    assert "turn_in" in cues_invertidas
    assert "throttle_on" not in cues_invertidas


def test_frenada_protegida_universal_pese_a_su_prioridad_en_config():
    """La frenada sigue siendo PROTEGIDA (nunca la tira la cabida) incluso si
    su prioridad en cue_config es la mas baja del catalogo."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.3, "flags": ""},
        {"id": "C02", "name": "C02", "time_lost": 0.3, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 1000}}},
        {"id": "C02", "name": "C02", "milestones": {"throttle_on": {"d": 1020}}},
    ]
    cue_config = {**DEFAULT_CONFIG, "brake": {"enabled": True, "priority": 1}}
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50, cue_config=cue_config)
    brakes = [e for e in plan["events"] if e["cue"] == "brake"]
    assert [e["distance"] for e in brakes] == [1000]
    assert not any(e["cue"] == "throttle_on" for e in plan["events"])


# ── _cue_cfg: config resuelta, sin literales duplicados (Reviewer WS-2) ───────


def test_cue_cfg_resuelve_config_completa():
    """_cue_cfg devuelve el dict COMPLETO (enabled + priority + demas campos)
    de DEFAULT_CONFIG mezclado con el override; una clave ausente en el
    override cae al default sin perder el resto de los campos del tipo."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, _cue_cfg

    assert _cue_cfg(None, "turn_in") == DEFAULT_CONFIG["turn_in"]
    assert _cue_cfg({"turn_in": {"priority": None}}, "turn_in") == DEFAULT_CONFIG["turn_in"]
    assert _cue_cfg({"turn_in": {"priority": 999}}, "turn_in") == {
        "enabled": True,
        "priority": 999,
    }
    # coast trae un campo extra (solo_sin_frenada): un override que solo toca
    # priority no debe perderlo.
    resolved = _cue_cfg({"coast": {"priority": 10}}, "coast")
    assert resolved == {"enabled": False, "priority": 10, "solo_sin_frenada": True}


def test_cue_cfg_priority_none_no_crashea_el_sort_de_la_cabida():
    """Un cue_config con priority=None (p.ej. una UI que manda 'usa el
    default') no debe crashear sorted(..., key=lambda c: -c['priority']); cae
    al valor de DEFAULT_CONFIG (60 para turn_in) en vez de None."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"turn_in": {"d": 1000}}}]
    cue_config = {**DEFAULT_CONFIG, "turn_in": {"enabled": True, "priority": None}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    turn_events = [e for e in plan["events"] if e["cue"] == "turn_in"]
    assert turn_events and turn_events[0]["priority"] == 60


# ── Countdown wireado: enabled gatea, priority reemplaza el 100 (WS-2) ───────


def test_countdown_deshabilitado_omite_tics_pero_la_frenada_sigue():
    """brake_countdown.enabled=False apaga los tics del countdown, pero el
    tono de frenada protegido sigue sonando intacto: el countdown se apaga,
    la frenada no (decision del PO)."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]

    cue_config = {**DEFAULT_CONFIG, "brake_countdown": {"enabled": False, "priority": 100}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    assert not any(e["cue"] == "brake_tic" for e in plan["events"])
    brakes = [e for e in plan["events"] if e["cue"] == "brake"]
    assert brakes and brakes[0]["distance"] == 2000 and brakes[0].get("protected")


def test_countdown_priority_configurable_se_refleja_en_los_tics():
    """brake_countdown.priority reemplaza el 100 hardcodeado: el campo
    priority de cada brake_tic generado en el plan sale de cue_config, no de
    un literal fijo en plan_tone_events."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]

    cue_config = {**DEFAULT_CONFIG, "brake_countdown": {"enabled": True, "priority": 42}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    tics = [e for e in plan["events"] if e["cue"] == "brake_tic"]
    assert len(tics) == 2
    assert all(t["priority"] == 42 for t in tics)
