"""Smoke tests NiceGUI — ng_step5 (Pace Notes para CrewChief).

Verifica que el Paso 5 renderiza sin crash y que el guard aparece
cuando el analisis (Paso 2) aun no se ha ejecutado.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step5.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step5_heading_visible(user):
    """El Paso 5 muestra su heading; siempre visible antes del guard."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    await user.should_see("Paso 5")


@pytest.mark.asyncio
async def test_step5_guard_without_analysis(user):
    """Sin analisis previo el guard dirige al Paso 2."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    # El guard se activa porque state.rows es None y state.corners es None
    await user.should_see("Paso 2")
