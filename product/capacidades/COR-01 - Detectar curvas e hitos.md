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
- `corners`: lista de dicts por curva con `id`, `direction`, `milestones` (apex, brake_start y opcionalmente gas_start, g_lat_max, brake_starts).

## Reglas de negocio
- El canal `speed` es obligatorio; sin él se lanza `ValueError`.
- El canal `dist` es obligatorio; sin él se lanza `ValueError` con un aviso accionable (re-exportar incluyendo el canal de distancia). No se sintetiza desde la velocidad (ADR 0017).
- Se detecta un evento V-Min por cada mínimo local de velocidad significativo.
- La dirección de la curva (left / right) se toma del canal `glat` si está disponible.
- Sin canal `glat`, no se calcula `g_lat_max` en los hitos, pero las curvas V-Min siguen detectándose.
- `brake_start` ancla en la **primera muestra de la fase de frenada de pico máximo** anterior al ápex, no en la última pisada ni en un blip débil previo: cuando el piloto modula una sola frenada en dos pisadas fuertes seguidas, el cue debe sonar donde empieza a cargar el pedal hacia el máximo freno (el algoritmo de fases y el filtro `brake_strong` son SSOT de [`formato-datos.md`](../../docs/formato-datos.md#detección-de-curvas-resumen-del-algoritmo); la semántica la fija el [ADR 0031](../../docs/decisions/0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md)).
- Cada curva es dueña de toda fase de frenada posterior al ápex de su vecina previa; la frenada real puede empezar antes de `segment_m[0]` (p. ej. tras un kink rápido) sin que se trunque en el borde del segmento ([ADR 0031](../../docs/decisions/0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md), Opción A).
- Cuando la curva tiene **dos o más frenadas fuertes reales** (el piloto readministra gas de forma sostenida entre pisadas, no un simple roce de trail-braking), `milestones` incluye además `brake_starts`: la lista cronológica de todas ellas, para que el audio de pace notes anuncie cada una. `brake_start` (escalar) no cambia — sigue siendo la métrica de coaching/`compare` ([ADR 0033](../../docs/decisions/0033-frenadas-multiples-por-curva.md), enmienda al ADR 0031; esquema en [`formato-datos.md`](../../docs/formato-datos.md)).

## Criterios de aceptación
- Dado una vuelta con N valles de velocidad conocidos, cuando se ejecuta `detect_corners`, entonces se identifican exactamente N curvas con evento de tipo `vmin`.
- Dado que la vuelta no tiene canal `speed`, cuando se ejecuta `detect_corners`, entonces se lanza `ValueError`.
- Dado que la vuelta no tiene canal `dist`, cuando se ejecuta `detect_corners`, entonces se lanza `ValueError` (no un `KeyError` desnudo).
- Dado una vuelta con valles de velocidad, cuando se extraen los hitos con `extract_milestones`, entonces cada curva incluye al menos `apex` y `brake_start` en sus milestones.
- Dado una vuelta sin canal `glat`, cuando se detectan las curvas, entonces se encuentran las curvas V-Min pero ninguna incluye el campo `g_lat_max` en sus hitos.
- Dado una curva cuya frenada tiene dos pisadas fuertes seguidas (una modulación, no dos frenazos), cuando se extraen los hitos, entonces `brake_start` ancla en la primera muestra de la fase de mayor pico de freno, no en la segunda pisada.
- Dado una curva precedida por un kink sin frenada, cuando se extraen los hitos, entonces `brake_start` puede caer antes de `segment_m[0]` (la frenada no se trunca en el borde del segmento).
- Dado una curva con dos frenadas fuertes reales separadas por readministración sostenida de gas, cuando se extraen los hitos, entonces `milestones.brake_starts` trae las dos en orden cronológico y `brake_start` sigue apuntando a la de pico máximo, sin cambio.

## Dependencias funcionales
- [[NRM-03 - Remuestrear por distancia]]

## Fuera de alcance
- Comparación de hitos entre piloto y referencia (es [[CMP-02 - Métricas y flags por curva]]).

## Verificación
- Cubierta por `tests/core/test_corners.py` (`test_detects_one_event_per_valley`, `test_detect_requires_speed_channel`, `test_detect_requires_dist_channel`, `test_milestones_have_apex_and_brake_start`, `test_corner_direction_matches_valley`, `test_detection_without_glat_still_finds_vmin_corners`, `test_brake_starts_dos_frenadas_con_gas_en_hueco`, `test_brake_starts_ausente_si_suelta_sin_gas`, `test_brake_starts_ausente_en_trail_braking`, `test_brake_starts_no_parte_por_blip_de_gas`).

## Relacionado con
- [[Detección de curvas e hitos]]
- [TEC-COR-01 — Detección de curvas e hitos](../../engineering/especificaciones/TEC-COR-01%20-%20Deteccion%20de%20curvas%20e%20hitos.md)
