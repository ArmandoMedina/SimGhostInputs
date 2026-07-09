---
tipo: guia
estado: vigente
---

# Perfiles de cues de ejemplo

Plantillas del formato `simghost-cue-profile` (`fantasma/viz/cue_profiles.py`) para
armar y compartir "packs de cues", mismo espiritu que los track packs de
`CONTRIBUTING.md` SS7. Son datos de ejemplo/documentacion, **no** se empaquetan
con la app ni el motor los lee directo de aqui — copialos a tu carpeta de
perfiles (`profiles_dir()`, por defecto `~/.simghostinputs/cue-profiles/`) o
cargalos con `load_profile(path)` desde la ruta que quieras.

| Archivo | Que trae |
| :-- | :-- |
| `default.json` | El pack de hoy: mismos tipos activos y prioridades que `DEFAULT_CONFIG` |
| `solo-frenada.json` | Solo el tono de frenada y su countdown de aviso; todo lo demas apagado |
| `coast-y-apex.json` | El default mas `coast` (inercia) y `apex` (V-Min) encendidos |

## Esquema

```json
{
  "schema": "simghost-cue-profile",
  "version": 1,
  "name": "nombre del pack",
  "description": "texto libre, opcional",
  "cues": [
    {"type": "brake", "enabled": true, "priority": 80}
  ]
}
```

`cues` es una lista de objetos `{type, enabled, priority, ...}` — un tipo por
entrada, con los campos extra que le correspondan (p. ej. `solo_sin_frenada`
en `coast`). Un tipo desconocido para la version instalada de
SimGhostInputs se ignora al cargar (con aviso), no rompe el resto del pack.
