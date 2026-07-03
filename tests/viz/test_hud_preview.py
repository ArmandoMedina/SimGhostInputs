"""Tier 3 — tests para fantasma/viz/hud_preview (sin PIL ni ffmpeg reales)."""

import subprocess
from unittest.mock import patch

import pytest


def test_compose_preview_frame_no_ffmpeg_in_path(tmp_path):
    """Sin ffmpeg en PATH -> RuntimeError con mensaje util, no FileNotFoundError/WinError 2."""
    from fantasma.viz import hud_preview

    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="ffmpeg"):
            hud_preview.compose_preview_frame(str(tmp_path / "fake.webm"), "bottom-right", 1.0)


def test_compose_preview_frame_ffmpeg_failure_includes_stderr(tmp_path):
    """ffmpeg falla (returncode != 0) -> RuntimeError incluye stderr de ffmpeg."""
    from fantasma.viz import hud_preview

    stderr_msg = b"Invalid data found when processing input\n"
    err = subprocess.CalledProcessError(1, ["ffmpeg"], stderr=stderr_msg)

    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("subprocess.run", side_effect=err):
            with pytest.raises(RuntimeError, match="Invalid data"):
                hud_preview.compose_preview_frame(str(tmp_path / "bad.webm"), "bottom-right", 1.0)
