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
