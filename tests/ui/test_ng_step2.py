"""Smoke tests NiceGUI — ng_step2 (Analisis por curva).

Verifica que el Paso 2 renderiza sin crash en estado inicial
(sin archivos cargados) y muestra el mensaje de guardia correcto.

Nota: user.find("Análisis") también encuentra el brand HTML del sidebar
("Análisis de simracing") que tiene un ID menor que el botón. Se filtra
por kind=ui.button para garantizar que se clickea el botón correcto.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step2.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step2_heading_visible(user):
    """El Paso 2 muestra su heading aunque no haya datos cargados."""
    from nicegui import ui
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Filtrar por kind=ui.button para evitar el HTML del sidebar-brand
    # que también contiene "Análisis de simracing"
    user.find(kind=ui.button, content="Análisis").click()
    await user.should_see("Paso 2")


@pytest.mark.asyncio
async def test_step2_guard_without_data(user):
    """Sin ref_lap, el Paso 2 muestra mensaje pidiendo ir al Paso 1."""
    from nicegui import ui
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find(kind=ui.button, content="Análisis").click()
    # Guard: "Primero carga los archivos en el Paso 1."
    await user.should_see("Primero carga")
