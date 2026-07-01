"""Tests de compose_video: retorno con encoder y duracion.

Tanda A cambio compose_video() para retornar dict en lugar de string.
Estos tests verifican el contrato: {path, encoder, duration_s}.
"""

from unittest.mock import MagicMock, patch


def test_compose_video_returns_dict_with_encoder(tmp_path):
    """compose_video() debe retornar dict con path, encoder y duration_s."""
    from fantasma.viz.compose import compose_video

    video = str(tmp_path / "video.mp4")
    overlay = str(tmp_path / "overlay.webm")
    output = str(tmp_path / "out.mp4")
    open(video, "wb").close()
    open(overlay, "wb").close()

    with (
        patch("shutil.which", return_value="/usr/bin/ffmpeg"),
        patch("fantasma.viz.compose._nvenc_available", return_value=False),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = compose_video(video, overlay, output)

    assert isinstance(result, dict), "compose_video debe retornar dict"
    assert "path" in result
    assert "encoder" in result
    assert "duration_s" in result
    assert result["encoder"] in ("h264_nvenc", "libx264")
    assert result["path"] == output


def test_compose_video_reports_nvenc_when_available(tmp_path):
    """compose_video() reporta h264_nvenc en el dict si NVENC esta disponible."""
    from fantasma.viz.compose import compose_video

    video = str(tmp_path / "video.mp4")
    overlay = str(tmp_path / "overlay.webm")
    output = str(tmp_path / "out.mp4")
    open(video, "wb").close()
    open(overlay, "wb").close()

    with (
        patch("shutil.which", return_value="/usr/bin/ffmpeg"),
        patch("fantasma.viz.compose._nvenc_available", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = compose_video(video, overlay, output)

    assert isinstance(result, dict), "compose_video debe retornar dict"
    assert result["encoder"] == "h264_nvenc"
