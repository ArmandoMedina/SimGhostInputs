"""Tier 3 — helpers PUROS de compose (sin invocar ffmpeg de verdad).

Tests de regresión de bugs ya corregidos:
- construcción del filtro ffmpeg (el bug de los operadores en `scale`);
- `_nvenc_available` como contrato del fallback CPU (el falso positivo de NVENC).
"""

import os

from fantasma.viz import compose

# --- _build_filter ---------------------------------------------------------


def test_build_filter_scale_has_multiply_operator():
    # regresión: el filtro de escala debe llevar 'scale=iw*<f>:ih*<f>'
    fc = compose._build_filter("bottom-right", scale=0.5)
    assert "scale=iw*0.500000:ih*0.500000" in fc
    assert "[out]" in fc


def test_build_filter_no_scale_step_when_scale_is_one():
    fc = compose._build_filter("bottom-right", scale=1.0)
    assert "scale=" not in fc
    assert "overlay=" in fc


def test_build_filter_setpts_only_with_offset():
    sin_offset = compose._build_filter("center", scale=1.0, offset=0.0)
    con_offset = compose._build_filter("center", scale=1.0, offset=2.5)
    assert "setpts" not in sin_offset
    assert "setpts=PTS+2.500000/TB" in con_offset


def test_build_filter_unknown_position_falls_back_to_bottom_right():
    fc = compose._build_filter("posicion-inexistente", scale=1.0)
    px, py = compose.POSITIONS["bottom-right"]
    assert "overlay=x=%s:y=%s" % (px, py) in fc


def test_build_filter_burns_subs_after_overlay():
    # con subs_file: el overlay va a un label intermedio y luego se quema el .ass
    fc = compose._build_filter("bottom-right", scale=1.0, subs_file="cue_subs.ass")
    assert "[ovl]" in fc
    assert "ass=cue_subs.ass[out]" in fc
    # sin subs_file no aparece el filtro ass
    assert "ass=" not in compose._build_filter("bottom-right", scale=1.0)


def test_audio_mix_filter_with_video_audio():
    assert "amix=inputs=2" in compose._audio_mix_filter(video_has_audio=True)


def test_audio_mix_filter_no_normalize():
    # normalize=0 evita que amix divida cada entrada entre el nº de inputs
    # (-6 dB), lo que enterraba los cues bajo el audio del motor. Regresion.
    assert "normalize=0" in compose._audio_mix_filter(video_has_audio=True)


def test_audio_mix_filter_without_video_audio():
    assert compose._audio_mix_filter(video_has_audio=False) == "[2:a]anull[aout]"


# --- _nvenc_available (contrato del fallback) ------------------------------


class _FakeProc:
    def __init__(self, returncode):
        self.returncode = returncode


def test_nvenc_available_true_on_returncode_zero(monkeypatch):
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProc(0))
    assert compose._nvenc_available("ffmpeg") is True


def test_nvenc_available_false_on_nonzero(monkeypatch):
    # regresión: NVENC compilado pero sin GPU usable -> probe falla -> fallback CPU
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProc(1))
    assert compose._nvenc_available("ffmpeg") is False


def test_nvenc_available_false_on_exception(monkeypatch):
    def boom(*a, **k):
        raise OSError("ffmpeg no está")

    monkeypatch.setattr(compose.subprocess, "run", boom)
    assert compose._nvenc_available("ffmpeg") is False


# --- compose_video return dict (C20) ---------------------------------------


def test_compose_video_returns_dict_with_path_encoder_duration(monkeypatch, tmp_path):
    """compose_video devuelve un dict con path, encoder y duration_s (C20).

    Se monkeypatchea shutil.which para simular ffmpeg disponible y
    subprocess.run para no invocar ffmpeg de verdad.
    """
    fake_out = str(tmp_path / "out.mp4")

    # Simula que ffmpeg existe y que nvenc NO está disponible (returncode=1)
    monkeypatch.setattr(
        compose.shutil, "which", lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None
    )
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProc(1))

    # nvenc check returns 1 (no nvenc), luego el run real devuelve 0
    run_calls = [0]

    def dispatch_run(cmd, **kwargs):
        run_calls[0] += 1
        if run_calls[0] == 1:
            # primera llamada: _nvenc_available
            return _FakeProc(1)
        # segunda llamada: el encode real
        open(fake_out, "w").close()
        return _FakeProc(0)

    monkeypatch.setattr(compose.subprocess, "run", dispatch_run)

    result = compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
    )

    assert isinstance(result, dict), "compose_video debe devolver un dict"
    assert "path" in result
    assert "encoder" in result
    assert "duration_s" in result
    assert result["path"] == fake_out
    assert result["encoder"] == "libx264"
    assert isinstance(result["duration_s"], float)


