# ADR 0026 — Cues de frenada universales: tono de frenada protegido, countdown oportunista y fuera el tono de apex (enmienda a los ADR 0024 y 0025)

- **Estado:** Aceptada
- **Fecha:** 2026-07-06

## Contexto

Con el motor de los [ADR 0024](0024-sincronia-pace-notes.md) (gap global por prioridad) y
[ADR 0025](0025-countdown-ancla-en-la-frenada.md) (countdown anclado en la frenada) en
producción, el PO validó de oído y reportó dos defectos que compartían raíz:

1. **Frenadas mudas por competencia de gap.** "En el metro 819 no suena el sonido de
   frenada." El `brake` plano (prioridad 80) lo tiraba el **gap global** cuando un vecino
   de mayor prioridad caía a menos de `min_gap_m` (50 m): el tono de apex (prioridad 90) o
   un tic de countdown (100) le ganaba la posición y la curva quedaba sin su marca de
   frenada. El diseño del 0024 protegía al de mayor prioridad; pero la frenada es LA señal
   de coaching y estaba perdiendo contra refuerzos.

2. **Tres bips sin frenada cerca (bug 4463, ADR 0025).** El chequeo de solape del countdown
   miraba solo las posiciones finales de los cues, no los **tics entre sí**: dos countdowns
   encadenados amontonaban sus tics y sonaban "1-2-3" en una zona sin frenada real.

Además, el PO juzgó que el **tono de apex** no aporta ("quita los sonidos de apex, no
suman") y, de hecho, era uno de los vecinos de prioridad 90 que hacían perder frenadas por
gap.

## Decisión

Rediseño del modelo de cues que **enmienda el gating por severidad del 0024** y el
**countdown empaquetado del 0025**, con tres reglas:

1. **Tono de inicio de frenada UNIVERSAL y protegido.** Toda curva con milestone
   `brake_start` emite su tono de frenada en el metro exacto (`brake_d`), marcado
   `protected`. Ningún gap lo descarta: protegido contra no-protegido cae el no-protegido;
   **protegido contra protegido se quedan ambos** (dos frenadas reales pegadas suenan las
   dos). El gap global sigue rigiendo solo entre no-protegidos.

2. **Countdown OPORTUNISTA, por cabida y no por severidad.** Los 2 tics de aviso
   (`brake_tic`, `step` 0 y 1, en `brake_d - lead_m` y `brake_d - lead_m/2`) se colocan en
   **toda** curva donde quepan: cada tic entra solo si está a `≥ min_gap_m` de **todo**
   sonido ya en la línea de tiempo — frenadas, cues y tics ya insertados, **incluidos los
   tics de otras curvas**. Se recorren en orden de distancia (greedy) para resolver
   tic-contra-tic. En curvas encadenadas o densas no caben y la curva queda solo con su
   tono de frenada. Esto reemplaza el gate `time_lost >= 0.35 or braking_issue`. El 3er
   sonido ES la frenada (2 tics + tono en `brake_d`); no hay 4º "ya".

3. **Fuera el TONO de apex.** El `apex` se retira de `PLAN_CUES`: deja de sonar. El
   **milestone** apex se conserva intacto — sigue en los datos, en las notas de voz y en el
   matching de curvas; solo se retira como cue sonoro.

Implementado en `fantasma/viz/pacenotes.py`, commit `2f426ae`.

## Razones

- **El valor de coaching es que TODA frenada esté marcada.** Suprimir tonos de frenada por
  competencia de gap era el defecto de fondo del 0024: un refuerzo (apex, tic) no puede
  costar la marca del evento que refuerza. Proteger la frenada invierte la prioridad donde
  importa.
- **Un solo modelo cierra los dos bugs.** El 4463 nacía de que el solape del countdown no
  chequeaba los tics entre sí. Separar el **tono de frenada** (protegido, intocable por
  gap) de los **tics** (oportunistas, chequeados contra TODA la timeline) resuelve el 819 y
  el 4463 con una sola regla, sin gates de severidad que afinar.
- **Cabida, no importancia.** El countdown es refuerzo de anticipación: si hay espacio, se
  pone; si no, la frenada basta. Regla objetiva y determinista (testeable), sin umbral de
  `time_lost` que calibrar por pista.
- **El apex no suma de oído** (juicio del PO) y su tono era además el vecino de prioridad 90
  que más frenadas hacía perder; retirarlo destapa esas frenadas como efecto secundario.

## El camino que NO se toma (y por qué tienta)

- **Countdown por severidad (solo en las N peores curvas o sobre umbral de `time_lost`).**
  Es lo que sugería la lógica "fault-matched" que quedó pendiente en el 0024 y lo que
  tentaría a una sesión nueva ("marca solo donde se pierde tiempo"). El PO lo descartó
  explícitamente: "ninguna, será en todas las que lo permitan; si hay espacio se pone". La
  regla es de **cabida (espacio)**, no de importancia — así ninguna frenada se queda sin
  refuerzo por un ranking, y el modelo no depende de calibrar umbrales.
- **Mantener el tono de apex y solo subir la prioridad de la frenada.** Arreglaría el 819
  sin tocar el apex, pero deja sonando un cue que el PO juzgó ruido y conserva un vecino de
  prioridad 90 compitiendo por gap. Retirar el tono de apex es más simple y es lo pedido.
- **Chequear los tics solo contra las frenadas (no contra otros tics).** Es el defecto
  exacto del 0025 que produjo el 4463. Un tic debe respetar el gap contra **todo** lo que
  ya suena, tics ajenos incluidos.

## Consecuencias

- Se gana: **toda** frenada real suena en su metro exacto (regresión 819 cerrada); los tics
  encadenados ya no se amontonan (4463 cerrado); una sola regla —protegido vs oportunista—
  sin gates de severidad; la leyenda del Paso 5 se auto-actualiza al retirarse `apex` de
  `PLAN_CUES`.
- Se pierde: el tono de apex como cue sonoro (el milestone permanece); en curvas densas la
  curva queda solo con el tono de frenada (los tics no caben — esperado por diseño).
- Implementación (commit `2f426ae`): `_corner_candidates` emite siempre `brake` protegido
  con `lead_m` y sin apex; `plan_tone_events` protege la frenada en el gap global y añade la
  pasada de countdown oportunista que emite `brake_tic` (con `step` 0/1); `build_tone_pack`
  renderiza directo (se borró `_countdown_parts` y el muerto `generate_countdown`).
- Tests en `tests/viz/test_pacenotes.py` cubren la regresión 819 (frenada protegida
  sobrevive al gap), la 4463 (tics encadenados no se amontonan) y la ausencia de apex.
  Suite: 248 passed.
- Queda enmendado el **ADR 0024** (el gating global por prioridad ya no puede tirar una
  frenada; el gate de severidad del countdown desaparece) y el **ADR 0025** (el countdown
  deja de ser un evento único anclado y pasa a tics oportunistas `brake_tic`; el "el 3 es
  el ya" sigue vigente: el 3er sonido es la frenada). El cálculo de `lead_m` por tiempo
  (0024 punto 3, 0025) sigue en pie.
