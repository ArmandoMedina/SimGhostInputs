"""Unit tests de AppState — sin NiceGUI testing, sin user fixture.

Se parchea fantasma.ui.ng_state._ng_app con un MagicMock para aislar
AppState del storage real de NiceGUI. Requiere nicegui instalado, pero
no el servidor ni nicegui.testing.

Ejecutar: pytest tests/ui/test_ng_state.py -v
"""

import pytest

# Si nicegui no esta instalado, ng_state.py no puede importarse
pytest.importorskip("nicegui", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'")

from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_state():
    """AppState con storage simulado en un dict plano (sin servidor NiceGUI)."""
    m = MagicMock()
    # ng_state.py accede a _ng_app.storage.user como dict; usamos uno real
    m.storage.user = {}
    with patch("fantasma.ui.ng_state._ng_app", m):
        from fantasma.ui.ng_state import AppState

        yield AppState()


def test_appstate_defaults(mock_state):
    """nav_step == 0, flow_chosen == False, flow_key es el default (str)."""
    state = mock_state
    assert state.nav_step == 0
    assert state.flow_chosen is False
    assert isinstance(state.flow_key, str)
    assert len(state.flow_key) > 0


def test_appstate_flow_key_setter(mock_state):
    """Asignar flow_key='analisis' y leerlo de vuelta da el mismo valor."""
    state = mock_state
    state.flow_key = "analisis"
    assert state.flow_key == "analisis"


def test_appstate_clear_analysis(mock_state):
    """clear_analysis() elimina summary/trace/rows/charts_paths.

    ref_lap y drv_lap no deben tocarse.
    """
    state = mock_state
    # Poblar las claves que clear_analysis debe borrar
    state.summary = {"total_delta": 0.5}
    state.trace = [1, 2, 3]
    state.rows = [{"name": "C01"}]
    state.charts_paths = ["/tmp/chart.png"]
    # Poblar claves que NO deben borrarse
    sentinel_ref = object()
    sentinel_drv = object()
    state.ref_lap = sentinel_ref
    state.drv_lap = sentinel_drv

    state.clear_analysis()

    assert state.summary is None
    assert state.trace is None
    assert state.rows is None
    assert state.charts_paths is None
    # ref_lap y drv_lap no deben tocarse
    assert state.ref_lap is sentinel_ref
    assert state.drv_lap is sentinel_drv


def test_appstate_clear_drv_removes_drv_lap_data(mock_state):
    """clear_drv() elimina drv_lap, drv_laps y drv_path.

    ref_lap y ref_path NO deben tocarse.
    Nota: drv_name no esta en la lista de clear_drv(); no se elimina.
    """
    state = mock_state
    sentinel_lap = object()
    state.drv_lap = sentinel_lap
    state.drv_laps = [sentinel_lap]
    state.drv_path = "/tmp/drv.csv"
    state.drv_name = "mi_vuelta.csv"

    sentinel_ref = object()
    state.ref_lap = sentinel_ref
    state.ref_path = "/tmp/ref.csv"

    state.clear_drv()

    # drv_lap, drv_laps, drv_path deben haberse eliminado
    assert state.drv_lap is None
    assert state.drv_laps is None
    assert state.drv_path is None
    # ref_lap y ref_path no deben tocarse
    assert state.ref_lap is sentinel_ref
    assert state.ref_path == "/tmp/ref.csv"


def test_appstate_nav_step_advance(mock_state):
    """Asignar nav_step=3 y verificar que se lee 3."""
    state = mock_state
    state.nav_step = 3
    assert state.nav_step == 3


def test_appstate_clear_drv_removes_drv_name(mock_state):
    """clear_drv() debe borrar drv_name para no dejar datos viejos del piloto."""
    mock_state.drv_lap = object()
    mock_state.drv_laps = []
    mock_state.drv_path = "/ruta/piloto.csv"
    mock_state.drv_name = "archivo_piloto.csv"
    mock_state.clear_drv()
    assert mock_state.drv_name is None, "drv_name debe quedar None tras clear_drv()"
    assert mock_state.drv_lap is None