# --- compose_video wiring: pace_notes_dir ----------------------------------


class _FakeProcOk:
    returncode = 0


def test_compose_video_wires_pace_notes_dir_to_render_and_ffmpeg(monkeypatch, tmp_path):
    """compose_video con pace_notes_dir invoca render_pace_notes_track y pasa
    el WAV resultante al comando ffmpeg como input -i.

    Ni ffmpeg ni render_pace_notes_track se ejecutan de verdad: se mockean
    para verificar el wiring sin I/O real.
    """
    import fantasma.viz.pacenotes as _pn_mod
    from tests.conftest import make_lap

    lap = make_lap()
    pn_dir = str(tmp_path / "pndir")
    os.makedirs(pn_dir, exist_ok=True)
    fake_out = str(tmp_path / "out.mp4")

    pn_calls = []

    def fake_render_pn(pn_d, lap_arg, out_path, volume=1.0):
        pn_calls.append({"dir": pn_d, "lap": lap_arg, "path": out_path, "volume": volume})
        # crea el archivo para que cue_audio sea un path real (no requerido por ffmpeg mockeado)
        open(out_path, "wb").close()

    monkeypatch.setattr(_pn_mod, "render_pace_notes_track", fake_render_pn)

    ffmpeg_cmds = []

    def fake_run(cmd, **kwargs):
        ffmpeg_cmds.append(list(cmd))
        return _FakeProcOk()

    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose, "_has_audio", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", fake_run)

    result = compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
        pace_notes_dir=pn_dir,
        pace_notes_volume=0.75,
        lap=lap,
    )

    # render_pace_notes_track debe haberse llamado exactamente una vez
    assert len(pn_calls) == 1, "render_pace_notes_track debe llamarse una vez"
    assert pn_calls[0]["dir"] == pn_dir
    assert pn_calls[0]["lap"] is lap
    assert pn_calls[0]["volume"] == 0.75

    # el WAV generado debe aparecer como input en el comando ffmpeg
    assert ffmpeg_cmds, "ffmpeg debe haber sido invocado"
    cmd = ffmpeg_cmds[0]
    assert pn_calls[0]["path"] in cmd, "el WAV de pace notes debe ser un input -i de ffmpeg"

    # el resultado sigue siendo el dict de contrato
    assert isinstance(result, dict)
    assert result["path"] == fake_out
    assert result["encoder"] == "libx264"


def test_compose_video_burn_cue_subs_wires_ass_filter(monkeypatch, tmp_path):
    """Con burn_cue_subs, compose_video genera el .ass, lo mete como filtro ass
    del ffmpeg y corre el proceso con cwd en la carpeta del .ass."""
    import fantasma.viz.pacenotes as _pn_mod
    from tests.conftest import make_lap

    lap = make_lap()
    pn_dir = str(tmp_path / "pndir")
    os.makedirs(pn_dir, exist_ok=True)
    fake_out = str(tmp_path / "out.mp4")

    monkeypatch.setattr(
        _pn_mod, "render_pace_notes_track", lambda *a, **k: open(a[2], "wb").close()
    )
    monkeypatch.setattr(_pn_mod, "build_cue_ass", lambda *a, **k: "[Script Info]\nfake")
    monkeypatch.setattr(compose, "_probe_resolution", lambda *a: (1024, 1024))

    runs = []

    def fake_run(cmd, **kwargs):
        cwd = kwargs.get("cwd")
        # el .ass existe DURANTE el encode; el tmpdir se limpia al volver.
        ass_ok = bool(cwd) and os.path.exists(os.path.join(cwd, "cue_subs.ass"))
        runs.append({"cmd": list(cmd), "cwd": cwd, "ass_ok": ass_ok})
        return _FakeProcOk()

    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose, "_has_audio", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", fake_run)

    compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
        pace_notes_dir=pn_dir,
        lap=lap,
        burn_cue_subs=True,
    )

    assert runs, "ffmpeg debe haber sido invocado"
    fc = next(
        (runs[0]["cmd"][i + 1] for i, a in enumerate(runs[0]["cmd"]) if a == "-filter_complex"), ""
    )
    assert "ass=cue_subs.ass" in fc, "el filtro ass debe quemar el .ass por nombre relativo"
    assert runs[0]["cwd"], "ffmpeg debe correr con cwd en la carpeta del .ass"
    assert runs[0]["ass_ok"], "el .ass debe existir en cwd durante el encode"


