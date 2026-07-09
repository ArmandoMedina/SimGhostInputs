# ADR 0030 — Modos estudio y en vivo: qué ancla cada cue (enmienda a ADR 0028)

- **Estado:** Aceptada
- **Fecha:** 2026-07-09

## Contexto

Los pace notes de SimGhostInputs se usan en **dos modalidades distintas**, y la diferencia
entre ambas es una regla de producto que el PO ha tenido que explicar varias veces en varias
sesiones sin que quede registrada donde se decide.

1. **Modo estudio (el video / la "cinta").** Es una banda sonora de coaching sobre el video de
   una vuelta. **TODOS los cues salen de la vuelta de REFERENCIA** — la rápida, la ideal. El
   objetivo es imaginería mental: el piloto ve el video, memoriza los sonidos y sus puntos, y
   cuando llega a pista con CrewChief los sonidos le resultan familiares y adopta los puntos de
   frenada correctos de la referencia. La regla de producto es explícita: *nunca generar cues
   desde la vuelta del piloto* (`ROADMAP.md:132`; el mismo principio, aplicado al cambio de
   marcha, en `ROADMAP.md:144`).

2. **Modo en vivo (asistente en tiempo real).** Un producto futuro y distinto que reacciona al
   piloto mientras conduce, no a la vuelta ideal grabada.

La regla tiene **una sola excepción**, y es el corazón de por qué la conversación se repite: el
**cambio de marcha**. El cue de marcha **no es un cue de posición, es un cue de estado del
motor**. En vivo, su disparo debe venir de las **RPM reales del piloto**, no de la distancia
donde cambió la referencia: si el piloto sale mal de una curva llega con menos revoluciones, y
cambiar donde cambió la referencia lo deja fuera del rango de potencia — el cue le **empeora** el
error en vez de corregirlo (`ROADMAP.md:145`).

Hasta hoy, esta regla estaba escrita **en un solo lugar y mal ubicado**: dentro de un ítem de
backlog marcado `[x]` (resuelto) en `ROADMAP.md:143-145`. No había ADR. No está en
`docs/guia-usuario.md`, ni en `product/`, ni en `docs/formato-datos.md` (que solo la cita de
paso, `docs/formato-datos.md:103`). Un ítem tachado del ROADMAP no lo lee nadie al decidir, y por
eso la distinción se pierde entre sesiones.

**El hallazgo nuevo que nadie había conectado** es lo que convierte esta regla de producto en una
restricción de arquitectura, no solo una preferencia:

> Un pace note de CrewChief **se dispara por `distanceRoundTrack`** — el metro de pista, y por nada
> más. Evidencia externa, de una auditoría del código fuente de CrewChief (no de este repo):
> `DriverTrainingService.cs::checkDistanceAndPlayIfNeeded` dispara cuando
> `previousDistanceRoundTrack < entry.distanceRoundTrack && currentDistanceRoundTrack > entry.distanceRoundTrack`
> — **solo distancia**: ni RPM, ni marcha, ni tiempo, ni velocidad. Y la propia entrada,
> `MetaDataEntry`, tiene **exactamente cuatro campos** (`description`, `distanceRoundTrack`,
> `recordingNames`, `fileNames`): no hay ningún campo por el que expresar "suena cuando el motor
> llegue a X RPM". CrewChief tampoco trae un beep de cambio de marcha por RPM propio. El formato,
> por construcción, **no tiene forma de expresar un disparo por estado del motor**.

Por lo tanto, un cue de cambio de marcha por revoluciones **no cabe, por construcción, en un pack
de CrewChief**. Ese cue exige un **listener en vivo** (UDP, en tiempo real) — precisamente
`fantasma-live`, el sistema que el [ADR 0002](0002-crewchief-pacenotes.md) dejó como un proyecto
**separado y fuera de este repositorio**: el pace note es post-sesión y no requiere listener UDP
ni conexión en tiempo real (`docs/decisions/0002-crewchief-pacenotes.md:151-157`).

## Decisión

Se fija una **taxonomía de cues por anclaje**, que decide de una vez qué puede y qué no puede
viajar en un pack de CrewChief:

- **Cues de POSICIÓN** — frenada, countdown de frenada, turn-in, soltar freno, gas, gas a fondo,
  ápex, coast. Se anclan a la **distancia de la vuelta de referencia**. Caben en el formato de
  CrewChief (`distanceRoundTrack`) y **viajan en el pack exportable**.

- **Cues de ESTADO DEL COCHE** — el cambio de marcha, y cualquiera futuro que dependa de RPM,
  temperaturas o combustible. Se anclan al **estado del piloto en vivo**, en tiempo real. **No
  pueden viajar en un pack de CrewChief**, porque el formato solo dispara por metro de pista, no
  por estado del motor.

Corolario operativo, que este ADR deja clavado: en **modo estudio** el cue `gear` es legítimo
únicamente como **subtítulo** del video (hoy `sound=False`, [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)),
y **nunca debe ganar un WAV en el pack exportable**.

## Razones

- **La regla de producto y la restricción de formato apuntan al mismo lado.** El PO ya había
  decidido, por criterio de coaching, que el cambio de marcha en vivo debe salir de las RPM del
  piloto y no de la referencia (`ROADMAP.md:145`). El hallazgo de arquitectura muestra que ni
  siquiera es una opción hacerlo dentro de un pack: la auditoría del código fuente de CrewChief
  (ver Contexto: `checkDistanceAndPlayIfNeeded` dispara solo por distancia y `MetaDataEntry` no
  tiene campo de RPM) confirma que el formato **no puede** disparar por estado del motor. Las dos
  razones —producto y construcción— coinciden, y por eso conviene registrarlas juntas para que
  ninguna sesión futura intente saltarse una ignorando la otra. **La tesis de este ADR queda
  CONFIRMADA por evidencia externa (el código de CrewChief), no por autorreferencia al propio
  repositorio.**
