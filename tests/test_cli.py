"""Regresion CLI — contratos de callbacks de progreso.

El test central (test_overlay_progress_acepta_status_kwarg) habria fallado con
el codigo anterior, donde el CLI definia:

    def progress(n, total):   # dentro de cmd_overlay

y overlay.py lo invoca con:

    progress(enc, n_frames, status="Codificando video... frame N / M")

provocando TypeError: progress() got an unexpected keyword argument 'status',
que el except BaseException mataba ffmpeg y re-lanzaba -> webm vacio + exit 1.
"""

from fantasma.cli import _overlay_progress


def test_overlay_progress_acepta_status_kwarg():
    """Habria fallado antes del fix: overlay.py llama progress(n, total, status=...)
    pero el CLI definia def progress(n, total): sin aceptar status."""
    # No debe lanzar TypeError
    _overlay_progress(5, 100, status="Codificando video... frame 5 / 100")


def test_overlay_progress_sin_status_kwarg():
    """Tambien funciona con llamada puramente posicional."""
    _overlay_progress(5, 100)


def test_overlay_progress_total_cero_no_crashea():
    """Division por cero protegida cuando total=0."""
    _overlay_progress(0, 0, status="iniciando")


def test_overlay_progress_firma_compatible_con_ui():
    """Homologa la firma con el callback de la UI (_helpers.py:222):
    def _cb(n, total, status=None) — mismos tres parametros."""
    import inspect

    sig = inspect.signature(_overlay_progress)
    params = list(sig.parameters.keys())
    assert params == ["n", "total", "status"]
    # status debe tener default None
    assert sig.parameters["status"].default is None
