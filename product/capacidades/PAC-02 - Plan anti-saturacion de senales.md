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
- No se generan más de `max_events_per_corner` (3 por defecto) eventos **no protegidos** por curva; los candidatos sobrantes se descartan con razón `max_events_per_corner`. El tono de frenada (protegido) no cuenta contra este límite: entra siempre.
- Dos eventos no protegidos de la misma curva no pueden quedar a menos de `min_gap_m` metros; el segundo se descarta con razón `too_close_in_corner`.
- **Tono de frenada universal y protegido** ([ADR 0026](../../docs/decisions/0026-cues-frenada-universal-countdown-oportunista.md), enmienda al 0024): toda curva con milestone `brake_start` emite su tono de frenada en el metro exacto, marcado `protected`. Ningún gap lo descarta: en el gap global entre curvas encadenadas, protegido contra no-protegido cae el no-protegido; protegido contra protegido se quedan ambos (dos frenadas reales pegadas suenan las dos). Entre eventos no-protegidos sigue rigiendo la prioridad, y el perdedor se descarta con razón `too_close_global`.
- Los candidatos no protegidos se seleccionan por prioridad y luego se ordenan por distancia. Desde el [ADR 0027](../../docs/decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md) (enmienda al 0026), el catálogo de cues —qué tipos suenan y con qué prioridad: turn-in, inicio de acelerador, gas completo, ápex, coast— es **configurable por el usuario** en el Paso 5 ([[UI-04 - Generar pace notes desde la UI]]), con un `DEFAULT_CONFIG` que reproduce el comportamiento anterior sin regresión. El tono de **ápex** vuelve al catálogo como opción **apagada por defecto** (el 0026 lo había retirado por completo); el milestone siempre se conserva en los datos, en las notas de voz y en el matching de curvas, suene o no. El nuevo cue `coast` (inercia, apagado por defecto) se suma como candidato no protegido más, con la opción de limitarlo a curvas sin frenada.
- **Countdown oportunista, por cabida y no por severidad** ([ADR 0026](../../docs/decisions/0026-cues-frenada-universal-countdown-oportunista.md), enmienda al 0025): en cada frenada protegida con `lead_m`, se intentan 2 tics de aviso (`brake_tic`, `step` 0 y 1, en `brake_d - lead_m` y `brake_d - lead_m/2`). Cada tic entra solo si está a `≥ min_gap_m` de **todo** sonido ya en la línea de tiempo — frenadas, cues y tics ya insertados, **incluidos los tics de otras curvas** — recorridos en orden de distancia (greedy). `lead_m` sigue calculándose **por tiempo**: `countdown_s` segundos a la velocidad de llegada, acotado a [60, 350] m (ADR 0024); sin `v`, fallback fijo `countdown_m`. En curvas encadenadas o densas los tics pueden no caber y la curva queda solo con su tono de frenada — no hay gate de severidad (`time_lost`/`braking_issue`) que decida si el countdown aplica.
- Un evento cuyo anticipo caiga antes de la meta (`d ≤ 0`) se descarta con razón `antes_de_la_meta` — nunca se clampa a 0 (un cue en el segundo 0 del video suena aleatorio).
- **El pack de VOZ pasa por el mismo gap mínimo global que el de tonos** ([ADR 0024](../../docs/decisions/0024-sincronia-pace-notes.md), enmienda "notas de voz" 2026-07-09): `build_voice_pack` arma un candidato por curva top-N (anticipo derivado de la velocidad de llegada a la frenada, no metros fijos) y lo pasa por `_resolve_min_gap` — la misma función que resuelve el gap global de esta capacidad, extraída a nivel de módulo para compartirla sin duplicar la lógica. A diferencia del tono de frenada, el evento de voz **no es protegido**: una narración de ~7.5 s sí debe poder ceder su hueco ante una curva vecina cercana; en la colisión sobrevive la curva con más `time_lost`. El modo `"both"` (tonos + voz) todavía no cruza el gap entre ambos packs (deuda en `ROADMAP.md`).

