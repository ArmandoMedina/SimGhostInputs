# ADR 0024 — Sincronía de pace notes: anticipación por tiempo, gap global y sidecar video↔vuelta

- **Estado:** Aceptada · enmendada por [ADR 0025](0025-countdown-ancla-en-la-frenada.md) (2026-07-06)
- **Fecha:** 2026-07-05

> **Enmienda (ADR 0025):** el countdown ya no es un WAV único de 3 tics en el punto de
> anticipo. El evento se ancla en la FRENADA y se expande en 2 tics de aviso + el tono de
> frenada exacto en el punto de frenada de la referencia ("el 3 es el ya"). El cálculo del
> anticipo por tiempo (punto 3 de este ADR) sigue vigente.

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
