"""Fixtures para el smoke visual de la UI NiceGUI (Playwright).

Levanta la app NiceGUI en un proceso aparte (puerto 8765) con SGI_HEADLESS=1
(sin ventana de escritorio, sin auto-open del browser) y lo mata al terminar
la sesion de pytest. Session-scope para no reiniciar NiceGUI entre tests del
mismo modulo.

pw_page: devuelve una pagina de Chromium headless apuntando al servidor;
         skipea limpiamente si Chromium no esta instalado.
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

_PORT = 8765
_BASE_URL = f"http://localhost:{_PORT}"


def _wait_for_nicegui(url: str, timeout: int = 30) -> bool:
    """Sondea la raiz de NiceGUI hasta que responde 200 o se agota el tiempo."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def nicegui_url():
    """Servidor NiceGUI local en el puerto 8765.

    Session-scope: la app arranca una sola vez y se comparte entre todos los
    tests visuales de la sesion. Se termina el proceso al finalizar pytest.

    Usa SGI_HEADLESS=1 para que ng_app.py arranque con native=False y
    show=False, sin abrir ventana de escritorio ni browser.
    """
    pytest.importorskip("nicegui")

    env = os.environ.copy()
    env["SGI_HEADLESS"] = "1"

    # Eliminar PYTEST_CURRENT_TEST del entorno del subproceso:
    # NiceGUI detecta esa variable y entra en modo test interno (lee
    # NICEGUI_SCREEN_TEST_PORT) en vez de arrancar el servidor normal.
    env.pop("PYTEST_CURRENT_TEST", None)

    proc = subprocess.Popen(
        [sys.executable, "-m", "fantasma.ui.ng_app"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ready = _wait_for_nicegui(_BASE_URL, timeout=30)
    if not ready:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        pytest.skip("NiceGUI no arranco en 30 s -- test visual omitido.")

    yield _BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def pw_page(nicegui_url):
    """Pagina de Chromium headless apuntando al servidor NiceGUI.

    Skipea limpiamente si el browser no esta instalado
    (instala con: playwright install chromium).
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:
            pytest.skip(
                f"Chromium no disponible (instala con `playwright install chromium`): {exc}"
            )

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()

        yield page

        context.close()
        browser.close()
