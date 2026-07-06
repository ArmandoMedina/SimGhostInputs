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
- `corners` con los metros de cada hito (y la velocidad `v` en la frenada, si existe).
- Parámetros: `top` (0 = todas las curvas), `min_gap_m` (separación mínima entre eventos), `max_events_per_corner` (default 3), `countdown_s` (anticipo del countdown en segundos, default 3.5) y `countdown_m` (fallback fijo en metros si el hito no trae `v`).

## Salidas funcionales
- `plan.json` con, por curva, los eventos `selected` y los `skipped` con su razón (`too_close_in_corner`, `max_events_per_corner`, `antes_de_la_meta`), más la lista global `skipped_global` (razón `too_close_global`).
- Preview de la mezcla de audio por distancia vía `fantasma compose --pace-notes-dir`.

## Reglas de negocio
- No se generan más de `max_events_per_corner` (3 por defecto) eventos por curva; los candidatos sobrantes se descartan con razón `max_events_per_corner`.
- Dos eventos de la misma curva no pueden quedar a menos de `min_gap_m` metros; el segundo se descarta con razón `too_close_in_corner`.
- La separación mínima aplica también **entre curvas** (curvas encadenadas): en conflicto sobrevive el evento de mayor prioridad y el otro se descarta con razón `too_close_global` ([ADR 0024](../../docs/decisions/0024-sincronia-pace-notes.md)).
- Los candidatos se seleccionan por prioridad (frenada y ápex por encima de matices de salida) y luego se ordenan por distancia.
- En frenadas prioritarias, el evento `brake_countdown` se **ancla en la frenada** y lleva su anticipo como `lead_m` **por tiempo**: `countdown_s` segundos a la velocidad de llegada, acotado a [60, 350] m (ADR 0024). Al generar el pack se expande en 2 tics de aviso (a `lead_m` y `lead_m/2` antes) y el **tono de frenada exacto en el punto de frenada de la referencia** — "el 3 es el ya" ([ADR 0025](../../docs/decisions/0025-countdown-ancla-en-la-frenada.md)). Un tic que caiga en `d ≤ 0` o a < `min_gap_m` de otro cue se omite; el tono de frenada nunca se pierde.
- Un evento cuyo anticipo caiga antes de la meta (`d ≤ 0`) se descarta con razón `antes_de_la_meta` — nunca se clampa a 0 (un cue en el segundo 0 del video suena aleatorio).

## Criterios de aceptación
- Dado dos hitos muy próximos en la misma curva, cuando se genera el plan, entonces la separación mínima entre eventos garantiza que no se superponen (el segundo queda como `skipped` con razón `too_close_in_corner`).
- Dado una curva con frenada, ápex y aceleración, cuando se planea, entonces se generan como máximo 3 eventos.
- Dado una frenada prioritaria, cuando se planea, entonces se emite un evento `brake_countdown` anclado en la frenada con `lead_m`, y el pack lo expande en tics de aviso más el tono de frenada exacto en el punto de frenada.
- Dado dos curvas encadenadas con eventos a menos de `min_gap_m`, cuando se planea, entonces solo suena el de mayor prioridad y el otro queda en `skipped_global` con razón `too_close_global`.
- Dado un hito de frenada con velocidad `v`, cuando se planea el countdown, entonces el anticipo (`lead_m`) equivale a `countdown_s` segundos a esa velocidad (acotado a [60, 350] m); sin `v`, se usa el fallback fijo `countdown_m`.
- Dado un countdown cuyo tic de aviso caiga a menos de `min_gap_m` de otro cue (o en `d ≤ 0`), cuando se genera el pack, entonces ese tic se omite pero el tono de frenada del countdown se genera siempre.
- Dado una curva pegada a la meta cuyo anticipo caiga en `d ≤ 0`, cuando se planea, entonces el evento se descarta con razón `antes_de_la_meta` y ningún evento del plan queda en `d ≤ 0`.
- Dado `top=0`, cuando se planea, entonces se incluyen todas las curvas detectadas (también donde no se pierde tiempo).

## Dependencias funcionales
- [[PAC-01 - Generar pack de pace notes CrewChief]]

## Fuera de alcance
- La generación de los WAV y el `metadata.json` en sí (es [[PAC-01 - Generar pack de pace notes CrewChief]]).

## Verificación
- Cubierta por `tests/viz/test_pacenotes.py` (`test_plan_tone_events_limits_dense_corner`, `test_plan_gap_global_entre_curvas_gana_prioridad`, `test_countdown_anticipa_por_tiempo_con_v`, `test_plan_descarta_cue_antes_de_la_meta`, `test_top_cero_incluye_curvas_sin_perdida`, `test_pack_expande_countdown_y_el_tercer_bip_es_el_ya`, `test_pack_omite_tic_encimado_pero_nunca_el_ya`).
- E2E con datos reales: `qa_runs/charbel-20260705-pr2-e2e/` (55 curvas, 101 cues, anticipo mediano 3.60 s).

## Relacionado con
- [[Coaching de voz]]
