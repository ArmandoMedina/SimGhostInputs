"""Regresion: boton 'Generar overlay' se deshabilita durante el render.

Guarda contra el bug de doble click que causaba PermissionError [WinError 5]
en PyInstaller al lanzar dos procesos multiprocessing simultaneos en native mode.

Requiere: pip install -e ".[ui-ng]"
Ejecutar:  pytest tests/ui/test_step3_render_guard.py -v
"""

import asyncio
import sys
import types

import pytest

pytest.importorskip(
    "nicegui.testing",
    reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'",
)


class _SimpleState:
    """Estado minimo para el wizard — cubre todos los atributos que ng_app y ng_step3 leen."""

    def __init__(self, ref_lap, drv_lap):
        # navegacion
        self.nav_step = 0
        self.flow_key = "overlay"
        self.flow_chosen = True
        # laps
        self.ref_lap = ref_lap
        self.drv_lap = drv_lap
        # analisis (no usados en paso 3)
        self.summary = None
        self.last_compose_video = None
        # paso 3
        self.corners = None
        self.corners_editable = False
        self.gear_shifts = None
        self.last_overlay = None
        self.last_pacenotes = None
        self.active_overlay_job = None
        self.auto_compose = False
        self.pending_autocompose = False
        self.active_overlay_job = None


class _NoOpTimer:
    """Timer sintetico sin scheduling real.

    ui.timer creado en _start_render persiste hasta que poll() lo auto-cancela
    (0.5 s). En Windows, el loop se cierra antes y NiceGUI lanza RuntimeError en
    teardown corrompiendo los tests siguientes. Este stub corta el problema de raiz.
    """

    def cancel(self):
        pass


@pytest.mark.asyncio
async def test_render_guard_prevents_double_start(user, monkeypatch, lap_factory):
    """Doble click en 'Generar overlay' no lanza dos renders simultaneos.

    Verifica:
    1. El primer clic inicia exactamente un job de render.
    2. El segundo clic es absorbido: boton deshabilitado + early-return en _start_render.
    3. start_bg_render se llama exactamente una vez aunque el boton se clickee dos veces.
    """
    from nicegui import ui as _ui

    # -- Job sintetico siempre en progreso (done=False) -------------------------
    started_jobs: list = []

    class _FakeRunningJob:
        done = False
        error = None
        result = None
        n = 0
        total = 100
        status = "Renderizando..."

        def cancel(self):
            pass

    def _fake_start_bg(fn, progress_kw="progress", **kwargs):
        job = _FakeRunningJob()
        started_jobs.append(job)
        return job

    # Sin ffmpeg el paso retorna antes del boton; se inyecta ruta fake para
    # que el flujo llegue a "Generar overlay" sin ffmpeg real en el runner.
    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    # Parche en el modulo ng_step3 (no en nicegui directamente).
    # Importar explicitamente antes de parcharlo: fantasma.ui.__init__ no
    # re-exporta ng_step3, por lo que la resolucion del string dotted-path falla
    # si el submodulo no esta aun en sys.modules.
    import fantasma.ui.ng_step3 as _ng_step3_mod

    monkeypatch.setattr(_ng_step3_mod, "start_bg_render", _fake_start_bg)

    # Modulo overlay sintetico: evita ImportError si los extras [overlay] no estan instalados
    _fake_overlay = types.ModuleType("fantasma.viz.overlay")
    _fake_overlay.render_overlay = lambda **kw: "/fake/overlay.webm"
    monkeypatch.setitem(sys.modules, "fantasma.viz.overlay", _fake_overlay)

    # ui.timer: no-op para evitar RuntimeError en teardown de Windows
    monkeypatch.setattr(_ui, "timer", lambda *a, **kw: _NoOpTimer())

    # -- Laps sinteticos via fixture del harness --------------------------------
    ref = lap_factory()
    drv = lap_factory()

    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr(_ng_mod, "AppState", lambda: _SimpleState(ref, drv))

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Paso 3")

    # Con ref_lap cargado el guard "Primero carga..." NO debe mostrarse
    await user.should_not_see("Primero carga")
    await user.should_see("Generar overlay")

    # -- Primer clic -----------------------------------------------------------
    # Filtrar por kind=ui.button para evitar que find() elija el label
    # "Paso 3 — Generar overlay HUD" (tiene menor id que el boton y matchea
    # el mismo texto, pero no tiene listeners de click).
    from nicegui import ui as _ng_ui

    user.find(kind=_ng_ui.button, content="Generar overlay").click()
    # Ceder el loop para que NiceGUI procese el evento de click y ejecute _start_render
    await asyncio.sleep(0)
    assert len(started_jobs) == 1, "El primer clic debe lanzar exactamente un job"

    # -- Segundo clic (guard activo) -------------------------------------------
    # El boton queda deshabilitado; en nicegui.testing, click() puede igualmente
    # invocar el callback, pero el early-return en _start_render lo descarta.
    user.find(kind=_ng_ui.button, content="Generar overlay").click()
    await asyncio.sleep(0)
    assert len(started_jobs) == 1, "El guard debe absorber el segundo clic (no lanzar job extra)"
