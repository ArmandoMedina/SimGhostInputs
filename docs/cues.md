# Sistema de cues

Mapa de un vistazo del sistema de cues (pace notes) de SimGhostInputs: qué cue existe,
con qué prioridad, cuál suena y cuál es mudo, qué está protegido, cómo funciona el
countdown de frenada y qué separa el modo estudio del modo en vivo.

Este documento es el **QUÉ**. El **porqué** de cada decisión vive en los ADR 0024–0028,
0030 y 0031, y no se duplica aquí: se enlaza. La fuente de verdad del catálogo y sus
valores por defecto es `DEFAULT_CONFIG` en
[`fantasma/viz/pacenotes.py`](../fantasma/viz/pacenotes.py); si un número de esta página
discrepa del código, manda el código.

> **Alcance.** Aquí se describe el catálogo de cues **sonoros/subtitulados** que arma el
> pack de CrewChief y la cinta de estudio. La detección de los hitos que anclan cada cue
> (frenada, turn-in, coast, ápex, cambio de marcha) es de `fantasma/core/corners.py` y su
> SSOT es [`docs/formato-datos.md`](formato-datos.md).

---

## Catálogo

Valores tomados de `DEFAULT_CONFIG` (`fantasma/viz/pacenotes.py`). «Prioridad» es el número
que usa la regla de cabida cuando dos cues compiten por el mismo tramo; «Suena» distingue el
cue que sintetiza WAV del que solo se subtitula; «Por defecto» indica si el cue está
habilitado de fábrica (los apagados existen en el catálogo y el usuario los prende en el
Paso 5, [ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md)).

