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
    # trazabilidad (D1): el tic omitido antes de la meta deja rastro en
    # skipped_global (antes se perdia con un `continue` mudo y plan.json mentia).
    skipped_tics = [s for s in plan["skipped_global"] if s["cue"] == "brake_tic"]
    assert any(s["reason"] == "antes_de_la_meta" and s["distance"] <= 0 for s in skipped_tics)


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
    <min_gap de otro sonido. Formula-agnostico: no hardcodea distancias de tic,
    solo los invariantes (cabida y que no se pierda ninguna frenada)."""
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
    for tic in tics:
        # excluye la frenada de SU MISMA curva: es un solo grupo cohesivo
        # (ADR 0026) y con el countdown uniforme (0.75 s) el gap tic->propia
        # frenada es, A PROPOSITO, menor que min_gap_m — la cabida se exige
        # solo contra sonidos de OTRAS curvas.
        others = [
            e["distance"]
            for e in events
            if e["distance"] != tic["distance"] and e["corner_id"] != tic["corner_id"]
        ]
        assert all(abs(tic["distance"] - o) >= 50 for o in others)
    # se omitieron tics: los 4 (2 por curva) no caben sin encimarse
    assert len(tics) < 4


def test_countdown_tics_no_se_autorrechazan_contra_su_propia_frenada():
    """Regresion: con lead_m < 2*min_gap_m (curvas lentas), el tic step=1
    (brake_d - lead_m/2) caia a <min_gap_m de SU PROPIA frenada y se perdia
    aunque no compitiera con ningun otro sonido. El tono de frenada y sus 2
    tics son un solo grupo cohesivo (ADR 0026): la cabida se chequea contra
    OTROS sonidos, nunca contra el propio grupo."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    # v=90 km/h -> lead_m=90/3.6*0.75*2=37.5, redondeado a 38 (< 2*min_gap_m=100):
    # sin la exclusion de grupo, el tic step=1 (2000-19=1981) caia a 19 m de
    # la frenada (<50) y se descartaria pese a no competir con nada mas.
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 90}}}]
    plan = plan_tone_events(rows, corners, top=1)
    brake = next(e for e in plan["events"] if e["cue"] == "brake")
    assert brake["distance"] == 2000
    assert brake["lead_m"] == 38
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1962, 1981]


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
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}},
        # throttle_on de C00 a 10 m del tic step=0 de C01 (1910): se descarta
        # por cabida contra OTRA curva; el step=1 (1955), a 55 m, si cabe y
        # sobrevive.
        {"id": "C00", "name": "C00", "milestones": {"throttle_on": {"d": 1900}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1955]


def test_countdown_tic_sin_espacio_deja_rastro_con_el_evento_que_lo_choco():
    """Trazabilidad (D1): un tic descartado por cabida no desaparece en silencio
    — aparece en skipped_global con reason 'tic_sin_espacio' y CONTRA que evento
    choco (cue, corner_id, distancia), para que el PO pueda auditarlo. NO entra
    en plan['events'] (la fuente de verdad de lo que se renderiza)."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C00", "name": "C00", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}},
        # throttle_on de C00 a 10 m del tic step=0 de C01 (1910): lo descarta.
        {"id": "C00", "name": "C00", "milestones": {"throttle_on": {"d": 1900}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    assert not any(e["cue"] == "brake_tic" and e["distance"] == 1910 for e in plan["events"])
    skipped = [
        s for s in plan["skipped_global"] if s["cue"] == "brake_tic" and s["distance"] == 1910
    ]
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "tic_sin_espacio"
    assert skipped[0]["against"] == {
        "corner_id": "C00",
        "cue": "throttle_on",
        "distance": 1900,
    }


def test_countdown_tic_vs_tic_reporta_el_tic_que_lo_choco_no_la_frenada():
    """Trazabilidad (D1) cuando el estorbo es OTRO tic, no una frenada de `kept`.

    Dos curvas protegidas y pegadas (frenadas en 3000 y 2995, ambas a 216 km/h ->
    lead_m=90) generan tics en 2905/2950 (C02) y 2910/2955 (C01). El tic de C01 en
    2910 choca a 5 m contra el tic YA ACEPTADO de C02 en 2905. `against` debe
    describir ESE tic (cue 'brake_tic', distancia 2905), no la frenada de C02 en
    2995. Con el bug (indexar por own_idx a `kept`) reportaba brake@2995: un cue
    equivocado a 90 m de la distancia real del estorbo."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C02", "name": "C02", "time_lost": 0.5, "flags": "frenada"},
    ]
    corners = [
        {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 3000, "v": 216}}},
        {"id": "C02", "name": "C02", "milestones": {"brake_start": {"d": 2995, "v": 216}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    assert not any(e["cue"] == "brake_tic" and e["distance"] == 2910 for e in plan["events"])
    skipped = [
        s for s in plan["skipped_global"] if s["cue"] == "brake_tic" and s["distance"] == 2910
    ]
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "tic_sin_espacio"
    assert skipped[0]["against"] == {
        "corner_id": "C02",
        "cue": "brake_tic",
        "distance": 2905,
    }


def test_plan_legacy_tiene_mismo_esquema():
    """El plan legacy (smart=False) expone skipped_global vacio: mismo esquema."""
    from fantasma.viz.pacenotes import _legacy_tone_events

    plan = _legacy_tone_events([], [], 5, ["brake"])
    assert plan["skipped_global"] == []


def test_countdown_anticipa_por_tiempo_con_v():
    """Con v en el milestone, el anticipo es POR TIEMPO a esa velocidad: 2
    gaps de DEFAULT_COUNTDOWN_GAP_S segundos cada uno (216 km/h = 60 m/s ->
    0.75 s = 45 m por gap -> lead_m=90), no los 120 m fijos. La frenada se
    ancla en su punto real (protegida) y lleva el anticipo en lead_m; los
    tics se colocan a lead_m y lead_m/2 antes — dos gaps de exactamente el
    mismo tamano (lead_m/2 cada uno), sin importar el clamp."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]
    plan = plan_tone_events(rows, corners, top=1)
    brake = next(e for e in plan["events"] if e["cue"] == "brake")
    assert brake["distance"] == 2000
    assert brake["lead_m"] == 90
    assert brake.get("protected")
    # 2 tics de aviso antes de la frenada, en brake_d - lead_m y brake_d - lead_m/2
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1910, 1955]
    # los dos gaps (tic0->tic1, tic1->frenada) son iguales: countdown uniforme
    assert tics[1] - tics[0] == brake["distance"] - tics[1]
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
        (1910, "contador de frenada"),
        (1955, "contador de frenada"),
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
        # throttle_on de C00 a 30 m del tic 0 de C01 (1910): el tic se omite
        {"id": "C00", "name": "C00", "milestones": {"throttle_on": {"d": 1880}}},
    ]
    build_tone_pack(rows, corners, str(tmp_path), top=0)
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    dists = {e["distanceRoundTrack"]: e["description"] for e in entries}
    assert 1910 not in dists
    assert "contador de frenada" in dists[1955]
    assert "punto de frenada" in dists[2000]


def test_countdown_lead_clamps_y_fallback():
    from fantasma.viz.pacenotes import DEFAULT_COUNTDOWN_GAP_S, _countdown_lead_m

    # 36 km/h -> 10 m/s * 0.75 s * 2 = 15 m -> clamp al minimo de 30 m
    assert _countdown_lead_m({"v": 36}, 120, DEFAULT_COUNTDOWN_GAP_S) == 30
    # 700 km/h -> 194.4 m/s * 0.75 s * 2 = 291.7 m -> clamp al maximo de 250 m
    assert _countdown_lead_m({"v": 700}, 120, DEFAULT_COUNTDOWN_GAP_S) == 250
    # sin v (corners viejos, tests sinteticos) -> fallback al countdown_m fijo
    assert _countdown_lead_m({"d": 500}, 120, DEFAULT_COUNTDOWN_GAP_S) == 120


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
        "brake": 100,
        "brake_tic": 50,
        "brake_release": 45,
        "turn_in": 70,
        "throttle_on": 95,
        "full_throttle": 90,
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
    """gear esta apagado por defecto (DEFAULT_CONFIG) y NO se detecta desde un
    milestone de la curva: sus eventos salen exclusivamente del parametro
    `gear_shifts` de plan_tone_events (detect_gear_shifts, lap-wide), nunca de
    `_corner_candidates`. Un milestone 'gear' colgado de una curva no genera
    ningun candidato de tipo gear, con o sin cue_config habilitado."""
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
        "sound": True,
    }
    # coast trae un campo extra (solo_sin_frenada): un override que solo toca
    # priority no debe perderlo.
    resolved = _cue_cfg({"coast": {"priority": 10}}, "coast")
    assert resolved == {
        "enabled": False,
        "priority": 10,
        "solo_sin_frenada": True,
        "sound": True,
    }


def test_cue_cfg_priority_none_no_crashea_el_sort_de_la_cabida():
    """Un cue_config con priority=None (p.ej. una UI que manda 'usa el
    default') no debe crashear sorted(..., key=lambda c: -c['priority']); cae
    al valor de DEFAULT_CONFIG (70 para turn_in) en vez de None."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"turn_in": {"d": 1000}}}]
    cue_config = {**DEFAULT_CONFIG, "turn_in": {"enabled": True, "priority": None}}
    plan = plan_tone_events(rows, corners, top=1, cue_config=cue_config)
    turn_events = [e for e in plan["events"] if e["cue"] == "turn_in"]
    assert turn_events and turn_events[0]["priority"] == 70


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


def _write_cue_pack(tmp_path, entries):
    """Escribe un metadata.json de pack para probar build_cue_ass."""
    import json

    (tmp_path / "metadata.json").write_text(
        json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8"
    )
    return str(tmp_path)


def test_build_cue_ass_rotula_cada_cue(tmp_path, lap_factory):
    """build_cue_ass emite un Dialogue por cue, con su etiqueta, color y leyenda."""
    from fantasma.viz.pacenotes import CUE_SUB_COLORS, _metadata_entry, build_cue_ass

    lap = lap_factory(length_m=1500.0)
    entries = [
        _metadata_entry("Curva 1", "brake", 400, "400_0.wav"),
        _metadata_entry("Curva 2", "throttle_on", 1000, "1000_0.wav"),
    ]
    pack = _write_cue_pack(tmp_path, entries)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    assert "PlayResX: 1024" in ass and "PlayResY: 1024" in ass
    assert "punto de frenada" in ass
    assert "inicio de acelerador" in ass
    assert "Curva 1" in ass and "Curva 2" in ass
    assert CUE_SUB_COLORS["punto de frenada"] in ass
    assert "LEYENDA DE SONIDOS" in ass
    # dos cues -> dos Dialogue de estilo Cue (+ la leyenda)
    assert ass.count("Dialogue: 0,") == 3


def test_build_cue_ass_sincroniza_con_el_tono(tmp_path, lap_factory):
    """El tiempo del rotulo usa _dist_to_time igual que el audio (t - LEAD)."""
    from fantasma.viz.pacenotes import (
        CUE_SUB_LEAD_S,
        _ass_time,
        _dist_to_time,
        _metadata_entry,
        build_cue_ass,
    )

    lap = lap_factory(length_m=1500.0)
    entries = [_metadata_entry("Curva 1", "brake", 400, "400_0.wav")]
    pack = _write_cue_pack(tmp_path, entries)
    t = _dist_to_time(lap, 400.0)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    assert _ass_time(t - CUE_SUB_LEAD_S) in ass


def test_build_cue_ass_ventana_adaptativa(tmp_path, lap_factory):
    """La duracion del rotulo se estira hasta el siguiente cue (acotada por
    MIN/MAX), no la ventana fija de 1.5 s de la #32.

    Con dos cues, el fin del primero es min(t2 - GAP, t1 + MAX) acotado a >=
    t1 + MIN; el segundo (sin siguiente) dura hasta t2 + MAX.
    """
    from fantasma.viz.pacenotes import (
        CUE_SUB_GAP_S,
        CUE_SUB_MAX_S,
        CUE_SUB_MIN_S,
        _ass_time,
        _dist_to_time,
        _metadata_entry,
        build_cue_ass,
    )

    lap = lap_factory(length_m=1500.0)
    entries = [
        _metadata_entry("Curva 1", "brake", 400, "400_0.wav"),
        _metadata_entry("Curva 2", "throttle_on", 460, "460_0.wav"),
    ]
    pack = _write_cue_pack(tmp_path, entries)
    t1 = _dist_to_time(lap, 400.0)
    t2 = _dist_to_time(lap, 460.0)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    end1 = max(t1 + CUE_SUB_MIN_S, min(t2 - CUE_SUB_GAP_S, t1 + CUE_SUB_MAX_S))
    end2 = min(t2 + CUE_SUB_MAX_S, lap.laptime)
    assert _ass_time(end1) in ass
    assert _ass_time(end2) in ass
    # ya no es la ventana fija de la #32
    assert _ass_time(t1 + 1.35) not in ass


def test_build_cue_ass_coast_rotula_inercia(tmp_path, lap_factory):
    """Un cue coast se rotula 'inercia' con su color propio (catalogo WS-1/WS-2)."""
    from fantasma.viz.pacenotes import CUE_SUB_COLORS, _metadata_entry, build_cue_ass

    lap = lap_factory(length_m=1500.0)
    entries = [_metadata_entry("Curva 3", "coast", 700, "700_0.wav")]
    pack = _write_cue_pack(tmp_path, entries)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    assert "inercia" in ass
    assert CUE_SUB_COLORS["inercia"] in ass


def test_build_cue_ass_sin_entradas_no_rotula(tmp_path, lap_factory):
    """Un pack sin cues no tiene nada que rotular -> None."""
    from fantasma.viz.pacenotes import build_cue_ass

    lap = lap_factory(length_m=1500.0)
    pack = _write_cue_pack(tmp_path, [])

    assert build_cue_ass(pack, lap, 1024, 1024) is None


# ── Reencuadre de prioridades (QA 2026-07-08): freno/gas arriba, turn_in su ──
# ── propio escalon, countdown/soltar-freno/coast oportunistas ────────────────


def test_turn_in_gana_a_brake_release_en_saturacion_por_prioridad():
    """Con la tabla nueva turn_in=70 > brake_release=45: en una saturacion
    global entre ambos, turn_in se queda con el hueco y brake_release cae."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C_release", "name": "C_release", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C_turn", "name": "C_turn", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C_release", "name": "C_release", "milestones": {"brake_release": {"d": 1000}}},
        # a 20 m de brake_release (<50): compiten por el mismo hueco
        {"id": "C_turn", "name": "C_turn", "milestones": {"turn_in": {"d": 1020}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    assert any(e["cue"] == "turn_in" for e in plan["events"])
    assert not any(e["cue"] == "brake_release" for e in plan["events"])
    assert any(
        s["cue"] == "brake_release" and s["reason"] == "too_close_global"
        for s in plan["skipped_global"]
    )


def test_turn_in_ya_colocado_bloquea_los_tics_del_countdown_cercano():
    """Un turn_in de otra curva, ya asentado en 'kept', bloquea AMBOS tics del
    countdown de una frenada vecina si caen a <min_gap_m -- el freno protegido
    (el "ya") no se ve afectado."""
    from fantasma.viz.pacenotes import plan_tone_events

    rows = [
        {"id": "C_brake", "name": "C_brake", "time_lost": 0.5, "flags": "frenada"},
        {"id": "C_turn", "name": "C_turn", "time_lost": 0.5, "flags": ""},
    ]
    corners = [
        {"id": "C_brake", "name": "C_brake", "milestones": {"brake_start": {"d": 2000, "v": 216}}},
        # lead_m=90 -> tics candidatos en 1910 y 1955; turn_in en 1950 cae a
        # <50 m de AMBOS.
        {"id": "C_turn", "name": "C_turn", "milestones": {"turn_in": {"d": 1950}}},
    ]
    plan = plan_tone_events(rows, corners, top=2, min_gap_m=50)
    assert any(e["cue"] == "turn_in" and e["distance"] == 1950 for e in plan["events"])
    assert any(e["cue"] == "brake" and e["distance"] == 2000 for e in plan["events"])
    assert not any(e["cue"] == "brake_tic" for e in plan["events"])


def test_countdown_gap_uniforme_en_dos_velocidades():
    """El gap tic0->tic1 y el gap tic1->frenada son EXACTAMENTE iguales entre
    si (tolerancia +-1m por redondeo), en dos velocidades distintas -- el
    countdown de frenada suena parejo sin importar que tan rapido se llegue."""
    from fantasma.viz.pacenotes import plan_tone_events

    for v, brake_d in ((90, 2000), (216, 2000)):
        rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
        corners = [
            {"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": brake_d, "v": v}}}
        ]
        plan = plan_tone_events(rows, corners, top=1)
        tic0, tic1 = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
        gap0 = tic1 - tic0
        gap1 = brake_d - tic1
        assert abs(gap0 - gap1) <= 1, "v=%s: gap0=%s gap1=%s" % (v, gap0, gap1)


# ── Cue "gear" (cambio de marcha, solo subtitulo) — detect_gear_shifts wireado ─


def test_plan_tone_events_gear_shifts_genera_eventos_gear():
    """gear_shifts se mergea a la lista de candidatos y participa en la MISMA
    resolucion de cabida/prioridad global: los eventos "gear" salen con la
    prioridad configurada (75 por defecto)."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    assert DEFAULT_CONFIG["gear"]["priority"] == 75
    gear_shifts = [
        {"distance": 500, "gear_from": 2, "gear_to": 3},
        {"distance": 900, "gear_from": 3, "gear_to": 4},
    ]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events([], [], top=5, cue_config=cue_config, gear_shifts=gear_shifts)
    gear_events = sorted(e["distance"] for e in plan["events"] if e["cue"] == "gear")
    assert gear_events == [500, 900]
    priorities = {e["priority"] for e in plan["events"] if e["cue"] == "gear"}
    assert priorities == {75}


def test_gear_shift_event_gs_malformado_se_descarta_sin_crashear():
    """_gear_shift_event es la frontera contra gear_shifts malformado (p.ej.
    un corners_detected.json viejo o editado a mano sin "distance"/"gear_to"):
    devuelve None en vez de KeyError -- mismo espiritu defensivo que
    cue_profiles.py con perfiles de terceros."""
    from fantasma.viz.pacenotes import _gear_shift_event

    assert _gear_shift_event({"gear_to": 3}, 75) is None  # sin "distance"
    assert _gear_shift_event({"distance": 500}, 75) is None  # sin "gear_to"
    assert _gear_shift_event({"distance": 500, "gear_to": None}, 75) is None
    assert _gear_shift_event({"distance": "no-numero", "gear_to": 3}, 75) is None
    assert _gear_shift_event({"distance": 500, "gear_to": "no-numero"}, 75) is None
    # una entrada valida si construye el evento normalmente
    ok = _gear_shift_event({"distance": 500, "gear_to": 3}, 75)
    assert ok is not None
    assert ok["distance"] == 500 and ok["cue"] == "gear"


def test_plan_tone_events_gear_shifts_con_entradas_malformadas_no_crashea():
    """plan_tone_events con un gear_shifts que trae entradas malformadas
    (sin las claves de detect_gear_shifts) descarta esas entradas y sigue
    generando las validas -- no revienta el pack completo por una entrada
    corrupta."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    gear_shifts = [
        {"distance": 500, "gear_from": 2, "gear_to": 3},  # valida
        {"distance": 900},  # sin gear_to: se descarta
        {"gear_to": 4},  # sin distance: se descarta
        {"distance": "x", "gear_to": 5},  # distance no numerica: se descarta
    ]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events([], [], top=5, cue_config=cue_config, gear_shifts=gear_shifts)
    gear_events = [e for e in plan["events"] if e["cue"] == "gear"]
    assert len(gear_events) == 1
    assert gear_events[0]["distance"] == 500


def test_plan_tone_events_gear_shift_distance_no_positiva_se_descarta():
    """Mismo guard que el resto de candidatos (linea ~267, 'antes_de_la_meta'):
    un cambio de marcha con distance<=0 (dato malformado o curva pegada a la
    meta) se descarta, no se clampea a 0 -- un cue en t=0 del video suena
    aleatorio (QA 2026-07-05)."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    gear_shifts = [
        {"distance": 0, "gear_from": 1, "gear_to": 2},
        {"distance": -10, "gear_from": 2, "gear_to": 3},
        {"distance": 500, "gear_from": 3, "gear_to": 4},
    ]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events([], [], top=5, cue_config=cue_config, gear_shifts=gear_shifts)
    gear_events = [e for e in plan["events"] if e["cue"] == "gear"]
    assert len(gear_events) == 1
    assert gear_events[0]["distance"] == 500


def test_default_freqs_tiene_entrada_gear_sin_colisionar():
    """DEFAULT_FREQS trae "gear" (gear=False por sound en el catalogo, pero
    un perfil de terceros puede forzar sound=true via cue_profiles.py): sin
    esta entrada, _render_cue caeria al fallback de 440 Hz, casi pegado a
    apex (400 Hz) y reabriendo la colision de frecuencias que este cambio
    corrige para el resto del catalogo."""
    from fantasma.viz.pacenotes import DEFAULT_FREQS

    assert "gear" in DEFAULT_FREQS
    freqs = list(DEFAULT_FREQS.values())
    # unica: no coincide exacto con ninguna otra frecuencia del catalogo
    assert freqs.count(DEFAULT_FREQS["gear"]) == 1
    # bien separada (ratio >= 1.14, mismo criterio que el resto de la tabla)
    # de sus dos vecinas mas cercanas en la escala.
    others = sorted(f for f in freqs if f != DEFAULT_FREQS["gear"])
    gear_f = DEFAULT_FREQS["gear"]
    neighbor_below = max((f for f in others if f < gear_f), default=None)
    neighbor_above = min((f for f in others if f > gear_f), default=None)
    if neighbor_below:
        assert gear_f / neighbor_below >= 1.14
    if neighbor_above:
        assert neighbor_above / gear_f >= 1.14


def test_render_cue_gear_con_sound_forzado_usa_default_freqs_no_fallback(monkeypatch):
    """Si un perfil de terceros fuerza sound=true para gear, _render_cue debe
    sonar a DEFAULT_FREQS["gear"], no al fallback generico de 440 Hz (que
    "apex" SI usa a proposito por no tener entrada propia)."""
    import fantasma.viz.pacenotes as pacenotes_mod
    from fantasma.viz.pacenotes import DEFAULT_FREQS, _render_cue

    captured = {}

    def _fake_generate_tone(freq_hz, duration_s, volume=0.8, sample_rate=24000):
        captured["freq_hz"] = freq_hz
        return b"RIFF"

    monkeypatch.setattr(pacenotes_mod, "generate_tone", _fake_generate_tone)

    _render_cue({"cue": "gear", "distance": 500}, DEFAULT_FREQS, 0.1, 0.8)

    assert captured["freq_hz"] == DEFAULT_FREQS["gear"]
    assert captured["freq_hz"] != 440


def test_plan_tone_events_gear_apagado_por_defecto_no_genera_nada():
    """Sin habilitar 'gear' en cue_config, un gear_shifts no vacio no produce
    ningun evento (no-regresion: gear sigue apagado por defecto)."""
    from fantasma.viz.pacenotes import plan_tone_events

    gear_shifts = [{"distance": 500, "gear_from": 2, "gear_to": 3}]
    plan = plan_tone_events([], [], top=5, gear_shifts=gear_shifts)
    assert not any(e["cue"] == "gear" for e in plan["events"])


def test_plan_tone_events_gear_shift_no_compite_por_cabida_de_audio():
    """Un cambio de marcha (mudo, sound=False) cerca de un cue de AUDIO
    (throttle_on) no le quita el hueco ni lo pierde el mismo -- la cabida
    global (min_gap_m) es una regla de MEZCLA DE AUDIO (evitar sopa de
    tonos), y gear no suena. Regresion real (QA 2026-07-08): con gear
    compitiendo por cabida contra cues de audio, activar "gear" + "Coast"
    juntos en la cinta de estudio vacio por completo los eventos de coast
    en zonas sin relacion con ningun cambio de marcha."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": ""}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"throttle_on": {"d": 1020}}}]
    gear_shifts = [{"distance": 1000, "gear_from": 2, "gear_to": 3}]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events(
        rows, corners, top=1, min_gap_m=50, cue_config=cue_config, gear_shifts=gear_shifts
    )
    assert any(e["cue"] == "throttle_on" for e in plan["events"])
    assert any(e["cue"] == "gear" for e in plan["events"])
    assert not any(s["cue"] in ("gear", "throttle_on") for s in plan["skipped_global"])


def test_plan_tone_events_gear_shifts_cercanos_resuelven_cabida_entre_si():
    """Dos cambios de marcha mudos a <min_gap_m entre si SI compiten por
    cabida -- entre ellos (rachas de bajada de cambios en una frenada fuerte
    quedarian con subtitulos amontonados sin este corte), aunque ninguno
    compita contra cues de audio."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    gear_shifts = [
        {"distance": 1000, "gear_from": 4, "gear_to": 3},
        {"distance": 1020, "gear_from": 3, "gear_to": 2},
    ]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events(
        [], [], top=5, min_gap_m=50, cue_config=cue_config, gear_shifts=gear_shifts
    )
    gear_events = [e for e in plan["events"] if e["cue"] == "gear"]
    assert len(gear_events) == 1
    assert any(
        s["cue"] == "gear" and s["reason"] == "too_close_global" for s in plan["skipped_global"]
    )


def test_plan_tone_events_gear_no_bloquea_tic_de_countdown():
    """Un cambio de marcha mudo justo en la distancia de un tic de countdown
    candidato NO lo tira -- el countdown SI suena, asi que solo debe medirse
    contra otros sonidos (mismo principio del split sound/silent, encontrado
    por el Reviewer un choke point mas abajo: la resolucion global ya no
    comparte pool con gear, pero el timeline del countdown seguia armandose
    con la lista completa sin filtrar)."""
    from fantasma.viz.pacenotes import DEFAULT_CONFIG, plan_tone_events

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 2000, "v": 216}}}]
    # v=216 con el gap default (0.75s) da lead_m=90 -> tics candidatos en
    # 1910 (step=0) y 1955 (step=1), ver test_pack_expande_countdown_...
    gear_shifts = [{"distance": 1910, "gear_from": 4, "gear_to": 3}]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    plan = plan_tone_events(
        rows, corners, top=1, min_gap_m=50, cue_config=cue_config, gear_shifts=gear_shifts
    )
    tics = sorted(e["distance"] for e in plan["events"] if e["cue"] == "brake_tic")
    assert tics == [1910, 1955]
    assert any(e["cue"] == "gear" and e["distance"] == 1910 for e in plan["events"])


