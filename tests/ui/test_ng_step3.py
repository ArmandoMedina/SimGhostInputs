"""Smoke tests NiceGUI — ng_step3 (Generar overlay HUD).

Verifica que el Paso 3 renderiza sin crash en estado inicial
(sin archivos cargados) y muestra el mensaje de guardia correcto.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step3.py -v
"""

import ast
import asyncio
import sys
import types
from pathlib import Path

import pytest

_NG_STEP3 = Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step3.py"

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


# ---------------------------------------------------------------------------
# Guardia AST: closures de run.io_bound no deben acceder state.* en el thread
# ---------------------------------------------------------------------------


def _find_fn_in_ast(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    """Busca la primera FunctionDef con ese nombre (incluye funciones anidadas)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _state_accesses(fn: ast.FunctionDef) -> list[str]:
    """Devuelve lista de atributos de state.* accedidos dentro de fn."""
    return [
        node.attr
        for node in ast.walk(fn)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "state"
    ]


def test_detect_no_accede_state_en_thread():
    """_detect no debe leer state.* dentro del closure (Fix C-02).

    app.storage.user solo puede usarse en contexto UI; en run.io_bound lanza
    'app.storage.user can only be used within a UI context'.
    ref_lap debe capturarse ANTES de definir el closure (line 45 de ng_step3.py).
    """
    tree = ast.parse(_NG_STEP3.read_text(encoding="utf-8"))
    fn = _find_fn_in_ast(tree, "_detect")
    assert fn is not None, "_detect no encontrada en ng_step3.py"
    accesses = _state_accesses(fn)
    assert not accesses, (
        "_detect accede a state.%s dentro del thread; "
        "captura las variables antes del closure en el contexto UI." % ", state.".join(accesses)
    )


@pytest.mark.asyncio
async def test_step3_heading_visible(user):
    """El Paso 3 muestra su heading aunque no haya datos cargados."""
    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Boton de sidebar "Overlay" navega al Paso 3
    user.find("Overlay").click()
    await user.should_see("Paso 3")


@pytest.mark.asyncio
async def test_step3_no_ffmpeg_shows_warning(user, monkeypatch):
    """Sin ffmpeg instalado, el Paso 3 muestra el aviso de instalacion."""
    monkeypatch.setattr("shutil.which", lambda name: None)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("ffmpeg no está instalado")


@pytest.mark.asyncio
async def test_step3_guard_without_data(user, monkeypatch):
    """Sin ref_lap, el Paso 3 muestra mensaje pidiendo ir al Paso 1."""
    # Sin ffmpeg el paso retorna antes del guard; se inyecta una ruta fake
    # para que el flujo llegue al guard "Primero carga" sin ffmpeg real.
    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    # Guard: "Primero carga los archivos en el Paso 1."
    await user.should_see("Primero carga")


# ---------------------------------------------------------------------------
# Smoke: detect_corners via run.io_bound (Fix C-02)
# ---------------------------------------------------------------------------


class _StateWithRef:
    """Estado minimo con ref_lap cargado para ejercer la rama de detect_corners."""

    def __init__(self, ref_lap):
        self.nav_step = 0
        self.flow_key = "overlay"
        self.flow_chosen = True
        self.ref_lap = ref_lap
        self.drv_lap = None
        self.summary = None
        self.last_compose_video = None
        self.corners = None
        self.corners_editable = False
        self.gear_shifts = None
        self.last_overlay = None
        self.last_pacenotes = None
        self.active_overlay_job = None
        self.auto_compose = False
        self.pending_autocompose = False


class _StateForCompose:
    """Estado minimo con flow_key='compose' para el checkbox de auto-compose."""

    def __init__(self, ref_lap):
        self.nav_step = 0
        self.flow_key = "compose"
        self.flow_chosen = True
        self.ref_lap = ref_lap
        self.drv_lap = None
        self.summary = None
        self.last_compose_video = None
        self.corners = None
        self.corners_editable = False
        self.gear_shifts = None
        self.last_overlay = None
        self.last_pacenotes = None
        self.auto_compose = False
        self.pending_autocompose = False
        self.compose_offset = 0.0
        self.active_overlay_job = None


class _NoOpTimer:
    def cancel(self):
        pass


@pytest.mark.asyncio
async def test_step3_auto_compose_checkbox_visible_in_compose_flow(user, monkeypatch, lap_factory):
    """El checkbox 'componer automaticamente' aparece cuando flow_key=='compose'.

    Con flow_key='overlay' ese checkbox NO se renderiza (no aplica al flujo
    solo-overlay). La clase _StateForCompose siembra flow_key='compose'.
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
    _fake_corners_mod.detect_gear_shifts = lambda lap: []
    monkeypatch.setitem(sys.modules, "fantasma.core.corners", _fake_corners_mod)

    monkeypatch.setattr(_ui, "timer", lambda *a, **kw: _NoOpTimer())

    ref = lap_factory()
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateForCompose(ref))

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Paso 3")
    await user.should_not_see("Primero carga")
    await user.should_see("componer automáticamente")


