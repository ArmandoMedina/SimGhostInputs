---
tipo: capacidad
clave: COR-01
modulo: COR
dominio: Detección de curvas e hitos
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# COR-01 - Detectar curvas e hitos

## Módulo
- [[COR - Detección de curvas e hitos]]

## Propósito funcional
Detectar las curvas de una vuelta como mínimos locales de velocidad (V-Min) y extraer para cada una los hitos de conducción: ápex, inicio de frenada, punto de aplicación de gas y, si está disponible, el G-lat máximo.

## Actor principal
Sistema (ejecutado sobre la vuelta remuestreada, antes de la comparación por curva).

## Entradas funcionales
- Objeto `Lap` remuestreado con al menos el canal `speed`.
- Opcionalmente: `glat`, `brake`, `throttle`.

## Salidas funcionales
- `events`: lista de tuplas `(kind, dist)` donde `kind` es `"vmin"`.
- `corners`: lista de dicts por curva con `id`, `direction`, `milestones` (apex, brake_start y opcionalmente gas_start, g_lat_max).

## Reglas de negocio
- El canal `speed` es obligatorio; sin él se lanza `ValueError`.
- El canal `dist` es obligatorio; sin él se lanza `ValueError` con un aviso accionable (re-exportar incluyendo el canal de distancia). No se sintetiza desde la velocidad (ADR 0017).
- Se detecta un evento V-Min por cada mínimo local de velocidad significativo.
- La dirección de la curva (left / right) se toma del canal `glat` si está disponible.
- Sin canal `glat`, no se calcula `g_lat_max` en los hitos, pero las curvas V-Min siguen detectándose.

## Criterios de aceptación
- Dado una vuelta con N valles de velocidad conocidos, cuando se ejecuta `detect_corners`, entonces se identifican exactamente N curvas con evento de tipo `vmin`.
- Dado que la vuelta no tiene canal `speed`, cuando se ejecuta `detect_corners`, entonces se lanza `ValueError`.
- Dado que la vuelta no tiene canal `dist`, cuando se ejecuta `detect_corners`, entonces se lanza `ValueError` (no un `KeyError` desnudo).
- Dado una vuelta con valles de velocidad, cuando se extraen los hitos con `extract_milestones`, entonces cada curva incluye al menos `apex` y `brake_start` en sus milestones.
- Dado una vuelta sin canal `glat`, cuando se detectan las curvas, entonces se encuentran las curvas V-Min pero ninguna incluye el campo `g_lat_max` en sus hitos.

## Dependencias funcionales
- [[NRM-03 - Remuestrear por distancia]]

## Fuera de alcance
- Comparación de hitos entre piloto y referencia (es [[CMP-02 - Métricas y flags por curva]]).

## Verificación
- Cubierta por `tests/core/test_corners.py` (`test_detects_one_event_per_valley`, `test_detect_requires_speed_channel`, `test_detect_requires_dist_channel`, `test_milestones_have_apex_and_brake_start`, `test_corner_direction_matches_valley`, `test_detection_without_glat_still_finds_vmin_corners`).

## Relacionado con
- [[Detección de curvas e hitos]]
- [TEC-COR-01 — Detección de curvas e hitos](../../engineering/especificaciones/TEC-COR-01%20-%20Deteccion%20de%20curvas%20e%20hitos.md)