def test_compose_video_no_burn_when_build_cue_ass_returns_none(monkeypatch, tmp_path):
    """Si build_cue_ass devuelve None (nada que rotular), no se quema ningun .ass."""
    import fantasma.viz.pacenotes as _pn_mod
    from tests.conftest import make_lap

    lap = make_lap()
    pn_dir = str(tmp_path / "pndir")
    os.makedirs(pn_dir, exist_ok=True)

    monkeypatch.setattr(
        _pn_mod, "render_pace_notes_track", lambda *a, **k: open(a[2], "wb").close()
    )
    monkeypatch.setattr(_pn_mod, "build_cue_ass", lambda *a, **k: None)
    monkeypatch.setattr(compose, "_probe_resolution", lambda *a: (1024, 1024))

    runs = []
    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose, "_has_audio", lambda *a: False)
    monkeypatch.setattr(
        compose.subprocess,
        "run",
        lambda cmd, **k: runs.append({"cmd": list(cmd), "cwd": k.get("cwd")}) or _FakeProcOk(),
    )

    compose.compose_video(
        video="v.mp4",
        overlay="o.webm",
        output=str(tmp_path / "out.mp4"),
        pace_notes_dir=pn_dir,
        lap=lap,
        burn_cue_subs=True,
    )

    fc = next(
        (runs[0]["cmd"][i + 1] for i, a in enumerate(runs[0]["cmd"]) if a == "-filter_complex"), ""
    )
    assert "ass=" not in fc
    assert runs[0]["cwd"] is None


def test_compose_video_no_pace_notes_when_no_dir(monkeypatch, tmp_path):
    """Sin pace_notes_dir, render_pace_notes_track NO se llama."""
    import fantasma.viz.pacenotes as _pn_mod
    from tests.conftest import make_lap

    lap = make_lap()
    fake_out = str(tmp_path / "out.mp4")
    pn_calls = []

    monkeypatch.setattr(_pn_mod, "render_pace_notes_track", lambda *a, **k: pn_calls.append(1))
    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProcOk())

    compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
        lap=lap,
        # pace_notes_dir omitido
    )

    assert pn_calls == [], "sin pace_notes_dir no debe llamarse render_pace_notes_track"


def test_compose_video_explicit_cue_audio_skips_pace_notes(monkeypatch, tmp_path):
    """Si ya se pasó cue_audio explícito, pace_notes_dir se ignora (no doble mezcla)."""
    import fantasma.viz.pacenotes as _pn_mod
    from tests.conftest import make_lap

    lap = make_lap()
    fake_out = str(tmp_path / "out.mp4")
    explicit_cue = str(tmp_path / "explicit.wav")
    open(explicit_cue, "wb").close()
    pn_calls = []

    monkeypatch.setattr(_pn_mod, "render_pace_notes_track", lambda *a, **k: pn_calls.append(1))
    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose, "_has_audio", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProcOk())

    compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
        cue_audio=explicit_cue,
        pace_notes_dir=str(tmp_path / "pndir"),
        lap=lap,
    )

    assert pn_calls == [], "cue_audio explicito debe tener prioridad sobre pace_notes_dir"


# --- mux_pace_notes_into_video wiring -----------------------------------------