| Cue (etiqueta) | Clave | Prioridad | Suena | Por defecto | Protegido | Notas |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Punto de frenada | `brake` | 100 | Sí | Habilitado | **Sí (R1)** | La señal de coaching. Nunca cede su hueco; ningún gap lo descarta ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md)). **Una curva puede emitir más de uno:** si tiene ≥2 frenadas fuertes reales (`milestones.brake_starts`), suena un `brake` protegido por cada una — protegido contra protegido, se quedan todas ([ADR 0033](decisions/0033-frenadas-multiples-por-curva.md)) |
| Contador de frenada | `brake_countdown` → `brake_tic` | 50 | Sí | Habilitado | No | 2 tics de aviso antes de **cada** frenada de la curva. **Oportunista por frenada:** cada countdown entra solo si cabe (puede ceder con `tic_sin_espacio` si choca con el de la frenada anterior de la misma curva); su prioridad es metadata, no pelea por cabida (ver [Countdown](#countdown-de-frenada)) |
| Inicio de acelerador | `throttle_on` | 95 | Sí | Habilitado | No | Ancla en la aceleración **sostenida**, no en el primer roce de pedal ([ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md)) |
| Gas completo | `full_throttle` | 90 | Sí | Habilitado | No | |
| Turn-in | `turn_in` | 70 | Sí | Habilitado | No | Solo se emite si en esa curva se pierde ≥ 0.25 s (gate propio en `_corner_candidates`) |
| Soltar freno | `brake_release` | 45 | Sí | Habilitado | No | |
| Apex | `apex` | 90 | Sí | **Apagado** | No | El **tono** está apagado por defecto (no-regresión); el **milestone** apex sigue vivo en datos, voz y matching ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md) lo retiró como sonido, [ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md) lo reincorporó apagado) |
| Inercia (coast) | `coast` | 20 | Sí | **Apagado** | No | `solo_sin_frenada`: se reserva para curvas **sin** freno, donde es la única pista de «ni freno ni gas». Un solo cue en `coast_start` |
| Cambio de marcha | `gear` | 75 | **No (mudo)** | **Apagado** | No | Único cue `sound=False`: solo subtítulo, sin WAV. **Por diseño no debe sonar nunca en el pack exportable** (ver [Frontera estudio / en vivo](#frontera-estudio--en-vivo) y [ADR 0030](decisions/0030-modos-estudio-en-vivo-que-ancla-cada-cue.md)) |

Notas de lectura del catálogo:

- **Solo `gear` es mudo.** `apex` y `coast` tienen `sound=True`: no se oyen por estar
  **apagados** (`enabled=False`), no por ser mudos. Prenderlos en un perfil los hace sonar.
- **`throttle_on` (95) pesa más que `full_throttle` (90).** El cue de mayor prioridad tras
  la frenada es el inicio de acelerador, no el gas a fondo.
- **La prioridad del `brake_countdown` (50) es baja a propósito.** El countdown no compite
  por cabida como los demás; su prioridad es metadata. Ver la sección siguiente.
- El pack de **voz** (`build_voice_pack`) es un carril aparte: una narración por curva top-N,
  anclada a la frenada, que pasa por el mismo gap global pero **no** se marca como protegida
  ([ADR 0024](decisions/0024-sincronia-pace-notes.md), enmienda «notas de voz»).

---

## Prioridades y anti-saturación

El problema que resuelven las prioridades es la **sopa de tonos**: en curvas encadenadas,
cues de curvas vecinas caían a menos de un segundo entre sí. La regla base es un **gap
mínimo global** de 50 m (`DEFAULT_MIN_GAP_M`): cuando dos cues quedan más cerca, uno cede.

Quién cede lo decide, en orden:

1. **Protección (R1).** El `brake` es el único cue **protegido**. Protegido contra
   no-protegido: cae el no-protegido. Protegido contra protegido: **se quedan los dos** (dos
   frenadas reales pegadas suenan ambas — incluidas dos frenadas de la **misma** curva cuando
   trae `milestones.brake_starts`, [ADR 0033](decisions/0033-frenadas-multiples-por-curva.md)).
   Ningún ranking ni configuración puede sacar la frenada del pool sonoro — es la señal que
   evita que el piloto se pase y se mate.
2. **Prioridad.** Entre no-protegidos gana el de mayor `priority`; en empate sobrevive el
   primero por distancia.

Detalles que conviene tener presentes:

- **Cues mudos y sonoros resuelven cabida por separado.** Un cue sin WAV (`gear`) no debe
  desplazar a un cue que sí suena solo por estar cerca: el gap se resuelve en dos grupos
  independientes (sonoros vs. mudos) y se recombinan ([ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md),
  enmienda del mismo día).
- **La prioridad es del usuario.** Sale de `cue_config`, no de literales en el motor: subir
  la prioridad de un cue cambia quién gana la colisión — salvo la frenada, que sigue
  protegida pase lo que pase ([ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md)).
- Cada descarte queda registrado con su razón en `plan.json` (`too_close_global`,
  `max_events_per_corner`, `antes_de_la_meta`, `tic_sin_espacio`, `cedio_al_countdown`):
  ese archivo es la auditoría de qué suena y qué no.

---

## Countdown de frenada

El contador es un **refuerzo de anticipación** de la frenada. La regla que lo gobierna es
**«el 3 es el ya»**: no es «1, 2, 3, ya», sino **tic — tic — FRENADA**. El tercer sonido no
es un tic propio: es el tono de frenada, exacto en el punto de frenada de la referencia
([ADR 0025](decisions/0025-countdown-ancla-en-la-frenada.md)).

Mecánica actual:

- El evento se **ancla en la frenada** (`brake_d`) y lleva su anticipo como dato (`lead_m`).
  `build_tone_pack` lo expande en 2 tics de aviso, en `brake_d − lead_m` y `brake_d − lead_m/2`.
  **Si la curva trae varias frenadas fuertes reales** (`milestones.brake_starts`,
  [ADR 0033](decisions/0033-frenadas-multiples-por-curva.md)), cada una arma **su propio**
  evento de countdown, anclado a su propia `brake_d`.
- Los tics son **oportunistas por cabida**, con la regla **«solo cede lo que puede ceder»**: un
  tic se coloca salvo que su hueco (< 50 m) lo ocupe un sonido **no cedible** —una **frenada
  protegida** o un **tic del countdown de OTRA curva** (u **otra frenada de la misma curva**)—,
  en cuyo caso es el tic el que cae (razón `tic_sin_espacio`). Un cue **no protegido** de otra
  curva (`turn_in`, `throttle_on`, `full_throttle`, `brake_release`, `coast`) **no bloquea**:
  **cede su hueco** y el tic se coloca. En curvas muy densas, con dos frenadas ajenas pegadas
  (de otra curva o de la misma), el tic no cabe y esa frenada queda sonando **sin** su
  countdown — nunca se pierde la frenada en sí
  ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md),
  [ADR 0032](decisions/0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md),
  [ADR 0033](decisions/0033-frenadas-multiples-por-curva.md)).
