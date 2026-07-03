---
tipo: capacidad
clave: PAC-02
modulo: PAC
dominio: Coaching de voz
producto: Fantasma
estado: vigente
prioridad: Should Have
---

# PAC-02 - Plan anti-saturacion de senales

## Módulo
- [[PAC - Pace Notes CrewChief]]

## Propósito funcional
Limitar cuántas señales suenan por curva para que el piloto reaccione sin saturarse: máximo 3 eventos por curva, con una separación mínima entre señales y un countdown compacto en las frenadas prioritarias.

## Actor principal
Sistema (paso de planning dentro de `build_pack`, antes de escribir los WAVs).

## Entradas funcionales
- Filas del compare con `time_lost` y `flags` por curva.
- `corners` con los metros de cada hito.
- Parámetros: `top`, `min_gap_m` (separación mínima entre eventos), `max_events_per_corner` (default 3) y `countdown_m`.

## Salidas funcionales
- `plan.json` con, por curva, los eventos `selected` y los `skipped` con su razón (`too_close_in_corner`, `max_events_per_corner`).
- Preview de la mezcla de audio por distancia vía `fantasma compose --pace-notes-dir`.

## Reglas de negocio
- No se generan más de `max_events_per_corner` (3 por defecto) eventos por curva; los candidatos sobrantes se descartan con razón `max_events_per_corner`.
- Dos eventos de la misma curva no pueden quedar a menos de `min_gap_m` metros; el segundo se descarta con razón `too_close_in_corner`.
- Los candidatos se seleccionan por prioridad (frenada y ápex por encima de matices de salida) y luego se ordenan por distancia.
- En frenadas prioritarias, el punto de frenada se reemplaza por un countdown compacto anticipado (`brake_countdown`).

## Criterios de aceptación
- Dado dos hitos muy próximos en la misma curva, cuando se genera el plan, entonces la separación mínima entre eventos garantiza que no se superponen (el segundo queda como `skipped` con razón `too_close_in_corner`).
- Dado una curva con frenada, ápex y aceleración, cuando se planea, entonces se generan como máximo 3 eventos.
- Dado una frenada prioritaria, cuando se planea, entonces se emite un evento `brake_countdown` anticipado en lugar del tono simple de frenada.

## Dependencias funcionales
- [[PAC-01 - Generar pack de pace notes CrewChief]]

## Fuera de alcance
- La generación de los WAV y el `metadata.json` en sí (es [[PAC-01 - Generar pack de pace notes CrewChief]]).

## Verificación
- Cubierta por `tests/viz/test_pacenotes.py` (`test_plan_tone_events_limits_dense_corner`).

## Relacionado con
- [[Coaching de voz]]
