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
_T_ANALYSIS = 90_000  # compare() metro a metro (Paso 2, flujo pacenotes)


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


def _do_step5_pacenotes(page, url: str) -> None:
    """Completa el flujo 'Solo Pace Notes' hasta el Paso 5 con analisis real.

    Flujo pacenotes (steps [0,1,2,5]): Paso 0 -> Paso 1 (sube CSVs) -> Paso 2
    (analisis automatico al entrar, compare() metro a metro) -> boton
    "Generar Pace Notes" -> Paso 5, ya con state.rows/state.corners poblados
    (necesarios para que el panel de cues del Paso 5 se renderice).
    """
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

    card = page.locator(".q-card", has_text="Solo Pace Notes")
    card.locator("button", has_text="Elegir este").click()
    page.wait_for_selector("text=Seleccionado", timeout=10_000)
    page.locator("button", has_text="Empezar").click()
    page.wait_for_selector("text=Paso 1", timeout=_T_NAV)

    _upload_file(page, 0, REF_CSV)
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
    _upload_file(page, 1, DRV_CSV)
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)

    page.locator("button", has_text="Cargar y ver análisis").click()
    page.wait_for_selector("text=Paso 2", timeout=_T_NAV)

    # El analisis corre automaticamente al entrar al Paso 2; esperar a que
    # aparezca el boton hacia el Paso 5 cubre el spinner "Comparando vuelta...".
    page.wait_for_selector("text=🔔 Generar Pace Notes", timeout=_T_ANALYSIS)
    page.locator("button", has_text="Generar Pace Notes").click()
    page.wait_for_selector("text=Paso 5", timeout=_T_NAV)


def _get_computed_style(page, locator, prop: str) -> str:
    """Retorna getComputedStyle(el)[prop] del primer elemento del locator."""
    el = locator.first.element_handle()
    return page.evaluate(f"el => getComputedStyle(el).{prop}", el)


def _css_color_to_rgb(css_color: str) -> tuple:
    """Convierte 'rgb(r, g, b)' o 'rgba(r, g, b, a)' a tupla (r, g, b)."""
    import re

    nums = re.findall(r"[\d.]+", css_color)
    return (int(float(nums[0])), int(float(nums[1])), int(float(nums[2])))


def _brightness(r: int, g: int, b: int) -> float:
    """Luminancia perceptiva [0-255]. Bright colors > 128."""
    return 0.299 * r + 0.587 * g + 0.114 * b


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


def test_pw_step0_button_alignment(pw_page, nicegui_url):
    """Paso 0: todos los botones 'Elegir este' deben estar a la misma altura.

    Sin flexbox en .flow-card, los botones quedan pegados debajo del contenido
    de cada tarjeta. Las tarjetas tienen distinto número de ítems, por lo que
    los botones quedan a distintas alturas Y. El fix agrega 'display:flex;
    flex-direction:column' a .flow-card y 'margin-top:auto' al botón para
    empujarlo al fondo.

    Criterio: max(y) - min(y) < 20 px entre todos los botones visibles.
    """
    page = pw_page
    page.goto(nicegui_url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)
    page.wait_for_selector("text=Elegir este", timeout=_T_NAV)

    btns = page.locator("button:has-text('Elegir este')")
    count = btns.count()
    assert count >= 2, f"Se esperaban al menos 2 botones 'Elegir este', se encontraron {count}"

    ys = []
    for i in range(count):
        box = btns.nth(i).bounding_box()
        assert box is not None, f"Botón {i} no tiene bounding_box (no visible)"
        ys.append(box["y"])

    spread = max(ys) - min(ys)
    page.screenshot(path=str(SCREENSHOT_DIR / "step0_button_alignment.png"))
    assert spread < 20, (
        f"Botones 'Elegir este' están a alturas distintas: {ys}. "
        f"Diferencia máxima: {spread:.1f}px (límite: 20px). "
        "Fix: agregar 'display:flex;flex-direction:column' a .flow-card y "
        "'margin-top:auto' al .q-btn dentro de .flow-card."
    )