def test_mux_pace_notes_into_video_wiring(monkeypatch, tmp_path):
    """mux_pace_notes_into_video llama a render_pace_notes_track con el lap y volume
    correctos, y pasa el WAV generado a ffmpeg con -c:v copy (sin re-encodear video).

    Ni ffmpeg ni render_pace_notes_track se ejecutan de verdad.
    """
    import fantasma.viz.pacenotes as _pn_mod
    from fantasma.viz.compose import mux_pace_notes_into_video
    from tests.conftest import make_lap

    lap = make_lap()
    pn_dir = str(tmp_path / "pndir")
    os.makedirs(pn_dir, exist_ok=True)
    fake_out = str(tmp_path / "out_pacenotes.mp4")

    pn_calls = []

    def fake_render_pn(pn_d, lap_arg, out_path, volume=1.0):
        pn_calls.append({"dir": pn_d, "lap": lap_arg, "path": out_path, "volume": volume})
        # crea el archivo WAV falso para que la ruta sea un path valido en el comando
        open(out_path, "wb").close()

    monkeypatch.setattr(_pn_mod, "render_pace_notes_track", fake_render_pn)

    ffmpeg_cmds = []

    def fake_run(cmd, **kwargs):
        ffmpeg_cmds.append(list(cmd))
        return _FakeProcOk()

    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose.subprocess, "run", fake_run)

    result = mux_pace_notes_into_video(
        video="fake_video.mp4",
        pace_notes_dir=pn_dir,
        lap=lap,
        output=fake_out,
        volume=0.5,
    )

    # (a) render_pace_notes_track llamado una vez con el lap y volume correctos
    assert len(pn_calls) == 1, "render_pace_notes_track debe llamarse exactamente una vez"
    assert pn_calls[0]["lap"] is lap, "debe recibir el lap correcto"
    assert pn_calls[0]["volume"] == 0.5, "debe recibir el volume correcto"
    assert pn_calls[0]["dir"] == pn_dir, "debe recibir el pace_notes_dir correcto"

    # (b) ffmpeg invocado con -c:v copy y el WAV como input -i
    assert ffmpeg_cmds, "ffmpeg debe haberse invocado"
    cmd = ffmpeg_cmds[0]
    assert "-c:v" in cmd, "el comando ffmpeg debe incluir -c:v"
    cvc_idx = cmd.index("-c:v")
    assert cmd[cvc_idx + 1] == "copy", "-c:v debe ir seguido de copy (sin re-encodear)"
    assert pn_calls[0]["path"] in cmd, "el WAV de pace notes debe aparecer como input en ffmpeg"

    # la funcion devuelve la ruta de salida
    assert result == fake_out


# --- Sidecar de sincronia video<->vuelta (ADR 0024) ----------------------------


def test_sync_sidecar_roundtrip(tmp_path):
    video = str(tmp_path / "lap_composed.mp4")
    path = compose.write_sync_sidecar(
        video, {"csv_path": "vuelta.csv", "laptime": 394.05, "offset": 12.3}
    )
    assert path == video + compose.SYNC_SIDECAR_SUFFIX
    data = compose.read_sync_sidecar(video)
    assert data["format"] == "sgi-sync-v1"
    assert data["laptime"] == 394.05
    assert data["csv_path"] == "vuelta.csv"


def test_read_sync_sidecar_missing_or_corrupt(tmp_path):
    video = str(tmp_path / "externo.mp4")
    assert compose.read_sync_sidecar(video) is None
    with open(compose.sync_sidecar_path(video), "w", encoding="utf-8") as f:
        f.write("{esto no es json")
    assert compose.read_sync_sidecar(video) is None


def test_read_sync_sidecar_rechaza_formato_desconocido(tmp_path):
    """Un sgi-sync-v2 futuro (semantica posiblemente distinta) no debe ser
    validado por un lector v1: read devuelve None y el mux no valida."""
    import json

    video = str(tmp_path / "lap.mp4")
    with open(compose.sync_sidecar_path(video), "w", encoding="utf-8") as f:
        json.dump({"format": "sgi-sync-v2", "laptime": 100.0}, f)
    assert compose.read_sync_sidecar(video) is None


def test_check_sync_sidecar_rechaza_origen_distinto(tmp_path):
    """Dos vueltas de archivos distintos pueden durar casi igual: si el sidecar
    registra el origen y el caller lo provee, el origen tambien se compara."""
    import pytest

    from fantasma.core.lap import Lap

    video = str(tmp_path / "lap.mp4")
    compose.write_sync_sidecar(video, {"csv_path": r"C:\datos\race_A.csv", "laptime": 394.05})
    lap = Lap(channels={"time": [0.0, 394.05], "dist": [0.0, 20571.0]})
    # mismo laptime, mismo origen -> pasa
    compose.check_sync_sidecar(video, lap, source_name="race_A.csv")
    # mismo laptime, origen distinto -> error
    with pytest.raises(RuntimeError):
        compose.check_sync_sidecar(video, lap, source_name="race_B.csv")
    # sin source_name (CLI, sidecars viejos) -> solo laptime, pasa
    compose.check_sync_sidecar(video, lap)