- **Anclar por "posición" vs. "estado del coche" es el eje que de verdad separa los cues**, no
  "cuál suena bien". Todos los cues de posición comparten que su disparo correcto es un metro de
  la referencia; el cambio de marcha (y sus futuros hermanos por RPM/temperatura/combustible) no,
  porque su disparo correcto depende de cómo llega el piloto en ese instante. Nombrar el eje evita
  volver a discutir cada cue nuevo desde cero.
- **El subtítulo mudo sí es correcto en estudio.** En la cinta el video ES la referencia, así que
  marcar dónde cambió de marcha la referencia es información válida de imaginería. Lo que no es
  válido es convertir ese subtítulo en un sonido que viaje al pack y se dispare por distancia en
  la vuelta real del piloto.

## El camino que NO se toma (y por qué tienta)

- **Darle un WAV a `gear` en el pack de CrewChief** — activar el "slot de sonido abierto" que el
  [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md) dejó reversible con
  una línea de config (`sound=False` → `sound=True`, `docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md:149`).
  Es la lectura más simple ("ya está el subtítulo, solo falta el sonido") y lo que tentaría a una
  sesión nueva. **Es activamente dañino, no solo prematuro.** Un cue de `gear` con `sound=True` se
  renderiza a WAV y entra al `metadata.json` con su `distanceRoundTrack` — es decir, se dispararía
  en la vuelta real del piloto **en el metro donde cambió la referencia**, que es exactamente el
  cue que empeora el error descrito en el contexto (`ROADMAP.md:145`): con las revoluciones
  equivocadas, ordenar el cambio donde lo hizo la referencia saca al piloto del rango de potencia.
  El "slot abierto" del ADR 0028 es, para `gear`, una **trampa**.
- **Tratar el cambio de marcha como un cue de posición más** (anclarlo a la distancia de la
  referencia, como el resto). Es lo que haría el motor si nadie marca la excepción, porque
  `detect_gear_shifts` ya recorre la referencia y devuelve distancias. Pero un cambio de marcha no
  es una posición de pista, es un estado del motor: anclarlo a la distancia es correcto solo para
  el subtítulo de estudio (donde el video ES la referencia) y erróneo para cualquier cosa sonora
  que se dispare sobre la vuelta del piloto.

## Consecuencias

- **`gear` se queda mudo en el exportable por diseño, no por falta de QA de oído.** Hoy sale con
  `sound=False`, se subtitula pero no sintetiza WAV y su entrada de `metadata.json` lleva
  `fileNames`/`recordingNames: []` (`docs/formato-datos.md:113`;
  `fantasma/viz/pacenotes.py:1070`, `:1080`). El ADR 0028 lo dejaba como "falta el audio, follow-up
  de menor riesgo"; este ADR aclara que, para el **pack exportable**, no es un follow-up
  pendiente: no debe tener audio nunca, porque el disparo por distancia sería dañino.
- **Riesgo conocido (SIN verificar al 100 %): una lista de audio vacía podría reventar CrewChief en
  pista.** La misma auditoría del código fuente detectó que `getRandomRecordingName()` indexa
  `recordingNames[Utilities.random.Next(recordingNames.Count)]`; con `Count == 0` eso lanzaría
  `ArgumentOutOfRangeException`, y nuestros cues mudos emiten precisamente `recordingNames: []`. El
  auditor **no pudo trazar** si la ruta de reproducción filtra las entradas sin audio antes de esa
  llamada, así que **no está confirmado** que el crash se alcance; solo se manifestaría en pista.
  Arreglo propuesto si se confirma: WAV silencioso en vez de lista vacía. Deuda con el detalle en
  `ROADMAP.md` (ítem "Nadie ha verificado que CrewChief acepte una entrada de `metadata.json` sin
  audio").
- **El cambio de marcha sonoro es una feature de `fantasma-live`, no de este repo.** Un cue de
  marcha que suene en el momento correcto exige leer las RPM del piloto en tiempo real, lo que
  requiere el listener UDP que vive fuera de este repositorio
  (`docs/decisions/0002-crewchief-pacenotes.md:151-157`).
- **Enmienda al [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md):** aquel
  ADR dejó el "slot de sonido" de `gear` abierto y reversible sin advertir el peligro
  (`docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md:149`). Este ADR
  cierra ese slot **para `gear`**: el mecanismo genérico `sound` sigue siendo válido para otros
  cues de posición que quieran separar "qué suena" de "qué se subtitula", pero para `gear` activar
  `sound=True` en el pack está proscrito por diseño. El resto del ADR 0028 (prioridades, countdown,
  frecuencias, `gear` acotado a subtítulo en estudio) sigue vigente sin cambio.
- **Referencia al [ADR 0002](0002-crewchief-pacenotes.md):** este ADR se apoya en el hecho, ya
  documentado allí, de que el pace note solo dispara por `distanceRoundTrack` y de que el coaching
  en tiempo real pertenece a `fantasma-live`, un proyecto separado.
- Pendiente de validar: nada nuevo de oído. La regla es de arquitectura y de producto, ya decidida
  por el PO; este ADR solo la coloca donde se decide.
