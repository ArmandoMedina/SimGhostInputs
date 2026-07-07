"""Fixtures compartidas para tests de UI NiceGUI."""

import logging


class _DropBenignNiceguiJsTimeout(logging.Filter):
    """Descarta el ERROR benigno del simulador ``User`` de NiceGUI.

    El fixture ``user`` de ``nicegui.testing`` falla el test si hubo CUALQUIER
    log de nivel ERROR durante la fase de llamada (``user_plugin.py``:
    ``pytest.fail('There were unexpected ERROR logs.')``). En el simulador no
    hay navegador, así que los ``ui.run_javascript`` (fire-and-forget del render
    y los internos de NiceGUI al conectar) nunca reciben respuesta y NiceGUI
    loguea ``JavaScript did not respond within 1.0 s`` ~1 s después. En CI lento
    ese timeout cae dentro de la ventana de un test cualquiera (a menudo otro
    distinto al que lo originó) y lo tumba de forma flaky — visto en Paso 2 y
    Paso 3, sin relación con lo que prueban.

    Es ruido del simulador, no un fallo del producto: se descarta por mensaje.
    Cualquier OTRO ERROR sigue propagando y tumbando el test.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "JavaScript did not respond" not in record.getMessage()


def pytest_configure(config):
    """Parcha el teardown de Storage y silencia el ERROR flaky de JS del simulador.

    En Windows, ``pathlib.Path.unlink()`` falla con ``PermissionError`` cuando el
    file handle de NiceGUI sigue abierto en teardown. Como es limpieza de
    archivos temporales de test, se ignora silenciosamente.

    Además se filtra el ERROR benigno de JS-timeout del simulador (ver
    ``_DropBenignNiceguiJsTimeout``), que hacía flaky la suite de UI en CI.
    """
    try:
        from nicegui.storage import Storage

        _orig = Storage.clear

        def _safe_clear(self):
            try:
                _orig(self)
            except PermissionError:
                pass

        Storage.clear = _safe_clear
    except ImportError:
        pass

    logging.getLogger("nicegui").addFilter(_DropBenignNiceguiJsTimeout())
