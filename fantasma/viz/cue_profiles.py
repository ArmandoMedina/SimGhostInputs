"""Formato de perfil de cues compartible: serializa/deserializa cue_config a JSON.

Vive aparte de pacenotes.py a proposito: este modulo no genera audio, solo lee
el catalogo (DEFAULT_CONFIG) y la funcion de resolucion (_cue_cfg) de ahi para
no duplicar la semantica de "campo ausente cae al default". Mismo espiritu que
los track packs de CONTRIBUTING.md SS7: los perfiles de cues son datos de la
comunidad, no del motor -- ver docs/cue-profiles-ejemplo/ para plantillas.
"""

import json
import sys
from pathlib import Path

from fantasma.viz.pacenotes import DEFAULT_CONFIG, _cue_cfg

SCHEMA_NAME = "simghost-cue-profile"
SCHEMA_VERSION = 1


def profiles_dir() -> Path:
    """Carpeta-libreria por defecto de los packs de cues del usuario (se crea si falta)."""
    path = Path.home() / ".simghostinputs" / "cue-profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_to_profile(cue_config=None, name="", description="") -> dict:
    """Arma el dict serializable de un perfil desde un cue_config.

    cue_config=None (o vacio) produce el perfil "default": cada tipo del
    catalogo (DEFAULT_CONFIG) se resuelve via _cue_cfg, asi el perfil siempre
    queda completo (enabled + priority + campos extra) aunque el cue_config de
    entrada sea parcial o None.
    """
    cue_config = cue_config or {}
    cues = [{"type": cue_type, **_cue_cfg(cue_config, cue_type)} for cue_type in DEFAULT_CONFIG]
    return {
        "schema": SCHEMA_NAME,
        "version": SCHEMA_VERSION,
        "name": name,
        "description": description,
        "cues": cues,
    }


def _coerce_priority(value, cue_type: str):
    """Fuerza priority a int; ValueError claro (no el TypeError/ValueError
    crudo de int()) si el valor no es coercible -- frontera robusta ante un
    pack de terceros con "priority": "alta"."""
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(
            'el perfil de cues no es valido: "priority" del cue "%s" debe ser un numero, '
            "se recibio %r" % (cue_type, value)
        ) from e


def profile_to_config(profile: dict) -> dict:
    """Convierte el dict de un perfil (ya cargado) de vuelta a cue_config.

    Degradacion con gracia: un `type` ausente de DEFAULT_CONFIG se ignora con
    un aviso por stderr, nunca un crash -- un pack armado con una version
    futura de esta app debe seguir cargando los cues que esta version conoce.
    Campos faltantes por cue quedan tal cual (build_pack los resuelve al
    default via _cue_cfg, misma semantica que un override parcial hoy).

    Frontera robusta: "cues" debe ser una lista de objetos con "type" (si no,
    ValueError claro, nunca AttributeError). priority se fuerza a int;
    enabled/solo_sin_frenada se fuerzan a bool -- un JSON de un tercero con
    tipos torcidos no debe reventar mas adelante en la UI o en build_pack.
    Un valor explicito None se trata como campo ausente (mismo criterio que
    _assemble_cue_config en ng_step5.py).
    """
    cues = profile.get("cues", [])
    if not isinstance(cues, list):
        raise ValueError(
            'el perfil de cues no es valido: "cues" debe ser una lista, se recibio %s'
            % type(cues).__name__
        )
    cue_config = {}
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError(
                'el perfil de cues no es valido: cada elemento de "cues" debe ser un '
                "objeto, se recibio %s" % type(cue).__name__
            )
        cue_type = cue.get("type")
        if not isinstance(cue_type, str) or not cue_type:
            raise ValueError('el perfil de cues no es valido: un cue no tiene "type"')
        if cue_type not in DEFAULT_CONFIG:
            print(
                'aviso: perfil de cues trae un tipo desconocido "%s", se ignora' % cue_type,
                file=sys.stderr,
            )
            continue
        entry = {}
        for key, value in cue.items():
            if key == "type" or value is None:
                continue
            if key == "priority":
                entry[key] = _coerce_priority(value, cue_type)
            elif key in ("enabled", "solo_sin_frenada"):
                entry[key] = bool(value)
            else:
                entry[key] = value
        cue_config[cue_type] = entry
    return cue_config


def _validate_profile_shape(profile, source: str) -> None:
    if not isinstance(profile, dict):
        raise ValueError(
            "%s no es un perfil de cues valido: se esperaba un objeto JSON, se "
            "recibio %s" % (source, type(profile).__name__)
        )
    schema = profile.get("schema")
    if schema != SCHEMA_NAME:
        raise ValueError(
            '%s no es un perfil de cues valido: falta o no coincide "schema" '
            '(se esperaba "%s", se recibio %r)' % (source, SCHEMA_NAME, schema)
        )
    version = profile.get("version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            "%s tiene version %r, no soportada por esta version de SimGhostInputs "
            "(solo se conoce la version %d). Actualiza la app o revisa el perfil."
            % (source, version, SCHEMA_VERSION)
        )


def load_profile(path) -> dict:
    """Lee y valida un perfil JSON, devuelve un cue_config listo para build_pack.

    Errores claros y accionables: JSON malformado, schema incorrecto o version
    desconocida lanzan ValueError con el motivo, nunca un traceback pelado.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError("no se pudo leer el perfil de cues %s: %s" % (path, e)) from e
    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError("el perfil de cues %s no es JSON valido: %s" % (path, e)) from e
    _validate_profile_shape(profile, str(path))
    return profile_to_config(profile)


def save_profile(path, cue_config, name, description="") -> Path:
    """Escribe el JSON de un perfil (UTF-8 sin BOM, indentado, acentos legibles)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = config_to_profile(cue_config, name=name, description=description)
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_profiles() -> list:
    """Perfiles disponibles en profiles_dir(): [{"name", "path"}, ...] para un dropdown.

    Un archivo que no se puede leer, parsear, o cuyo JSON valido no es un
    objeto (p. ej. una lista suelta) se lista igual (con el nombre de archivo
    como fallback y un aviso a stderr) en vez de romper el listado completo
    por un pack corrupto de un tercero. Nunca llama profile_to_config aqui:
    "cues" mal formado no afecta el listado, solo se valida al cargar.
    """
    results = []
    for file in sorted(profiles_dir().glob("*.json")):
        name = file.stem
        try:
            profile = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(
                'aviso: no se pudo leer el perfil de cues "%s": %s' % (file.name, e),
                file=sys.stderr,
            )
        else:
            if isinstance(profile, dict):
                name = profile.get("name") or file.stem
            else:
                print(
                    'aviso: el perfil de cues "%s" no es un objeto JSON valido, se usa '
                    "el nombre de archivo" % file.name,
                    file=sys.stderr,
                )
        results.append({"name": name, "path": str(file)})
    return results
