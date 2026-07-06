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
    assert any(e["cue"] == "brake_countdown" for e in selected)
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


def test_countdown_antes_de_la_meta_cae_a_brake_plano():
    """Si el anticipo del countdown caeria en d<=0 (curva pegada a la meta), la
    curva NO se queda muda ni suena en el segundo 0: cae al tono de frenada
    plano en el punto real de frenada (Reviewer sobre ADR 0024)."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    # brake a 100 m sin v -> fallback countdown_m=120 -> el countdown caeria en -20 m
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 100}}}]
    plan = plan_tone_events(rows, corners, top=1)
    assert all(e["distance"] > 0 for e in plan["events"])
    brakes = [e for e in plan["events"] if e["cue"] == "brake"]
    assert brakes and brakes[0]["distance"] == 100
    assert not any(e["cue"] == "brake_countdown" for e in plan["events"])


def test_plan_gap_global_entre_curvas_gana_prioridad():
    """El gap minimo tambien aplica ENTRE curvas: en encadenadas quedaban cues a
    <1 s de distancia (sopa de tonos). Sobrevive el de mayor prioridad."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.3, "flags": "vmin"},
        {"id": "C02", "name": "C02", "time_lost": 0.1, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"apex": {"d": 1000}}},
        {"id": "C02", "name": "C02", "milestones": {"brake_start": {"d": 1030}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    # apex (prioridad 90) sobrevive; la frenada de la curva vecina (80) se descarta
    assert [e["distance"] for e in plan["events"]] == [1000]
    assert any(
        s["reason"] == "too_close_global" and s["distance"] == 1030 for s in plan["skipped_global"]
    )
    # plan.json reconciliado: el cue descartado globalmente NO queda en el
    # "selected" de su curva (selected == WAVs generados), sino en su skipped
    c02 = next(c for c in plan["corners"] if c["id"] == "C02")
    assert not any(s["distance"] == 1030 for s in c02["selected"])
    assert any(s["distance"] == 1030 and s["reason"] == "too_close_global" for s in c02["skipped"])


def test_plan_legacy_tiene_mismo_esquema():
    """El plan legacy (smart=False) expone skipped_global vacio: mismo esquema."""
    from fantasma.viz.pacenotes import _legacy_tone_events

    plan = _legacy_tone_events([], [], 5, ["brake"])
    assert plan["skipped_global"] == []


def test_countdown_anticipa_por_tiempo_con_v():
    """Con v en el milestone, el anticipo es countdown_s segundos a esa velocidad
    (216 km/h = 60 m/s -> 3.5 s = 210 m), no los 120 m fijos. El evento se ancla
    en la FRENADA (el ultimo tono es el "¡ya!"; PO 2026-07-06) y lleva el
    anticipo en lead_m para que build_tone_pack expanda los tics."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]
    plan = plan_tone_events(rows, corners, top=1, countdown_s=3.5)
    assert plan["events"][0]["cue"] == "brake_countdown"
    assert plan["events"][0]["distance"] == 2000
    assert plan["events"][0]["lead_m"] == 210


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


def _write_pack(tmp_path, entries):
    import json

    (tmp_path / "metadata.json").write_text(
        json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8"
    )
    return str(tmp_path)


def test_build_cue_ass_rotula_cada_cue(tmp_path, lap_factory):
    """build_cue_ass emite un Dialogue por cue, con su etiqueta, color y leyenda."""
    from fantasma.viz.pacenotes import (
        CUE_SUB_COLORS,
        _metadata_entry,
        build_cue_ass,
    )

    lap = lap_factory(length_m=1500.0)
    entries = [
        _metadata_entry("Curva 1", "brake", 400, "400_0.wav"),
        _metadata_entry("Curva 2", "throttle_on", 1000, "1000_0.wav"),
    ]
    pack = _write_pack(tmp_path, entries)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    assert "PlayResX: 1024" in ass and "PlayResY: 1024" in ass
    # un rotulo por cue: etiqueta + nombre de curva
    assert "punto de frenada" in ass
    assert "inicio de acelerador" in ass
    assert "Curva 1" in ass and "Curva 2" in ass
    # color por tipo y leyenda solo con las etiquetas que suenan
    assert CUE_SUB_COLORS["punto de frenada"] in ass
    assert "LEYENDA DE SONIDOS" in ass
    # dos cues -> dos lineas Dialogue de estilo Cue (+ la leyenda)
    assert ass.count("Dialogue: 0,") == 3


def test_build_cue_ass_sincroniza_con_el_tono(tmp_path, lap_factory):
    """El tiempo del rotulo usa _dist_to_time igual que el audio del cue."""
    from fantasma.viz.pacenotes import _dist_to_time, _metadata_entry, build_cue_ass

    lap = lap_factory(length_m=1500.0)
    entries = [_metadata_entry("Curva 1", "brake", 400, "400_0.wav")]
    pack = _write_pack(tmp_path, entries)
    t = _dist_to_time(lap, 400.0)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    # El Dialogue de la curva arranca ~0.15 s antes del tono (t-0.15).
    h, m, s = int((t - 0.15) // 3600), int(((t - 0.15) % 3600) // 60), (t - 0.15) % 60
    esperado = "%d:%02d:%05.2f" % (h, m, s)
    assert esperado in ass


def test_build_cue_ass_sin_entradas_no_rotula(tmp_path, lap_factory):
    """Un pack sin cues no tiene nada que rotular -> None (no se quema nada)."""
    from fantasma.viz.pacenotes import build_cue_ass

    lap = lap_factory(length_m=1500.0)
    pack = _write_pack(tmp_path, [])

    assert build_cue_ass(pack, lap, 1024, 1024) is None
