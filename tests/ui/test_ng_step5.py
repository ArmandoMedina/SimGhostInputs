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


# ---------------------------------------------------------------------------
# Estado: analisis presente pero sin drv_lap
# ---------------------------------------------------------------------------


class _StateWithRowsNoDrv:
    """Estado minimo con rows y corners pero sin vuelta del piloto."""

    def __init__(self):
        self.nav_step = 0
        self.flow_key = "compose"
        self.flow_chosen = True
        self.ref_lap = None
        self.drv_lap = None  # sin vuelta -> Aplicar sonido deshabilitado
        self.corners = [{"name": "C01", "apex_d": 100}]
        self.corners_editable = False
        self.summary = None
        self.rows = [{"name": "C01", "apex_d": 100, "time_lost": 0.5}]
        self.trace = []
        self.charts_paths = None
        self.last_overlay = None
        self.last_compose_video = None
        self.last_pacenotes = ""


@pytest.mark.asyncio
async def test_step5_apply_btn_disabled_without_drv_lap(user, monkeypatch):
    """Sin drv_lap, el boton Aplicar sonido esta deshabilitado."""
    from nicegui import ui

    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithRowsNoDrv())

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    # El guard no se activa porque rows y corners estan presentes
    await user.should_not_see("Primero corre el Analisis")
    await user.should_see("Aplicar sonido")

    # Con drv_lap=None el boton debe estar deshabilitado
    found = [
        e
        for e in user.client.elements.values()
        if isinstance(e, ui.button) and e._props.get("label") == "Aplicar sonido"
    ]
    assert found, "Boton 'Aplicar sonido' no encontrado en el DOM"
    assert found[0]._props.get("disable"), (
        "Boton 'Aplicar sonido' debe estar deshabilitado cuando drv_lap es None"
    )
