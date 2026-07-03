"""Smoke tests NiceGUI — ng_step1 (Importar telemetria).

Verifica que el Paso 1 renderiza sin crash y muestra los elementos
clave de la UI de carga de archivos.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step1.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step1_renders_without_crash(user):
    """Navegar al Paso 1 no produce error; el heading es visible."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Botone de sidebar "Importar" navega al Paso 1
    user.find("Importar").click()
    # El heading del Paso 1 esta en ui.html; should_see busca en el contenido HTML
    await user.should_see("Paso 1")


@pytest.mark.asyncio
async def test_step1_upload_panels_visible(user):
    """El Paso 1 muestra las instrucciones de carga de archivos."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Importar").click()
    # El label de estado inicial indica que hay que subir el archivo de referencia
    await user.should_see("referencia")
