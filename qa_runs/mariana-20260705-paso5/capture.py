"""Mariana QA visual — PR 3 (feat/pacenotes-ui-paso5).

Evidencia de: breadcrumb por flujo (Solo Pace Notes = 4 pasos), leyenda de tonos,
checkbox "Todas las curvas", caption "Falta: ..." del boton Aplicar sonido, y
aviso de sidecar video<->vuelta (ADR 0024). Basado en el harness de la ronda r2.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

RUN_DIR = Path(__file__).parent
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

REF_CSV = r"C:\Repositorio personal\Paterial para test (no es un repo)\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
DRV_CSV = r"C:\Repositorio personal\Paterial para test (no es un repo)\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"

log_lines = []


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
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
    try:
        page.screenshot(path=str(RUN_DIR / name), full_page=full)
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
    # Sidecars de prueba para el aviso video<->vuelta: uno que NO corresponde
    # (laptime imposible) y uno que SI (el laptime de la vuelta rapida que la
    # UI va a elegir del CSV del piloto).
    sys.path.insert(0, r"C:\Repositorio personal\SimGhostInputs")
    from fantasma.importers import load_laps

    fastest = min(
        (
            lap
            for lap in load_laps(DRV_CSV)
            if lap.has("dist") and lap.has("time") and lap.laptime > 60
        ),
        key=lambda lap: lap.laptime,
    ).laptime
    log(f"vuelta rapida del CSV piloto: {fastest:.2f} s")
    mismatch_video = RUN_DIR / "video_de_OTRA_vuelta.mp4"
    match_video = RUN_DIR / "video_de_la_vuelta_cargada.mp4"
    (RUN_DIR / (mismatch_video.name + ".sync.json")).write_text(
        json.dumps({"format": "sgi-sync-v1", "csv_path": "otra_carrera.csv", "laptime": 500.0}),
        encoding="utf-8",
    )
    (RUN_DIR / (match_video.name + ".sync.json")).write_text(
        json.dumps(
            {"format": "sgi-sync-v1", "csv_path": os.path.basename(DRV_CSV), "laptime": fastest}
        ),
        encoding="utf-8",
    )

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
            ctx = browser.new_context(viewport={"width": 1440, "height": 960})
            page = ctx.new_page()
            page.set_default_timeout(20000)

            # ---- Paso 0: elegir flujo Solo Pace Notes ----
            log("Paso 0: elegir Solo Pace Notes")
            page.goto(BASE, wait_until="domcontentloaded")
            page.wait_for_selector("text=Elegir este", timeout=20000)
            page.locator(".q-card", has_text="Solo Pace Notes").locator(
                "button", has_text="Elegir este"
            ).click()
            page.wait_for_selector("text=Seleccionado", timeout=10000)
            time.sleep(0.7)
            shot(page, "01_step0_pacenotes_elegido.png")

            # ---- Paso 1: breadcrumb de 4 pasos ----
            log("Paso 1: breadcrumb del flujo pacenotes (sin Overlay ni Video)")
            page.locator("button", has_text="Empezar").click()
            page.wait_for_selector("text=Importar telemetr", timeout=15000)
            time.sleep(0.8)
            shot(page, "02_step1_breadcrumb_4pasos.png")

            log("Paso 1: subir referencia y piloto")
            upload(page, 0, REF_CSV)
            page.wait_for_selector("text=Referencia cargada", timeout=120000)
            upload(page, 1, DRV_CSV)
            page.wait_for_selector("text=Tu vuelta cargada", timeout=120000)
            time.sleep(0.5)
            shot(page, "03_step1_ambas_cargadas.png")

            # ---- Avanzar (flujo pacenotes: 1 -> 2) ----
            log("Avanzar al Paso 2 (analisis)")
            page.locator("button", has_text="Cargar").first.click()
            page.wait_for_selector("text=Análisis por curva", timeout=60000)
            page.wait_for_selector("table.data-table", timeout=240000)
            time.sleep(1.0)
            shot(page, "04_step2_breadcrumb_flujo.png")

            # ---- Paso 5 via boton del Paso 2 ----
            log("Paso 5 via 'Generar Pace Notes'")
            page.locator("button", has_text="Generar Pace Notes").first.click()
            page.wait_for_selector("text=Pace Notes para CrewChief", timeout=30000)
            time.sleep(1.0)
            shot(page, "05_step5_default_breadcrumb.png", full=True)

            # ---- Leyenda de tonos ----
            log("Leyenda de tonos (expandir)")
            page.locator("text=Leyenda de tonos").first.click()
            time.sleep(0.8)
            shot(page, "06_step5_leyenda_tonos.png", full=True)

            # ---- Todas las curvas ----
            log("Checkbox Todas las curvas (Top N se deshabilita)")
            page.locator("text=Todas las curvas").first.click()
            time.sleep(0.6)
            shot(page, "07_step5_todas_las_curvas.png")

            # ---- Caption del boton: quitar el video -> Falta: ... ----
            log("Caption 'Falta: ...' bajo Aplicar sonido (campos vacios)")
            time.sleep(0.4)
            shot(page, "08_step5_apply_caption_falta.png")

            # ---- Sidecar mismatch ----
            # fill() no dispara los key-events que el debounce de Quasar espera
            # (el modelo quedaba "una accion atras"): teclear de verdad.
            def type_into(label, text):
                box = page.get_by_label(label)
                box.click()
                box.clear()
                box.press_sequentially(text, delay=5)
                page.keyboard.press("Tab")

            log("Sidecar que NO corresponde -> aviso amarillo")
            type_into("Carpeta del pack de Pace Notes", str(RUN_DIR))
            type_into("Video existente (mp4, webm, mov...)", str(mismatch_video))
            # espera determinista del texto del aviso, no un sleep
            page.wait_for_selector("text=El mux se negará", timeout=20000)
            shot(page, "09_step5_sidecar_mismatch.png")

            # ---- Sidecar match ----
            log("Sidecar que SI corresponde -> verificado en verde")
            type_into("Video existente (mp4, webm, mov...)", str(match_video))
            page.wait_for_selector("text=Video verificado", timeout=20000)
            shot(page, "10_step5_sidecar_ok.png")

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
