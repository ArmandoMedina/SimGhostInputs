"""Smoke tests NiceGUI — ng_step4 (Componer video final).

Verifica que el Paso 4 renderiza sin crash en cualquier entorno:
- Si ffmpeg no esta instalado: muestra el aviso de instalacion.
- Si ffmpeg esta instalado: muestra la UI de composicion.

El heading del paso se renderiza antes de la verificacion de ffmpeg,
por lo que siempre debe ser visible.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step4.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step4_heading_visible(user):
    """El Paso 4 muestra su heading; se renderiza antes de la guardia de ffmpeg."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Boton de sidebar "Video" navega al Paso 4
    user.find("Video").click()
    await user.should_see("Paso 4")


@pytest.mark.asyncio
async def test_step4_renders_without_crash(user):
    """El Paso 4 renderiza hasta el final sin lanzar excepcion."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Video").click()
    # "Componer" aparece en el heading ui.label (siempre visible)
    await user.should_see("Componer")
