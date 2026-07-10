# ADR 0033 — Frenadas múltiples por curva: cada frenada real suena (enmienda al ADR 0031)

- **Estado:** Aceptada
- **Fecha:** 2026-07-10

## Contexto

El [ADR 0031](0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md) fijó cómo se elige EL
punto de frenada de una curva: los bloques de `brake > brake_on` (10) se agrupan en **fases**,
el piso `brake_strong` (50) filtra las débiles, y entre las que sobreviven `brake_start` ancla en
la **primera muestra de la fase de pico máximo** (ante empate de pico, la más tardía). Ese
escalar es el metro comparable de coaching: lo consume `compare` para medir `d_brake_m` y lo lee
`viz/pacenotes.py` para generar el cue `brake` y su countdown. El esquema del hito
(`milestones.brake_start = {d,t,v,gear,brake_pct}`) es propiedad de
[`docs/formato-datos.md`](../formato-datos.md).

Midiendo la vuelta real de referencia (BMW M4 GT3 Nordschleife, 55 curvas) Charbel confirmó dos
frenadas encadenadas que el sistema NO anuncia — el piloto frena, **suelta el pedal a fondo,
vuelve a pisar gas y frena otra vez dentro de la misma curva** (evidencia en
[`qa_runs/charbel-20260710-frenos-encadenadas/`](../../qa_runs/charbel-20260710-frenos-encadenadas/LEEME.md)):

- **C05 (ancla en m1119):** dos frenadas reales — 100 % en m1042, el coche suelta y **vuelve a
  pisar gas hasta el 78 % sostenido ~27 m** (m1089-1116), y luego 90 % en m1117 (la que entra al
  `turn_in`=1123 y al ápex=1149). El agrupador de fases ya ve **dos fases distintas** (hueco de
  1.34 s ≥ `phase_gap_s`), pero la selección por pico máximo del 0031 se queda con la de m1042
  (100 % > 90 %) y la segunda **queda muda**.
- **C03 (ancla en m803):** 100 % en m721, el pedal **cae a 0** y el gas sube a ~26 % en el hueco,
  y vuelve a 100 % desde m801. Aquí el agrupador las **funde en una sola fase** (hueco ≈0.46 s <
  `phase_gap_s`=0.5 s, con la velocidad todavía cayendo) → un solo aviso. Bajo la lógica de fusión
  por velocidad monótona de `select_brake_phase`, Charbel dio a este metro veredicto "no-bug"; el
  criterio de producto de este ADR (pedal soltado a fondo + readministración real de gas) lo
  reclasifica como **dos frenadas reales** que deben sonar ambas.

El norte del PO (registrado ya en el 0031 y en [`docs/cues.md`](../cues.md)): el cue de frenada es
**el que evita que el piloto se pase y se mate**; cada frenada real que mete el coche a la curva
debe sonar. Pero con una restricción simétrica: **no debe pitar en trail-braking** (arrastre de
freno modulado donde el pedal nunca se suelta del todo) — eso es una sola maniobra, no dos avisos.

El 0031 resolvía con **un solo algoritmo** dos preguntas que en realidad son distintas: "¿cuál es
el punto de frenada comparable?" (métrica de coaching) y "¿qué frenadas deben sonar?" (audio del
piloto). Mientras cada curva tuvo una sola frenada fuerte, la respuesta coincidía y la distinción
no importaba. Las frenadas encadenadas la vuelven visible.

## Decisión

Se **separan las dos preguntas** que el 0031 respondía con un solo reductor. La regla de selección
del 0031 no cambia; se le añade, al lado, un reductor nuevo para el audio.

