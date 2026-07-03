"""Smoke tests NiceGUI — ng_step0.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step0.py -v
"""

import pytest

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


@pytest.mark.asyncio
async def test_step0_hero_visible(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    await user.should_see("SimGhostInputs")


@pytest.mark.asyncio
async def test_step0_flow_cards_visible(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    await user.should_see("Solo an")
    await user.should_see("Solo overlay")
    await user.should_see("Video con HUD")


@pytest.mark.asyncio
async def test_step0_question_label(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    await user.should_see("quieres obtener hoy")


@pytest.mark.asyncio
async def test_step0_start_button_visible(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    await user.should_see("Empezar")


@pytest.mark.asyncio
async def test_step0_no_ffmpeg_warning_without_flow_chosen(user):
    """No muestra aviso ffmpeg hasta que el usuario elige un flujo explícitamente."""
    from unittest.mock import patch

    from fantasma.ui.ng_app import main_page  # noqa: F401

    with patch("fantasma.ui.ng_step0.shutil.which", return_value=None):
        await user.open("/")
        await user.should_not_see("ffmpeg no detectado")


@pytest.mark.asyncio
async def test_step0_no_card_selected_on_load(user):
    """F-01: ninguna tarjeta muestra checkmark al cargar — estado neutro."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    await user.should_not_see("Seleccionado")