def test_build_tone_pack_gear_sin_audio_pero_en_metadata(tmp_path):
    """gear (sound=False) no genera un WAV propio pero si queda en metadata.json
    para que build_cue_ass lo subtitule. Su entry referencia el silent.wav
    compartido (inaudible) en vez de listas vacias, que revientan CrewChief
    (issue #9)."""
    import json

    from fantasma.viz.pacenotes import DEFAULT_CONFIG, build_tone_pack

    gear_shifts = [{"distance": 500, "gear_from": 2, "gear_to": 3}]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    result = build_tone_pack(
        [], [], str(tmp_path), top=5, cue_config=cue_config, gear_shifts=gear_shifts
    )
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    gear_entries = [e for e in entries if "cambio de marcha" in e["description"]]
    assert len(gear_entries) == 1
    entry = gear_entries[0]
    assert entry["distanceRoundTrack"] == 500
    # NO listas vacias: alineadas, largo >= 1, y el WAV referenciado existe.
    assert entry["fileNames"] == entry["recordingNames"]
    assert len(entry["fileNames"]) >= 1
    for fname in entry["fileNames"]:
        assert (tmp_path / fname).exists()
    # gear no sintetiza un WAV propio (no hay 500_*.wav); usa el silent compartido.
    assert not list(tmp_path.glob("500_*.wav"))
    assert (tmp_path / "silent.wav").exists()
    assert result["entries"] == 1


