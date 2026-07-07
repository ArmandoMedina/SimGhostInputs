import json

import pytest

from fantasma.viz import cue_profiles
from fantasma.viz.pacenotes import DEFAULT_CONFIG


def test_config_to_profile_default_matches_default_config():
    """config_to_profile(None) refleja DEFAULT_CONFIG tipo por tipo."""
    profile = cue_profiles.config_to_profile(None, name="default")
    assert profile["schema"] == cue_profiles.SCHEMA_NAME
    assert profile["version"] == cue_profiles.SCHEMA_VERSION
    assert profile["name"] == "default"
    by_type = {cue["type"]: cue for cue in profile["cues"]}
    assert set(by_type) == set(DEFAULT_CONFIG)
    for cue_type, default_cfg in DEFAULT_CONFIG.items():
        for key, value in default_cfg.items():
            assert by_type[cue_type][key] == value


def test_round_trip_default_config(tmp_path):
    """config_to_profile -> save_profile -> load_profile reproduce el cue_config."""
    path = tmp_path / "pack.json"
    cue_profiles.save_profile(path, None, name="default")
    loaded = cue_profiles.load_profile(path)
    for cue_type, default_cfg in DEFAULT_CONFIG.items():
        for key, value in default_cfg.items():
            assert loaded[cue_type][key] == value


def test_round_trip_custom_config(tmp_path):
    """Un cue_config custom (solo brake+countdown activos) sobrevive el round-trip."""
    custom = {
        "brake_countdown": {"enabled": True, "priority": 100},
        "brake": {"enabled": True, "priority": 80},
        "brake_release": {"enabled": False, "priority": 70},
        "turn_in": {"enabled": False, "priority": 60},
        "throttle_on": {"enabled": False, "priority": 85},
        "full_throttle": {"enabled": False, "priority": 75},
        "apex": {"enabled": False, "priority": 90},
        "coast": {"enabled": False, "priority": 50, "solo_sin_frenada": True},
        "gear": {"enabled": False, "priority": 65},
    }
    path = tmp_path / "solo-frenada.json"
    cue_profiles.save_profile(path, custom, name="solo-frenada")
    loaded = cue_profiles.load_profile(path)
    assert loaded == custom


def test_load_profile_malformed_json_raises_clear_error(tmp_path):
    """JSON malformado da un ValueError con mensaje claro, no un traceback pelon."""
    path = tmp_path / "roto.json"
    path.write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(ValueError, match="no es JSON valido"):
        cue_profiles.load_profile(path)


def test_load_profile_unknown_version_raises_clear_error(tmp_path):
    """Una version desconocida (999) da un error accionable, no un crash."""
    path = tmp_path / "futuro.json"
    profile = {
        "schema": cue_profiles.SCHEMA_NAME,
        "version": 999,
        "name": "del futuro",
        "cues": [],
    }
    path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        cue_profiles.load_profile(path)


def test_load_profile_wrong_schema_raises_clear_error(tmp_path):
    """Un schema que no es simghost-cue-profile da un error accionable."""
    path = tmp_path / "otro-esquema.json"
    profile = {"schema": "algo-mas", "version": 1, "cues": []}
    path.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        cue_profiles.load_profile(path)


def test_load_profile_not_an_object_raises_clear_error(tmp_path):
    """Un JSON valido pero que no es un objeto (p.ej. una lista) da error claro."""
    path = tmp_path / "lista.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="objeto JSON"):
        cue_profiles.load_profile(path)


def test_profile_to_config_ignores_unknown_type_with_warning(capsys):
    """Un tipo desconocido se ignora (con aviso), los conocidos se cargan igual."""
    profile = {
        "schema": cue_profiles.SCHEMA_NAME,
        "version": 1,
        "cues": [
            {"type": "brake", "enabled": True, "priority": 99},
            {"type": "cue_del_futuro", "enabled": True, "priority": 1},
        ],
    }
    cue_config = cue_profiles.profile_to_config(profile)
    assert "brake" in cue_config
    assert cue_config["brake"]["priority"] == 99
    assert "cue_del_futuro" not in cue_config
    err = capsys.readouterr().err
    assert "cue_del_futuro" in err


