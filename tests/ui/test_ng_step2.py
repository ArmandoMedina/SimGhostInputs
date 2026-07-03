"""Smoke tests NiceGUI — ng_step2 (Analisis por curva).

Verifica que el Paso 2 renderiza sin crash en estado inicial
(sin archivos cargados) y muestra el mensaje de guardia correcto.

Nota: user.find("Análisis") también encuentra el brand HTML del sidebar
("Análisis de simracing") que tiene un ID menor que el botón. Se filtra
por kind=ui.button para garantizar que se clickea el botón correcto.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step2.py -v
"""

import ast
import sys
import types
from pathlib import Path

import pytest

_NG_STEP2 = Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step2.py"

pytest.importorskip(
    "nicegui.testing", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'"
)


# ---------------------------------------------------------------------------
# Guardia AST H-01c: ui.html no debe usarse como context manager (sin <slot>)
# ---------------------------------------------------------------------------

_NG_FILES = [
    Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step1.py",
    Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step2.py",
    Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step3.py",
    Path(__file__).parents[2] / "fantasma" / "ui" / "ng_step4.py",
    Path(__file__).parents[2] / "fantasma" / "ui" / "ng_helpers.py",
]


def _html_context_managers(src: str) -> list[int]:
    """Devuelve lineas donde ui.html(...) se usa como context manager (ast.With).

    El componente Vue de ui.html no tiene <slot>, asi que cualquier hijo
    NiceGUI se descarta en el renderer silenciosamente (H-01c).
    Los contenedores deben ser ui.element("div") o ui.column()/ui.row().
    """
    tree = ast.parse(src)
    bad_lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            expr = item.context_expr
            # Detectar ui.html(...) o ui.html(...).classes(...) etc. (cadena de llamadas)
            # Desenvolver cadena de atributos/llamadas hasta encontrar el Call raiz
            call = expr
            while isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                call = call.func.value
            if not isinstance(call, ast.Call):
                continue
            # call debe ser ui.html(...)
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "html"
                and isinstance(func.value, ast.Name)
                and func.value.id == "ui"
            ):
                bad_lines.append(node.lineno)
    return bad_lines


def test_no_ui_html_context_manager_in_ng_files():
    """Ningun ng_*.py usa ui.html(...) como context manager (Fix H-01c).

    ui.html monta un componente Vue sin <slot>: los hijos NiceGUI se descartan
    silenciosamente en el renderer aunque el WebSocket los mande.
    Los contenedores con hijos deben ser ui.element("div").classes(...) o
    ui.column()/ui.row().
    """
    violations: list[str] = []
    for path in _NG_FILES:
        src = path.read_text(encoding="utf-8")
        lines = _html_context_managers(src)
        for ln in lines:
            violations.append(f"{path.name}:{ln}")
    assert not violations, (
        "ui.html() usado como context manager (hijos descartados en renderer). "
        "Migrar a ui.element('div').classes(...) — H-01c.\n  " + "\n  ".join(violations)
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


def test_do_render_charts_no_accede_state_en_thread():
    """_do_render_charts no debe leer state.* dentro del closure (Fix H-01).

    app.storage.user solo puede usarse en contexto UI; en run.io_bound lanza
    'app.storage.user can only be used within a UI context'.
    Los valores de state deben capturarse ANTES de definir el closure.
    """
    tree = ast.parse(_NG_STEP2.read_text(encoding="utf-8"))
    fn = _find_fn_in_ast(tree, "_do_render_charts")
    assert fn is not None, "_do_render_charts no encontrada en ng_step2.py"
    accesses = _state_accesses(fn)
    assert not accesses, (
        "_do_render_charts accede a state.%s dentro del thread; "
        "captura las variables antes del closure en el contexto UI." % ", state.".join(accesses)
    )


def test_do_compare_no_accede_state_en_thread():
    """_do_compare no debe leer state.* dentro del closure (guardia de regresion).

    ref_lap, drv_lap y corners ya estan capturados como locales antes del closure.
    """
    tree = ast.parse(_NG_STEP2.read_text(encoding="utf-8"))
    fn = _find_fn_in_ast(tree, "_do_compare")
    assert fn is not None, "_do_compare no encontrada en ng_step2.py"
    accesses = _state_accesses(fn)
    assert not accesses, (
        "_do_compare accede a state.%s dentro del thread; "
        "captura las variables antes del closure en el contexto UI." % ", state.".join(accesses)
    )


def test_ui_image_nunca_recibe_bytes():
    """Ningun ui.image() en ng_step2.py debe recibir el resultado de f.read() o bytes crudos.

    ui.image() acepta str/Path/PIL_Image unicamente. Pasar bytes crea un elemento
    zombie con _props['src'] = bytes que no es JSON-serializable; el outbox descarta
    el batch completo de actualizaciones DOM (H-01b).

    Detectamos el patron: ui.image(<expr>.read()) donde <expr> es cualquier nombre.
    """
    src = _NG_STEP2.read_text(encoding="utf-8")
    tree = ast.parse(src)

    bad_calls: list[str] = []
    for node in ast.walk(tree):
        # Buscar Call nodes donde la funcion es ui.image(...)
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "image"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ui"
        ):
            continue
        # Revisar cada argumento posicional
        for arg in node.args:
            # Detectar patron <name>.read() o <expr>.read()
            if (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Attribute)
                and arg.func.attr == "read"
            ):
                bad_calls.append(
                    "linea %d: ui.image(%s.read(...))"
                    % (
                        node.lineno,
                        ast.unparse(arg.func.value) if hasattr(ast, "unparse") else "?",
                    )
                )
            # Detectar literal bytes b"..."
            if isinstance(arg, ast.Constant) and isinstance(arg.value, bytes):
                bad_calls.append("linea %d: ui.image(b'...')" % node.lineno)

    assert not bad_calls, (
        "ui.image() recibe bytes en ng_step2.py (H-01b). "
        "Usa ui.image(p) con la ruta local — NiceGUI la sirve estaticamente. "
        "Sitios a corregir:\n  " + "\n  ".join(bad_calls)
    )