def test_build_tone_pack_ningun_entry_con_listas_vacias(tmp_path):
    """Ningun entry del metadata.json puede quedar con recordingNames/fileNames
    vacias: getRandomRecordingName de CrewChief indexa recordingNames[0] sobre la
    lista vacia y mata el hilo (issue #9). Se cubre un pack MIXTO con cue sonoro
    (frenada) + cue mudo (gear)."""
    import json

    from fantasma.viz.pacenotes import DEFAULT_CONFIG, build_tone_pack

    rows = [{"name": "Curva 1", "apex_d": 500.0}]
    corners = [{"id": 1, "name": "Curva 1", "milestones": {"apex": {"d": 500.0}}}]
    gear_shifts = [{"distance": 500, "gear_from": 2, "gear_to": 3}]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    build_tone_pack(
        rows, corners, str(tmp_path), top=5, cue_config=cue_config, gear_shifts=gear_shifts
    )
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    assert entries, "el pack de prueba deberia producir al menos un entry"
    for entry in entries:
        assert len(entry["recordingNames"]) == len(entry["fileNames"]) >= 1, entry
        for fname in entry["fileNames"]:
            assert (tmp_path / fname).exists(), fname


def test_build_tone_pack_silent_wav_es_inaudible_y_valido(tmp_path):
    """El silent.wav que embarcan los cues mudos es un WAV mono 16-bit valido
    (cargable por CrewChief) y de amplitud CERO (inaudible): el video de estudio
    no debe sonar en el cue mudo."""
    import wave

    from fantasma.viz.pacenotes import DEFAULT_CONFIG, build_tone_pack

    gear_shifts = [{"distance": 500, "gear_from": 2, "gear_to": 3}]
    cue_config = {**DEFAULT_CONFIG, "gear": {"enabled": True, "priority": 75, "sound": False}}
    build_tone_pack([], [], str(tmp_path), top=5, cue_config=cue_config, gear_shifts=gear_shifts)
    silent = tmp_path / "silent.wav"
    assert silent.exists()
    with wave.open(str(silent), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        frames = wav.readframes(wav.getnframes())
    assert wav.getnframes() > 0
    assert set(frames) == {0}, "el silent.wav debe ser todo ceros (inaudible)"


def test_write_silent_wav_regenera_wav_corrupto(tmp_path):
    """Hardening #9: _write_silent_wav SIEMPRE escribe (ya no usa el guard
    `if not path.exists()`), igual que los WAV sonoros. Asi un silent.wav
    truncado/corrupto de una corrida interrumpida se regenera a un WAV valido
    en vez de quedar como el WAV-que-CrewChief-no-puede-cargar que #9 cierra.
    Con el viejo guard este test fallaba: el archivo existia y no se
    reescribia, dejando la cabecera truncada."""
    import wave

    from fantasma.viz.pacenotes import _SILENT_WAV_NAME, _write_silent_wav

    corrupt = tmp_path / _SILENT_WAV_NAME
    corrupt.write_bytes(b"RIFF\x00\x00")  # cabecera truncada: no cargable como WAV
    name = _write_silent_wav(tmp_path)
    assert name == _SILENT_WAV_NAME
    # Se regenero a un WAV mono 16-bit valido y de amplitud cero (inaudible).
    with wave.open(str(corrupt), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        frames = wav.readframes(wav.getnframes())
    assert wav.getnframes() > 0
    assert set(frames) == {0}


def test_build_cue_ass_gear_rotula_cambio_de_marcha(tmp_path, lap_factory):
    """Un cue gear se rotula 'cambio a 3ª' bajo la etiqueta 'cambio de
    marcha', con su color propio -- aunque no tenga WAV asociado."""
    from fantasma.viz.pacenotes import CUE_SUB_COLORS, _metadata_entry, build_cue_ass

    lap = lap_factory(length_m=1500.0)
    entries = [_metadata_entry("cambio a 3ª", "gear", 700, None)]
    pack = _write_cue_pack(tmp_path, entries)

    ass = build_cue_ass(pack, lap, 1024, 1024)

    assert "cambio de marcha" in ass
    assert "cambio a 3ª" in ass
    assert CUE_SUB_COLORS["cambio de marcha"] in ass


# ── build_voice_pack: mismo plan anti-saturacion que plan_tone_events ─────────
# (ADR 0024, enmienda "notas de voz" -- ROADMAP: "las notas de VOZ no pasan
# por el plan anti-saturacion"). edge_tts esta instalado en el entorno de
# CI/dev (extra [voice]), pero estos tests igual mockean Communicate.save y
# la conversion ffmpeg para no depender de red ni de un binario real.


class _FakeCommunicate:
    """Reemplaza edge_tts.Communicate: escribe un mp3 falso sin red."""

    def __init__(self, text, voice=None):
        self.text = text
        self.voice = voice

    async def save(self, path):
        from pathlib import Path

        Path(path).write_bytes(b"fake-mp3")


def _fake_ffmpeg_run(cmd, check=True, capture_output=True):
    """Reemplaza subprocess.run del paso mp3->wav: escribe un WAV valido
    minimo en la ruta de salida (ultimo argumento del comando ffmpeg)."""
    from pathlib import Path

    from fantasma.viz.pacenotes import generate_tone

    Path(cmd[-1]).write_bytes(generate_tone(440, 0.05))

    class _Result:
        returncode = 0

    return _Result()


def _mock_voice_deps(monkeypatch):
    """Mockea edge_tts (sin red) y ffmpeg (sin binario real) -- patron
    compartido por los tests de build_voice_pack de abajo."""
    import edge_tts

    import fantasma.viz.pacenotes as pacenotes_mod

    monkeypatch.setattr(edge_tts, "Communicate", _FakeCommunicate)
    monkeypatch.setattr(pacenotes_mod.subprocess, "run", _fake_ffmpeg_run)
    monkeypatch.setattr(pacenotes_mod.shutil, "which", lambda name: "/fake/ffmpeg")


def test_build_voice_pack_una_nota_por_curva(tmp_path, monkeypatch):
    """Con una sola curva top-N, build_voice_pack genera exactamente una nota
    de voz: el limite de 1 por curva es estructural (un candidato por fila,
    milestone de frenada), sin necesidad de un max_events_per_corner aparte."""
    _mock_voice_deps(monkeypatch)
    from fantasma.viz.pacenotes import build_voice_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 1000}}}]
    result = build_voice_pack(rows, corners, str(tmp_path), top=1)
    assert result["entries"] == 1
    assert len(list(tmp_path.glob("*.wav"))) == 1


