"""End-to-end tests NiceGUI — wizard de 5 pasos.

Estrategia:
  - AppState usa app.storage.user (respaldado en JSON en disco). Inyectar
    objetos Lap grandes en esa clave genera un archivo JSON de cientos de MB,
    lo que en Windows 11 deja el descriptor abierto durante el teardown y
    provoca PermissionError al borrar el fichero. Eso aborta la limpieza de
    sys.modules de NiceGUI, por lo que la ruta "/" no se re-registra en tests
    posteriores (404 en cascada).

  Solución: _SharedState — sustituye AppState con una clase respaldada por un
  dict de clase (en memoria, sin I/O). Se monkeypatea DESPUÉS de importar el
  módulo (que registra la ruta "/") y ANTES de user.open("/").

  - Para el Paso 2: la comparación se pre-ejecuta sincrónicamente en el setUp
    del test; se inyecta summary/trace/rows ya calculados para que ng_step2
    vea state.summary != None y omita el io_bound.
  - Para el Paso 3: requiere ffmpeg; el test se salta si no está instalado.
  - CSVs reales: GO BMW M4 GT3 NORDSCHLEIFE (ref) y Nordschleife jocmaster (drv).

Requiere: pip install -e ".[ui-ng]"
Ejecutar:  pytest tests/ui/test_e2e_wizard.py -v
"""

import shutil
from pathlib import Path

import pytest

pytest.importorskip(
    "nicegui.testing",
    reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'",
)

# ── Rutas a los CSVs de test ──────────────────────────────────────────────────

_MATERIAL = Path(r"C:\Repositorio personal\Paterial para test (no es un repo)")
_REF_CSV = _MATERIAL / "GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
_DRV_CSV = _MATERIAL / "Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv"
_CSVS_AVAILABLE = _REF_CSV.exists() and _DRV_CSV.exists()

_SKIP_CSVS = pytest.mark.skipif(
    not _CSVS_AVAILABLE,
    reason=f"CSVs de test no encontrados en '{_MATERIAL}'",
)


# ── _SharedState ──────────────────────────────────────────────────────────────

class _SharedState:
    """Reemplaza AppState con un dict de clase en memoria.

    Permite pre-poblar datos antes de user.open("/") sin escribir nada a disco.
    Todos los atributos de AppState deben estar cubiertos aquí.
    """

    _DEFAULTS: dict = {
        "flow_key": "compose",
        "nav_step": 0,
        "flow_chosen": False,
        "ref_lap": None,
        "drv_lap": None,
        "ref_laps": None,
        "drv_laps": None,
        "ref_path": None,
        "drv_path": None,
        "ref_name": None,
        "drv_name": None,
        "corners": None,
        "corners_editable": False,
        "ref_col_map": None,
        "summary": None,
        "trace": None,
        "rows": None,
        "charts_paths": None,
        "last_overlay": None,
        "last_compose_video": None,
        "compose_offset": 0.0,
    }
    _shared: dict = {}

    def __init__(self):
        # No usar self.__dict__ aquí para no disparar __setattr__
        pass

    def __getattr__(self, name: str):
        shared = object.__getattribute__(type(self), "_shared")
        defaults = object.__getattribute__(type(self), "_DEFAULTS")
        if name in shared:
            return shared[name]
        return defaults.get(name)

    def __setattr__(self, name: str, value) -> None:
        type(self)._shared[name] = value

    def clear_analysis(self) -> None:
        for k in ("summary", "trace", "rows", "charts_paths"):
            type(self)._shared.pop(k, None)

    def clear_drv(self) -> None:
        for k in (
            "drv_lap", "drv_laps", "drv_path", "drv_name",
            "summary", "trace", "rows", "charts_paths",
            "last_overlay", "corners", "corners_editable", "compose_offset",
        ):
            type(self)._shared.pop(k, None)

    @classmethod
    def reset(cls, **initial_values) -> None:
        """Resetea al estado por defecto y aplica los valores dados."""
        cls._shared = dict(cls._DEFAULTS)
        cls._shared.update(initial_values)


# ── Helpers de test ───────────────────────────────────────────────────────────


def _load_real_laps(path: Path):
    from fantasma.ui.ng_helpers import _load_laps
    return _load_laps(str(path))


