"""E2E: el mux del Paso 5 no debe leer AppState dentro del hilo run.io_bound.

Cierra el hueco de cobertura documentado en ROADMAP.md ("Ningún test unitario
cubre lectura de `app.storage.user` en hilos `run.io_bound`"): el mock plano
usado en tests/ui/test_ng_step5.py (`_StateWithRowsNoDrv`) evade por completo
el proxy real de NiceGUI sobre `app.storage.user`, que solo lanza
``RuntimeError: app.storage.user can only be used within a UI context`` fuera
de contexto de request -- exactamente donde corre un hilo de `run.io_bound`.
Por eso el bug real de `_do_mux` (fantasma/ui/ng_step5.py: `state.drv_name` se
leía DENTRO del hilo en vez de capturarse antes) pasó la suite en verde y solo
lo cazó el E2E Playwright manual (corregido en PR #30).

Este test ejerce la RUTA REAL de producción (clics reales sobre `_do_mux` vía
el botón "Aplicar sonido", contra un server NiceGUI real levantado por
`nicegui_url`/`pw_page` de conftest.py -- nunca llamando `_do_mux` ni
`AppState` por fuera de la UI). No requiere telemetría real del filesystem del
usuario: `state.drv_lap`/`state.drv_name` se cargan subiendo dos CSVs
sintéticos mínimos (columnas dist+time, ~30 filas) que el importador genérico
de fantasma reconoce sin necesitar un export real de MoTeC.

El video y la carpeta del pack apuntan a rutas que NO existen a propósito: el
mux SÍ debe fallar (sin ffmpeg instalado, o sin metadata.json en el pack), y
esa es precisamente la señal que el test usa -- el mensaje de error mostrado
debe ser el de negocio esperado (ffmpeg/pack), nunca el de
`app.storage.user`. Si alguien reintroduce el bug de PR #30 (mueve la lectura
de una propiedad de AppState de vuelta dentro del hilo), este test debe
fallar con el RuntimeError real de NiceGUI en el toast de la UI.
"""

import csv
from pathlib import Path

import pytest

# Skipea el módulo completo si playwright no está disponible (mismo patrón
# que el resto de tests/ui/visual/).
playwright_api = pytest.importorskip("playwright.sync_api")

from .test_e2e_playwright_wizard import _do_step0, _upload_file  # noqa: E402

_T_NAV = 15_000
_T_UPLOAD = 15_000
_T_MUX = 30_000


def _write_synthetic_csv(path: Path, n_rows: int = 30) -> None:
    """CSV sintético mínimo, reconocido por fantasma.importers.generic_csv.

    Encabezados en minúsculas ("time"/"dist"/"speed") a propósito: el primer
    cell en mayúscula exacta "Time" dispara la detección de formato MoTeC
    (fantasma/importers/motec_csv.py), que espera metadatos/fila de unidades
    antes de los datos -- estructura que este CSV no tiene. En minúsculas cae
    de forma confiable al importador genérico (columnas dist+time bastan,
    fantasma/importers/generic_csv.py::GUESS), sin necesitar un export real.
    30 filas: por encima del mínimo de 10 muestras que exige
    fantasma.core.normalize.split_laps para aceptar el segmento como vuelta.
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "dist", "speed"])
        for i in range(n_rows):
            writer.writerow([f"{i * 0.5:.3f}", f"{i * 20.0:.1f}", "120.0"])


def test_pw_step5_mux_error_never_mentions_storage_context(pw_page, nicegui_url, tmp_path):
    """Clic real en "Aplicar sonido" con datos sintéticos: el error mostrado
    nunca debe ser el RuntimeError de app.storage.user fuera de contexto UI.
    """
    page = pw_page

    ref_csv = tmp_path / "ref.csv"
    drv_csv = tmp_path / "drv.csv"
    _write_synthetic_csv(ref_csv)
    _write_synthetic_csv(drv_csv)

    _do_step0(page, nicegui_url)

    _upload_file(page, 0, str(ref_csv))
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
    _upload_file(page, 1, str(drv_csv))
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)

    # do_load() (ng_step1.py) fija state.drv_lap/state.drv_name -- exactamente
    # las propiedades que _do_mux debe capturar en contexto UI ANTES de lanzar
    # el hilo de run.io_bound.
    page.locator("button", has_text="Cargar y generar overlay").click()
    page.wait_for_selector("text=Paso 3", timeout=_T_NAV)

    # El nav lateral "Pace Notes" salta directo al Paso 5 (navigate(5), sin
    # guardas) -- el panel ② solo necesita state.drv_lap, no state.rows /
    # state.corners (esos alimentan el panel ①, que no se usa en este test).
    page.locator("button.nav-btn", has_text="Pace Notes").click()
    page.wait_for_selector("text=Aplicar sonido a video existente", timeout=_T_NAV)

    # Rutas inventadas a propósito: el mux DEBE fallar, pero por una razón de
    # negocio (ffmpeg ausente o pack sin metadata.json), nunca por leer
    # AppState dentro del hilo.
    fake_video = tmp_path / "no_existe.mp4"
    fake_pn_dir = tmp_path / "pack_vacio"
    fake_pn_dir.mkdir()

    page.get_by_label("Video existente (mp4, webm, mov...)").fill(str(fake_video))
    page.keyboard.press("Tab")
    page.get_by_label("Carpeta del pack de Pace Notes").fill(str(fake_pn_dir))
    page.keyboard.press("Tab")

    # El botón queda deshabilitado hasta que _update_apply_enabled() confirma
    # video + carpeta + drv_lap (debounce=400 en el input de video).
    page.wait_for_function(
        """() => {
            const btns = [...document.querySelectorAll('button')];
            const btn = btns.find(b => b.textContent.includes('Aplicar sonido'));
            return !!btn && !btn.disabled;
        }""",
        timeout=_T_NAV,
    )

    page.locator("button", has_text="Aplicar sonido").click()

    notification = page.locator(".q-notification__message").first
    notification.wait_for(state="visible", timeout=_T_MUX)
    message = (notification.text_content() or "").lower()

    assert "app.storage.user" not in message, (
        f"Regresión del bug de PR #30: _do_mux volvió a leer una propiedad de "
        f"AppState (app.storage.user) dentro del hilo run.io_bound sin "
        f"capturarla antes en contexto UI. Mensaje mostrado: {message!r}"
    )
    assert "ui context" not in message, (
        f"Regresión del bug de PR #30 (RuntimeError de contexto UI de "
        f"NiceGUI). Mensaje mostrado: {message!r}"
    )
    assert "ffmpeg no encontrado" in message or "no existe metadata.json" in message, (
        "Se esperaba que el mux fallara por una razón de negocio esperada "
        f"(ffmpeg ausente o pack sin metadata.json), no: {message!r}"
    )