def test_build_voice_pack_gap_global_descarta_la_narracion_mas_cercana(
    tmp_path, monkeypatch, capsys
):
    """Dos curvas con puntos de frenada MUY cercanos (a <DEFAULT_MIN_GAP_M
    tras el anticipo): el MISMO gap global que usa plan_tone_events descarta
    una de las dos narraciones en vez de generar ambas encimadas -- antes
    build_voice_pack no aplicaba ningun gap entre curvas."""
    _mock_voice_deps(monkeypatch)
    import json

    from fantasma.viz.pacenotes import build_voice_pack

    rows = [
        {"id": "A", "name": "A", "time_lost": 0.8, "flags": "frenada"},
        {"id": "B", "name": "B", "time_lost": 0.3, "flags": "frenada"},
    ]
    # sin "v": el anticipo cae al fallback fijo de 200 m para ambas -> las
    # distancias narradas (800 y 820) quedan a 20 m entre si (< 50 m default)
    corners = [
        {"id": "A", "name": "A", "milestones": {"brake": {"d": 1000}}},
        {"id": "B", "name": "B", "milestones": {"brake": {"d": 1020}}},
    ]
    result = build_voice_pack(rows, corners, str(tmp_path), top=2)
    assert result["entries"] == 1
    assert len(list(tmp_path.glob("*.wav"))) == 1
    # sobrevive la curva con mas tiempo perdido (A): mismo criterio de
    # prioridad que el resto del catalogo cuando dos cues colisionan.
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    assert entries[0]["description"].startswith("A ")
    assert "descartada" in capsys.readouterr().err


