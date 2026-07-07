"""Tests unitarios (sin fixture de UI) para la lógica pura del Paso 5 (WS-4).

_assemble_cue_config y _safe_profile_filename son funciones puras — dict/str
entra, dict/str sale — que no dependen de renderizar nada. Se testean aparte
de los smoke tests de nicegui.testing para no depender solo de Playwright.

Requiere: pip install -e ".[ui-ng]" (ng_step5.py importa nicegui a nivel de
módulo aunque estos tests no rendericen UI).
"""

import pytest

pytest.importorskip("nicegui", reason="nicegui no instalado; ejecuta: pip install -e '.[ui-ng]'")

from fantasma.ui.ng_step5 import _assemble_cue_config, _safe_profile_filename  # noqa: E402


class TestAssembleCueConfig:
    def test_empty_raw_returns_empty_config(self):
        assert _assemble_cue_config({}) == {}

    def test_full_entry_normaliza_priority_a_int(self):
        raw = {"brake": {"enabled": True, "priority": 80.0}}
        assert _assemble_cue_config(raw) == {"brake": {"enabled": True, "priority": 80}}

    def test_enabled_se_fuerza_a_bool(self):
        raw = {"apex": {"enabled": 1, "priority": 90}}
        cfg = _assemble_cue_config(raw)
        assert cfg["apex"]["enabled"] is True

    def test_campos_extra_se_preservan(self):
        raw = {"coast": {"enabled": False, "priority": 50, "solo_sin_frenada": True}}
        cfg = _assemble_cue_config(raw)
        assert cfg["coast"] == {
            "enabled": False,
            "priority": 50,
            "solo_sin_frenada": True,
        }

    def test_claves_none_se_omiten_para_caer_al_default(self):
        raw = {"brake": {"enabled": None, "priority": None}}
        assert _assemble_cue_config(raw) == {}

    def test_valores_vacios_se_omiten_del_resultado(self):
        raw = {"brake": {}, "apex": None}
        assert _assemble_cue_config(raw) == {}

    def test_multiples_tipos_independientes(self):
        raw = {
            "brake": {"enabled": True, "priority": 80.0},
            "apex": {"enabled": False, "priority": 90.0},
        }
        cfg = _assemble_cue_config(raw)
        assert set(cfg) == {"brake", "apex"}
        assert cfg["brake"]["priority"] == 80
        assert cfg["apex"]["enabled"] is False


class TestSafeProfileFilename:
    def test_nombre_simple(self):
        assert _safe_profile_filename("rally") == "rally.json"

    def test_espacios_se_preservan(self):
        assert _safe_profile_filename("mi perfil") == "mi perfil.json"

    def test_separadores_de_ruta_se_sanitizan(self):
        name = _safe_profile_filename("../../etc/passwd")
        assert "/" not in name
        assert ".." not in name

    def test_backslash_se_sanitiza(self):
        name = _safe_profile_filename(r"..\..\windows\system32")
        assert "\\" not in name

    def test_nombre_vacio_cae_a_default(self):
        assert _safe_profile_filename("") == "perfil.json"
        assert _safe_profile_filename("   ") == "perfil.json"

    def test_none_cae_a_default(self):
        assert _safe_profile_filename(None) == "perfil.json"