@pytest.mark.asyncio
async def test_step3_renders_with_ref_lap_and_detect_corners_mocked(user, monkeypatch, lap_factory):
    """Paso 3 renderiza sin crash con ref_lap; detect_corners ejecutado via run.io_bound.

    Mocked: detect_corners devuelve corners vacios rapidamente para evitar CPU real.
    El boton 'Generar overlay' debe ser visible al final del render.
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod

    # Sin ffmpeg el paso retorna antes del boton; se inyecta ruta fake.
    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    # Stub para corners: evita importar fantasma.core.corners real
    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
    _fake_corners_mod.detect_gear_shifts = lambda lap: []
    monkeypatch.setitem(sys.modules, "fantasma.core.corners", _fake_corners_mod)

    # ui.timer: no-op para evitar RuntimeError en teardown de Windows
    monkeypatch.setattr(_ui, "timer", lambda *a, **kw: _NoOpTimer())

    ref = lap_factory()
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithRef(ref))

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Paso 3")
    await user.should_not_see("Primero carga")
    await user.should_see("Generar overlay")


@pytest.mark.asyncio
async def test_step3_detect_puebla_state_gear_shifts(user, monkeypatch, lap_factory):
    """La deteccion bajo demanda del Paso 3 tambien detecta cambios de marcha
    sobre la vuelta de REFERENCIA (ref_lap) y los guarda en state.gear_shifts,
    con el mismo mecanismo (run.io_bound) que detect_corners."""
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod

    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    _gear_shifts = [{"distance": 250, "gear_from": 2, "gear_to": 3}]
    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
    _fake_corners_mod.detect_gear_shifts = lambda lap: _gear_shifts
    monkeypatch.setitem(sys.modules, "fantasma.core.corners", _fake_corners_mod)

    monkeypatch.setattr(_ui, "timer", lambda *a, **kw: _NoOpTimer())

    ref = lap_factory()
    _state = _StateWithRef(ref)
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _state)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Generar overlay")

    assert _state.gear_shifts == _gear_shifts


# ---------------------------------------------------------------------------
# Regresion BUG 1 -- poll() async: el encadenado auto-compose navega al Paso 4
# ---------------------------------------------------------------------------


def test_step3_autocompose_poll_navigates_to_step4():
    """poll() debe ser async def y usar await navigate() -- guard de BUG1.

    Si poll() fuera def (sync), llamar navigate(4) sin await devolveria un
    coroutine que se descartaria silenciosamente; state.nav_step no cambiaria
    a 4 y el encadenado auto-compose fallaria en silencio.

    El test detecta dos escenarios de regresion via analisis AST:
    - poll revertido a def (sync): no hay AsyncFunctionDef 'poll' -> falla.
    - await eliminado en navigate(4): no hay nodo Await sobre navigate -> falla.
    """
    tree = ast.parse(_NG_STEP3.read_text(encoding="utf-8"))

    # poll debe ser async def (no def sync)
    poll_async = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "poll"
    ]
    assert poll_async, (
        "poll no es async def en ng_step3.py. "
        "Si fuera def sync, navigate(4) retornaria un coroutine que se "
        "descartaria silenciosamente y state.nav_step no llegaria a 4."
    )

    # dentro de poll debe haber 'await navigate(...)'
    poll_fn = poll_async[0]
    await_navigate = [
        node
        for node in ast.walk(poll_fn)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "navigate"
    ]
    assert await_navigate, (
        "poll no contiene 'await navigate(...)' en ng_step3.py. "
        "Sin await, el coroutine de navigate se descarta silenciosamente."
    )


# ---------------------------------------------------------------------------
# Regresion ROADMAP: el job de render debe vivir en state, no en variable
# local -- navegar fuera del Paso 3 durante un render activo y volver no
# debe arrancar un segundo render sobre el mismo outdir.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step3_reentering_during_active_render_does_not_start_second_job(
    user, monkeypatch, lap_factory
):
    """Navegar a Inicio y volver al Paso 3 con un render activo no duplica el job.

    Antes del fix, el job vivia en un dict local a render() (job_holder); al
    navegar fuera y volver, render() se ejecutaba de nuevo desde cero y
    job_holder se recreaba vacio, así que el guard de _start_render no veía
    el render en background y un segundo clic (o incluso el propio
    render()) podía disparar un start_bg_render concurrente sobre el mismo
    outdir. Con el job en state.active_overlay_job, el guard lo sigue viendo
    aunque la funcion render() se re-ejecute, y en vez de mostrar el boton
    "Generar overlay" vuelve a enganchar el polling sobre el job existente.
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod
    import fantasma.ui.ng_step3 as _ng_step3_mod

    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
    _fake_corners_mod.detect_gear_shifts = lambda lap: []
    monkeypatch.setitem(sys.modules, "fantasma.core.corners", _fake_corners_mod)

    started_jobs: list = []

    class _FakeRunningJob:
        """Job sintetico que nunca termina — simula un render aun en curso."""

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

    monkeypatch.setattr(_ng_step3_mod, "start_bg_render", _fake_start_bg)

    _fake_overlay = types.ModuleType("fantasma.viz.overlay")
    _fake_overlay.render_overlay = lambda **kw: "/fake/overlay.webm"
    monkeypatch.setitem(sys.modules, "fantasma.viz.overlay", _fake_overlay)

    monkeypatch.setattr(_ui, "timer", lambda *a, **kw: _NoOpTimer())

    ref = lap_factory()
    _state = _StateWithRef(ref)
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _state)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Generar overlay")

    # Arranca el render (equivalente a pulsar "Generar overlay").
    user.find(kind=_ui.button, content="Generar overlay").click()
    await asyncio.sleep(0)
    assert len(started_jobs) == 1, "El clic debe lanzar exactamente un job"
    assert _state.active_overlay_job is started_jobs[0], (
        "El job debe quedar guardado en state.active_overlay_job, no solo en "
        "una variable local a render()"
    )

    # Navega fuera del Paso 3 con el render aun en curso (done=False).
    user.find("Inicio").click()
    await user.should_see("SimGhostInputs")

    # Vuelve al Paso 3: render() se re-ejecuta desde cero.
    user.find("Overlay").click()
    await user.should_see("Detener render")

    # No debe haberse arrancado un segundo job sobre el mismo outdir.
    assert len(started_jobs) == 1, (
        "Reentrar al Paso 3 con un render activo arranco un SEGUNDO render "
        "concurrente (bug: job_holder era local a render() y se perdia al "
        "navegar fuera)."
    )
    # El job heredado sigue siendo el mismo objeto (reenganchado, no reemplazado).
    assert _state.active_overlay_job is started_jobs[0]