- **Invariante de seguridad: un tic nunca desplaza una frenada.** La frenada protegida es, por
  construcción, uno de los dos sonidos no cedibles que bloquean al tic; si chocan, cede el tic,
  nunca la frenada ([ADR 0032](decisions/0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md)).
- El ritmo es un **gap uniforme** de 0.75 s entre sonidos (`DEFAULT_COUNTDOWN_GAP_S`), no una
  fracción de un anticipo total: `lead_m = v/3.6 · gap · 2`, acotado a [30, 250] m
  ([ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)).
- Todo silencio deja rastro en `plan.json`: un tic descartado (`d ≤ 0` o sin espacio no cedible)
  y también el **cue no protegido que cede su hueco** (razón `cedio_al_countdown`, con el tic
  contra el que chocó). **La frenada nunca se pierde**, aunque el countdown esté apagado o no
  quepan sus tics.

### `brake_start`: dónde está exactamente el «ya»

Los ADR 0025/0026/0028 anclan el countdown al «metro exacto de la frenada» pero tratan ese
metro como dato dado. Qué muestra es cuando la curva tiene varias fases de freno lo define
[ADR 0031](decisions/0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md):

- `brake_start` = **inicio de la fase que lleva al máximo freno**, no la última pisada fuerte
  ni el arrastre de trail-braking. Los puntos con freno se agrupan en fases; entre las que
  superan el piso de intensidad, `brake_start` ancla en la **primera muestra de la fase de
  pico máximo**.
- La ventana de detección se deriva de los **hitos**, no de un campo publicado: cada curva es
  dueña de la fase de frenada posterior al ápex de su vecina previa. Por eso `brake_start`
  puede caer fuera del `segment_m` que la curva declara — `segment_m` es banda de vecindad,
  no contrato de contención.
- `brake_start` (el escalar de esta sección) **no cambia** cuando la curva tiene varias
  frenadas fuertes reales: sigue siendo la métrica comparable de coaching. Qué frenadas
  **suenan** es una pregunta aparte que responde `milestones.brake_starts`
  ([ADR 0033](decisions/0033-frenadas-multiples-por-curva.md), esquema en
  [`docs/formato-datos.md`](formato-datos.md)) — de ahí que el catálogo de arriba diga que
  `brake` puede emitirse más de una vez por curva.

---

## Frontera estudio / en vivo

Hay **dos modalidades** de uso, y no todo cue cabe en ambas
([ADR 0030](decisions/0030-modos-estudio-en-vivo-que-ancla-cada-cue.md)):

- **Modo estudio (la cinta / el video).** Todos los cues salen de la vuelta de
  **referencia**. El piloto memoriza los sonidos y sus puntos, y al llegar a pista con
  CrewChief le resultan familiares. Es el modo de este repositorio.
- **Modo en vivo.** Un asistente en tiempo real que reacciona al piloto. Vive en
  `fantasma-live` (UDP), **fuera de este repositorio**
  ([ADR 0002](decisions/0002-crewchief-pacenotes.md)).

La taxonomía que decide qué puede viajar en un pack de CrewChief:

- **Cues de POSICIÓN** — frenada, countdown, turn-in, soltar freno, gas, gas a fondo, ápex,
  coast. Se anclan a la **distancia de la referencia**. Un pace note de CrewChief se dispara
  por `distanceRoundTrack` (metro de pista), así que estos cues **caben** y viajan en el pack.