@pytest.mark.asyncio
async def test_step2_heading_visible(user):
    """El Paso 2 muestra su heading aunque no haya datos cargados."""
    from nicegui import ui

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Filtrar por kind=ui.button para evitar el HTML del sidebar-brand
    # que también contiene "Análisis de simracing"
    user.find(kind=ui.button, content="Análisis").click()
    await user.should_see("Paso 2")


@pytest.mark.asyncio
async def test_step2_guard_without_data(user):
    """Sin ref_lap, el Paso 2 muestra mensaje pidiendo ir al Paso 1."""
    from nicegui import ui

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find(kind=ui.button, content="Análisis").click()
    # Guard: "Primero carga los archivos en el Paso 1."
    await user.should_see("Primero carga")


# ---------------------------------------------------------------------------
# Smoke: render_charts via run.io_bound (Fix H-01)
# ---------------------------------------------------------------------------


class _StateWithSummary:
    """Estado mínimo con summary pre-cargado para ejercer la rama de render_charts."""

    def __init__(self, ref_lap):
        self.nav_step = 0
        self.flow_key = "analisis"
        self.flow_chosen = True
        self.ref_lap = ref_lap
        self.drv_lap = None
        self.corners = []
        self.corners_editable = False
        self.summary = {
            "avisos": [],
            "ref_laptime": 90.0,
            "drv_laptime": 92.5,
            "total_delta": 2.5,
        }
        self.rows = []
        self.trace = []
        self.charts_paths = None
        self.last_overlay = None
        self.last_compose_video = None


@pytest.mark.asyncio
async def test_step2_renders_with_summary_and_charts_mocked(user, monkeypatch, lap_factory):
    """Paso 2 renderiza sin crash con summary pre-cargado; render_charts ejecutado via run.io_bound.

    Mocked: render_charts devuelve [] rapidamente para evitar matplotlib real.
    Verifica que el computo pesado fue delegado a run.io_bound (mock fue invocado).
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod

    charts_called = []

    def _fake_render_charts(trace, rows, corners, outdir, top=None):
        charts_called.append(True)
        return []

    _fake_charts_mod = types.ModuleType("fantasma.viz.charts")
    _fake_charts_mod.render_charts = _fake_render_charts
    monkeypatch.setitem(sys.modules, "fantasma.viz.charts", _fake_charts_mod)

    ref = lap_factory()
    monkeypatch.setattr(_ng_mod, "AppState", lambda: _StateWithSummary(ref))

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find(kind=_ui.button, content="Análisis").click()
    await user.should_see("Paso 2")
    await user.should_not_see("Primero carga")
    assert charts_called, "render_charts no fue invocado — run.io_bound no lo ejecuto"
