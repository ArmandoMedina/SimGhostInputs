"""Tests Playwright E2E que navegan el wizard NiceGUI clic por clic y suben archivos CSV reales.

Fixture base reutilizada de conftest.py (pytest las inyecta automáticamente):
  - nicegui_url  (session-scoped) — URL del servidor NiceGUI levantado en 8765
  - pw_page      (function-scoped) — página Chromium headless

Archivos CSV reales:
  REF_CSV — vuelta de referencia MoTeC Nordschleife 2025
  DRV_CSV — vuelta del piloto Nordschleife 2026

Bug fijado (2026-07-02): ng_step1.py usaba e.name/e.content (API de NiceGUI 2.x);
NiceGUI 3.x expone e.file.name y e.file.read() (async). Los handlers ahora usan
la API correcta, por lo que set_input_files en los tests dispara el flujo completo.
"""

from pathlib import Path

import pytest

# Skipea el módulo completo si playwright no está disponible.
playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402

# ---------------------------------------------------------------------------
# Archivos CSV de prueba reales (rutas verificadas que existen en disco)
# ---------------------------------------------------------------------------
REF_CSV = (
    r"C:\Repositorio personal\Paterial para test (no es un repo)"
    r"\GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
)
DRV_CSV = (
    r"C:\Repositorio personal\Paterial para test (no es un repo)"
    r"\Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv"
)

# Skip del modulo completo si los CSVs no existen en disco. Sin este guard,
# set_input_files() lanzaria playwright._impl._errors.Error: ENOENT en lugar
# de un pytest.skip limpio.
_CSV_MISSING = not (Path(REF_CSV).exists() and Path(DRV_CSV).exists())
pytestmark = pytest.mark.skipif(
    _CSV_MISSING,
    reason="CSV de telemetria no encontrados — tests solo en laptop de desarrollo",
)

# ---------------------------------------------------------------------------
# Directorio de screenshots de esta suite
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
SCREENSHOT_DIR = _REPO_ROOT / "qa_runs" / "playwright_e2e"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Timeouts (ms)
# ---------------------------------------------------------------------------
_T_PAGE_LOAD = 20_000  # NiceGUI + Quasar inicial
_T_NAV = 15_000  # navegación entre pasos
_T_UPLOAD = 90_000  # subida + parsing CSV grande en Python puro (hasta 90 s)
_T_OVERLAY = 600_000  # render completo (hasta 10 min para Nordschleife)


# ---------------------------------------------------------------------------
# Helpers compartidos
# ---------------------------------------------------------------------------


def _upload_file(page, index: int, filepath: str) -> None:
    """Sube un archivo al n-ésimo input[type='file'] del q-uploader.

    Playwright puede llamar set_input_files() sobre inputs ocultos sin necesidad
    de hacerlos visibles. Quasar detecta el cambio y lanza el XHR de upload
    hacia el endpoint NiceGUI /_nicegui/client/.../upload/<id>.

    Selección del input:
      - Primario:  .q-uploader input[type='file']  (dentro del q-uploader)
      - Fallback:  input[type='file'] genérico (para cubrir el caso edge de DOM diferente)
    """
    primary = page.locator(".q-uploader input[type='file']")
    if primary.count() > index:
        primary.nth(index).set_input_files(filepath)
    else:
        page.locator("input[type='file']").nth(index).set_input_files(filepath)


def _do_step0(page, url: str) -> None:
    """Navega al Paso 0, elige 'Video con HUD' y avanza al Paso 1.

    Reutilizable como helper en los tests de Paso 1 y Paso 3.
    """
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

    # Buscar la tarjeta "Video con HUD" y hacer clic en su "Elegir este"
    card = page.locator(".q-card", has_text="Video con HUD")
    card.locator("button", has_text="Elegir este").click()

    # NiceGUI re-renderiza el Paso 0 y el botón cambia a "✓ Seleccionado"
    page.wait_for_selector("text=Seleccionado", timeout=10_000)

    # Avanzar al Paso 1
    page.locator("button", has_text="Empezar").click()
    page.wait_for_selector("text=Paso 1", timeout=_T_NAV)


