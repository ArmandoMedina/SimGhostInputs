"""Verificacion 4 H-01c: 11 contenedores ui.html('<div>') migrados a ui.element("div").

Corrida: qa_runs/mariana-20260703-0740/
Escenario: BMW M4 GT3 (REF) vs AUDI R8 LMS EVO II (DRV), Nordschleife 2025.
Fix evaluado: ui.element("div") en los 11 contenedores de ng_step2.py que antes
usaban ui.html('<div>') y descartaban sus children por falta de <slot> en html.js.

Salida: paso2_fix4.png en qa_runs/mariana-20260703-0740/

Verificaciones:
  - Footer "Analisis completado" visible
  - Tabla de curvas con filas reales (tbody tr > 0)
  - Imagenes de graficas cargadas (naturalWidth > 0; cero imgs rotas)

Uso:
    python _qa_run_mariana.py
"""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ── Rutas ─────────────────────────────────────────────────────────────────────

_QA_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_QA_DIR))  # qa_runs/mariana-*/ -> qa_runs/ -> repo

REF_CSV = os.path.join(
    r"C:\Repositorio personal\Paterial para test (no es un repo)",
    "Pruebas finales",
    "Pruebas finales",
    "GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv",
)
DRV_CSV = os.path.join(
    r"C:\Repositorio personal\Paterial para test (no es un repo)",
    "Pruebas finales",
    "Pruebas finales",
    "GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv",
)

SCREENSHOT_DIR = _QA_DIR
SCREENSHOT_OUT = os.path.join(SCREENSHOT_DIR, "paso2_fix4.png")

# ── Servidor ───────────────────────────────────────────────────────────────────

_PORT = 8765
_BASE_URL = f"http://localhost:{_PORT}"

# ── Timeouts (ms para Playwright; s para polling HTTP) ────────────────────────

_T_PAGE_LOAD = 20_000   # carga inicial de NiceGUI + Quasar
_T_NAV = 15_000         # navegacion entre pasos
_T_UPLOAD = 120_000     # upload + parsing CSV (Nordschleife ~31 MB, parsing lento)
_T_STEP2 = 150_000      # compare (~1.2 s) + render_charts (~13 s) + margen generoso


def _wait_for_nicegui(url: str, timeout: int = 30) -> bool:
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


def _upload_file(page, index: int, filepath: str) -> None:
    """Sube un archivo al n-esimo input[type='file'] del q-uploader."""
    primary = page.locator(".q-uploader input[type='file']")
    if primary.count() > index:
        primary.nth(index).set_input_files(filepath)
    else:
        page.locator("input[type='file']").nth(index).set_input_files(filepath)


