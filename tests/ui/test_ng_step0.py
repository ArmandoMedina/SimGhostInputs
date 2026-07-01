"""Smoke tests NiceGUI — ng_step0.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step0.py -v
"""

import pytest

pytest.importorskip("nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'")
pytest_plugins = ["nicegui.testing"]


@pytest.fixture
def user(user):
    return user


@pytest.mark.asyncio
async def test_step0_hero_visible(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401
    await user.open("/")
    await user.should_see("SimGhostInputs")


@pytest.mark.asyncio
async def test_step0_flow_cards_visible(user):
    from fantasma.ui.ng_app import main_page  # noqa: F401
    await user.open("/")
    await user.should_see("Solo analisis")
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
