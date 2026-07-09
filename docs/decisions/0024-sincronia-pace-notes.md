# ADR 0024 — Sincronía de pace notes: anticipación por tiempo, gap global y sidecar video↔vuelta

- **Estado:** Aceptada · enmendada por [ADR 0025](0025-countdown-ancla-en-la-frenada.md), [ADR 0026](0026-cues-frenada-universal-countdown-oportunista.md) (2026-07-06) y una enmienda propia sin ADR nuevo (2026-07-09, "notas de voz")
- **Fecha:** 2026-07-05

> **Enmienda (ADR 0025):** el countdown ya no es un WAV único de 3 tics en el punto de
> anticipo. El evento se ancla en la FRENADA y se expande en 2 tics de aviso + el tono de
> frenada exacto en el punto de frenada de la referencia ("el 3 es el ya"). El cálculo del
> anticipo por tiempo (punto 3 de este ADR) sigue vigente.
>
> **Enmienda (ADR 0026):** el gap global por prioridad (punto 2) ya no puede descartar un
> tono de frenada — la frenada queda protegida y suena universal. El countdown deja de
> depender de severidad/prioridad y pasa a tics oportunistas por cabida.
>
> **Enmienda (2026-07-09, "notas de voz"):** los puntos 1–3 de este ADR (descarte en vez de
> clamp, gap mínimo global, anticipo por tiempo) se aplicaban solo a `plan_tone_events` /
> `build_tone_pack`. `build_voice_pack` los reimplementaba a medias por su cuenta: sí
> descartaba `distance<=0`, pero con un anticipo fijo de 200 m (no por tiempo) y **sin ningún
> gap entre curvas** — dos frenadas cercanas podían narrar frases de ~7.5 s que se encimaban
> (deuda del ROADMAP, señalada originalmente por el Reviewer sobre este mismo ADR). Ver
> sección "Enmienda: notas de voz" más abajo para el detalle del fix.

## Contexto

En el QA real del flujo pacenotes (Nordschleife, vuelta de 394.05 s sobre `2_composed.mp4`) el PO
reportó los cues como "desincronizados" y se rindió tras 6 demos. La sesión murió con una hipótesis
sin verificar: que la referencia (MoTeC 2025) y la vuelta del piloto (2020) medían la pista con
calibración de distancia distinta.

**La hipótesis se verificó y es FALSA** (evidencia reproducible en
`qa_runs/charbel-20260705-desync/`): los largos difieren 0.1 % (20 592 vs 20 571 m), el ajuste
lineal entre apexes da pendiente 0.9997, y los cues de los packs que el PO escuchó caen a **±1 s
del paso real** por cada curva, sin deriva. El motor de mapeo distancia→tiempo
(`render_pace_notes_track` + `_dist_to_time`) es correcto — lo confirmó también el demo de marchas.

El desync **percibido** viene de decisiones de diseño del plan de cues, todas medidas:

1. Cues clampados a `d=0` (`max(0, brake_d - anticipo)`) → suenan en el segundo 0 del video.
2. El gap mínimo de 50 m solo aplicaba dentro de una curva; entre curvas encadenadas quedaban
   cues a 23 m (~0.4 s) → sopa de tonos.
3. Anticipación fija de 120 m ≈ 2 s a velocidad GT3 (el PO pidió 3–4 s).
4. `brake` y `brake_countdown` ambos a 880 Hz → indistinguibles.
5. El panel ② del Paso 5 muxea con **la vuelta que esté cargada**: no hay vínculo video↔vuelta, y
   dos vueltas de laptime parecido (394.05 vs 394.07) tienen splits distintos → desync real de
   segundos si se carga otra vuelta.

## Decisión

Cinco cambios en el motor (`fantasma/viz/pacenotes.py`, `fantasma/viz/compose.py`):

1. Un anticipo que caiga en `d ≤ 0` **se descarta** (razón `antes_de_la_meta`), no se clampa a 0.
2. El gap mínimo (`min_gap_m=50`) aplica también **entre curvas**; en conflicto sobrevive el cue
   de mayor prioridad (razón `too_close_global`).
3. La anticipación del countdown es **por tiempo**: `countdown_s=3.5` a la velocidad de llegada a
   la frenada (`v` del milestone, km/h), acotada a [60, 350] m; fallback al `countdown_m=120` fijo
   si el milestone no trae `v`.