1. **Una curva puede emitir más de un aviso de frenada.** Suena un cue `brake` por cada **frenada
   fuerte real**: pico ≥ `BRAKE_STRONG` (50) separada de la anterior por una **readministración
   real de gas** en el hueco — el pedal de freno cae por debajo de `BRAKE_ON` (10) **y** el
   `throttle` supera `THROTTLE_REAPPLY` (valor inicial **15 %**). El trail-braking modulado no
   cuenta: si el pedal nunca baja de `BRAKE_ON`, es un solo bloque y **la fusión ni se evalúa**, así
   que el arrastre continuo jamás se parte en dos avisos.

2. **"¿Cuál es EL punto de frenada comparable?" — no cambia.** Sigue siendo
   `select_brake_phase` → `chosen` → el escalar `milestones.brake_start`. La regla del 0031 (fase
   de pico máximo, desempate a la más tardía) y la **simetría de `compare`** (`d_brake_m == 0`
   cuando piloto y referencia son la misma vuelta) quedan **intactas**.

3. **"¿Qué frenadas deben SONAR?" — función nueva.** `detect_brakings` en
   `fantasma/core/corners.py` recorre la misma ventana de frenada y devuelve la **lista cronológica
   de toda frenada fuerte** según el criterio del punto 1. Alimenta un campo NUEVO,
   `milestones.brake_starts` (lista, misma forma `{d,t,v,gear,brake_pct}` que `brake_start`),
   presente **solo cuando hay ≥2 frenadas fuertes**. El esquema de este campo es propiedad de
   [`docs/formato-datos.md`](../formato-datos.md); su único consumidor es `fantasma/viz/pacenotes.py`.

4. **Dos campos, dos responsabilidades — respuesta explícita a "¿qué campo uso?":**
   - `brake_start` (**escalar**) = frenada de pico máximo. Para coaching, `compare` y todo
     consumidor previo. **No se rompe nada.**
   - `brake_starts` (**lista**) = todas las frenadas que suenan. Solo audio de pacenotes.

5. **Cada frenada de la lista lleva su propio countdown** (3-2-freno) en pacenotes. `brake_release`
   sigue siendo **singular**, anclado al final de la última fase cronológica (como en el 0031). En
   el audio, cada cue `brake` es **protegido**; la regla de cabida ya soporta protegido-vs-protegido
   ("se quedan los dos", [`docs/cues.md`](../cues.md) §Prioridades;
   [ADR 0032](0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md)), así que dos
   frenadas pegadas suenan ambas sin que una desplace a la otra.

## Razones

- **El criterio es del PO, traducido a algoritmo.** Dos pisadas de freno reales, con el coche
  re-acelerando de por medio, son dos avisos: el piloto vuelve a cargar peso sobre el eje delantero
  dos veces y necesita saberlo las dos. El disparador de la separación es el **gas readministrado**
  (`throttle ≥ THROTTLE_REAPPLY`), no un simple hueco de tiempo, precisamente para distinguir "volví
  a acelerar y frené otra vez" de "solté un instante para rotar" (trail-braking).
- **Separar las dos preguntas, y no torcer una para servir a la otra.** El escalar comparable y el
  audio tienen dueños y contratos distintos. `compare` exige un `brake_start` **simétrico y único**
  (un piloto contra una referencia da un solo `d_brake_m`); el audio exige **todas** las frenadas.
  Un solo reductor no puede honrar ambas sin romper una. Poner la lógica nueva en `detect_brakings`
  deja el escalar del 0031 exactamente donde estaba.
- **El campo escalar sigue siendo la fuente para los consumidores viejos**, y la lista es aditiva y
  opcional (solo aparece con ≥2 frenadas). El reparo del 0031 contra publicar un segundo campo
  redundante (Opción C, "¿qué campo uso?") no aplica aquí: `brake_starts` no duplica `brake_start`,
  responde una pregunta **distinta** (qué suena vs. qué se compara) y su consumo está acotado a un
  solo módulo.
- **La protección protegido-vs-protegido ya existía** en la regla de cabida del 0026/0032; este ADR
  solo la ejercita con más de una frenada por curva. No hay lógica de audio nueva que inventar para
  que las dos quepan.