def test_build_voice_pack_curvas_lejanas_narran_ambas(tmp_path, monkeypatch):
    """Dos curvas separadas por mas del gap minimo global narran ambas, sin
    descartes -- el gap no recorta de mas cuando no hace falta."""
    _mock_voice_deps(monkeypatch)
    from fantasma.viz.pacenotes import build_voice_pack

    rows = [
        {"id": "A", "name": "A", "time_lost": 0.5, "flags": "frenada"},
        {"id": "B", "name": "B", "time_lost": 0.5, "flags": "frenada"},
    ]
    corners = [
        {"id": "A", "name": "A", "milestones": {"brake": {"d": 1000}}},
        {"id": "B", "name": "B", "milestones": {"brake": {"d": 3000}}},
    ]
    result = build_voice_pack(rows, corners, str(tmp_path), top=2)
    assert result["entries"] == 2
    assert len(list(tmp_path.glob("*.wav"))) == 2


def test_build_voice_pack_anticipo_por_tiempo_con_v(tmp_path, monkeypatch):
    """Con "v" en el milestone de frenada, el anticipo se deriva de la
    velocidad (mismo criterio que el countdown de tonos, _voice_lead_m) en
    vez del fijo de 200 m: 216 km/h = 60 m/s * 4.0 s (DEFAULT_VOICE_LEAD_S)
    = 240 m de anticipo -> nota en 2000-240=1760."""
    _mock_voice_deps(monkeypatch)
    import json

    from fantasma.viz.pacenotes import build_voice_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 2000, "v": 216}}}]
    build_voice_pack(rows, corners, str(tmp_path), top=1)
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    assert entries[0]["distanceRoundTrack"] == 1760


def test_build_voice_pack_sin_v_usa_fallback_fijo_200m(tmp_path, monkeypatch):
    """Sin "v" en el milestone (corners JSON viejos, tests sinteticos), el
    anticipo cae al fijo historico de 200 m -- no-regresion exacta con el
    comportamiento previo a este fix para fixtures sin canal de velocidad."""
    _mock_voice_deps(monkeypatch)
    import json

    from fantasma.viz.pacenotes import build_voice_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 1000}}}]
    build_voice_pack(rows, corners, str(tmp_path), top=1)
    entries = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))["entries"]
    assert entries[0]["distanceRoundTrack"] == 800


def test_build_voice_pack_sin_ffmpeg_no_genera_wav_ni_crashea(tmp_path, monkeypatch, capsys):
    """Sin ffmpeg disponible, build_voice_pack no revienta: devuelve
    entries=0 con metadata.json igual escrito, y un aviso en stderr (no un
    descarte silencioso que haga creer que edge-tts fallo)."""
    from fantasma.viz.pacenotes import build_voice_pack

    monkeypatch.setattr("shutil.which", lambda name: None)
    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 1000}}}]
    result = build_voice_pack(rows, corners, str(tmp_path), top=1)
    assert result["entries"] == 0
    assert (tmp_path / "metadata.json").exists()
    assert "ffmpeg" in capsys.readouterr().err


