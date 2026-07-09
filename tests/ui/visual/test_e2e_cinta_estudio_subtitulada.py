"""E2E cinta de estudio subtitulada: pace notes con Coast + video con HUD quemado.

ADR-0027/ADR-0028 / QA del PO (2026-07-08): produce, con clics reales de Playwright
sobre la UI NiceGUI (nunca llamando compose_video/build_pack por fuera -- "agarrar
el programa y generarlo por fuera no son pruebas confiables"), un video de estudio
que demuestre el cue "Coast (inercia)" quemado como subtitulo. Encadena DOS flujos
reales del wizard porque ninguno solo cubre "generar pack + video con HUD + quemar
esos subtitulos" de punta a punta:

  A) "Solo Pace Notes" (Paso 0->1->2->5): genera el pack de audio con el catalogo
     de cues default y la casilla Coast activada (unico cambio pedido por el PO).
  B) "Video con HUD" (Paso 0->1->3->4): genera el overlay de 2.mp4 y lo compone
     apuntando al pack del flujo A, con "Quemar subtítulos de cues" activado y el
     slider "Tamaño" del HUD (Paso 4) fijado en 0.50 -- el PO vio la cinta anterior
     (2_estudio_coast_ADR0027.mp4, overlay a 1.0x) y pidio bajar la escala a la
     mitad porque "no veo nada".

Material real de esta PC (SIMGHOST_TEST_MATERIAL): 2.mp4 es la grabación cuya
identidad de sincronía (offset, vuelta) quedó registrada en
2_composed.mp4.sync.json por una composición manual anterior -- de ahí sale que el
DRV_CSV correcto es la variante "...T113535.csv" (NO la "...T122432.csv" que usan
otros tests de este directorio, que corresponde a una vuelta distinta).
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

# Skipea el módulo completo si playwright no está disponible.
playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402

from .test_e2e_playwright_wizard import _do_step0, _upload_file  # noqa: E402

# ---------------------------------------------------------------------------
# Material real (configurable via SIMGHOST_TEST_MATERIAL, ver conftest de la suite)
# ---------------------------------------------------------------------------
_MATERIAL_DIR = os.environ.get(
    "SIMGHOST_TEST_MATERIAL",
    r"C:\Repositorio personal\Paterial para test (no es un repo)",
)
_REF_CSV = str(Path(_MATERIAL_DIR) / "GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv")
# La identidad de 2.mp4 (offset 17.0 s, laptime 394.05 s) esta fijada por
# 2_composed.mp4.sync.json -- apunta a la vuelta "...T113535", no a "...T122432".
_DRV_CSV = str(
    Path(_MATERIAL_DIR) / "Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
)
_VIDEO = str(Path(_MATERIAL_DIR) / "2.mp4")
_SIDECAR = Path(_MATERIAL_DIR) / "2_composed.mp4.sync.json"

_MISSING = not (Path(_REF_CSV).exists() and Path(_DRV_CSV).exists() and Path(_VIDEO).exists())
_NO_FFMPEG = shutil.which("ffmpeg") is None
pytestmark = pytest.mark.skipif(
    _MISSING or _NO_FFMPEG,
    reason="Material de 2.mp4/CSVs o ffmpeg no disponibles -- solo corre en la PC de QA del PO.",
)

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
# Directorio propio (NO "cinta-adr0027"): esa corrida anterior esta citada desde
# HANDOFF.md con sus propios nombres de archivo -- reusar el directorio pisaria
# esa evidencia ya referenciada. Esta corrida (escala 0.50, reencuadre ADR-0028)
# deja su propio rastro; Mariana copia lo relevante a qa_runs/mariana-<fecha>/
# como parte del checkpoint (ver docs/ux-patterns.md 2-B).
_QA_DIR = _REPO_ROOT / "qa_runs" / "cinta-adr0028"
_QA_DIR.mkdir(parents=True, exist_ok=True)

_FINAL_VIDEO = Path(_MATERIAL_DIR) / "2_estudio_reencuadre_ADR0028.mp4"
_COMPOSE_OUTDIR = Path(_MATERIAL_DIR) / "e2e_adr0028_compose"

# Slider "Tamaño" del HUD (ng_step4.py: ui.slider(min=0.25, max=1.5, step=0.05)).
# El PO pidió reducir la escala a la mitad ("no veo nada" con el overlay a 1.0x).
_HUD_SCALE_MIN = 0.25
_HUD_SCALE_MAX = 1.5
_HUD_SCALE_TARGET = 0.50

# ---------------------------------------------------------------------------
# Timeouts (ms)
# ---------------------------------------------------------------------------
_T_PAGE_LOAD = 20_000
_T_NAV = 15_000
_T_UPLOAD = 90_000
_T_ANALYSIS = 90_000
_T_RENDER = 600_000  # overlay y compose de 2.mp4 (~700 MB) pueden tardar varios minutos
_T_AUTOSYNC = 120_000


# ---------------------------------------------------------------------------
# Helpers locales
# ---------------------------------------------------------------------------


def _known_offset_s():
    """Offset (s) de una composición manual anterior de este mismo 2.mp4.

    Fallback si la detección automática de sincronía falla: sigue siendo un
    valor tecleado a mano en un input real, equivalente a leerlo en VLC (la
    ruta manual que la propia UI documenta), no un bypass de la UI.
    """
    if not _SIDECAR.exists():
        return None
    try:
        data = json.loads(_SIDECAR.read_text(encoding="utf-8"))
        return float(data.get("offset"))
    except (OSError, ValueError, TypeError):
        return None


def _do_step5_pacenotes_coast(page, url):
    """Flujo 'Solo Pace Notes' con los CSVs de este módulo, hasta Paso 5.

    Variante local de _do_step5_pacenotes (test_e2e_playwright_wizard.py): ese
    helper cierra sobre el REF_CSV/DRV_CSV de SU módulo, que no son la pareja
    correcta para la identidad de sincronía de 2.mp4 (ver _DRV_CSV arriba).
    """
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("text=SimGhostInputs", timeout=_T_PAGE_LOAD)

    card = page.locator(".q-card", has_text="Solo Pace Notes")
    card.locator("button", has_text="Elegir este").click()
    page.wait_for_selector("text=Seleccionado", timeout=10_000)
    page.locator("button", has_text="Empezar").click()
    page.wait_for_selector("text=Paso 1", timeout=_T_NAV)

    _upload_file(page, 0, _REF_CSV)
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
    _upload_file(page, 1, _DRV_CSV)
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)

    page.locator("button", has_text="Cargar y ver análisis").click()
    page.wait_for_selector("text=Paso 2", timeout=_T_NAV)

    page.wait_for_selector("text=🔔 Generar Pace Notes", timeout=_T_ANALYSIS)
    page.locator("button", has_text="Generar Pace Notes").click()
    page.wait_for_selector("text=Paso 5", timeout=_T_NAV)


def _click_checkbox(page, label_text: str):
    """Clickea un ui.checkbox de NiceGUI por su label y espera a que quede marcado.

    NiceGUI aplica el estado tras un round-trip por WebSocket, así que el click y
    la lectura del estado NO son síncronos: reintenta hasta que aria-checked (o la
    clase q-checkbox--checked) confirme el cambio. Devuelve el locator del
    contenedor .q-checkbox.
    """
    box = page.locator(".q-checkbox", has_text=label_text).first
    box.wait_for(state="visible", timeout=_T_NAV)
    for _ in range(3):
        box.click()
        # 2.5 s es de sobra para el round-trip; si ya quedó marcado, no re-clickea
        # (evita togglearlo de vuelta a apagado).
        if _checkbox_is_checked(box, timeout_ms=2500):
            break
    return box


def _checkbox_is_checked(box, timeout_ms: int = 0) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while True:
        classes = box.get_attribute("class") or ""
        if "q-checkbox--checked" in classes:
            return True
        if box.get_attribute("aria-checked") == "true":
            return True
        if time.monotonic() >= deadline:
            return False
        box.page.wait_for_timeout(100)


def _set_hud_scale(
    page, target: float, min_v: float = _HUD_SCALE_MIN, max_v: float = _HUD_SCALE_MAX
):
    """Fija el slider "Tamaño" del HUD (Paso 4, ng_step4.py:425) por clic real.

    El q-slider de Quasar/NiceGUI no es un <input type=range>: es un div con
    role="slider" cuyo valor, al clickear el track, se calcula a partir de la
    fraccion horizontal del punto clickeado -- value = min + fraccion*(max-min),
    redondeado al step. Se verifico en vivo (montando solo el Paso 4 con
    Playwright, en una pagina que cabia entera en el viewport) que un click de
    precision en esa fraccion cae exacto en el step deseado.

    PRIMER INTENTO FALLIDO (corrida real 2026-07-08): con page.mouse.click(x,y)
    sobre coordenadas de bounding_box() el slider se quedo en su valor default
    (1.0) -- en la pagina completa del wizard (con paneles arriba) el track
    puede no estar dentro del viewport visible, y mouse.click() NO hace
    auto-scroll (a diferencia de locator.click()). Por eso aqui se usa
    track.click(position=...): mismo calculo de fraccion, pero dejando que
    Playwright resuelva scroll-into-view + actionability antes del click.

    No hay un patron previo de sliders en la suite (los demas tests solo tocan
    checkboxes/inputs) -- este helper es nuevo, documentado para reuso.
    """
    track = page.locator(".q-slider__track-container").first
    track.wait_for(state="visible", timeout=_T_NAV)
    track.scroll_into_view_if_needed(timeout=_T_NAV)
    box = track.bounding_box()
    fraction = (target - min_v) / (max_v - min_v)
    track.click(position={"x": fraction * box["width"], "y": box["height"] / 2})

    root = page.locator(".q-slider[role=slider]").first
    deadline = time.monotonic() + 3.0
    current = None
    while time.monotonic() < deadline:
        current = root.get_attribute("aria-valuenow")
        if current is not None and abs(float(current) - target) < 1e-9:
            return
        page.wait_for_timeout(100)
    # Fallback: nudge con flechas si el click no cayo exacto (p.ej. redondeo
    # por un layout/DPI distinto al de la maquina donde se verifico el helper).
    # El propio click de arriba ya dejo el foco en el track (tabindex=0).
    for _ in range(10):
        current = float(root.get_attribute("aria-valuenow") or 0.0)
        if abs(current - target) < 1e-9:
            return
        page.keyboard.press("ArrowRight" if current < target else "ArrowLeft")
        page.wait_for_timeout(150)
    final = root.get_attribute("aria-valuenow")
    assert final is not None and abs(float(final) - target) < 1e-9, (
        f"El slider 'Tamaño' del HUD quedo en {final!r}, no en {target} tras click+ajuste"
    )


def _wait_autosync(page, timeout_ms: int = _T_AUTOSYNC) -> bool:
    """Espera el resultado de 'Detectar sincronía automáticamente' y lo resuelve.

    Devuelve True si al terminar el offset quedó fijado (directo o tras elegir
    la vuelta ambigua); False si la detección falló -- el llamador cae entonces
    al offset conocido del sidecar (_known_offset_s).
    """
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if page.locator("text=Offset detectado:").count() > 0:
            return True
        if page.locator("text=Confirmar esta vuelta").count() > 0:
            page.locator("button", has_text="Confirmar esta vuelta").click()
            return True
        if page.locator("text=Correlación insuficiente").count() > 0:
            return False
        if page.locator("text=Error en auto-sync").count() > 0:
            return False
        if page.locator(".text-red-400").count() > 0:
            return False
        page.wait_for_timeout(1000)
    return False


def _extract_frame(video_path: Path, time_s: float, out_png: Path) -> None:
    """Recorta un frame del video en el segundo dado (evidencia de QA)."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            "%.3f" % max(0.0, time_s),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out_png),
        ],
        check=True,
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