## El camino que NO se toma (y por qué tienta)

- **Partir m803 (y las encadenadas) dentro de `select_brake_phase`.** Tienta porque sería **un solo
  algoritmo**: si la selección ya distingue fases, que devuelva varias y listo, sin campo nuevo. Se
  rechaza con dato. Las dos fases de C03 quedan **empatadas a 100 %**, y la regla de desempate del
  0031 ("ante empate de pico, gana la más tardía") movería el `brake_start` **primario** de m721 a
  m806 — ~80 m tarde, justo el fallo que el 0031 introdujo para evitar y que el PO describió como
  "matar al piloto". Además obligaría a **voltear la regla del 0031**, rompería el test
  `test_brake_start_desempate_de_picos_iguales_gana_la_fase_mas_tardia` y desplazaría `d_brake_m` en
  varias curvas reales de la vuelta. Mantener `select_brake_phase` intacto y poner la separación en
  `detect_brakings`/`brake_starts` da **el mismo resultado audible sin ese radio de daño**.
- **Separar por hueco de tiempo puro** (dos fases distintas ⇒ dos avisos), sin exigir gas
  readministrado. Tienta por simple y por reusar el agrupador de fases. Se rechaza: haría pitar el
  trail-braking modulado —una suelta breve del pedal para rotar, con el coche aún frenando— como si
  fueran dos frenadas, saturando de avisos las curvas técnicas. El gas por encima de
  `THROTTLE_REAPPLY` es lo que separa "volví a acelerar" de "solté para rotar".
- **Cambiar el desempate del 0031 a "la última fuerte".** Es el arreglo "mínimo" que sugería la
  primera lectura del diagnóstico de C05. Se rechaza por la misma razón que el 0031 ya lo rechazó:
  rompe C05 al revés (movería su `brake_start` primario de m1042 a m1117) y contradice el criterio
  de "empezar a cargar el pedal hacia el máximo". La segunda frenada debe **sumarse** al audio, no
  **sustituir** al escalar comparable.

## Consecuencias

- **Conviven dos reductores sobre la misma ventana de frenada:** `select_brake_phase` (para el
  escalar comparable `brake_start`) y `detect_brakings` (para la lista audible `brake_starts`). Es
  el precio explícito de **no tocar `compare` ni la regla del 0031**. Ambos leen los mismos bloques
  de freno pero responden preguntas distintas; quien toque uno debe tener presente el otro.
- **`brake_start` (escalar) no cambia para nadie**; `brake_starts` (lista) es aditivo y solo aparece
  con ≥2 frenadas fuertes. Los consumidores previos (`compare`, HUD, gráficas) no se enteran.
- **`THROTTLE_REAPPLY=15` es un valor inicial afinable.** Marca el umbral entre "readministración de
  gas real" y "roce". Ajustarlo cambia qué curvas emiten un segundo aviso; se mueve con conciencia
  del piso `BRAKE_ON` y de `phase_gap_s`.
- **Pendiente de validar:**
  - **Charbel (telemetría):** que C03 (m803) y C05 (m1119) emitan exactamente **2** frenadas, y que
    **no aparezcan segundos avisos espurios** en las 55 curvas de la vuelta real.
  - **Mariana (oído):** que el **doble countdown** de dos frenadas pegadas no sature la cinta.
- **Enmienda al [ADR 0031](0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md):** el 0031
  definió `brake_start` como el escalar de la fase de pico máximo y ese punto **sigue vigente sin
  cambio** para coaching y `compare`. Lo que este ADR añade es que "qué frenadas suenan" ya **no** es
  la misma pregunta que "cuál es el punto comparable": esa segunda pregunta la responde ahora
  `detect_brakings`/`brake_starts`. La regla de selección, la simetría de `compare` y el límite
  conocido del trail-braking del 0031 quedan intactos.