@pytest.mark.asyncio
async def test_step3_active_overlay_job_cleared_after_completion(user, monkeypatch, lap_factory):
    """poll() debe liberar state.active_overlay_job cuando el job termina.

    Si no se limpia, el RenderJob terminado (con su threading.Event) se queda
    parado en app.storage.tab indefinidamente en vez de reflejar "sin render
    activo" (destapado en la revision del fix de ROADMAP linea 119).
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod
    import fantasma.ui.ng_step3 as _ng_step3_mod

    monkeypatch.setattr("shutil.which", lambda name: "/fake/ffmpeg")

    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
    _fake_corners_mod.detect_gear_shifts = lambda lap: []
    monkeypatch.setitem(sys.modules, "fantasma.core.corners", _fake_corners_mod)

    class _FakeJob:
        done = False
        error = None
        result = "/fake/outdir/overlay.webm"
        n = 100
        total = 100
        status = "Listo"

        def cancel(self):
            pass

    fake_job = _FakeJob()

    def _fake_start_bg(fn, progress_kw="progress", **kwargs):
        return fake_job

    monkeypatch.setattr(_ng_step3_mod, "start_bg_render", _fake_start_bg)

    _fake_overlay = types.ModuleType("fantasma.viz.overlay")
    _fake_overlay.render_overlay = lambda **kw: "/fake/overlay.webm"
    monkeypatch.setitem(sys.modules, "fantasma.viz.overlay", _fake_overlay)

    _timer_callbacks: list = []

    class _CapturingTimer:
        def __init__(self, callback):
            self.callback = callback

        def cancel(self):
            pass

    def _fake_timer(interval, callback):
        timer = _CapturingTimer(callback)
        _timer_callbacks.append(timer)
        return timer

    monkeypatch.setattr(_ui, "timer", _fake_timer)

    ref = lap_factory()
    _state = _StateWithRef(ref)
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _state)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Generar overlay")

    user.find(kind=_ui.button, content="Generar overlay").click()
    await asyncio.sleep(0)
    assert _state.active_overlay_job is fake_job

    # Simula que el job termino: el siguiente tick de poll() lo procesa.
    fake_job.done = True
    assert _timer_callbacks, "ui.timer no fue invocado por _watch_job"
    await _timer_callbacks[0].callback()

    assert _state.active_overlay_job is None, (
        "poll() debe liberar state.active_overlay_job al terminar el job, "
        "para no dejar un RenderJob colgado en app.storage.tab"
    )
    assert _state.last_overlay == fake_job.result