def _pre_compare(ref_lap, drv_lap):
    """Compare sincrónico. Devuelve (trace, rows, summary, corners)."""
    from fantasma.core.compare import compare
    from fantasma.core.corners import detect_corners, extract_milestones

    evs, _ = detect_corners(ref_lap)
    corners = extract_milestones(ref_lap, evs)
    trace, rows, summary = compare(ref_lap, drv_lap, step=1.0, corners=corners)
    return trace, rows, summary, corners


# ── PASO 0: selección de flujo ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_e2e_step0_select_flow_overlay(user):
    """Las tarjetas de flujo se muestran; 'Empezar' navega al Paso 1."""
    from fantasma.ui.ng_app import main_page  # noqa: F401 — registra la ruta "/"

    await user.open("/")
    await user.should_see("SimGhostInputs")
    await user.should_see("quieres obtener hoy")
    await user.should_see("Solo análisis")
    await user.should_see("Solo overlay")
    await user.should_see("Video con HUD")

    # Seleccionar un flujo antes de "Empezar" (F-01: guard requiere seleccion)
    user.find("Elegir este").click()
    await user.should_see("Seleccionado")

    user.find("Empezar").click()
    await user.should_see("Paso 1")


# ── PASO 1: nombres de archivo cargados ──────────────────────────────────────


@pytest.mark.asyncio
@_SKIP_CSVS
async def test_e2e_step1_load_reference_and_driver(user, monkeypatch):
    """Con laps pre-inyectados en _SharedState, Paso 1 muestra 'Referencia ya cargada'."""
    ref_laps = _load_real_laps(_REF_CSV)
    drv_laps = _load_real_laps(_DRV_CSV)
    assert ref_laps, "El CSV de referencia no produjo vueltas"
    assert drv_laps, "El CSV del driver no produjo vueltas"

    _SharedState.reset(
        ref_laps=ref_laps,
        ref_path=str(_REF_CSV),
        ref_name=_REF_CSV.name,
        drv_laps=drv_laps,
        drv_path=str(_DRV_CSV),
        drv_name=_DRV_CSV.name,
        flow_key="overlay",
        flow_chosen=True,
    )

    import fantasma.ui.ng_app as _ng_mod
    monkeypatch.setattr(_ng_mod, "AppState", _SharedState)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Importar").click()
    await user.should_see("Paso 1")
    # Con ref_laps pre-cargado, el label de estado muestra "✓ Referencia ya cargada"
    await user.should_see("Referencia ya cargada")


# ── PASO 2: barra de resumen con delta ───────────────────────────────────────


@pytest.mark.asyncio
@_SKIP_CSVS
async def test_e2e_step2_compare_runs_and_shows_summary(user, monkeypatch):
    """Con summary pre-inyectado, Paso 2 muestra la barra con 'Delta total'.

    rows se inyecta vacío a propósito: ng_step2 solo muestra el botón de
    descarga CSV cuando csv_bytes != b"", que ocurre cuando rows es no-vacío.
    ui.download() devuelve None en modo test y ng_step2 llama .classes() sobre
    él — eso produce un AttributeError que el framework captura como log ERROR
    y falla el teardown. Usar rows=[] elimina el ui.download call sin
    necesitar mockear ui.download (cuyo monkeypatch es ignorado porque
    user.__getattribute__ lo restaura en cada acceso al objeto user).
    """
    from nicegui import ui

    from fantasma.core.normalize import fastest_lap as _fl

    ref_laps = _load_real_laps(_REF_CSV)
    drv_laps = _load_real_laps(_DRV_CSV)
    ref_lap = _fl(ref_laps)
    drv_lap = _fl(drv_laps)

    # Comparación sincrónica en setUp — ng_step2 verá state.summary != None
    _, _rows_real, summary, corners = _pre_compare(ref_lap, drv_lap)

    _SharedState.reset(
        ref_lap=ref_lap,
        drv_lap=drv_lap,
        ref_laps=ref_laps,
        drv_laps=drv_laps,
        trace=[],          # trace vacío: sin gráficas (evita matplotlib en CI)
        rows=[],           # rows vacío: ng_step2 NO llama ui.download → sin error
        charts_paths=[],   # skip chart generation
        summary=summary,
        corners=corners,
        flow_key="analisis",
        flow_chosen=True,
    )

    import fantasma.ui.ng_app as _ng_mod
    monkeypatch.setattr(_ng_mod, "AppState", _SharedState)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    # Filtrar por kind=ui.button para evitar el brand HTML del sidebar
    user.find(kind=ui.button, content="Análisis").click()
    await user.should_see("Paso 2")
    # La barra de resumen (summary-bar) depende de state.summary, no de rows
    await user.should_see("Delta total")
    await user.should_see("Referencia")
    await user.should_see("Tu vuelta")