- **Cues de ESTADO DEL COCHE** — el cambio de marcha, y cualquiera futuro por RPM,
  temperatura o combustible. Su disparo correcto depende de cómo llega el piloto en ese
  instante, no de un metro. El formato de CrewChief **no tiene forma de expresar un disparo
  por estado del motor**, así que **no pueden viajar en el pack**.

Corolario operativo: en modo estudio el `gear` es legítimo como **subtítulo** del video (por
eso `sound=False`), pero **nunca debe ganar un WAV en el exportable**. Un `gear` sonoro se
dispararía por distancia sobre la vuelta real del piloto, en el metro donde cambió la
*referencia* — con las revoluciones equivocadas, empeora el error en vez de corregirlo. El
cambio de marcha sonoro es una feature de `fantasma-live`.

---

## Pendiente de decisión del PO

Queda **un** aspecto del sistema medido y cableado pero sin decisión final del PO: el **perfil
de sonido por defecto** (§2). La **regla de cabida del countdown** (§1) ya se decidió e
implementó esta sesión y solo espera la validación auditiva del PO; se deja aquí como cerrada
en lo técnico pero **revisable** de oído.

### 1. Regla de cabida del countdown — decidida (revisable), implementada, pendiente de validación auditiva del PO

**«Solo cede lo que puede ceder».** Un cue **no protegido** (turn-in, gas, gas a fondo, soltar
freno, coast) **cede su hueco al tic del countdown**: entra el tic y el cue no protegido se
desplaza. Solo cuentan como «espacio ocupado» las **frenadas protegidas** y los **tics de otras
curvas**. El cue desplazado se registra en `plan.json` con la razón `cedio_al_countdown` y el
tic contra el que chocó (sin descartes silenciosos). **Invariante de seguridad:** un tic
**nunca** desplaza una frenada — la frenada protegida es, por construcción, uno de los dos
bloqueadores no-cedibles del tic.

- **Estado:** **decidida por el orquestador bajo delegación explícita del PO, revisable** —
  implementada en `plan_tone_events` (commit `3d14d41`) y documentada como el PORQUÉ en el
  [ADR 0032](decisions/0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md).
  **Pendiente solo del veto de oído del PO** sobre el «precio» (silenciar ~8 avisos de
  `full_throttle` de salida por vuelta): se le entregó un **A/B de audio** para juzgarlo. No es
  cerrada-inmutable: si de oído no convence, se afina o revierte sin tocar la invariante.
- **Evidencia medida** sobre la vuelta real (BMW M4 GT3, Nordschleife): el countdown completo
  (3-2-freno) pasa de **24 → 35** curvas, **11 recuperadas** (C12, C14, C17, C18, C20, C23,
  C33, C38, C41, C43, C50), con **0 frenadas protegidas perdidas ni movidas** (35 == 35, mismo
  metro, misma energía). El precio son 11 cues no protegidos de la curva anterior desplazados,
  cada uno con su rastro. Corridas: `qa_runs/charbel-20260709-cabida/` (medición de cabida) y
  `qa_runs/mariana-20260709-countdown/` (A/B auditivo E2E). Detalle y trade-offs en el
  [ADR 0032](decisions/0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md).

### 2. Perfil de sonido por defecto

Hoy los cues solo cambian de **frecuencia** (seno puro). Existe la opción `--sound-profile`
(y su equivalente en la UI) con cuatro paletas de síntesis:

- `seno` — comportamiento actual: seno puro, solo cambia la frecuencia.
- `timbre` — una forma de onda por familia (freno cuadrada, tics seno, gas triangular…).
- `ritmo` — mismo seno separado por duración/patrón (freno más largo, gas doble-blip…).
- `chirp` — barridos (el freno baja de frecuencia, el gas sube).

El default de fábrica es **`seno`** (`DEFAULT_SOUND_PROFILE`), pero es **provisional**: el PO
elige la paleta definitiva **de oído**, con los videos comparativos de `qa_runs/`. Hasta esa
decisión, `seno` es solo el valor por defecto que no cambia el comportamiento previo, no la
paleta elegida.
