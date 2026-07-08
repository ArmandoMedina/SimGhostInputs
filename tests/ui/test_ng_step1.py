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


# ---------------------------------------------------------------------------
# I1: indicadores de listo — clase 'ok' aparece cuando ref_laps ya está cargado
# ---------------------------------------------------------------------------


class _StateWithRefLaps:
    """Estado mínimo con ref_laps ya cargado para probar el render inicial."""

    def __init__(self, ref_lap):
        self.nav_step = 1
        self.flow_key = "overlay"
        self.flow_chosen = True
        self.ref_lap = ref_lap
        self.ref_laps = [ref_lap]
        self.drv_lap = None
        self.drv_laps = None
        self.ref_path = ""
        self.drv_path = ""
        self.ref_name = "ref.csv"
        self.drv_name = ""
        self.corners = None
        self.corners_editable = False
        self.gear_shifts = None
        self.summary = None
        self.last_overlay = None
        self.last_compose_video = None
        self.last_pacenotes = None


@pytest.mark.asyncio
async def test_step1_ref_indicator_ok_when_preloaded(user, monkeypatch, lap_factory):
    """El indicador 'Referencia' muestra clase ok cuando ref_laps ya está cargado.

    Valida que el render inicial del container de indicadores respeta el estado
    de la vuelta — sin necesitar un upload real (I1).
    """
    import fantasma.ui.ng_app as _ng_mod

    ref = lap_factory()
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithRefLaps(ref))

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Importar").click()
    await user.should_see("Paso 1")

    # Busca el contenedor de indicadores y verifica que el HTML del indicador
    # de referencia tiene la clase 'ok' (verde) en el render inicial.
    from nicegui.elements.html import Html

    html_els = [e for e in user.client.elements.values() if isinstance(e, Html)]
    ref_indicator_found = any(
        "readiness-item ok" in (getattr(e, "content", "") or "")
        and "Referencia" in (getattr(e, "content", "") or "")
        for e in html_els
    )
    assert ref_indicator_found, (
        "El indicador 'Referencia' no tiene clase 'ok' en el render inicial "
        "aunque ref_laps está pre-cargado (I1)"
    )


# ---------------------------------------------------------------------------
# "Detectar curvas automaticamente": tambien detecta cambios de marcha
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step1_detectar_curvas_puebla_gear_shifts(user, monkeypatch, lap_factory):
    """El boton 'Detectar curvas automaticamente' tambien corre
    detect_gear_shifts sobre la vuelta de REFERENCIA (fastest_lap de
    ref_laps) y lo guarda en state.gear_shifts, junto con state.corners.

    Parchea funciones puntuales del modulo REAL (monkeypatch.setattr), no
    reemplaza fantasma.core.corners entero en sys.modules: un reemplazo total
    rompe imports transitivos ajenos (p.ej. fantasma/core/__init__.py hace
    `from .corners import ..., samples`) si algo dispara esa importacion
    fresca mientras el modulo esta sustituido (regresion detectada en esta
    sesion combinando tests)."""
    import fantasma.core.corners as _real_corners
    import fantasma.ui.ng_app as _ng_mod

    _gear_shifts = [{"distance": 150, "gear_from": 1, "gear_to": 2}]
    _seen_gear_shift_lap = []

    monkeypatch.setattr(_real_corners, "detect_corners", lambda lap: ([], {}))
    monkeypatch.setattr(_real_corners, "extract_milestones", lambda lap, evs: [])

    def _fake_detect_gear_shifts(lap):
        _seen_gear_shift_lap.append(lap)
        return _gear_shifts

    monkeypatch.setattr(_real_corners, "detect_gear_shifts", _fake_detect_gear_shifts)

    ref = lap_factory()
    _state = _StateWithRefLaps(ref)
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _state)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Importar").click()
    await user.should_see("Paso 1")

    user.find("Detectar curvas automaticamente").click()
    # should_see tambien revisa ui.notify() (UserNotify.contains) -- espera a
    # que el handler async termine antes de leer el estado mutado.
    await user.should_see("curvas detectadas automaticamente")

    assert _state.gear_shifts == _gear_shifts
    # detect_gear_shifts se llamo con la vuelta de REFERENCIA (fastest_lap de
    # ref_laps), no con una vuelta del piloto.
    assert _seen_gear_shift_lap == [ref]
