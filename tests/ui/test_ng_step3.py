"""Smoke tests NiceGUI — ng_step3 (Generar overlay HUD).

Verifica que el Paso 3 renderiza sin crash en estado inicial
(sin archivos cargados) y muestra el mensaje de guardia correcto.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step3.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step3_heading_visible(user):
    """El Paso 3 muestra su heading aunque no haya datos cargados."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Boton de sidebar "Overlay" navega al Paso 3
    user.find("Overlay").click()
    await user.should_see("Paso 3")


@pytest.mark.asyncio
async def test_step3_guard_without_data(user):
    """Sin ref_lap, el Paso 3 muestra mensaje pidiendo ir al Paso 1."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    # Guard: "Primero carga los archivos en el Paso 1."
    await user.should_see("Primero carga")
