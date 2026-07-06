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
