"""Tests para el bind de red a localhost (Fix M-01 seguridad).

Verifica que ui.run() en ng_app.py y main.py pasan host='127.0.0.1'
para evitar que el servidor escuche en 0.0.0.0 (todas las interfaces).

Se usa inspeccion de AST en vez de ejecutar ui.run() directamente para
evitar contaminar el estado del harness de tests de NiceGUI.
"""

import ast
from pathlib import Path

_ROOT = Path(__file__).parents[2]


def _find_ui_run_host(path: Path) -> str | None:
    """Devuelve el valor de host= en la llamada ui.run() del archivo, o None."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "run"
            and isinstance(func.value, ast.Name)
            and func.value.id == "ui"
        ):
            continue
        for kw in node.keywords:
            if kw.arg == "host" and isinstance(kw.value, ast.Constant):
                return kw.value.value
    return None


def test_ng_app_run_usa_localhost():
    """ng_app.py pasa host='127.0.0.1' a ui.run (inspeccion de AST)."""
    host = _find_ui_run_host(_ROOT / "fantasma" / "ui" / "ng_app.py")
    assert host == "127.0.0.1", (
        f"ng_app.py: ui.run() debe recibir host='127.0.0.1'; encontrado: {host!r}"
    )


def test_main_py_run_usa_localhost():
    """main.py pasa host='127.0.0.1' a ui.run (inspeccion de AST)."""
    host = _find_ui_run_host(_ROOT / "main.py")
    assert host == "127.0.0.1", (
        f"main.py: ui.run() debe recibir host='127.0.0.1'; encontrado: {host!r}"
    )


def test_ng_app_run_tiene_ui_run():
    """ng_app.py contiene al menos una llamada ui.run() — guard de regresion."""
    tree = ast.parse((_ROOT / "fantasma" / "ui" / "ng_app.py").read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "run"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "ui"
    ]
    assert calls, "ng_app.py debe tener una llamada ui.run()"
