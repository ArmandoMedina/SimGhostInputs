"""Script de captura de evidencia para mariana-20260705-pacenotes."""
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

PORT = 8765
BASE_URL = f"http://localhost:{PORT}"
OUT_DIR = pathlib.Path(__file__).parent

env = os.environ.copy()
env["SGI_HEADLESS"] = "1"
env.pop("PYTEST_CURRENT_TEST", None)

REPO = pathlib.Path(__file__).parent.parent.parent

proc = subprocess.Popen(
    [sys.executable, "-m", "fantasma.ui.ng_app"],
    cwd=str(REPO),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

print("Esperando NiceGUI...")
deadline = time.monotonic() + 35
ready = False
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(BASE_URL, timeout=2) as resp:
            if resp.status == 200:
                ready = True
                break
    except Exception:
        pass
    time.sleep(0.5)

if not ready:
    proc.terminate()
    proc.wait()
    print("ERROR: NiceGUI no arranco en 35s")
    sys.exit(1)

print("NiceGUI listo. Capturando...")

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page = ctx.new_page()

    # --- Paso 0: 4 tarjetas ---
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=20000)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT_DIR / "paso0_4tarjetas.png"), full_page=False)
    print("  paso0_4tarjetas.png OK")

    # --- Paso 5 via sidebar ---
    # El sidebar tiene un boton "Pace Notes" en la seccion Salidas
    pn_btn = page.locator("button", has_text="Pace Notes")
    if pn_btn.count() > 0:
        pn_btn.first.click()
    else:
        # Fallback: navegar directamente via URL no funciona con NiceGUI SPA;
        # intentar con el locator de texto generico
        page.locator("text=Pace Notes").first.click()

    page.wait_for_timeout(2000)
    page.screenshot(path=str(OUT_DIR / "paso5_dos_paneles.png"), full_page=True)
    print("  paso5_dos_paneles.png OK")

    page.screenshot(path=str(OUT_DIR / "paso5_viewport.png"), full_page=False)
    print("  paso5_viewport.png OK")

    ctx.close()
    browser.close()

proc.terminate()
try:
    proc.wait(timeout=5)
except subprocess.TimeoutExpired:
    proc.kill()
    proc.wait()

print("Capturas completadas OK")