def test_build_voice_pack_sin_edge_tts_lanza_error_accionable(tmp_path, monkeypatch):
    """Sin edge-tts instalado (import fallido), build_voice_pack lanza un
    RuntimeError con el comando de instalacion en vez de un ImportError
    crudo -- la frontera se verifica ANTES de tocar filas o curvas."""
    import pytest

    from fantasma.viz.pacenotes import build_voice_pack

    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    with pytest.raises(RuntimeError, match="edge-tts"):
        build_voice_pack([], [], str(tmp_path), top=1)


def test_build_voice_pack_top_limita_curvas_igual_que_tone_pack(tmp_path, monkeypatch):
    """top=N sigue seleccionando las N curvas de mayor time_lost, mismo
    criterio (_top_rows) que build_tone_pack -- no cambia cuantas curvas
    narra por defecto."""
    _mock_voice_deps(monkeypatch)
    from fantasma.viz.pacenotes import build_voice_pack

    rows = [
        {"id": "A", "name": "A", "time_lost": 0.9, "flags": "frenada"},
        {"id": "B", "name": "B", "time_lost": 0.1, "flags": "frenada"},
    ]
    corners = [
        {"id": "A", "name": "A", "milestones": {"brake": {"d": 1000}}},
        {"id": "B", "name": "B", "milestones": {"brake": {"d": 5000}}},
    ]
    result = build_voice_pack(rows, corners, str(tmp_path), top=1)
    assert result["entries"] == 1
    entries_json = (tmp_path / "metadata.json").read_text(encoding="utf-8")
    assert "A " in entries_json
    assert "B " not in entries_json


def test_build_pack_mode_voice_wiring(tmp_path, monkeypatch):
    """build_pack(mode='voice') sigue despachando a build_voice_pack tal
    cual (wiring end-to-end, no solo la funcion aislada)."""
    _mock_voice_deps(monkeypatch)
    from fantasma.viz.pacenotes import build_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 1000}}}]
    result = build_pack(rows, corners, str(tmp_path), mode="voice", top=1)
    assert result["entries"] == 1
    assert len(list(tmp_path.glob("*.wav"))) == 1


def test_build_pack_mode_voice_reenvia_min_gap_m_y_voice_lead_s(tmp_path, monkeypatch):
    """build_pack(mode='voice', min_gap_m=..., voice_lead_s=...) reenvia esos
    kwargs a build_voice_pack -- antes se perdian en silencio (build_pack solo
    reenviaba 'lang'), dejando los nuevos parametros inalcanzables desde el
    punto de entrada publico."""
    _mock_voice_deps(monkeypatch)
    import fantasma.viz.pacenotes as pacenotes_mod
    from fantasma.viz.pacenotes import build_pack

    captured = {}
    real_build_voice_pack = pacenotes_mod.build_voice_pack

    def _spy(*args, **kwargs):
        captured.update(kwargs)
        return real_build_voice_pack(*args, **kwargs)

    monkeypatch.setattr(pacenotes_mod, "build_voice_pack", _spy)

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake": {"d": 1000}}}]
    build_pack(rows, corners, str(tmp_path), mode="voice", top=1, min_gap_m=99, voice_lead_s=2.5)
    assert captured["min_gap_m"] == 99
    assert captured["voice_lead_s"] == 2.5


def test_build_pack_mode_tones_ignora_kwargs_solo_de_voz(tmp_path):
    """build_pack(mode='tones', min_gap_m=..., voice_lead_s=...) no revienta:
    esos kwargs son especificos de build_voice_pack (que no participa en modo
    tones) y build_tone_pack no los acepta -- se descartan en silencio, igual
    criterio que 'lang' en este mismo modo."""
    from fantasma.viz.pacenotes import build_pack

    rows = [{"id": "C01", "name": "C01", "time_lost": 0.5, "flags": "frenada"}]
    corners = [{"id": "C01", "name": "C01", "milestones": {"brake_start": {"d": 1000}}}]
    result = build_pack(
        rows, corners, str(tmp_path), mode="tones", top=1, min_gap_m=99, voice_lead_s=2.5
    )
    assert result["entries"] >= 1


# ── Perfiles de sonido de los cues (QA 2026-07-09) ────────────────────────────


def _decode_wav(data):
    """(muestras float [-1,1], sample_rate) de un WAV mono 16-bit en bytes."""
    import io
    import wave

    import numpy as np

    with wave.open(io.BytesIO(data)) as w:
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0, rate


_PROFILE_ROWS = [{"id": "C01", "name": "C01", "time_lost": 0.6, "flags": "vmin+frenada"}]
_PROFILE_CORNERS = [
    {
        "id": "C01",
        "name": "C01",
        "milestones": {
            "brake_start": {"d": 1000, "v": 216},
            "brake_release": {"d": 1200},
            "turn_in": {"d": 1400},
            "throttle_on": {"d": 1800},
            "full_throttle": {"d": 2000},
        },
    }
]


def test_sound_profile_default_es_seno_byte_identico(tmp_path):
    """Requisito duro: sin `sound_profile` (o con 'seno') el pack es
    BYTE-IDENTICO. Se compara muestra por muestra el WAV de cada cue, no solo
    que 'no reviente'."""
    from fantasma.viz.pacenotes import DEFAULT_SOUND_PROFILE, build_tone_pack

    assert DEFAULT_SOUND_PROFILE == "seno"
    d_def = tmp_path / "default"
    d_seno = tmp_path / "seno"
    build_tone_pack(_PROFILE_ROWS, _PROFILE_CORNERS, str(d_def), top=1)
    build_tone_pack(_PROFILE_ROWS, _PROFILE_CORNERS, str(d_seno), top=1, sound_profile="seno")

    wavs_def = {p.name: p.read_bytes() for p in sorted(d_def.glob("*.wav"))}
    wavs_seno = {p.name: p.read_bytes() for p in sorted(d_seno.glob("*.wav"))}
    assert wavs_def and set(wavs_def) == set(wavs_seno)
    for name in wavs_def:
        assert wavs_def[name] == wavs_seno[name], (
            "el default no es byte-identico a 'seno': %s" % name
        )


def test_sound_profile_seno_reproduce_generate_tone_exacto():
    """El perfil 'seno' de _render_cue es exactamente generate_tone con la misma
    frecuencia/duracion de hoy (freno 0.12 s a brake, tic 0.08 s a
    brake_countdown*scale) — la evidencia byte a byte de que el default no cambio."""
    from fantasma.viz.pacenotes import (
        COUNTDOWN_SCALE,
        DEFAULT_FREQS,
        _render_cue,
        generate_tone,
    )

    freqs = dict(DEFAULT_FREQS)
    brake = _render_cue({"cue": "brake"}, freqs, 0.12, 0.8, sound_profile="seno")
    assert brake == generate_tone(DEFAULT_FREQS["brake"], 0.12, volume=0.8)

    tic = _render_cue({"cue": "brake_tic", "step": 1}, freqs, 0.12, 0.8, sound_profile="seno")
    assert tic == generate_tone(
        DEFAULT_FREQS["brake_countdown"] * COUNTDOWN_SCALE[1], 0.08, volume=0.8
    )


def test_cada_perfil_genera_wav_valido_sin_clipping(tmp_path):
    """timbre/ritmo/chirp generan un pack de WAVs validos y sin clipping (pico
    <= 1.0) para todos los cues que suenan."""
    import numpy as np

    from fantasma.viz.pacenotes import build_tone_pack

    for profile in ("timbre", "ritmo", "chirp"):
        outdir = tmp_path / profile
        result = build_tone_pack(
            _PROFILE_ROWS, _PROFILE_CORNERS, str(outdir), top=1, sound_profile=profile
        )
        assert result["entries"] >= 1
        wavs = list(outdir.glob("*.wav"))
        assert wavs, "el perfil %s no genero ningun WAV" % profile
        for wav in wavs:
            samples, rate = _decode_wav(wav.read_bytes())
            assert rate == 24000
            assert len(samples) > 0
            peak = float(np.max(np.abs(samples)))
            assert peak <= 1.0, "clipping en %s (%s): pico=%.3f" % (profile, wav.name, peak)