def test_load_profile_unknown_type_does_not_crash(tmp_path):
    """load_profile con un tipo desconocido en el JSON carga los conocidos, no truena."""
    path = tmp_path / "mixto.json"
    profile = {
        "schema": cue_profiles.SCHEMA_NAME,
        "version": 1,
        "cues": [
            {"type": "brake", "enabled": True, "priority": 77},
            {"type": "hyperdrive", "enabled": True, "priority": 5},
        ],
    }
    path.write_text(json.dumps(profile), encoding="utf-8")
    cue_config = cue_profiles.load_profile(path)
    assert cue_config["brake"]["priority"] == 77
    assert "hyperdrive" not in cue_config


def test_profile_to_config_missing_fields_fall_back_to_default():
    """Un cue con solo 'type' (sin enabled/priority) cae al default via _cue_cfg."""
    profile = {
        "schema": cue_profiles.SCHEMA_NAME,
        "version": 1,
        "cues": [{"type": "coast"}],
    }
    cue_config = cue_profiles.profile_to_config(profile)
    # profile_to_config preserva el override tal cual (aqui vacio); el fallback
    # al default ocurre cuando el pipeline resuelve via _cue_cfg, no aqui.
    assert cue_config["coast"] == {}


def test_config_to_profile_missing_fields_resolved_via_cue_cfg():
    """Un cue_config parcial (solo enabled, sin priority) se completa al serializar."""
    partial = {"coast": {"enabled": True}}
    profile = cue_profiles.config_to_profile(partial, name="parcial")
    by_type = {cue["type"]: cue for cue in profile["cues"]}
    assert by_type["coast"]["enabled"] is True
    assert by_type["coast"]["priority"] == DEFAULT_CONFIG["coast"]["priority"]
    assert by_type["coast"]["solo_sin_frenada"] == DEFAULT_CONFIG["coast"]["solo_sin_frenada"]


def test_save_profile_writes_utf8_with_accents(tmp_path):
    """save_profile escribe UTF-8 (no escapado) con acentos legibles."""
    path = tmp_path / "acentuado.json"
    cue_profiles.save_profile(
        path, None, name="frenada útil", description="Ideal para pistas rápidas, sin gas a fondo."
    )
    raw = path.read_bytes()
    assert raw.decode("utf-8")  # no truena: es UTF-8 valido
    assert b"\xc3\xba" in raw  # 'ú' en UTF-8, no escapado como ú
    text = path.read_text(encoding="utf-8")
    assert "frenada útil" in text
    assert "rápidas" in text
    assert "\\u" not in text


def test_profiles_dir_creates_and_returns_path(tmp_path, monkeypatch):
    """profiles_dir() crea la carpeta-libreria si no existe y la devuelve."""
    monkeypatch.setattr(cue_profiles.Path, "home", classmethod(lambda cls: tmp_path))
    result = cue_profiles.profiles_dir()
    assert result == tmp_path / ".simghostinputs" / "cue-profiles"
    assert result.is_dir()


def test_list_profiles_returns_name_and_path(tmp_path, monkeypatch):
    """list_profiles() lista los perfiles guardados en profiles_dir() con nombre y ruta."""
    monkeypatch.setattr(cue_profiles.Path, "home", classmethod(lambda cls: tmp_path))
    lib = cue_profiles.profiles_dir()
    cue_profiles.save_profile(lib / "a.json", None, name="Pack A")
    cue_profiles.save_profile(lib / "b.json", None, name="Pack B")
    listed = cue_profiles.list_profiles()
    names = sorted(entry["name"] for entry in listed)
    assert names == ["Pack A", "Pack B"]
    for entry in listed:
        assert entry["path"].endswith(".json")


def test_list_profiles_survives_corrupt_file(tmp_path, monkeypatch):
    """Un archivo corrupto en profiles_dir() no rompe el listado completo."""
    monkeypatch.setattr(cue_profiles.Path, "home", classmethod(lambda cls: tmp_path))
    lib = cue_profiles.profiles_dir()
    cue_profiles.save_profile(lib / "bueno.json", None, name="Bueno")
    (lib / "corrupto.json").write_text("{esto no es json", encoding="utf-8")
    listed = cue_profiles.list_profiles()
    assert len(listed) == 2
    names = {entry["name"] for entry in listed}
    assert "Bueno" in names
    assert "corrupto" in names
