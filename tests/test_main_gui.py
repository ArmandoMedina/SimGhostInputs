"""Regresion: main_gui.py llama multiprocessing.freeze_support() antes de run().

Bug original: el exe PyInstaller crasheaba con PermissionError [WinError 5] en
multiprocessing.reduction.duplicate al iniciar native mode despues de multiples
clics en 'Generar overlay'. Causa raiz: freeze_support() ausente en __main__.
"""

import ast
import pathlib


def test_main_gui_has_freeze_support():
    """Verifica estaticamente que main_gui.py tiene el guard correcto para PyInstaller.

    Parsea el AST y confirma:
    1. 'import multiprocessing' existe a nivel modulo.
    2. Hay un bloque if __name__ == '__main__': (o '__mp_main__').
    3. multiprocessing.freeze_support() se llama ANTES de run() dentro de ese bloque.
    """
    root = pathlib.Path(__file__).parent.parent
    src = (root / "main_gui.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    # 1. import multiprocessing a nivel modulo
    mp_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        and any(alias.name == "multiprocessing" for alias in node.names)
    ]
    assert mp_imports, "main_gui.py debe tener 'import multiprocessing' a nivel modulo"

    # 2. bloque if __name__ == '__main__': o '__mp_main__'
    main_blocks = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value in ("__main__", "__mp_main__")
    ]
    assert main_blocks, "main_gui.py debe tener bloque if __name__ == '__main__':"

    # 3. freeze_support() antes de run() en el cuerpo del bloque
    call_order = []
    for stmt in main_blocks[0].body:
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
            continue
        call = stmt.value
        if isinstance(call.func, ast.Attribute) and call.func.attr == "freeze_support":
            call_order.append("freeze_support")
        elif isinstance(call.func, ast.Name) and call.func.id == "run":
            call_order.append("run")

    assert "freeze_support" in call_order, (
        "main_gui.py debe llamar multiprocessing.freeze_support() en el bloque __main__"
    )
    assert "run" in call_order, "main_gui.py debe llamar run() en el bloque __main__"
    assert call_order.index("freeze_support") < call_order.index("run"), (
        "freeze_support() debe aparecer ANTES que run() en el bloque __main__"
    )
