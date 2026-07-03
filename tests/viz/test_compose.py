"""Tier 3 — helpers PUROS de compose (sin invocar ffmpeg de verdad).

Tests de regresión de bugs ya corregidos:
- construcción del filtro ffmpeg (el bug de los operadores en `scale`);
- `_nvenc_available` como contrato del fallback CPU (el falso positivo de NVENC).
"""

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