def test_pw_cinta_estudio_subtitulada_default_coast(pw_page, nicegui_url, tmp_path):
    """Cinta de estudio: pack de pace notes (Coast ON) + video con HUD y subtítulos quemados.

    Reproduce la configuración elegida por el PO (QA 2026-07-08): catálogo de cues
    default, con la casilla Coast activada (resto tal cual viene). Encadena dos
    flujos reales del wizard (ver docstring del módulo).

    Verifica:
    - El pack generado en el flujo A trae al menos una entrada "coast" (inercia).
    - El slider "Tamaño" del HUD (Paso 4) quedó fijado en 0.50 antes de componer.
    - El video final del flujo B existe y pesa más que un archivo vacío/corrupto.
    - Se recorta un frame del video en el segundo del cue "inercia" (evidencia
      para el PO) y, si existe, también del cue "inicio de acelerador" más cercano.

    Guarda:
    - <SIMGHOST_TEST_MATERIAL>/2_estudio_reencuadre_ADR0028.mp4 -- el entregable.
    - qa_runs/cinta-adr0028/*.png -- capturas de Playwright + frames del subtítulo
      (directorio propio, NO pisa qa_runs/cinta-adr0027/ que ya está citado desde
      HANDOFF.md).
    """
    page = pw_page

    # ── Flujo A: Solo Pace Notes, con Coast activado ──────────────────────────
    _do_step5_pacenotes_coast(page, nicegui_url)

    page.wait_for_selector("text=Cues: selección y prioridad", timeout=_T_NAV)
    coast_box = _click_checkbox(page, "Coast (inercia)")
    assert _checkbox_is_checked(coast_box), "La casilla 'Coast (inercia)' no quedó activada"

    # La curva del 317/393 (C02, un kink sin frenada) NO está entre las de mayor
    # pérdida de tiempo, así que el Top-N default la deja fuera y el coast no
    # aparecería. "Todas las curvas" cubre TODAS las detectadas -> incluye C02 y
    # su coast (que solo_sin_frenada=True permite por ser curva sin freno).
    all_box = _click_checkbox(page, "Todas las curvas")
    assert _checkbox_is_checked(all_box), "La casilla 'Todas las curvas' no quedó activada"

    # Cue "gear" (cambio de marcha, solo subtítulo): viene enabled=False por
    # defecto (DEFAULT_CONFIG) -- sin este click el pack no trae NINGUNA
    # entrada "gear" y el metro ~1745 (el reclamo original del PO) se queda
    # sin subtítulo otra vez, aunque el motor ya lo soporte.
    gear_box = _click_checkbox(page, "Cambio de marcha (solo subtítulo)")
    assert _checkbox_is_checked(gear_box), "La casilla 'Cambio de marcha' no quedó activada"
    page.screenshot(path=str(_QA_DIR / "01_paso5_coast_activado.png"))

    page.locator("button", has_text="Generar Pace Notes").click()
    page.wait_for_selector("text=Listo:", timeout=_T_ANALYSIS)

    outdir_text = page.locator("text=Directorio:").first.text_content()
    pack_dir = outdir_text.split("Directorio:", 1)[1].strip()
    assert pack_dir and Path(pack_dir).exists(), f"Carpeta del pack no encontrada: {pack_dir!r}"

    metadata_path = Path(pack_dir) / "metadata.json"
    assert metadata_path.exists(), f"El pack no escribió metadata.json en {pack_dir}"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    entries = metadata.get("entries", [])

    coast_entries = [e for e in entries if e.get("description", "").endswith("— inercia")]
    assert coast_entries, (
        "No se generó ninguna entrada 'coast' (inercia) en el pack pese a activar "
        "la casilla Coast -- regresión en build_pack/plan_tone_events."
    )
    throttle_entries = [
        e for e in entries if e.get("description", "").endswith("— inicio de acelerador")
    ]
    gear_entries = [e for e in entries if e.get("description", "").endswith("— cambio de marcha")]
    assert gear_entries, (
        "No se generó ninguna entrada 'gear' (cambio de marcha) en el pack pese a "
        "activar la casilla -- regresión en detect_gear_shifts/plan_tone_events, o "
        "el wiring de state.gear_shifts se rompió."
    )

    page.screenshot(path=str(_QA_DIR / "02_paso5_pack_generado.png"))

    # ── Flujo B: Video con HUD, overlay de 2.mp4 + pack del flujo A quemado ───
    # Contexto NUEVO: la app recuerda el paso alcanzado en app.storage.user
    # (cookie de sesión), así que reusar la sesión del flujo A caería en Paso 5,
    # no en la selección de flujo -- el botón "Elegir este" no existiría. Un
    # contexto limpio = usuario NiceGUI nuevo = Paso 0 fresco. pack_dir (flujo A)
    # es una variable Python, se conserva entre contextos.
    page = page.context.browser.new_context(
        viewport={"width": 1280, "height": 900}, device_scale_factor=1
    ).new_page()
    _do_step0(page, nicegui_url)

    _upload_file(page, 0, _REF_CSV)
    page.wait_for_selector("text=Referencia cargada", timeout=_T_UPLOAD)
    _upload_file(page, 1, _DRV_CSV)
    page.wait_for_selector("text=Tu vuelta cargada", timeout=_T_UPLOAD)
    page.locator("button", has_text="Cargar y generar overlay").click()
    page.wait_for_selector("text=Paso 3", timeout=_T_NAV)

    if page.locator("text=ffmpeg no esta instalado").count() > 0:
        pytest.skip("ffmpeg no instalado -- Paso 3 no disponible en este entorno")

    overlay_dir = tmp_path / "overlay_adr0027"
    folder_input = page.locator("input[placeholder*='fantasma_salida']")
    if folder_input.count() == 0:
        folder_input = page.get_by_label("Carpeta donde guardar el overlay")
    folder_input.first.fill(str(overlay_dir))
    page.locator("button", has_text="Generar overlay").click()

    try:
        page.wait_for_selector("text=Overlay generado:", timeout=_T_RENDER)
    except PlaywrightTimeoutError:
        if not list(overlay_dir.glob("*.webm")):
            page.screenshot(path=str(_QA_DIR / "overlay_timeout.png"))
            pytest.skip("render de overlay superó el timeout -- Nordschleife es larga")

    page.screenshot(path=str(_QA_DIR / "03_paso3_overlay_listo.png"))
    page.locator("button", has_text="Ir al Paso 4").click()
    page.wait_for_selector("text=Paso 4", timeout=_T_NAV)

    # ① Archivos de entrada: el video de la grabación (el overlay ya viene
    # prefijado desde state.last_overlay, mismo tab/sesión que el Paso 3).
    video_input = page.get_by_label("Tu video de grabación")
    if video_input.count() == 0:
        video_input = page.locator("input[placeholder*='mi_sesion.mp4']")
    video_input.first.fill(_VIDEO)

    # ② Sincronía: intenta la detección automática real; si falla, cae al
    # offset ya conocido del sidecar de una composición manual anterior.
    page.locator("button", has_text="Detectar sincronía automáticamente").click()
    synced = _wait_autosync(page)
    if not synced:
        known_offset = _known_offset_s()
        if known_offset is None:
            pytest.skip(
                "Detección automática de sincronía falló y no hay offset de "
                "referencia conocido (2_composed.mp4.sync.json) para el fallback manual."
            )
        offset_input = page.get_by_label("Offset (s desde inicio del video hasta la meta)")
        offset_input.first.fill(str(known_offset))
        page.keyboard.press("Tab")

    offset_value = float(
        page.get_by_label("Offset (s desde inicio del video hasta la meta)").first.input_value()
    )

    # ③ Carpeta de salida: subcarpeta dedicada (NO pisa el 2_composed.mp4 ya existente)
    out_folder_input = page.get_by_label("Carpeta donde guardar el video final")
    if out_folder_input.count() == 0:
        out_folder_input = page.locator("input[type='text']").last
    out_folder_input.first.fill(str(_COMPOSE_OUTDIR))

    # ④ Pace Notes en el video: apunta al pack del flujo A y quema subtítulos
    pn_box = _click_checkbox(page, "Incluir pace notes en el video")
    assert _checkbox_is_checked(pn_box), "La casilla 'Incluir pace notes en el video' no se activó"
    pn_dir_input = page.get_by_label("Carpeta del pack de Pace Notes")
    pn_dir_input.first.fill(pack_dir)
    subs_box = _click_checkbox(page, "Quemar subtítulos de cues")
    assert _checkbox_is_checked(subs_box), "La casilla 'Quemar subtítulos de cues' no se activó"

    # ⑤ Escala del HUD: el PO pidió bajarla a la mitad (QA 2026-07-08, "no veo
    # nada" con el overlay a 1.0x) -- clic real sobre el slider "Tamaño".
    _set_hud_scale(page, _HUD_SCALE_TARGET)
    scale_label_text = page.locator("text=/Tamaño:/").first.text_content()
    assert "0.50" in scale_label_text, (
        f"La etiqueta del slider no confirma escala 0.50: {scale_label_text!r}"
    )

    page.screenshot(path=str(_QA_DIR / "04_paso4_config_lista.png"))

    page.locator("button", has_text="Componer video").click()

    try:
        page.wait_for_selector("text=Video guardado:", timeout=_T_RENDER)
    except PlaywrightTimeoutError:
        composed_early = _COMPOSE_OUTDIR / "2_composed.mp4"
        if not composed_early.exists():
            page.screenshot(path=str(_QA_DIR / "compose_timeout.png"))
            pytest.skip("compose de 2.mp4 superó el timeout de %d ms" % _T_RENDER)

    page.screenshot(path=str(_QA_DIR / "05_paso4_video_listo.png"))

    composed_path = _COMPOSE_OUTDIR / "2_composed.mp4"
    assert composed_path.exists(), f"compose_video no dejó el archivo esperado en {composed_path}"
    assert composed_path.stat().st_size > 10_000_000, (
        f"{composed_path} pesa menos de 10 MB -- probable render corrupto/incompleto"
    )

    if _FINAL_VIDEO.exists():
        _FINAL_VIDEO.unlink()
    shutil.move(str(composed_path), str(_FINAL_VIDEO))
    try:
        _COMPOSE_OUTDIR.rmdir()
    except OSError:
        pass

    # ── Evidencia: frame del video en el segundo del cue "inercia" ────────────
    # Introspección de solo-lectura sobre artefactos que la UI real ya generó
    # (metadata.json del pack + el propio DRV_CSV) para saber DÓNDE recortar el
    # frame -- no genera ni recompone nada, solo ubica el segundo del subtítulo.
    from fantasma.core.normalize import fastest_lap
    from fantasma.importers import load_laps
    from fantasma.viz.pacenotes import _dist_to_time

    drv_lap = fastest_lap(load_laps(_DRV_CSV))

    coast_entries.sort(key=lambda e: e.get("distanceRoundTrack", 0))
    coast_entry = coast_entries[0]
    t_coast = _dist_to_time(drv_lap, float(coast_entry["distanceRoundTrack"]))
    video_t_coast = offset_value + t_coast + 0.5
    _extract_frame(
        _FINAL_VIDEO,
        video_t_coast,
        _QA_DIR / ("subtitulo_inercia_m%d.png" % coast_entry["distanceRoundTrack"]),
    )

    if throttle_entries:
        throttle_entry = min(
            throttle_entries,
            key=lambda e: abs(e.get("distanceRoundTrack", 0) - coast_entry["distanceRoundTrack"]),
        )
        t_throttle = _dist_to_time(drv_lap, float(throttle_entry["distanceRoundTrack"]))
        video_t_throttle = offset_value + t_throttle + 0.5
        _extract_frame(
            _FINAL_VIDEO,
            video_t_throttle,
            _QA_DIR / ("subtitulo_acelerador_m%d.png" % throttle_entry["distanceRoundTrack"]),
        )

    # Evidencia puntual del reclamo original del PO (QA 2026-07-08): el metro
    # ~1745 traía un cambio de marcha sin sonido NI subtítulo. Recorta el cue
    # "gear" más cercano a esa distancia (el motor no promete exactamente 1745,
    # depende de dónde detect_gear_shifts marque el cambio real en la vuelta).
    gear_entry = min(gear_entries, key=lambda e: abs(e.get("distanceRoundTrack", 0) - 1745))
    t_gear = _dist_to_time(drv_lap, float(gear_entry["distanceRoundTrack"]))
    video_t_gear = offset_value + t_gear + 0.5
    _extract_frame(
        _FINAL_VIDEO,
        video_t_gear,
        _QA_DIR / ("subtitulo_cambio_marcha_m%d.png" % gear_entry["distanceRoundTrack"]),
    )
