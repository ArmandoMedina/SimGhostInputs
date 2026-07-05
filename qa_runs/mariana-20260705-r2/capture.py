"""Mariana QA visual — captura clic por clic del wizard NiceGUI (feat/pacenotes-ui).

Arranca fantasma.ui.ng_app en modo headless (SGI_HEADLESS=1, puerto 8765) y navega
cada pantalla con Playwright/Chromium, capturando estados: vacio, con datos,
botones habilitados/deshabilitados, loading, progreso.
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

RUN_DIR = Path(__file__).parent
SHOTS = RUN_DIR
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

REF_CSV = r"C:\Repositorio personal\Paterial para test (no es un repo)\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
DRV_CSV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv"
MUX_VIDEO = r"C:\Users\amedina\Downloads\0207\frames\2_composed.mp4"

log_lines = []


def log(msg):
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    log_lines.append(line)


def wait_server(url, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    return False


def shot(page, name, full=False):
    p = SHOTS / name
    try:
        page.screenshot(path=str(p), full_page=full)
        log(f"  screenshot -> {name}")
    except Exception as e:
        log(f"  screenshot FAIL {name}: {e}")


def upload(page, index, filepath):
    loc = page.locator(".q-uploader input[type='file']")
    if loc.count() > index:
        loc.nth(index).set_input_files(filepath)
    else:
        page.locator("input[type='file']").nth(index).set_input_files(filepath)


def main():
    env = os.environ.copy()
    env["SGI_HEADLESS"] = "1"
    env.pop("PYTEST_CURRENT_TEST", None)
    log("Arrancando NiceGUI headless...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "fantasma.ui.ng_app"],
        env=env,
        stdout=open(RUN_DIR / "server_stdout.log", "w"),
        stderr=open(RUN_DIR / "server_stderr.log", "w"),
    )
    try:
        if not wait_server(BASE, 45):
            log("ERROR: NiceGUI no arranco en 45s")
            return
        log("Servidor listo.")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(20000)

            # ---- STEP 0: empty ----
            log("Paso 0 (inicial / vacio)")
            page.goto(BASE, wait_until="domcontentloaded")
            page.wait_for_selector("text=SimGhostInputs", timeout=20000)
            page.wait_for_selector("text=Elegir este", timeout=15000)
            time.sleep(1.0)
            shot(page, "01_step0_empty.png")

            # ---- STEP 0: choose "Video con HUD" (compose) ----
            log("Paso 0 (elegir Video con HUD)")
            page.locator(".q-card", has_text="Video con HUD").locator(
                "button", has_text="Elegir este"
            ).click()
            page.wait_for_selector("text=Seleccionado", timeout=10000)
            time.sleep(0.7)
            shot(page, "02_step0_compose_selected.png")

            # ---- STEP 1: empty ----
            log("Paso 1 (vacio)")
            page.locator("button", has_text="Empezar").click()
            page.wait_for_selector("text=Importar telemetr", timeout=15000)
            time.sleep(0.8)
            shot(page, "03_step1_empty.png")

            # ---- STEP 1: upload ref (attempt to catch loading) ----
            log("Paso 1 (subir referencia)")
            upload(page, 0, REF_CSV)
            try:
                page.wait_for_selector("text=Leyendo CSV", timeout=4000)
                shot(page, "04_step1_ref_loading.png")
            except PWTimeout:
                log("  (no se alcanzo a capturar spinner 'Leyendo CSV' de ref)")
            page.wait_for_selector("text=Referencia cargada", timeout=120000)
            time.sleep(0.5)
            shot(page, "05_step1_ref_loaded.png")

            # ---- STEP 1: upload driver ----
            log("Paso 1 (subir vuelta piloto)")
            upload(page, 1, DRV_CSV)
            try:
                page.wait_for_selector("text=Leyendo CSV", timeout=4000)
                shot(page, "06_step1_drv_loading.png")
            except PWTimeout:
                log("  (no se alcanzo a capturar spinner 'Leyendo CSV' de piloto)")
            page.wait_for_selector("text=Tu vuelta cargada", timeout=120000)
            time.sleep(0.5)
            shot(page, "07_step1_both_loaded.png")

            # ---- Load -> advances to step 3 (compose flow) ----
            log("Paso 1 -> Cargar (avanza a Paso 3 en flujo compose)")
            page.locator("button", has_text="Cargar y generar overlay").click()
            page.wait_for_selector("text=Generar overlay HUD", timeout=30000)
            time.sleep(1.0)
            shot(page, "08_step3_overlay_empty.png")

            # ---- STEP 3: start render, catch progress, cancel ----
            log("Paso 3 (iniciar render para capturar progreso, luego cancelar)")
            try:
                page.locator("button", has_text="Generar overlay").first.click()
                # progress bar appears + "Detener render"
                page.wait_for_selector("text=Detener render", timeout=30000)
                time.sleep(2.5)  # deja avanzar unos frames
                shot(page, "09_step3_render_progress.png")
                page.locator("button", has_text="Detener render").click()
                page.wait_for_selector("text=Render cancelado", timeout=20000)
                time.sleep(0.5)
                shot(page, "09b_step3_render_cancelled.png")
            except Exception as e:
                log(f"  progreso Paso 3 no capturado: {e}")

            # ---- Navigate to Step 2 (Analisis) via sidebar to populate rows/corners ----
            log("Paso 2 (Analisis via sidebar; corre comparacion real)")
            page.locator(".nav-btn", has_text="Análisis").click()
            try:
                page.wait_for_selector("text=Análisis por curva", timeout=30000)
                # wait for table to render (spinner disappears)
                page.wait_for_selector("table.data-table", timeout=180000)
                time.sleep(1.5)
                shot(page, "10_step2_analysis_top.png")
                shot(page, "10b_step2_analysis_full.png", full=True)
            except Exception as e:
                log(f"  Paso 2 no capturado completo: {e}")
                shot(page, "10_step2_analysis_partial.png")

            # ---- STEP 4: Componer (via sidebar) ----
            log("Paso 4 (Componer)")
            page.locator(".nav-btn", has_text="Video").click()
            try:
                page.wait_for_selector("text=Componer video final", timeout=30000)
                time.sleep(1.0)
                shot(page, "11_step4_compose_default.png", full=True)
                # Fill inputs to enable "Componer video"
                vid = page.get_by_label("Tu video de grabacion")
                if vid.count() == 0:
                    vid = page.locator("input").filter(has_text="").first
                page.get_by_label("Tu video de grabacion").fill(MUX_VIDEO)
                page.get_by_label("Overlay del HUD (generado en el Paso 3)").fill(
                    r"C:\fake\overlay.webm"
                )
                time.sleep(0.8)
                shot(page, "12_step4_compose_filled.png", full=True)
            except Exception as e:
                log(f"  Paso 4 parcial: {e}")
                shot(page, "11_step4_partial.png", full=True)

            # ---- STEP 5: Pace Notes (via sidebar) ----
            log("Paso 5 (Pace Notes)")
            page.locator(".nav-btn", has_text="Pace Notes").click()
            try:
                page.wait_for_selector("text=Pace Notes para CrewChief", timeout=30000)
                time.sleep(1.0)
                shot(page, "13_step5_default.png", full=True)
                # Switch to voice mode -> language appears
                page.locator("text=Voz").first.click()
                time.sleep(0.8)
                shot(page, "14_step5_voice_mode.png", full=True)
                # Fill mux panel fields to enable "Aplicar sonido"
                page.get_by_label("Video existente (mp4, webm, mov...)").fill(MUX_VIDEO)
                page.get_by_label("Carpeta del pack de Pace Notes").fill(
                    r"C:\Users\amedina\fake_pack"
                )
                time.sleep(0.8)
                shot(page, "15_step5_mux_filled.png", full=True)
            except Exception as e:
                log(f"  Paso 5 parcial: {e}")
                shot(page, "13_step5_partial.png", full=True)

            log("Captura completa.")
            ctx.close()
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
        (RUN_DIR / "capture.log").write_text("\n".join(log_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
