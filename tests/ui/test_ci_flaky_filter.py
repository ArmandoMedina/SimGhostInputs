"""El filtro de conftest silencia el ERROR flaky de JS del simulador de NiceGUI.

Regresión de la inestabilidad de CI: el fixture ``user`` de nicegui.testing
tumbaba tests al ver el ERROR 'JavaScript did not respond within 1.0 s' que el
simulador (sin navegador) emite ~1 s tarde. El filtro de tests/ui/conftest.py
lo descarta por mensaje; cualquier otro ERROR sigue pasando.
"""

import logging


def test_js_timeout_error_se_filtra_pero_los_reales_no(caplog):
    caplog.set_level(logging.ERROR)
    logger = logging.getLogger("nicegui")

    logger.error("JavaScript did not respond within 1.0 s")
    logger.error("un error de verdad que SÍ debe tumbar el test")

    errores = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    # el ruido benigno del simulador no llega a caplog (no falla el fixture user)
    assert "JavaScript did not respond within 1.0 s" not in errores
    # pero un ERROR real sigue capturándose
    assert any("un error de verdad" in m for m in errores)
