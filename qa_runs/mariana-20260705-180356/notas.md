# QA — Fix de audio del mux de pace notes (`normalize=0`)

**Fecha:** 2026-07-05 · **Asiento:** Mariana (QA visual/render) · **Checkpoint que vuelve al PO.**

## Qué se validó
Caso de uso reportado por el PO: "tengo un video con overlay ya hecho y quiero ponerle
pace notes" (panel ② del Paso 5, `mux_pace_notes_into_video`). Se reprodujo **end-to-end
con material real** en sesión, no un "renderiza sin excepción".

## Material real usado
- Video: `C:\Users\amedina\Downloads\0207\frames\2_composed.mp4` (Nordschleife, 394.07 s, h264+aac 48 kHz).
- Pack: `C:\Users\amedina\Downloads\0207\frames\` (12 cues WAV + `metadata.json`, pista `Nordschleife_2025`).
- Vuelta piloto: lap 8 de `Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv`
  (laptime 394.05 s → coincide con la duración del video ⇒ misma vuelta).

## Hallazgo (bug real) y fix
`_audio_mix_filter` usaba `amix=inputs=2` **sin `normalize=0`**. Por defecto ffmpeg divide
cada entrada entre el nº de inputs (−6 dB), enterrando los cues bajo el audio del motor.
Fix: añadir `:normalize=0` (afecta panel ② y también `compose_video`).

## Medición objetiva (ffmpeg volumedetect, ventana en el cue #1 @137.2 s)
| audio | mean | max |
|---|---|---|
| tono solo (WAV de cues) | −11.9 dB | −1.9 dB |
| mezcla ANTES (buggy, `amix` default) | −19.4 dB | **−7.2 dB** ← cue enterrado |
| mezcla DESPUÉS (`normalize=0`) | −13.4 dB | **−0.9 dB** ← cue audible, sin clipear |
| control zona sin cue @60 s, DESPUÉS | −17.3 dB | — (motor conserva su nivel original) |

⇒ El fix sube el cue ~6 dB dejándolo casi al nivel del tono puro, y el motor no se atenúa.

## Sincronización (distancia → tiempo)
Los 12 cues caen **todos dentro** de la vuelta (ninguno fuera). Detalle en `cue-timing.txt`.
Clusters audibles: C21 ~2:17–2:26 · C30 ~3:43–3:53 · C37 ~4:22–4:28 · C53/54 ~6:19–6:24.

## Artefactos
- `cue-timing.txt` — mapa distancia→tiempo de los 12 cues (verificación de sync).
- Demo audible para el PO: `C:\Users\amedina\Downloads\0207\_DEMO_pacenotes_FIX.mp4`
  (442 MB, fuera del repo; el PO lo borra tras escuchar).

## Checklist QA visual/render (docs/ux-patterns.md §2-B)
- [x] Corrida real con caso de uso real (no solo "sin excepción").
- [x] Salida coherente: video intacto (`-c:v copy`), audio mezclado correctamente.
- [x] Vocabulario de pista correcto en los cues (C21/C30/C37…, "contador de frenada/apex/gas").
- [x] Estado audible: los cues ahora se oyen sobre el motor (medido, no supuesto).
- [x] Sin regresiones de nivel del audio original del motor.
- [ ] **Pendiente PO:** validar auditivamente el demo (¿volumen de tonos a gusto?).

## Notas del Reviewer atendidas
- ffmpeg ≥ 4.4 requerido por `normalize` → anotado en el comentario del código.
- Riesgo de clipping en picos motor+tono → documentado como tradeoff aceptable (tono breve,
  WAV ya clippeado); mitigación disponible (bajar `volume` o `alimiter`) si el PO oye distorsión.

## Veredicto
**Funciona; queda a validación auditiva del PO.** El pipeline del caso "traigo mi video y le
pongo pace notes" está probado con material real y el bug de volumen corregido y medido.
