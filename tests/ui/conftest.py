"""Fixtures compartidas para tests de UI NiceGUI."""


def pytest_configure(config):
    """Parchea Storage.clear al iniciar la sesión de tests.

    En Windows, pathlib.Path.unlink() falla con PermissionError cuando el
    file handle de NiceGUI sigue abierto en teardown. Como es limpieza de
    archivos temporales de test, ignoramos el error silenciosamente.
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
