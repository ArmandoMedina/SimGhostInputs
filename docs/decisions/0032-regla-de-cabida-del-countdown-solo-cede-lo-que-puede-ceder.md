# ADR 0032 — Regla de cabida del countdown: solo cede lo que puede ceder (enmienda a ADR 0025, 0026 y 0028)

- **Estado:** Aceptada (tomada por el orquestador bajo delegación explícita del PO) · **revisable** — pendiente de A/B de audio del PO
- **Fecha:** 2026-07-09

## Contexto

El countdown de frenada es **oportunista por cabida y no por severidad**: sus 2 tics de aviso
(`brake_tic`, en `brake_d − lead_m` y `brake_d − lead_m/2`) entran solo si hay espacio, y la
frenada protegida basta cuando no lo hay ([ADR 0026](0026-cues-frenada-universal-countdown-oportunista.md),
[ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)). El defecto D2 de la
Fase 3 está en cómo se define ese "espacio".

La prueba de cabida en `fantasma/viz/pacenotes.py` (`plan_tone_events`, pasada de tics) mide cada
tic candidato contra la **timeline de sonidos** ya resueltos y lo descarta si cae a menos de
`min_gap_m` (50 m) de **cualquier** cue de esa timeline. "Cualquier cue" incluye un cue
**informativo de baja jerarquía de la curva ANTERIOR** — típicamente el `full_throttle` ("gas a
fondo" de salida, prioridad 90), pero también `throttle_on`, `turn_in` o `brake_release`.

El efecto es una **jerarquía invertida**: un tic del countdown de frenada se descarta porque un
cue menor de la curva previa ocupaba el hueco. Y ese tic no es adorno — el countdown existe para
que el piloto **no se pase y se mate**; el cue de frenada, y su anticipación, son la señal de
seguridad cuyo norte fijó el PO ("todos los sonidos salen de la referencia para que el piloto
adopte los puntos de frenada correctos", registrado en `ROADMAP.md` y el
[ADR 0030](0030-modos-estudio-en-vivo-que-ancla-cada-cue.md)). Que un aviso de "gas a fondo" de la
salida anterior silencie la anticipación de la siguiente frenada pone lo cosmético por encima de
lo vital.

**Magnitud medida** sobre la vuelta de referencia real (BMW M4 GT3, Nordschleife 2025, 20592 m,
55 curvas, 35 con frenada; `qa_runs/charbel-20260709-cabida/`, pipeline real de HOY reproducido:
`load_laps → fastest_lap → detect_corners → extract_milestones → compare → plan_tone_events`):

- Con la regla de hoy, **24** de las 35 curvas con frenada tienen el countdown completo
  (tic-tic-freno); 6 quedan con 2 sonidos y 5 con solo la frenada. Se pierden **16 tics**, y el
  estorbo que los mata es, en su enorme mayoría, el cue de salida de la curva previa: **12
  `full_throttle`, 2 `brake_release`, 1 `throttle_on`, 1 `turn_in`** — un cue prioridad ≤ 95,
  nunca protegido, tumbando la anticipación de una frenada prioridad 100.

## Decisión

**Regla de cabida "solo cede lo que puede ceder".** Para un tic del countdown, "espacio ocupado"
pasa a significar **únicamente**:

1. Una **frenada protegida** (`brake`, prioridad 100 — el "ya" de seguridad), de cualquier curva.
2. Un **tic de countdown de OTRA curva** (`brake_tic` ya aceptado en la timeline).

Un cue **no protegido** (`turn_in`, `throttle_on`, `full_throttle`, `brake_release`, `coast`) **ya
no cuenta como espacio ocupado**: **cede su hueco al tic**. Cuando un tic colisiona con un cue no
protegido dentro de `min_gap_m`, entra el tic y el cue no protegido **se desplaza** (sale del plan
sonoro). El cue desplazado **se registra en el rastro de descartes** (`plan.json`) con su razón y
el tic contra el que chocó — **no hay descartes silenciosos**, coherente con la trazabilidad de la
Fase 1 / D1 (cada silencio queda auditado en `plan.json`: `too_close_global`,
`max_events_per_corner`, `tic_sin_espacio`, y ahora el cue no protegido que cede).

**Invariante de seguridad (no negociable): un tic NUNCA desplaza una frenada protegida.** Es
estructural, no una comprobación añadida: el `brake` protegido es él mismo uno de los dos únicos
bloqueadores del tic (punto 1). Si un tic no cabe porque choca contra una frenada protegida, es el
**tic** el que cede, nunca la frenada. Dos frenadas protegidas pegadas siguen sonando ambas, como
ya fija el ADR 0026.

Esto es una regla de **especificación** (qué cede y qué no, y la invariante), no de líneas: la
implementación en `plan_tone_events` la escribe otro asiento en paralelo. La verdad de "quién cede"
la decide la **protección**, no la prioridad numérica: la prioridad 50 del `brake_countdown` sigue
siendo metadata, no un boleto para ganar cabida por severidad (ADR 0026).

## Razones

- **La frenada, y su anticipación, mandan sobre un aviso informativo de salida.** El cue de
  frenada es prioridad 100 y protegido porque es el que evita que el piloto se pase; su countdown
  es el andamio perceptivo de esa misma señal. Que un `full_throttle` (prioridad 90, no protegido)
  de la curva ANTERIOR lo silencie es exactamente la jerarquía al revés. La regla nueva la endereza:
  entre "no perder un aviso de gas de salida" y "no perder la anticipación de la próxima frenada",
  manda la frenada.
- **Cabida, no severidad — pero con el orden de cesión correcto.** El ADR 0026 ya fijó que el
  countdown se coloca por espacio, no por ranking. Lo que faltaba era decir **qué ocupa espacio de
  verdad**: solo lo que no puede ceder (la frenada protegida) y lo que compite en su misma liga (el
  tic de otra curva). Un cue informativo puede ceder, así que cede.
- **Sin descartes silenciosos.** El cue que cede no desaparece de la auditoría: queda en
  `plan.json` con razón y contraparte, igual que ya se hace con los tics que mueren. La regla no
  crea un agujero de trazabilidad; lo respeta.
- **La invariante de seguridad es estructural, no un `if` frágil.** Como la frenada protegida es
  uno de los bloqueadores del tic, ningún reordenamiento de prioridades ni perfil de terceros puede
  hacer que un tic tumbe una frenada. Esa garantía no depende del material ni de la calibración.
- **El precio es acotado, de un solo color y medible.** Sobre la vuelta real, la regla lleva el
  countdown de **24 → 35** curvas completas (recupera **11**: C12, C14, C17, C18, C20, C23, C33,
  C38, C41, C43, C50; desaparecen los buckets de 1 y 2 sonidos) con **cero frenadas protegidas
  perdidas**. El precio son **11 cues no protegidos de la curva anterior desplazados** (8
  `full_throttle`, 1 `throttle_on`, 1 `brake_release`, 1 `turn_in`), la mayoría a 4–20 m del tic
  (pérdida casi cosmética: cue y tic prácticamente coinciden); los dos más "reales" son C11
  `full_throttle` a 42 m y C32 `turn_in` a 47 m (`qa_runs/charbel-20260709-cabida/`,
  `tabla2_desplazados_b.csv`).

## El camino que NO se toma (y por qué tienta)

- **Dejar la regla de hoy ("cualquier cue cercano ocupa espacio").** Es lo que una sesión nueva
  leería como vigente en el ADR 0026 ("cada tic entra solo si está a ≥ `min_gap_m` de **todo**
  sonido ya en la timeline"). Tienta porque es simétrica y simple: todos ocupan igual, nadie
  privilegiado. Se descarta con dato: esa simetría es justo la que invierte la jerarquía —
  sacrifica 16 anticipaciones de frenada (prioridad 100) para preservar avisos de salida
  (prioridad ≤ 95) de la curva previa.
- **Subir la prioridad del `brake_countdown` para que gane la colisión por número.** Tienta porque
  parece "arreglarlo con un solo valor de config". Se descarta: el countdown es por **cabida**, no
  por **severidad** (ADR 0026); meterlo a competir por prioridad reabre el modelo de gates que ese
  ADR cerró, y además haría que el tic pudiera, con la config equivocada, empezar a pelear contra
  cosas que no debe. La protección —no la prioridad— es lo que decide quién cede.
- **Que el tic desplace también la frenada protegida si "hace falta espacio".** Nadie lo pediría
  en voz alta, pero es el desenlace natural de "el countdown es importante, que gane siempre". Se
  descarta de raíz: es exactamente la invariante de seguridad. La anticipación jamás vale más que
  el "ya"; si hay que sacrificar algo entre un tic y una frenada real pegada, se sacrifica el tic.
- **Implementar la cesión sin registrar el cue desplazado.** Más corto de escribir (un `continue`
  mudo que quita el cue y mete el tic). Se descarta: repite el pecado que la Fase 1 / D1 ya condenó
  — un `plan.json` que miente por omisión. Todo lo que se silencia deja rastro.

## Consecuencias

- **Se gana:** las 35 curvas con frenada quedan con el countdown completo de 3 sonidos
  (tic-tic-freno); la jerarquía queda derecha (la anticipación de la señal de seguridad manda sobre
  el aviso de salida de la curva previa); 11 curvas recuperadas, medido y reproducible.
- **Se pierde / cuesta:** ~11 cues no protegidos de la curva anterior se silencian (8
  `full_throttle`, 1 `throttle_on`, 1 `brake_release`, 1 `turn_in`), cada uno con su rastro en
  `plan.json`. Si esos avisos de salida importan al oído es **juicio del PO/Mariana**, no medible en
  conteo.
- **Invariante de seguridad intacta y estructural:** 0 frenadas protegidas perdidas, por
  construcción, no por el material medido.
- **Decisión tomada por el orquestador bajo delegación explícita del PO** ("avanza todo lo que
  puedas, no podré revisar esta sesión") y **revisable**: el "precio" —silenciar ~8 `full_throttle`
  de salida por vuelta— es un juicio de oído que el PO validará con un **A/B de audio** que se le
  entregará. Queda escrito como decisión revisable, no como dogma: si el A/B dice que esos avisos
  hacen falta, la regla se afina (p. ej. ceder solo cuando el gap es menor a un umbral, o solo
  ciertos cues) sin tocar la invariante de seguridad.
- **Alcance del dato:** el 24→35 y el precio de 11 se midieron sobre **un** par de material (una
  pista, un coche). Otra pista/coche daría otro reparto; lo estructural (0 frenadas perdidas) no
  depende del material. Medición con `top=0` (las 55 curvas); con `top=N` el universo cambia.
- **Enmienda a los [ADR 0025](0025-countdown-ancla-en-la-frenada.md),
  [ADR 0026](0026-cues-frenada-universal-countdown-oportunista.md) y
  [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md):** los tres construyen
  la cabida del countdown sobre "el tic cede ante cualquier sonido cercano" — el 0025 al omitir un
  tic "a menos de `min_gap_m` del ancla de otro cue", el 0026 al chequearlo contra **todo** sonido
  de la timeline, y el 0028 al resolver la timeline del `brake_tic` en el pool sonoro. Este ADR
  **redefine qué de esa timeline cuenta como espacio ocupado** (solo frenadas protegidas y tics
  ajenos) e invierte el sentido de la cesión (cede el cue no protegido, no el tic). Lo demás de esos
  ADR sigue vigente sin cambio: el anclaje del countdown en la frenada real, "el 3 es el ya", la
  frenada protegida universal, el gap uniforme de 0.75 s, el split sonoro/mudo y la separación
  cabida-vs-severidad.
- **`docs/cues.md` es el QUÉ** de este sistema (catálogo, prioridades, countdown) y enlaza a este
  ADR como el PORQUÉ; su sección "Pendiente de decisión del PO §1" describe esta misma regla en su
  estado pre-decisión y la reconciliará el asiento dueño de ese documento (Escribano) cuando el
  código aterrice y el PO cierre el A/B. La implementación vive en
  `fantasma/viz/pacenotes.py::plan_tone_events` (pasada de tics del countdown), a cargo de otro
  asiento.
- **Pendiente de validar:** el A/B de audio del PO sobre la cinta regenerada con la regla nueva
  (¿molesta perder ~8 `full_throttle` de salida a cambio de 11 countdowns completos?).