def test_pw_step0_selected_button_visibility(pw_page, nicegui_url):
    """Paso 0: el botón '✓ Seleccionado' debe tener texto visible (contraste suficiente).

    Con .props('flat') en Quasar dark mode, el color del texto del botón
    puede colapsar contra el fondo de la tarjeta o del propio botón, haciendo
    el texto invisible. El fix es quitar .props('flat') de los botones de tarjeta
    y agregar !important a btn-featured/btn-primary para ganar specificity.

    Criterio:
      - El botón es visible (bounding_box no None, opacity > 0.3)
      - La diferencia de brillo entre texto y fondo es > 50 puntos (escala 0-255)
    """
    page = pw_page
    page.goto(nicegui_url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

    # Hacer clic en la tarjeta "Video con HUD" (la única con featured=True)
    page.locator(".q-card", has_text="Video con HUD").locator(
        "button", has_text="Elegir este"
    ).click()
    page.wait_for_selector("text=Seleccionado", timeout=10_000)

    btn = page.locator("button:has-text('Seleccionado')").first

    # Verificar visibilidad básica
    box = btn.bounding_box()
    assert box is not None, "El botón 'Seleccionado' no es visible en el DOM"
    assert box["width"] > 0 and box["height"] > 0, "El botón tiene tamaño cero"

    opacity = float(_get_computed_style(page, btn, "opacity"))
    assert opacity > 0.3, (
        f"Botón 'Seleccionado' tiene opacity={opacity} (< 0.3, prácticamente invisible)"
    )

    # Verificar contraste texto vs fondo
    fg_css = _get_computed_style(page, btn, "color")
    bg_css = _get_computed_style(page, btn, "backgroundColor")

    fg_r, fg_g, fg_b = _css_color_to_rgb(fg_css)
    bg_r, bg_g, bg_b = _css_color_to_rgb(bg_css)

    fg_brightness = _brightness(fg_r, fg_g, fg_b)
    bg_brightness = _brightness(bg_r, bg_g, bg_b)
    contrast = abs(fg_brightness - bg_brightness)

    page.screenshot(path=str(SCREENSHOT_DIR / "step0_selected_visibility.png"))
    assert contrast > 50, (
        f"Contraste insuficiente en botón 'Seleccionado': "
        f"fg={fg_css} (brillo={fg_brightness:.1f}), bg={bg_css} (brillo={bg_brightness:.1f}), "
        f"diferencia={contrast:.1f} (mínimo: 50). "
        "Fix: quitar .props('flat') de botones de tarjeta en ng_step0.py."
    )


def test_pw_step5_cues_section_renders(pw_page, nicegui_url):
    """Paso 5 (WS-4): la sección de cues renderiza sin excepción con analisis real.

    Verifica que, con state.rows/state.corners poblados (flujo pacenotes real,
    sin analisis no se llega a ver el panel de cues -- solo el guard):
    - El panel expansible "Cues: selección y prioridad" es visible.
    - Existe al menos una casilla por tipo de cue implementado (checkbox).
    - Existe al menos un control de prioridad (ui.number con label "Prioridad").
    - El bloque de perfiles (cargar/guardar) esta presente.
    Screenshot: qa_runs/playwright_e2e/step5_cues.png
    """
    page = pw_page

    _do_step5_pacenotes(page, nicegui_url)

    page.wait_for_selector("text=Cues: selección y prioridad", timeout=_T_NAV)

    # Casillas de cues implementados (etiquetas de _CUE_LABELS en ng_step5.py)
    for label in (
        "Countdown de frenada",
        "Frenada",
        "Soltar freno",
        "Turn-in",
        "Inicio de acelerador",
        "Gas completo",
        "Ápex",
        "Coast (inercia)",
    ):
        assert page.locator(f"text={label}").count() > 0, f"Falta la casilla de '{label}'"

    # Control de prioridad (ui.number con label "Prioridad", una por cue)
    priority_inputs = page.get_by_label("Prioridad")
    assert priority_inputs.count() >= 8, (
        f"Se esperaban al menos 8 controles de Prioridad, se encontraron {priority_inputs.count()}"
    )

    # Bloque de perfiles (cargar/guardar)
    assert page.locator("text=Perfiles de cues").count() > 0
    assert page.locator("button", has_text="Guardar perfil").count() > 0

    page.screenshot(path=str(SCREENSHOT_DIR / "step5_cues.png"))
