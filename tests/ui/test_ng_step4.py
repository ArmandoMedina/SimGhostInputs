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


@pytest.mark.asyncio
async def test_step4_compose_btn_disabled_without_inputs(user):
    """Componer video esta deshabilitado cuando video_input y overlay_input estan vacios."""
    import shutil

    from nicegui import ui

    from fantasma.ui.ng_app import main_page  # noqa: F401

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg no disponible en este entorno")

    await user.open("/")
    user.find("Video").click()
    await user.should_see("Componer video")

    # Con entradas vacias el boton debe estar deshabilitado (_props['disable'] = True)
    found = [
        e
        for e in user.client.elements.values()
        if isinstance(e, ui.button) and e._props.get("label") == "Componer video"
    ]
    assert found, "Boton 'Componer video' no encontrado en el DOM"
    assert found[0]._props.get("disable"), (
        "Boton 'Componer video' debe estar deshabilitado con video_input y overlay_input vacios"
    )
