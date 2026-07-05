"""Verifica la coherencia del SSOT de version (fantasma/__init__.py)."""

import os
import re
import sys


def test_version_semver():
    """__version__ debe ser un literal semver X.Y.Z."""
    import fantasma

    assert re.match(r"^\d+\.\d+\.\d+$", fantasma.__version__), (
        f"__version__ no es semver: {fantasma.__version__!r}"
    )


def test_build_installer_get_version_matches_ssot():
    """_get_version() debe devolver exactamente fantasma.__version__."""
    import fantasma

    tools_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import build_installer

    got = build_installer._get_version()
    assert got == fantasma.__version__, (
        f"build_installer._get_version()={got!r} != fantasma.__version__={fantasma.__version__!r}"
    )
