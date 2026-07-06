# ADR 0025 — El último tono del countdown ES el punto de frenada (enmienda al ADR 0024)

- **Estado:** Aceptada
- **Fecha:** 2026-07-06

## Contexto

Con el motor del [ADR 0024](0024-sincronia-pace-notes.md) en producción, el PO validó la
cinta de estudio (`qa_runs/charbel-20260706-cinta-estudio/`) y reportó, con dato exacto:
"metro 4463 salen los 3 bips de frenada y no hay ni cerca ninguna frenada […] el 3er bip
tiene que coincidir siempre con el inicio de la frenada, nada de 1,2,3, ya; el 3 debe ser
el ya".

El diagnóstico lo confirma: era el countdown de C13. El diseño del ADR 0024 ponía **un solo
WAV con los 3 tics** en el punto de anticipo (metro 4408, 274 m antes de la frenada real de
la referencia en 4682 a 282 km/h). Matemáticamente correcto (3.5 s de anticipo), pero al
oído: tres tics, ~3.5 s de silencio, y **nada suena donde de verdad hay que frenar**. El
oyente no tiene forma de saber que el silencio "termina" en la frenada.

## Decisión

El evento `brake_countdown` se ancla en la **frenada** (`distance = brake_d`) y lleva su
anticipo como dato (`lead_m`). Al generar el pack, `build_tone_pack` lo expande en WAVs
independientes:

- **2 tics de aviso** (660 y 770 Hz) a `lead_m` y `lead_m/2` metros antes de la frenada.
- El **"¡ya!" es el tono de frenada** (1000 Hz, duración normal), **exacto** en el punto
  de frenada de la referencia. `COUNTDOWN_SCALE` pasa de 3 tics a 2: el tercer "tic" ya no
  existe como tal — lo sustituye el tono de frenada.

Un tic que caiga en `d ≤ 0` o a menos de `min_gap_m` (50 m) del ancla de otro cue se
omite; **el "¡ya!" nunca se pierde** (es el ancla del evento y compite por prioridad como
siempre en el plan).

## Razones

- **El contrato perceptivo lo fija el oído, no la geometría.** El anticipo de 3.5 s del
  ADR 0024 sigue vigente (el primer tic suena a `lead_m`); lo que cambia es dónde termina
  la secuencia: en el evento que anuncia. Un countdown que no culmina en nada es ruido.
- **El "¡ya!" como tono de frenada (1000 Hz) y no como tercer tic (880 Hz)** porque así el
  punto de frenada suena idéntico en curvas con y sin countdown — un solo significado por
  frecuencia, que es la promesa de la leyenda de tonos de la UI.
- **Tics omitibles pero "¡ya!" intocable** porque los tics son ayuda de anticipación
  (redundante si hay tráfico de cues alrededor), pero el punto de frenada es LA señal.

## El camino que NO se toma (y por qué tienta)

- **Dejar el WAV de 3 tics en el anticipo y añadir un cuarto tono en la frenada.** Tienta
  porque no toca el formato del evento. Pero mantiene el defecto de fondo (la secuencia
  1-2-3 termina en el aire y el 4º tono parece otro cue) y sube el conteo de sonidos por
  curva sin subir la información.
- **Estirar el WAV único hasta cubrir los 3.5 s (tics + silencio + ya en un archivo).**
  Tienta por simplicidad de metadata (una sola entry). Pero CrewChief dispara por
  `distanceRoundTrack` con la vuelta del piloto mapeando dist→tiempo: un WAV largo anclado
  al inicio acumula el error de mapeo a lo largo de sus 3.5 s y el "ya" interno cae
  corrido justo donde más precisión se necesita. Con WAVs independientes, cada tono se
  re-ancla a su propio metro.
- **Volver al countdown de 3 tics del ADR 0024.** Es lo que una sesión nueva leería en el
  ADR 0024 tal cual estaba. Queda enmendado: el punto 3 del 0024 (anticipación por tiempo)
  sigue vigente para calcular `lead_m`, pero la expansión en WAVs y el anclaje en la
  frenada se rigen por este ADR.

## Consecuencias

- Se gana: el tono de frenada suena SIEMPRE exacto donde frena la referencia (verificado:
  C13 tics en 4408/4545 y "¡ya!" en 4682, la frenada real); un significado por frecuencia.
- Se pierde: el conteo de sonidos del pack sube (cada countdown son hasta 3 WAVs — la
  cinta de estudio pasó de 101 a 130 cues de coaching); los tics pueden desaparecer en
  zonas densas (C14 quedó solo con su "¡ya!" por vecindad con los cues de C13).
- El camino legado (`generate_countdown`, un WAV con N tics) se conserva solo para packs
  no-smart; no lo usa el plan del ADR 0024.
- Pendiente de validar: juicio de oído del PO sobre la cinta regenerada.