def test_compose_video_sin_sync_info_borra_sidecar_huerfano(monkeypatch, tmp_path):
    """Re-componer al mismo output sin vuelta cargada no debe dejar el sidecar
    de la corrida anterior validando el video nuevo (falsa luz verde)."""
    fake_out = str(tmp_path / "out.mp4")
    compose.write_sync_sidecar(fake_out, {"csv_path": "vieja.csv", "laptime": 100.0})
    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProcOk())

    compose.compose_video(video="fake_video.mp4", overlay="fake_overlay.webm", output=fake_out)

    assert compose.read_sync_sidecar(fake_out) is None


def test_check_sync_sidecar_acepta_vuelta_correcta_y_rechaza_otra(tmp_path):
    """El mux con la vuelta equivocada producia cues corridos segundos (la causa
    real de desync del panel 2 del Paso 5). Con sidecar, laptime distinto = error."""
    import pytest

    from fantasma.core.lap import Lap

    video = str(tmp_path / "lap_composed.mp4")
    compose.write_sync_sidecar(video, {"csv_path": "vuelta.csv", "laptime": 394.05})

    lap_ok = Lap(channels={"time": [0.0, 394.05], "dist": [0.0, 20571.0]})
    compose.check_sync_sidecar(video, lap_ok)  # no debe lanzar

    lap_otra = Lap(channels={"time": [0.0, 391.60], "dist": [0.0, 20571.0]})
    with pytest.raises(RuntimeError, match="394.05"):
        compose.check_sync_sidecar(video, lap_otra)


def test_check_sync_sidecar_sin_sidecar_no_valida(tmp_path):
    """Video externo sin sidecar: comportamiento previo intacto (no valida nada)."""
    from fantasma.core.lap import Lap

    lap = Lap(channels={"time": [0.0, 100.0], "dist": [0.0, 5000.0]})
    compose.check_sync_sidecar(str(tmp_path / "externo.mp4"), lap)  # no debe lanzar


def test_mux_rechaza_vuelta_que_no_corresponde(monkeypatch, tmp_path):
    """mux_pace_notes_into_video corta ANTES de invocar ffmpeg si el sidecar
    delata que la vuelta cargada no es la del video."""
    import pytest

    from fantasma.core.lap import Lap
    from fantasma.viz.compose import mux_pace_notes_into_video

    video = str(tmp_path / "lap_composed.mp4")
    compose.write_sync_sidecar(video, {"csv_path": "vuelta.csv", "laptime": 394.05})
    called = []
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: called.append(1))

    lap_otra = Lap(channels={"time": [0.0, 380.00], "dist": [0.0, 20571.0]})
    with pytest.raises(RuntimeError):
        mux_pace_notes_into_video(video, str(tmp_path), lap_otra, str(tmp_path / "out.mp4"))
    assert called == [], "ffmpeg no debe invocarse con vuelta equivocada"


def test_compose_video_escribe_sidecar(monkeypatch, tmp_path):
    """compose_video con sync_info escribe <output>.sync.json con offset y duracion."""
    fake_out = str(tmp_path / "out.mp4")
    monkeypatch.setattr(
        compose.shutil, "which", lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None
    )
    monkeypatch.setattr(compose, "_nvenc_available", lambda *a: False)
    monkeypatch.setattr(compose.subprocess, "run", lambda *a, **k: _FakeProcOk())

    compose.compose_video(
        video="fake_video.mp4",
        overlay="fake_overlay.webm",
        output=fake_out,
        offset=12.5,
        lap_duration=394.05,
        sync_info={"csv_path": "vuelta.csv", "laptime": 394.05},
    )

    data = compose.read_sync_sidecar(fake_out)
    assert data is not None
    assert data["csv_path"] == "vuelta.csv"
    assert data["laptime"] == 394.05
    assert data["offset"] == 12.5
    assert data["lap_duration"] == 394.05