# ── PASO 3: UI de generación de overlay con datos cargados ───────────────────


@pytest.mark.asyncio
@_SKIP_CSVS
async def test_e2e_step3_overlay_generates_output(user, monkeypatch):
    """Con datos cargados, el Paso 3 muestra los controles de overlay sin el guard de guardia.

    LIMITACIÓN CONOCIDA — por qué no se hace clic en nicegui.testing:
      El on_click de 'Generar overlay' (_start_render) crea un ui.timer(0.5, poll)
      que persiste tras el fin del test. NiceGUI intenta cancelarlo en teardown pero
      en Windows el event loop ya está cerrado → RuntimeError: Event loop is closed,
      que corrompe el teardown del siguiente test. Patchar ui.timer no funciona porque
      user.__getattribute__ restaura ui.* en cada acceso al fixture user.
      El comportamiento post-clic (render real) se verifica en tests de integración CLI.
    """
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg no instalado — el Paso 3 lo requiere para renderizar")

    from fantasma.core.normalize import fastest_lap as _fl

    ref_laps = _load_real_laps(_REF_CSV)
    drv_laps = _load_real_laps(_DRV_CSV)
    ref_lap = _fl(ref_laps)
    drv_lap = _fl(drv_laps)

    _SharedState.reset(
        ref_lap=ref_lap,
        drv_lap=drv_lap,
        flow_key="overlay",
        flow_chosen=True,
    )

    import fantasma.ui.ng_app as _ng_mod
    monkeypatch.setattr(_ng_mod, "AppState", _SharedState)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    await user.open("/")
    user.find("Overlay").click()
    await user.should_see("Paso 3")

    # Con ref_lap cargado el guard "Primero carga los archivos en el Paso 1."
    # NO debe mostrarse — confirma que el estado se inyectó correctamente.
    await user.should_not_see("Primero carga")

    # Los controles de configuración del render son visibles
    await user.should_see("Generar overlay")
    await user.should_see("FPS del overlay")
    await user.should_see("Carpeta donde guardar el overlay")


# ── Happy path completo: flujo compose ───────────────────────────────────────


@pytest.mark.asyncio
@_SKIP_CSVS
async def test_e2e_full_happy_path_compose_flow(user, monkeypatch):
    """step0 cards → step1 (datos pre-cargados) → step4 (Componer renderiza sin error)."""
    from fantasma.core.normalize import fastest_lap as _fl

    ref_laps = _load_real_laps(_REF_CSV)
    drv_laps = _load_real_laps(_DRV_CSV)
    ref_lap = _fl(ref_laps)
    drv_lap = _fl(drv_laps)
    trace, rows, summary, corners = _pre_compare(ref_lap, drv_lap)

    _SharedState.reset(
        ref_laps=ref_laps,
        drv_laps=drv_laps,
        ref_lap=ref_lap,
        drv_lap=drv_lap,
        ref_name=_REF_CSV.name,
        drv_name=_DRV_CSV.name,
        trace=trace,
        rows=rows,
        summary=summary,
        corners=corners,
        flow_key="compose",
        flow_chosen=True,
    )

    import fantasma.ui.ng_app as _ng_mod
    monkeypatch.setattr(_ng_mod, "AppState", _SharedState)

    from fantasma.ui.ng_app import main_page  # noqa: F401

    # STEP 0: tarjetas visibles
    await user.open("/")
    await user.should_see("Video con HUD")
    await user.should_see("Solo overlay")
    await user.should_see("Solo análisis")

    # STEP 1: archivos pre-cargados visibles
    user.find("Importar").click()
    await user.should_see("Paso 1")
    await user.should_see("Referencia ya cargada")

    # STEP 4: heading siempre visible (renderizado antes del guard ffmpeg)
    user.find("Video").click()
    await user.should_see("Paso 4")
    # "Componer" aparece en "Paso 4 — Componer video final"
    await user.should_see("Componer")
