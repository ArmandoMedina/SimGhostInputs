"""Smoke tests NiceGUI — ng_step3 (Generar overlay HUD).

Verifica que el Paso 3 renderiza sin crash en estado inicial
(sin archivos cargados) y muestra el mensaje de guardia correcto.

Requiere: pip install -e ".[ui-ng]"
Ejecutar: pytest tests/ui/test_ng_step3.py -v
"""

import ast
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
async def test_step3_guard_without_data(user):
    """Sin ref_lap, el Paso 3 muestra mensaje pidiendo ir al Paso 1."""
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
        self.last_overlay = None


class _NoOpTimer:
    def cancel(self):
        pass


@pytest.mark.asyncio
async def test_step3_renders_with_ref_lap_and_detect_corners_mocked(user, monkeypatch, lap_factory):
    """Paso 3 renderiza sin crash con ref_lap; detect_corners ejecutado via run.io_bound.

    Mocked: detect_corners devuelve corners vacios rapidamente para evitar CPU real.
    El boton 'Generar overlay' debe ser visible al final del render.
    """
    from nicegui import ui as _ui

    import fantasma.ui.ng_app as _ng_mod

    # Stub para corners: evita importar fantasma.core.corners real
    _fake_corners_mod = types.ModuleType("fantasma.core.corners")
    _fake_corners_mod.detect_corners = lambda lap: ([], {})
    _fake_corners_mod.extract_milestones = lambda lap, evs: []
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
