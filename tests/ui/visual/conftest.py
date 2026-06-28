"""Fixtures para el smoke visual de la UI Streamlit (Playwright).

Levanta la app Streamlit en un proceso aparte (puerto 8502) y lo mata al
terminar la sesion de pytest. Session-scope para no reiniciar Streamlit
entre tests del mismo modulo.

pw_page: devuelve una pagina de Chromium headless apuntando al servidor;
         skipea limpiamente si Chromium no esta instalado.
"""

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "fantasma" / "ui" / "app.py"
_PORT = 8502
_BASE_URL = f"http://localhost:{_PORT}"


def _wait_for_streamlit(url: str, timeout: int = 40) -> bool:
    """Sondea el endpoint de salud de Streamlit hasta que responde o se agota el tiempo."""
    health = f"{url}/_stcore/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health, timeout=2):
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def streamlit_url():
    """Servidor Streamlit local en el puerto 8502.

    Session-scope: la app arranca una sola vez y se comparte entre todos los
    tests visuales de la sesion. Se termina el proceso al finalizar pytest.
    """
    pytest.importorskip("streamlit")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP),
            "--server.port",
            str(_PORT),
            "--server.headless",
            "true",
            "--browser.serverAddress",
            "localhost",
            "--browser.gatherUsageStats",
            "false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ready = _wait_for_streamlit(_BASE_URL, timeout=40)
    if not ready:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        pytest.skip("Streamlit no arranco en 40 s -- test visual omitido.")

    yield _BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def pw_page(streamlit_url):
    """Pagina de Chromium headless apuntando al servidor Streamlit.

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