def main():
    # ── Validaciones previas ──────────────────────────────────────────────────
    for path, label in [(REF_CSV, "REF_CSV"), (DRV_CSV, "DRV_CSV")]:
        if not os.path.exists(path):
            print(f"[ERROR] {label} no encontrado: {path}")
            sys.exit(1)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # ── Arrancar NiceGUI ──────────────────────────────────────────────────────
    print("[*] Arrancando NiceGUI en modo headless (puerto 8765)...")
    env = os.environ.copy()
    env["SGI_HEADLESS"] = "1"
    env.pop("PYTEST_CURRENT_TEST", None)   # evita que NiceGUI entre en modo test interno

    _server_log_path = os.path.join(_QA_DIR, "_ng_server_fix4.log")
    _server_log_file = open(_server_log_path, "w", encoding="utf-8")
    env["PYTHONUNBUFFERED"] = "1"  # flush logs immediately
    proc = subprocess.Popen(
        [sys.executable, "-m", "fantasma.ui.ng_app"],
        env=env,
        stdout=_server_log_file,
        stderr=_server_log_file,
        cwd=_REPO_ROOT,
    )

    print("[*] Esperando que NiceGUI responda (hasta 30 s)...")
    ready = _wait_for_nicegui(_BASE_URL, timeout=30)
    if not ready:
        proc.terminate()
        proc.wait()
        print("[ERROR] NiceGUI no arranco en 30 s.")
        sys.exit(1)
    print(f"[OK] NiceGUI listo en {_BASE_URL}")

    # ── Playwright ────────────────────────────────────────────────────────────
    from playwright.sync_api import sync_playwright

    veredicto = "FALLA"
    evidencia = "(sin screenshot)"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
        )
        page = context.new_page()

        # Interceptar mensajes WebSocket para ver que envía NiceGUI
        _ws_msgs = []
        _ws_log_path = os.path.join(_QA_DIR, "_ws_fix4.log")
        _ws_log = open(_ws_log_path, "w", encoding="utf-8", errors="replace")
        def _on_ws(ws):
            def _on_msg(payload):
                if isinstance(payload, str):
                    _p_short = payload[:300].encode("ascii", "replace").decode("ascii")
                    _ws_log.write(f"TEXT {len(payload)} chars: {payload[:2000]}\n")
                    _ws_log.flush()
                else:
                    _p_short = f"[BINARY len={len(payload)}]"
                    _ws_log.write(f"BIN {len(payload)} bytes\n")
                    _ws_log.flush()
                _ws_msgs.append(_p_short)
            ws.on("framereceived", lambda payload: _on_msg(payload["payload"] if isinstance(payload, dict) else str(payload)))
        page.on("websocket", _on_ws)

        _prev_ws_count = 0

        # Capturar mensajes de consola del browser
        _console_msgs = []
        def _on_console(msg):
            t = msg.type
            txt = msg.text.encode("ascii", "replace").decode("ascii")[:200]
            _console_msgs.append(f"[{t}] {txt}")
        page.on("console", _on_console)

        try:
            # ── Paso 0: seleccionar flujo "Solo analisis" ─────────────────
            print("[*] Paso 0 — cargando pagina...")
            page.goto(_BASE_URL, wait_until="domcontentloaded")
            page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

            print("[*] Paso 0 — seleccionando 'Solo analisis'...")
            card = page.locator(".q-card", has_text="Solo an")
            card.locator("button", has_text="Elegir este").click()
            page.wait_for_selector("text=Seleccionado", timeout=10_000)

            print("[*] Paso 0 — avanzando al Paso 1...")
            page.locator("button", has_text="Empezar").click()
            page.wait_for_selector("text=Paso 1", timeout=_T_NAV)
            print("[OK] En el Paso 1")

            # ── Paso 1: subir CSVs ────────────────────────────────────────
            print(f"[*] Subiendo REF: {os.path.basename(REF_CSV)}...")
            _upload_file(page, 0, REF_CSV)
            page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
            print("[OK] Referencia cargada")

            print(f"[*] Subiendo DRV: {os.path.basename(DRV_CSV)}...")
            _upload_file(page, 1, DRV_CSV)
            page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)
            print("[OK] DRV cargada")

            print("[*] Clic en 'Cargar y ver analisis'...")
            page.locator("button", has_text="Cargar y ver an").click()
            page.wait_for_selector("text=Paso 2", timeout=_T_NAV)
            print("[OK] En el Paso 2 — esperando analisis y charts (hasta 90 s)...")

            # Snapshots de diagnostico en t+5s, t+25s (acumulado), t+65s (acumulado)
            _diag_base = os.path.join(SCREENSHOT_DIR, "diag_fix4")
            _elapsed = 0
            for _dt in (5, 20, 40):
                page.wait_for_timeout(_dt * 1000)
                _elapsed += _dt
                _snap = f"{_diag_base}_t{_elapsed:02d}s.png"
                page.screenshot(path=_snap, full_page=True)
                # Consultar texto completo del body y numero de elementos
                _body = page.evaluate("() => document.body.innerText")
                _n_elements = page.evaluate("() => document.querySelectorAll('*').length")
                _n_imgs = page.evaluate("() => document.querySelectorAll('img').length")
                _has_table = page.evaluate("() => document.querySelectorAll('table.data-table').length > 0")
                _errors = page.evaluate("() => Array.from(document.querySelectorAll('.text-red-400,.text-yellow-400')).map(e=>e.textContent).filter(t=>t.length>3).slice(0,3)")
                # Evitar crash por emojis u otros no-ASCII en stdout de Windows
                _snippet = _body[:300].encode("ascii", "replace").decode("ascii")
                print(f"  [diag t+{_elapsed}s] elements={_n_elements} imgs={_n_imgs} "
                      f"table={_has_table} errors={_errors}")
                print(f"    body[0:300]: {repr(_snippet)}")
                # Console messages del browser
                _recent_console = [m for m in _console_msgs[-8:]]
                print(f"    console msgs: {_recent_console}")
                # Verificar el popup de mensaje muy largo
                _popup_info = page.evaluate("""
                () => {
                    const popup = document.getElementById('too_long_message_popup');
                    if (!popup) return {found: false};
                    const style = window.getComputedStyle(popup);
                    return {
                        found: true,
                        display: style.display,
                        visibility: style.visibility,
                        text: popup.innerText.substring(0, 300)
                    };
                }
                """)
                print(f"    too_long_message_popup: {_popup_info}")
                # Tamanio del body del update que NiceGUI intenta enviar
                _html_size = page.evaluate("() => document.documentElement.outerHTML.length")
                print(f"    total HTML size: {_html_size} chars")
                # Mensajes WebSocket recibidos desde el checkpoint anterior
                _all_ws = _ws_msgs[:]
                _since_last = _all_ws[_prev_ws_count:]
                _prev_ws_count = len(_all_ws)
                print(f"    WS since last check ({len(_since_last)} msgs of {len(_all_ws)} total):")
                for _m in _since_last:
                    print(f"      {repr(_m[:200])}")

            # ── Paso 2: verificar contenido real ─────────────────────────
            # Fix 3: ui.image(ruta) reemplaza ui.image(bytes) en los 5 sitios.
            # Los elementos zombie ya no existen -> el batch del outbox se serializa
            # correctamente -> tabla, graficas y footer llegan al browser.
            page.wait_for_selector(
                "text=lisis completado",
                timeout=_T_STEP2,
            )
            print("[OK] 'Analisis completado' visible")

            # Tabla de curvas con filas reales
            tabla = page.locator("table.data-table")
            assert tabla.count() > 0, "Tabla de curvas NO encontrada en el DOM"
            row_count = tabla.first.locator("tbody tr").count()
            assert row_count > 0, f"Tabla existe pero sin filas (rows={row_count})"
            print(f"[OK] Tabla de curvas: {row_count} filas visibles")

            # Imagenes de graficas: verificar que cargan (naturalWidth > 0)
            # Esperar hasta 15 s a que todas las imagenes carguen (puede tardar en headless)
            _img_deadline = time.monotonic() + 15
            while time.monotonic() < _img_deadline:
                total_imgs = page.evaluate("() => document.querySelectorAll('img').length")
                broken_imgs = page.evaluate(
                    "() => Array.from(document.querySelectorAll('img'))"
                    ".filter(img => img.naturalWidth === 0 && img.complete).length"
                )
                pending_imgs = page.evaluate(
                    "() => Array.from(document.querySelectorAll('img'))"
                    ".filter(img => !img.complete).length"
                )
                if pending_imgs == 0:
                    break
                page.wait_for_timeout(1000)

            # Diagnostico de imagenes rotas
            broken_srcs = page.evaluate(
                "() => Array.from(document.querySelectorAll('img'))"
                ".filter(img => img.naturalWidth === 0)"
                ".map(img => img.src.substring(0, 120))"
            )
            loaded_imgs = total_imgs - broken_imgs
            print(f"[DIAG] Imagenes: total={total_imgs}, cargadas={loaded_imgs}, "
                  f"rotas={broken_imgs}, pending={pending_imgs}")
            for _src in broken_srcs:
                _src_ascii = _src.encode("ascii", "replace").decode("ascii")
                print(f"  [rota] {_src_ascii}")
            assert loaded_imgs > 0, (
                f"Ninguna imagen cargada (total={total_imgs}, rotas={broken_imgs})"
            )
            assert broken_imgs == 0, (
                f"{broken_imgs} imagenes rotas de {total_imgs}; srcs: {broken_srcs}"
            )
            print(f"[OK] Imagenes: {loaded_imgs} cargadas, 0 rotas (de {total_imgs})")

            page.screenshot(path=SCREENSHOT_OUT, full_page=True)
            print(f"[OK] Screenshot guardado: {SCREENSHOT_OUT}")
            veredicto = "PASA"
            evidencia = (
                f"'Analisis completado' visible; tabla {row_count} filas; "
                f"{loaded_imgs}/{total_imgs} imgs cargadas (0 rotas); screenshot: paso2_fix4.png"
            )

        except Exception as exc:
            print(f"[FALLA] {exc}")
            try:
                page.screenshot(path=SCREENSHOT_OUT)
                print(f"[*] Screenshot del estado actual: {SCREENSHOT_OUT}")
                evidencia = f"Error: {exc}; screenshot del estado actual: paso2_fix4.png"
            except Exception:
                pass

        finally:
            context.close()
            browser.close()

    # ── Detener NiceGUI ───────────────────────────────────────────────────────
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    _server_log_file.close()

    print()
    print(f"=== VEREDICTO H-01c (verificacion 4): {veredicto} ===")
    print(f"Evidencia: {evidencia}")
    return veredicto, evidencia


if __name__ == "__main__":
    veredicto, evidencia = main()
    sys.exit(0 if veredicto == "PASA" else 1)