## Criterios de aceptación
- Dado dos hitos no protegidos muy próximos en la misma curva, cuando se genera el plan, entonces la separación mínima entre eventos garantiza que no se superponen (el segundo queda como `skipped` con razón `too_close_in_corner`).
- Dado una curva con frenada, turn-in y aceleración, cuando se planea, entonces se generan como máximo 3 eventos no protegidos (el tono de frenada protegido se suma siempre, sin contar contra el límite).
- Dado una curva con milestone `brake_start`, cuando se planea, entonces se emite su tono de frenada protegido en el metro exacto, y ningún gap (ni con un vecino de mayor prioridad) lo descarta.
- Dado dos frenadas protegidas pegadas a menos de `min_gap_m`, cuando se planea, entonces **ambas** suenan.
- Dado dos curvas encadenadas con un evento protegido y uno no protegido a menos de `min_gap_m`, cuando se planea, entonces sobrevive el protegido y el no protegido queda en `skipped_global` con razón `too_close_global`.
- Dado un hito de frenada con velocidad `v`, cuando se planea el countdown, entonces el anticipo (`lead_m`) equivale a `countdown_s` segundos a esa velocidad (acotado a [60, 350] m); sin `v`, se usa el fallback fijo `countdown_m`.
- Dado un tic de countdown (`brake_tic`) que caiga a menos de `min_gap_m` de cualquier sonido ya en la línea de tiempo (tics de otras curvas incluidos) o en `d ≤ 0`, cuando se genera el pack, entonces ese tic se omite pero el tono de frenada nunca se pierde.
- Dado dos countdowns de curvas encadenadas, cuando se planea, entonces sus tics no se amontonan (cada uno respeta `min_gap_m` contra los tics ya colocados de la otra curva).
- Dado una curva pegada a la meta cuyo anticipo caiga en `d ≤ 0`, cuando se planea, entonces el evento se descarta con razón `antes_de_la_meta` y ningún evento del plan queda en `d ≤ 0`.
- Dado `top=0`, cuando se planea, entonces se incluyen todas las curvas detectadas (también donde no se pierde tiempo).
- Dado dos curvas con narración de voz a menos del gap mínimo global, cuando se genera el pack de voz, entonces solo una narra (la de mayor `time_lost`) y la otra queda descartada — no se generan dos narraciones que se encimen en el tiempo.

## Dependencias funcionales
- [[PAC-01 - Generar pack de pace notes CrewChief]]

## Fuera de alcance
- La generación de los WAV y el `metadata.json` en sí (es [[PAC-01 - Generar pack de pace notes CrewChief]]).

## Verificación
- Cubierta por `tests/viz/test_pacenotes.py` (`test_plan_tone_events_limits_dense_corner`, `test_frenada_protegida_sobrevive_vecino_de_mayor_prioridad`, `test_dos_frenadas_pegadas_ambas_suenan`, `test_dos_countdowns_encadenados_no_amontonan_tics`, `test_countdown_antes_de_la_meta_omite_tic_pero_conserva_la_frenada`, `test_countdown_anticipa_por_tiempo_con_v`, `test_countdown_lead_clamps_y_fallback`, `test_top_cero_incluye_curvas_sin_perdida`, `test_brake_y_countdown_frecuencias_distintas`, `test_plan_legacy_tiene_mismo_esquema`). Suite completa: 248 passed.
- Pack de voz: `test_build_voice_pack_gap_global_descarta_la_narracion_mas_cercana`, `test_build_voice_pack_curvas_lejanas_narran_ambas`, `test_build_voice_pack_anticipo_por_tiempo_con_v`, `test_build_voice_pack_sin_v_usa_fallback_fijo_200m`, `test_build_voice_pack_una_nota_por_curva`, `test_build_voice_pack_top_limita_curvas_igual_que_tone_pack` (`tests/viz/test_pacenotes.py`, ADR 0024 enmienda "notas de voz").
- E2E con datos reales: `qa_runs/charbel-20260705-pr2-e2e/` (55 curvas, 101 cues, anticipo mediano 3.60 s) — anterior al rediseño del ADR 0026; pendiente e2e con la cinta regenerada (ver HANDOFF).

## Relacionado con
- [[Coaching de voz]]