4. `brake` pasa a **1000 Hz** (el countdown termina su escala en 880).
5. `compose_video` escribe un **sidecar** `<video>.sync.json` (formato `sgi-sync-v1`: `csv_path`,
   `laptime`, `offset`, `lap_duration`) y el mux del Paso 5 **bloquea con error accionable** si la
   vuelta cargada difiere > 0.1 s del laptime del sidecar. Videos externos sin sidecar pasan como
   siempre. Además, `top=0` significa "todas las curvas" (pace notes de ritmo, estilo rally).

## Razones

- **Se atacan las causas medidas, no la sospecha.** Cada cambio corresponde a un hallazgo
  cuantificado del diagnóstico (cue en t=0.0 de C01; pares a 23 m entre C48–C49; countdown 2.0 s
  antes a 216 km/h). El fix es determinista y testeable (7 tests nuevos).
- **Anticipo por tiempo y no por metros** porque el oído juzga en segundos: 120 m son 2 s a
  216 km/h pero 6 s a 70 km/h — la misma distancia produce sensaciones opuestas según la curva.
- **Sidecar con error (no solo aviso)** porque el mux con vuelta equivocada produce exactamente el
  síntoma que quemó al PO, y es indetectable de oído hasta media vuelta. El costo de forzar es
  explícito (borrar el `.sync.json`), no un click en "continuar de todos modos".
- **Descartar en vez de clampear** porque un cue en el arranque del video transmite "esto está
  roto" en el primer segundo y contamina el juicio de todo lo demás.

## El camino que NO se toma (y por qué tienta)

- **"Recalibrar la distancia entre referencia y piloto" (escalar `d_ref` por el ratio de largos).**
  Es la hipótesis con la que murió la sesión anterior y lo primero que tentaría a una sesión nueva
  con el mismo contexto. **Está refutada con datos**: la diferencia es 0.1 % (≈0.4 s en toda la
  vuelta) y el "20 237 vs 20 571" que la motivó comparaba el último cue contra el largo de pista.
  Escalar añadiría complejidad sin atacar ninguna causa real.
- **Mapear los cues a los puntos del PILOTO en vez de los de la referencia.** Tienta porque "así
  coinciden con lo que hago". Pero el cue marca dónde frena/acelera **la referencia** — ese
  desfase ES el coaching (dónde pierdes). Lo que faltaba era explicárselo al usuario (leyenda en
  la UI, PR 3), no mover el cue a su error.
- **Auto-seleccionar la vuelta correcta desde el sidecar en vez de bloquear.** Cómodo, pero carga
  telemetría "por magia" saltándose el Paso 1 (selección explícita del PO) y falla silencioso si
  el CSV se movió. Puede evaluarse después como mejora de UX sobre el mismo sidecar.
- **Ducking/limiter en la mezcla** para el riesgo de clipping de `normalize=0`: se difiere — el
  tono es breve y el WAV ya viene acotado; si aparece distorsión audible, bajar `volume` del cue o
  añadir `alimiter` (nota en `_audio_mix_filter`).

## Enmienda: notas de voz pasan por el mismo plan anti-saturación (2026-07-09)

**Problema.** `build_voice_pack` (`fantasma/viz/pacenotes.py`) no llamaba a `plan_tone_events`:
recalculaba su propia selección de curvas top-N y su propio descarte de `distance<=0`, pero con
un anticipo **fijo de 200 m** (el mismo defecto que tenían los 120 m del countdown antes de este
ADR, corregido entonces solo para tonos) y **sin ningún gap mínimo entre curvas**. Dos frenadas
cercanas generaban dos narraciones de ~7.5 s que se encimaban en el audio final — síntoma
observado en la demo `_DEMO_VOZ_referencia`, deuda anotada en el ROADMAP.

**Decisión.** En vez de que `build_voice_pack` reimplemente su propio descarte/gap, reutiliza el
mecanismo ya existente:

1. El gap mínimo global de `plan_tone_events` (antes una función anidada, `_resolve_min_gap`) se
   extrajo a función de módulo para poder compartirla sin duplicar la lógica. `build_voice_pack`
   arma sus candidatos (uno por curva top-N, igual que antes) y los pasa por
   `_resolve_min_gap(candidates, min_gap_m)` con el mismo `min_gap_m` por defecto (50 m) que usa
   `plan_tone_events`.