def test_cada_perfil_respeta_la_duracion_disenada():
    """Cada cue del catalogo de cada perfil produce un WAV con la duracion de
    diseno (la misma evidencia de qa_runs/2026-07-09-sonidos/)."""
    from fantasma.viz.pacenotes import DEFAULT_FREQS, _render_cue

    freqs = dict(DEFAULT_FREQS)
    esperado = {
        "timbre": {"brake": 0.14, "brake_release": 0.10, "turn_in": 0.09, "throttle_on": 0.12},
        "ritmo": {"brake": 0.24, "turn_in": 0.05, "throttle_on": 0.15, "coast": 0.18},
        "chirp": {"brake": 0.16, "turn_in": 0.09, "throttle_on": 0.14, "brake_release": 0.12},
    }
    for profile, cues in esperado.items():
        for cue, dur in cues.items():
            data = _render_cue({"cue": cue}, freqs, 0.12, 0.8, sound_profile=profile)
            samples, rate = _decode_wav(data)
            assert abs(len(samples) / rate - dur) < 0.005, (profile, cue, len(samples) / rate)


def test_perfil_timbre_freno_band_limited_sin_alias():
    """Anti-aliasing del perfil A: el freno es cuadrada band-limited por SUMA de
    armonicos IMPARES; el mas alto sintetizado queda por debajo de 0.45*SR (no
    hay energia sobre Nyquist reflejada). Comprobado por el catalogo de
    armonicos Y por FFT (sin energia significativa sobre 0.47*SR)."""
    import numpy as np

    from fantasma.viz.pacenotes import (
        _NYQ_MARGIN,
        DEFAULT_FREQS,
        _odd_harmonics,
        _render_cue,
    )

    sr = 24000
    f0 = DEFAULT_FREQS["brake"]  # 1000 Hz
    harmonics = _odd_harmonics(f0, sr)
    # solo impares, estrictamente por debajo del limite de banda
    assert harmonics == [1, 3, 5, 7, 9]
    assert all(n % 2 == 1 for n in harmonics)
    assert max(harmonics) * f0 < _NYQ_MARGIN * sr

    data = _render_cue({"cue": "brake"}, dict(DEFAULT_FREQS), 0.12, 0.8, sound_profile="timbre")
    samples, rate = _decode_wav(data)
    spectrum = np.abs(np.fft.rfft(samples))
    freqs = np.fft.rfftfreq(len(samples), 1.0 / rate)
    total = float(np.sum(spectrum))
    above = float(np.sum(spectrum[freqs > _NYQ_MARGIN * sr + 500]))
    assert above / total < 0.01, "energia sobre el limite de banda: %.4f" % (above / total)


def test_sound_profile_desconocido_levanta_error_accionable(tmp_path):
    """Un perfil desconocido levanta ValueError con un mensaje accionable (lista
    los validos), tanto en build_tone_pack como en _render_cue — nunca falla en
    silencio ni cae a un fallback mudo."""
    import pytest

    from fantasma.viz.pacenotes import DEFAULT_FREQS, _render_cue, build_tone_pack

    with pytest.raises(ValueError) as exc:
        build_tone_pack(
            _PROFILE_ROWS, _PROFILE_CORNERS, str(tmp_path), top=1, sound_profile="bombo"
        )
    assert "bombo" in str(exc.value)
    assert "seno" in str(exc.value) and "timbre" in str(exc.value)

    with pytest.raises(ValueError):
        _render_cue({"cue": "brake"}, dict(DEFAULT_FREQS), 0.12, 0.8, sound_profile="bombo")


def test_build_pack_propaga_sound_profile_a_los_tonos(tmp_path):
    """build_pack reenvia `sound_profile` hasta build_tone_pack: el pack en
    'timbre' difiere byte a byte del default 'seno' (el e2e puede pedir un
    perfil concreto por el punto de entrada publico)."""
    from fantasma.viz.pacenotes import build_pack

    d_seno = tmp_path / "seno"
    d_timbre = tmp_path / "timbre"
    build_pack(_PROFILE_ROWS, _PROFILE_CORNERS, str(d_seno), mode="tones", top=1)
    build_pack(
        _PROFILE_ROWS, _PROFILE_CORNERS, str(d_timbre), mode="tones", top=1, sound_profile="timbre"
    )
    brake_seno = next(d_seno.glob("1000_*.wav")).read_bytes()
    brake_timbre = next(d_timbre.glob("1000_*.wav")).read_bytes()
    assert brake_seno != brake_timbre


# ── Defectos del sintetizador (revision adversarial 2026-07-09) ───────────────


def test_a_freq_cero_no_cuelga_y_error_accionable(tmp_path):
    """(a) freq <= 0 colgaba _odd_harmonics (bucle infinito, la lista crecia
    hasta agotar memoria) con las paletas aditivas. build_tone_pack ahora valida
    la frecuencia y falla RAPIDO con mensaje accionable. Se corre en un hilo con
    timeout: si el bug reaparece (cuelgue), el hilo sigue vivo y el test falla en
    vez de colgar la suite entera."""
    import threading

    from fantasma.viz.pacenotes import build_tone_pack

    result = {}

    def _run():
        try:
            build_tone_pack(
                _PROFILE_ROWS,
                _PROFILE_CORNERS,
                str(tmp_path / "z"),
                top=1,
                freqs={"brake": 0},
                sound_profile="timbre",
            )
        except ValueError as e:
            result["err"] = str(e)
        except BaseException as e:  # noqa: BLE001
            result["other"] = repr(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=5)
    assert not t.is_alive(), "build_tone_pack colgo con freq=0 (bucle infinito en _odd_harmonics)"
    assert "err" in result, "se esperaba ValueError, se obtuvo: %r" % result.get("other")
    assert "brake" in result["err"] and "0" in result["err"]


def test_a_validate_freqs_rechaza_negativa_y_sobre_nyquist():
    """(a) _validate_freqs exige positiva y < Nyquist (SR/2). Nombra la clave y
    el valor infractor. DEFAULT_FREQS pasa el guard sin tocar (no-regresion)."""
    import pytest

    from fantasma.viz.pacenotes import DEFAULT_FREQS, _validate_freqs

    _validate_freqs(dict(DEFAULT_FREQS))  # no levanta
    for mala in ({"brake": 0}, {"apex": -5}, {"gas": 20000}):
        with pytest.raises(ValueError) as exc:
            _validate_freqs({**DEFAULT_FREQS, **mala})
        (k,) = mala
        assert k in str(exc.value)


def test_b_odd_harmonics_freq_alta_falla_ruidosa():
    """(b) freq >= 0.45*SR dejaba _odd_harmonics con lista vacia -> onda en todo
    ceros -> cue MUDO sin aviso. Ahora levanta ValueError (falla ruidosa). En
    759413f devolvia [] sin quejarse."""
    import pytest

    from fantasma.viz.pacenotes import _NYQ_MARGIN, _odd_harmonics

    sr = 24000
    # Justo por debajo del limite: aun devuelve al menos el fundamental.
    assert _odd_harmonics(_NYQ_MARGIN * sr - 1, sr) == [1]
    # En o por encima del limite: antes -> [] (mudo); ahora -> ValueError.
    with pytest.raises(ValueError):
        _odd_harmonics(_NYQ_MARGIN * sr + 100, sr)


def test_c_float_to_wav_volumen_mayor_que_uno_satura_sin_dar_la_vuelta():
    """(c) con volume > 1 el clip previo a multiplicar por el volumen no protegia:
    1.0*1.5*32767 = 49150 desbordaba int16 y daba la vuelta a NEGATIVO (un
    chasquido con el signo invertido). Ahora se recorta DESPUES del volumen: una
    senal positiva satura a +1.0, nunca voltea de signo."""
    import numpy as np

    from fantasma.viz.pacenotes import _float_to_wav

    sig = np.ones(200, dtype=np.float64)  # constante +1.0
    data = _float_to_wav(sig, 1.5, 24000)
    samples, _ = _decode_wav(data)
    # Con el fix: saturado alto y positivo. En 759413f: ~ -0.5 (signo volteado).
    assert samples.min() > 0.99, "el volumen > 1 volteo el signo (int16 overflow): min=%.3f" % (
        samples.min()
    )


