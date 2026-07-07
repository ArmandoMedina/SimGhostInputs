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
    """Sin analisis previo el guard muestra orientacion y dirige al Paso 2."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    # El guard ahora distingue los dos caminos
    await user.should_see("GENERAR")
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
        self.cue_config = None


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
    await user.should_not_see("Primero corre el Análisis")
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


# ---------------------------------------------------------------------------
# Flujo pacenotes: next button y guard no oculta panel②
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pacenotes_next_from_step2_goes_to_step5(user):
    """Con flow_key='pacenotes', _render_next_btn en el Paso 2 apunta al Paso 5."""
    from nicegui import ui as _ui

    from fantasma.ui.ng_step2 import _render_next_btn

    class _St:
        flow_key = "pacenotes"

    @_ui.page("/test-pn-next-btn")
    def _page():
        _render_next_btn(_St(), 2, lambda _: None)

    await user.open("/test-pn-next-btn")
    await user.should_see("Pace Notes")


class _StateNoPaceData:
    """Estado sin rows ni corners — prueba que el guard de panel① no oculta panel②."""

    def __init__(self):
        self.nav_step = 0
        self.flow_key = "pacenotes"
        self.flow_chosen = True
        self.ref_lap = None
        self.drv_lap = None
        self.corners = None
        self.corners_editable = False
        self.summary = None
        self.rows = None
        self.trace = []
        self.charts_paths = None
        self.last_overlay = None
        self.last_compose_video = None
        self.last_pacenotes = ""


@pytest.mark.asyncio
async def test_guard_does_not_hide_panel2_without_analysis(user, monkeypatch):
    """Sin rows/corners el panel② sigue siendo visible — el guard solo bloquea panel①."""
    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateNoPaceData())

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    # Panel① muestra el guard con orientacion
    await user.should_see("GENERAR")
    # Panel② sigue renderizado
    await user.should_see("Aplicar sonido")


# ---------------------------------------------------------------------------
# Cues: selección, prioridad y perfiles (WS-4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step5_cues_section_renders_without_exception(user, monkeypatch):
    """Con rows/corners presentes, la sección de cues renderiza sin crash."""
    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithRowsNoDrv())

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    await user.should_see("Cues: selección y prioridad")
    await user.should_see("Perfiles de cues")


@pytest.mark.asyncio
async def test_step5_cues_have_checkbox_and_priority_control(user, monkeypatch):
    """Cada tipo de cue implementado trae su checkbox y su control de prioridad."""
    from nicegui import ui

    import fantasma.ui.ng_app as _ng_mod
    from fantasma.ui.ng_step5 import _CUE_LABELS, _CUE_TYPES

    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithRowsNoDrv())

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    await user.should_see("Cues: selección y prioridad")

    checkbox_texts = {e.text for e in user.client.elements.values() if isinstance(e, ui.checkbox)}
    for cue_type in _CUE_TYPES:
        label = _CUE_LABELS[cue_type]
        assert label in checkbox_texts, "Falta la casilla de '%s'" % label

    priority_numbers = [
        e
        for e in user.client.elements.values()
        if isinstance(e, ui.number) and e._props.get("label") == "Prioridad"
    ]
    assert len(priority_numbers) == len(_CUE_TYPES), (
        "Se esperaban %d controles de Prioridad (uno por tipo de cue), se "
        "encontraron %d" % (len(_CUE_TYPES), len(priority_numbers))
    )

    # coast trae ademas la casilla "solo curvas sin frenada"
    assert "Solo curvas sin frenada" in checkbox_texts

    # gear queda deshabilitado (slot sin implementar), no forma parte del catalogo activo
    gear_checkboxes = [
        e
        for e in user.client.elements.values()
        if isinstance(e, ui.checkbox) and e.text == "Cambio de marcha"
    ]
    assert gear_checkboxes and not gear_checkboxes[0].enabled


@pytest.mark.asyncio
async def test_step5_cue_config_persists_to_state(user, monkeypatch):
    """Apagar un checkbox de cue persiste el cambio en AppState.cue_config."""
    from nicegui import ui

    import fantasma.ui.ng_app as _ng_mod

    _state = _StateWithRowsNoDrv()
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _state)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Pace Notes").click()
    await user.should_see("Cues: selección y prioridad")

    apex_checkbox = next(
        e for e in user.client.elements.values() if isinstance(e, ui.checkbox) and e.text == "Ápex"
    )
    # Ápex esta apagado por defecto (DEFAULT_CONFIG); lo prendemos y verificamos
    # que el cambio se refleje en el cue_config persistido.
    apex_checkbox.set_value(True)
    await user.should_see("Cues: selección y prioridad")

    assert getattr(_state, "cue_config", None) is not None
    assert _state.cue_config.get("apex", {}).get("enabled") is True