2. A diferencia del tono de frenada, los eventos de voz **no se marcan como protegidos**: la
   garantía "nunca se descarta" (R1, ADR 0026) es una decisión específica del beep de 0.12 s, que
   en la práctica casi nunca se pisa de verdad. Una narración hablada de ~7.5 s sí necesita poder
   ceder su hueco — si no, el gap sería cosmético y el bug seguiría ahí. Al colisionar dos
   narraciones, sobrevive la de la curva con más `time_lost` (la que más vale la pena narrar).
3. El anticipo pasa de metros fijos a **tiempo**: `_voice_lead_m` deriva `lead_m` de la velocidad
   de llegada a la frenada (`v` del milestone) igual criterio que `_countdown_lead_m` — el oído
   juzga en segundos, no en metros. Nuevo parámetro `voice_lead_s` (`DEFAULT_VOICE_LEAD_S = 4.0`),
   acotado a `[60, 400]` m. Sin `v` en el milestone (corners JSON viejos, tests sintéticos), cae al
   anticipo fijo histórico de 200 m — no-regresión exacta para esos casos.

**Qué NO cambia.** El límite de ~1 nota de voz por curva sigue siendo estructural (un candidato
por fila con milestone de frenada) — no se agregó un `max_events_per_corner` explícito porque no
hace falta. El número de curvas narradas por defecto (`top`) no cambia.

**Wiring y efecto secundario benigno (`/code-review` sobre este mismo fix).** `build_pack` ya
reenviaba los kwargs de `build_tone_pack` desde su punto de entrada público, pero no hacía lo
mismo con los nuevos `min_gap_m`/`voice_lead_s` de `build_voice_pack` — quedaban inalcanzables
desde `mode="voice"`/`"both"`. Corregido reenviándolos igual que el resto. Como efecto colateral,
las entradas de `metadata.json` del pack de voz ahora quedan ordenadas por **distancia** (antes,
por orden de mayor `time_lost`, el mismo orden en que `_top_rows` procesa las curvas) — esto
iguala el criterio que `build_tone_pack` ya usaba (su `plan["events"]` siempre sale ordenado por
distancia) y no afecta a ningún consumidor: `render_pace_notes_track` mezcla cada entrada de forma
independiente por su `distanceRoundTrack`, y `build_cue_ass` reordena sus rótulos por tiempo antes
de emitirlos.

**Comportamiento observable pendiente del oído del PO.** Con telemetría real (que sí trae `v` en
los milestones), las distancias narradas cambian levemente respecto al fijo de 200 m — más
anticipo en curvas rápidas, menos en curvas lentas, igual que ya ocurre con el countdown de
tonos. El gap de 50 m entre curvas es el mismo default que tonos; no se subió pese a que una
frase de voz dura mucho más que un tono de 0.12 s (podría no bastar para evitar TODO solape a
velocidades muy altas) — se mantiene el mismo número para no reinventar un segundo criterio sin
evidencia de oído; si el PO sigue escuchando solapes tras este fix, subir `min_gap_m` para el pack
de voz es el siguiente paso, no un rediseño. El modo `"both"` (tonos + voces) sigue sin gap
cruzado entre ambos packs — cada uno resuelve el suyo por separado (deuda nueva en el ROADMAP,
fuera de alcance de este fix).

## Consecuencias

- Se gana: cues escasos y legibles (sin sopa), countdown con tiempo de reacción constante,
  imposible muxear la vuelta equivocada sin enterarse, y "todas las curvas" disponible para uso
  tipo rally.
- Se pierde: los packs generados antes de este ADR no tienen sidecar (siguen muxeando sin
  validación); el countdown ya no es determinista respecto a metros fijos (depende de `v`).
- Pendiente de validar: el juicio de oído del PO sobre `countdown_s=3.5` y la frecuencia 1000 Hz
  (demo e2e `_DEMO_FIXED.mp4`); la leyenda de tonos y el cableado UI del sidecar van en el PR 3.
- La lógica "fault-matched" de cues (disparar solo por el fallo puntual, no por `pierdes ≥ 0.25 s`)
  queda **fuera** — prototipada en demo, necesita definición de producto con el PO (ROADMAP).
