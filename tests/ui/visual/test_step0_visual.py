"""Tier 5 -- smoke visual del Paso 0 de la UI Streamlit (ADR 0012).

Captura un screenshot del Paso 0 y lo compara contra un baseline local.
Tolerancia GENEROSA: detecta "el layout se movio" (seccion desaparecida,
boton corrido, columnas rotas), NO diferencias de pixel o antialiasing
entre maquinas ni entre sistemas operativos.

VERDAD DEL BASELINE (ADR 0012 - Consecuencias):
  baselines/step0.png es PROVISIONAL -- generado en la primera corrida.
  La fuente de verdad canonica es el CI (ubuntu-latest de GitHub Actions,
  entorno consistente). Para actualizar el baseline:
    1. Borra baselines/step0.png y vuelve a correr -- se genera uno nuevo.
    2. O usa el screenshot del job `visual-smoke` del CI como baseline definitivo.
  El baseline local sirve para que la suite no falle en vacio; el CI es quien
  atrapa las regresiones reales en cada push.

Skip automatico (no rompe la suite existente):
  - Si playwright no esta instalado: importorskip al inicio del modulo.
  - Si Chromium no esta instalado: capturado en conftest.pw_page.
  - Si Streamlit no levanta en 40 s: capturado en conftest.streamlit_url.
  - Si no hay baseline: se genera y se skipea con mensaje.
"""

from io import BytesIO
from pathlib import Path

import pytest

# Skipea el modulo completo si playwright no esta disponible (igual que
# test_app_smoke.py skipea si streamlit no esta disponible).
pytest.importorskip("playwright.sync_api")

from PIL import Image  # noqa: E402 -- disponible junto con playwright en [dev]

# ---------------------------------------------------------------------------
# Umbrales de tolerancia (ADR 0012: tolerancia generosa, no pixel-perfect)
# ---------------------------------------------------------------------------
# PIXEL_THRESHOLD: un pixel "difiere" si algun canal RGB cambia mas de este
#   valor (normalizado 0..1). 0.12 ~ 31/255 -- absorbe antialiasing y
#   variaciones de renderizado de fuente entre maquinas, pero no un cambio
#   de color real.
# AREA_THRESHOLD: el test falla si mas de esta fraccion del area de la
#   pantalla contiene pixels que "difieren". 0.15 (15 %) atrapa una seccion
#   que se movio o un widget que desaparecio, sin fallar por ruido menor.
PIXEL_THRESHOLD = 0.12
AREA_THRESHOLD = 0.15

BASELINES_DIR = Path(__file__).parent / "baselines"
BASELINE_PATH = BASELINES_DIR / "step0.png"


# ---------------------------------------------------------------------------
# Comparacion de imagenes
# ---------------------------------------------------------------------------


def _diff_ratio(img_a: "Image.Image", img_b: "Image.Image") -> float:
    """Fraccion de pixels que difieren mas de PIXEL_THRESHOLD en algun canal RGB.

    Si los tamanos difieren (distintos DPI entre maquinas), se redimensiona
    img_b al tamano de img_a antes de comparar.
    """
    img_a = img_a.convert("RGB")
    img_b = img_b.convert("RGB")

    if img_a.size != img_b.size:
        img_b = img_b.resize(img_a.size, Image.LANCZOS)

    pixels_a = list(img_a.getdata())
    pixels_b = list(img_b.getdata())

    diff_count = sum(
        1
        for pa, pb in zip(pixels_a, pixels_b)
        if any(abs(ca - cb) / 255.0 > PIXEL_THRESHOLD for ca, cb in zip(pa, pb))
    )
    return diff_count / len(pixels_a)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


def test_step0_layout_smoke(pw_page, streamlit_url):
    """Screenshot del Paso 0 dentro del umbral de tolerancia contra el baseline.

    Primera corrida (sin baseline): guarda el screenshot y skipea con mensaje.
    Corridas posteriores: compara contra el baseline con tolerancia generosa.
    """
    # Navegar al Paso 0 (pagina raiz de la app)
    pw_page.goto(streamlit_url, wait_until="domcontentloaded")

    # Esperar a que el contenido del Paso 0 este renderizado.
    # Streamlit dibuja el paso 0 con un div class="step-header"; esperar ese
    # texto es mas robusto que esperar networkidle (que puede tardar mucho).
    pw_page.wait_for_selector(".step-header", timeout=20_000)

    # Pausa breve para que terminen las animaciones de carga de Streamlit
    # (spinner, transiciones) antes de capturar.
    pw_page.wait_for_timeout(1500)

    screenshot_bytes = pw_page.screenshot(full_page=False)

    # -- Baseline: generar si no existe --
    if not BASELINE_PATH.exists():
        BASELINES_DIR.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_bytes(screenshot_bytes)
        pytest.skip(
            "Baseline provisional generado en baselines/step0.png. "
            "Verifica que se ve bien y vuelve a correr para la comparacion. "
            "La verdad canonica es el entorno del CI (ADR 0012)."
        )

    # -- Comparar contra baseline --
    img_current = Image.open(BytesIO(screenshot_bytes))
    img_baseline = Image.open(BASELINE_PATH)

    ratio = _diff_ratio(img_current, img_baseline)

    assert ratio <= AREA_THRESHOLD, (
        f"Layout diff del Paso 0: {ratio:.1%} de pixels difieren "
        f"(umbral generoso: {AREA_THRESHOLD:.0%}). "
        "El layout se movio -- si fue intencional, actualiza el baseline: "
        "borra baselines/step0.png y vuelve a correr."
    )