def test_d_chirp_tic_no_revienta_con_countdown_de_3_tics(monkeypatch):
    """(d) el perfil chirp indexaba una tupla fija de longitud 2 con `step`,
    acoplado por convencion —no por codigo— a COUNTDOWN_SCALE. Con un
    COUNTDOWN_SCALE de 3 tics, chirp reventaba con IndexError mientras las otras
    paletas seguian. Ahora deriva el tono del tic de _tic_freq (cualquier
    longitud)."""
    import fantasma.viz.pacenotes as pn

    monkeypatch.setattr(pn, "COUNTDOWN_SCALE", (0.75, 0.875, 0.95))
    # step=2 solo existe con un COUNTDOWN_SCALE de 3: en 759413f -> IndexError.
    data = pn._render_cue(
        {"cue": "brake_tic", "step": 2}, dict(pn.DEFAULT_FREQS), 0.12, 0.8, sound_profile="chirp"
    )
    samples, rate = _decode_wav(data)
    assert rate == 24000 and len(samples) > 0
    # seno tambien debe soportar el 3er tic (deriva de COUNTDOWN_SCALE[step]).
    data_seno = pn._render_cue(
        {"cue": "brake_tic", "step": 2}, dict(pn.DEFAULT_FREQS), 0.12, 0.8, sound_profile="seno"
    )
    assert len(_decode_wav(data_seno)[0]) > 0


def test_e_paletas_respetan_duration_como_multiplicador():
    """(e) timbre/ritmo/chirp ignoraban `duration` (duraciones fijas), mientras
    seno la respetaba. Ahora cada cue escala con duration/_PROFILE_REF_DURATION:
    `duration` manda en todas las paletas y el contraste relativo se conserva."""
    from fantasma.viz.pacenotes import DEFAULT_FREQS, _render_cue

    freqs = dict(DEFAULT_FREQS)
    for profile in ("timbre", "ritmo", "chirp"):
        corta = _decode_wav(_render_cue({"cue": "brake"}, freqs, 0.12, 0.8, sound_profile=profile))[
            0
        ]
        larga = _decode_wav(_render_cue({"cue": "brake"}, freqs, 0.30, 0.8, sound_profile=profile))[
            0
        ]
        # En 759413f ambas duraban lo mismo (se ignoraba duration).
        assert len(larga) > len(corta) * 2, profile
        # Escala proporcional (x2.5) dentro de tolerancia de muestreo.
        assert abs(len(larga) / len(corta) - 2.5) < 0.05, (profile, len(larga) / len(corta))


def test_f_tic_fallback_unificado_seno_vs_paletas():
    """(f) el fallback del tono base del tic discrepaba: _tic_freq usaba 800 y la
    rama seno de _render_cue usaba 880. Inalcanzable por la API publica (el merge
    con DEFAULT_FREQS lo tapa) pero una bomba de relojeria. Ahora ambos caen a
    DEFAULT_FREQS['brake_countdown'] -> mismo tono base."""
    from fantasma.viz.pacenotes import _render_cue, _tic_freq, generate_tone

    # freqs SIN 'brake_countdown' fuerza el fallback en ambos caminos.
    seno_tic = _render_cue({"cue": "brake_tic", "step": 0}, {}, 0.12, 0.8, sound_profile="seno")
    esperado = generate_tone(_tic_freq({}, 0), 0.08, volume=0.8)
    # En 759413f: seno usa 880 (->660 Hz) y _tic_freq usa 800 (->600 Hz): difieren.
    assert seno_tic == esperado


def test_g_seno_y_paletas_comparten_un_unico_fade():
    """(g) generate_tone (seno) reimplementaba la tuberia de _wave_sine con un
    fade DISTINTO (0.01 s vs 0.008 s), sesgando la comparacion de oido del PO.
    Ahora generate_tone ES exactamente _float_to_wav(_wave_sine(...)): mismo fade
    unico. En 759413f estos bytes difieren (fade 0.01 vs 0.008)."""
    from fantasma.viz.pacenotes import _float_to_wav, _wave_sine, generate_tone

    f, dur, vol, sr = 1000, 0.12, 0.8, 24000
    assert generate_tone(f, dur, vol) == _float_to_wav(_wave_sine(f, dur, sr), vol, sr)


def _tone_pack_inputs():
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
    return rows, corners


def test_validate_freqs_rechaza_11000_solo_en_timbre():
    """A2: 11000 Hz supera la cota anti-alias de la sintesis aditiva band-limited
    (`_NYQ_MARGIN*SR = 10800`) que usa `timbre`, pero es legitima para
    `seno`/`ritmo`/`chirp` (seno puro / barrido, < Nyquist 12000). El guard debe
    fallar TEMPRANO y accionable en `timbre` sin regresionar a los demas."""
    import pytest

    from fantasma.viz.pacenotes import _validate_freqs

    with pytest.raises(ValueError) as exc:
        _validate_freqs({"brake": 11000.0}, sound_profile="timbre")
    msg = str(exc.value)
    # mensaje accionable: nombra el valor infractor y la bandera a revisar
    assert "11000" in msg
    assert "timbre" in msg
    assert "--brake-freq" in msg
    # sin regresion: seno/ritmo/chirp aceptan 11000 (no usan armonicos)
    for prof in ("seno", "ritmo", "chirp"):
        _validate_freqs({"brake": 11000.0}, sound_profile=prof)


def test_build_tone_pack_timbre_11000_falla_temprano(tmp_path):
    """A2 (end-to-end): `build_tone_pack` con timbre + brake 11000 revienta en la
    VALIDACION (ValueError accionable), no cripticamente dentro de la sintesis."""
    import pytest

    from fantasma.viz.pacenotes import build_tone_pack

    rows, corners = _tone_pack_inputs()
    with pytest.raises(ValueError) as exc:
        build_tone_pack(
            rows, corners, str(tmp_path), top=1, freqs={"brake": 11000.0}, sound_profile="timbre"
        )
    assert "11000" in str(exc.value)


def test_build_tone_pack_seno_11000_ok(tmp_path):
    """A2 (no-regresion): seno con 11000 Hz sigue generando WAVs (seno puro < Nyquist)."""
    from fantasma.viz.pacenotes import build_tone_pack

    rows, corners = _tone_pack_inputs()
    result = build_tone_pack(
        rows, corners, str(tmp_path), top=1, freqs={"brake": 11000.0}, sound_profile="seno"
    )
    assert result["entries"] >= 1
    assert list(tmp_path.glob("*.wav"))


def test_build_tone_pack_duration_cero_no_crashea_ningun_perfil(tmp_path):
    """A3: `--tone-duration 0` (o negativo) reventaba `timbre` (`_tone_norm` sobre
    array vacio) y `chirp` (division por cero). Con el piso `_MIN_TONE_DURATION`
    en `build_tone_pack`, NINGUN perfil crashea y todos generan WAVs audibles."""
    from fantasma.viz.pacenotes import build_tone_pack

    rows, corners = _tone_pack_inputs()
    for prof in ("seno", "timbre", "ritmo", "chirp"):
        for dur in (0, -0.5):
            out = tmp_path / ("%s_%s" % (prof, dur))
            result = build_tone_pack(
                rows, corners, str(out), top=1, duration=dur, sound_profile=prof
            )
            assert result["entries"] >= 1, "%s dur=%s" % (prof, dur)
            wavs = list(out.glob("*.wav"))
            assert wavs, "%s dur=%s no genero WAV" % (prof, dur)
            # WAV con muestras reales (no el mudo de 44 bytes que daba duration 0)
            assert all(w.stat().st_size > 44 for w in wavs), "%s dur=%s WAV mudo" % (prof, dur)