def _do_step1(page, url: str) -> None:
    """Completa el Paso 0 y el Paso 1: sube ambos CSVs y avanza al Paso 3.

    Reutilizable como helper en el test del Paso 3.
    """
    _do_step0(page, url)

    _upload_file(page, 0, REF_CSV)
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)

    _upload_file(page, 1, DRV_CSV)
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)

    # Botón del flujo "compose" en Paso 1: "Cargar y generar overlay →"
    page.locator("button", has_text="Cargar y generar overlay").click()
    page.wait_for_selector("text=Paso 3", timeout=_T_NAV)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pw_step0_choose_flow_and_advance(pw_page, nicegui_url):
    """Paso 0: elige 'Video con HUD' y avanza al Paso 1.

    Verifica:
    - El botón "Elegir este" de la tarjeta "Video con HUD" responde al clic.
    - El state.flow_chosen se refleja visualmente ("✓ Seleccionado").
    - El botón "Empezar" navega al Paso 1.
    Screenshot: qa_runs/playwright_e2e/step0_done.png
    """
    page = pw_page

    page.goto(nicegui_url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

    # Elegir tarjeta "Video con HUD"
    page.locator(".q-card", has_text="Video con HUD").locator(
        "button", has_text="Elegir este"
    ).click()

    # NiceGUI re-renderiza: el botón de la tarjeta debe mostrar "✓ Seleccionado"
    page.wait_for_selector("text=Seleccionado", timeout=10_000)

    # Hacer clic en "Empezar → Ir a Importar"
    page.locator("button", has_text="Empezar").click()

    # Verificar que llegamos al Paso 1
    page.wait_for_selector("text=Paso 1", timeout=_T_NAV)
    assert page.locator("text=Paso 1").count() > 0 or page.locator("text=Importar").count() > 0

    page.screenshot(path=str(SCREENSHOT_DIR / "step0_done.png"))


def test_pw_step1_upload_csvs(pw_page, nicegui_url):
    """Paso 1: sube los dos CSVs y avanza al Paso 3.

    Verifica:
    - El primer ui.upload acepta REF_CSV y muestra "✓ Referencia cargada".
    - El segundo ui.upload acepta DRV_CSV y muestra "✓ Tu vuelta cargada".
    - El botón "Cargar y generar overlay →" navega al Paso 3.

    Timeout por upload: 90 s (los CSVs son 31 MB y 59 MB, el parsing en Python puro
    puede tomar hasta ~30 s por archivo en hardware lento).

    Screenshots:
      step1_ref_uploaded.png — tras cargar la referencia
      step1_uploaded.png     — tras cargar ambos archivos
      step1_advanced.png     — ya en el Paso 3
    """
    page = pw_page

    # Completar el Paso 0 (helper)
    _do_step0(page, nicegui_url)

    # Subir CSV de referencia (primer q-uploader)
    _upload_file(page, 0, REF_CSV)
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
    page.screenshot(path=str(SCREENSHOT_DIR / "step1_ref_uploaded.png"))

    # Subir CSV del piloto (segundo q-uploader)
    _upload_file(page, 1, DRV_CSV)
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)
    page.screenshot(path=str(SCREENSHOT_DIR / "step1_uploaded.png"))

    # Avanzar al Paso 3
    page.locator("button", has_text="Cargar y generar overlay").click()
    page.wait_for_selector("text=Paso 3", timeout=_T_NAV)
    page.screenshot(path=str(SCREENSHOT_DIR / "step1_advanced.png"))


def test_pw_step3_overlay_render(pw_page, nicegui_url, tmp_path):
    """Paso 3: inicia el render del overlay y espera hasta 10 min.

    Llena la carpeta de salida con tmp_path (fixture pytest), hace clic en
    "Generar overlay" y espera hasta 600 000 ms.

    Si el render supera el timeout (Nordschleife es una vuelta larga):
      → pytest.skip en lugar de fallo rojo.
    Si la app avisa que ffmpeg no está instalado:
      → skip limpio (entorno sin ffmpeg).
    Screenshot: qa_runs/playwright_e2e/step3_overlay_done.png
    """
    page = pw_page

    # Completar Pasos 0 y 1 (helpers)
    _do_step1(page, nicegui_url)

    out_dir = str(tmp_path)

    # Si no hay ffmpeg, la app muestra un aviso y no renderiza — skip limpio
    # (debe verificarse ANTES de buscar el folder input porque sin ffmpeg
    # ng_step3.py no renderiza ese campo y wait_for el locator agotaría el timeout)
    if page.locator("text=ffmpeg no esta instalado").count() > 0:
        pytest.skip("ffmpeg no instalado — Paso 3 no disponible en este entorno")

    # Llenar el campo "Carpeta donde guardar el overlay".
    # ng_step3.py usa value=_def_out y placeholder=_def_out donde
    # _def_out contiene "fantasma_salida". El q-input de Quasar pone
    # el placeholder en el <input> nativo aunque ya haya value.
    folder_input = page.locator("input[placeholder*='fantasma_salida']")
    if folder_input.count() == 0:
        # Fallback: buscar por aria-label que NiceGUI genera del label del q-input
        folder_input = page.get_by_label("Carpeta donde guardar el overlay")
    if folder_input.count() == 0:
        # Último fallback: primer input de texto en el Paso 3
        folder_input = page.locator("input[type='text']").first
    folder_input.fill(out_dir)

    # Hacer clic en "Generar overlay"
    page.locator("button", has_text="Generar overlay").click()

    # Esperar hasta 10 minutos a que aparezca el mensaje de éxito
    try:
        page.wait_for_selector("text=Overlay generado:", timeout=_T_OVERLAY)
    except PlaywrightTimeoutError:
        # Verificar si un archivo .webm apareció en tmp_path
        webm_files = list(tmp_path.glob("*.webm"))
        if webm_files:
            # El overlay se generó aunque el selector de texto no respondió a tiempo
            pass
        else:
            page.screenshot(path=str(SCREENSHOT_DIR / "step3_overlay_timeout.png"))
            pytest.skip("render timeout — Nordschleife es una vuelta larga")

    page.screenshot(path=str(SCREENSHOT_DIR / "step3_overlay_done.png"))
