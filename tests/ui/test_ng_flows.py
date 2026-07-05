"""Tests puros (sin NiceGUI) del dict _FLOWS de ng_helpers.

Verifica la entrada pacenotes y regresion de los flujos existentes.
No requiere nicegui instalado.
"""

from fantasma.ui.ng_helpers import _FLOWS


def test_pacenotes_flow_steps():
    assert _FLOWS["pacenotes"]["steps"] == [0, 1, 2, 5]


def test_pacenotes_flow_next():
    assert _FLOWS["pacenotes"]["next"] == {1: 2, 2: 5, 5: None}


def test_analisis_flow_unchanged():
    assert _FLOWS["analisis"]["steps"] == [0, 1, 2]
    assert _FLOWS["analisis"]["next"] == {1: 2, 2: None}


def test_overlay_flow_unchanged():
    assert _FLOWS["overlay"]["steps"] == [0, 1, 3]
    assert _FLOWS["overlay"]["next"] == {1: 3, 3: None}


def test_compose_flow_unchanged():
    assert _FLOWS["compose"]["steps"] == [0, 1, 3, 4]
    assert _FLOWS["compose"]["next"] == {1: 3, 3: 4, 4: None}


def test_pacenotes_flow_has_required_fields():
    flow = _FLOWS["pacenotes"]
    assert "desc" in flow
    assert "requires" in flow
    assert "deliverables" in flow
