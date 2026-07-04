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


def test_audio_mix_filter_with_video_audio():
    assert "amix=inputs=2" in compose._audio_mix_filter(video_has_audio=True)


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
