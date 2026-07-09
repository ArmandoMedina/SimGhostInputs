# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).
>
> **Ciclo de vida (ADR 0019): se llena al cerrar, se lee y se LIMPIA al abrir.** Al arrancar
> sesión (`/arranca` lo instruye): lee esto y borra lo ya atendido — un HANDOFF que acumula
> historia deja de leerse. La historia va al CHANGELOG; el porqué, a los ADRs.

## Estado actual

**2026-07-09 madrugada — PR #35 FUNDIDO a `master` (`64d7cc0`). Release "cues configurables" cerrado.**
El PO reportó 5 problemas de audio/subtítulos sobre `2_estudio_coast_ADR0027.mp4` (plan
`~/.claude/plans/squishy-herding-pearl.md`): prioridades reordenadas, countdown a 0.75s uniforme,
tabla de frecuencias nueva, cue `gear` (cambio de marcha, solo subtítulo) implementado end-to-end. Al
probar con la UI real salió un bug real (no de test): activar `gear` desalojaba **todos** los `coast`
de la vuelta (mismo pool de cabida global). Fix: `plan_tone_events` resuelve la cabida en dos pools
independientes (sonoro/mudo); mismo fix aplicado al timeline de `brake_tic`. Code review (8 ángulos) +
pytest completo verde. ADR 0028 enmendado.

Cinta E2E de verificación (6ª corrida, `1 passed in 825.87s`): `coast_entries` y `gear_entries`
confirmados en `metadata.json`, subtítulo "cambio de marcha" capturado en el metro **1754** (el
reclamo original del PO era ~1745). Entregable: **`2_estudio_reencuadre_ADR0028.mp4`** (~974 MB,
overlay a 0.5x) en `C:\Users\jose_\Downloads\Pruebas finales\` y copiado a
`C:\Users\jose_\OneDrive\Videos\2_estudio_reencuadre_ADR0028.mp4`. Evidencia en
`qa_runs/cinta-adr0028/` (8 capturas: pasos del wizard + 3 frames de subtítulo — inercia m950,
acelerador m1425, cambio de marcha m1754).

**Merge realizado 2026-07-09 (autorizado explícitamente por el usuario, sin esperar el veredicto de
oído/ojo del PO sobre la cinta — decisión suya, no de la IA):**
1. `master` había avanzado con #31/#34; había conflicto real solo en `CHANGELOG.md` (los otros 5
   archivos marcados como conflictivos auto-fusionaron limpio). Resuelto por un agente Opus en
   worktree aislado, verificado a mano (nada de ambos lados se perdió), pytest 358 passed/0 failed.
2. CI corrió por primera vez sobre esta rama (el gap de plataforma de días previos se resolvió solo —
   no identifiqué la causa, si vuelve a pasar sí hay que investigarlo). Primer intento: `lint` falló
   por un archivo sin formatear que el agente dejó pasar (el hook local solo lo marca como aviso, CI
   sí lo bloquea) — arreglado en `0d8f501`. Segundo intento: **7/7 checks verdes**, PR mergeable
   `CLEAN`.
3. Squash-merge (`gh pr merge 35 --squash`, sigue la convención del repo: 1 commit por PR en
   `master`). Rama `feat/cues-configurables` borrada (local + remoto).

**Pendiente — decisión tuya, no la tomé yo:** el sistema me bloqueó cerrar **#29**
(`feat/cues-frenada-universal`) y **#32** (`feat/cue-subtitles`) porque no los nombraste
explícitamente al pedir el merge. Ambos están **100% absorbidos** en el commit ya fundido (verificado:
`git log` no muestra commits huérfanos de #29 contra la vieja `feat/cues-configurables`; `git diff`
muestra que #32 es subconjunto estricto, nada perdido) — son historia vieja redundante. Si querés que
los cierre (sin fusionar, con nota de que ya están absorbidos) y borre esas 2 ramas
(`feat/cues-frenada-universal`, `feat/cue-subtitles`), dímelo explícito la próxima sesión.

**Siguiente paso real: el PO mira/oye la cinta `2_estudio_reencuadre_ADR0028.mp4`** (ruta arriba) y da
el veredicto de oído/ojo sobre countdown más rápido, turn_in en más curvas, tonos ya no confundibles,
overlay 0.5x y el subtítulo de cambio de marcha — juicio subjetivo, ya con el código fundido a
`master` (no bloqueaba el merge esta vez, fue decisión explícita del usuario).

**Plan persistido:** `~/.claude/plans/tender-hugging-whale.md` — detalle de cada workstream (todos
cerrados, PR ya fundido).

**Hecho y revisado (commits en `feat/cues-configurables`, todo pusheado a origin):**
- **WS-1** `5bc17f9`+`3215095` — motor: `throttle_on` sostenido + modela **coast**; arregla el bug
  **317/393**. Doc dueño: `docs/formato-datos.md`.
- **WS-2** `1d62758`+`229c93e` — catálogo filtrable + prioridad configurable, `DEFAULT_CONFIG` sin
  regresión, frenada protegida universal.
- **WS-3** `d742513` — formato de perfil JSON compartible (`fantasma/viz/cue_profiles.py`).
- **WS-4** `f947a9d`+`6a61ce5`+`39cefb6`+`292b35d` — UI Paso 5 (casillas, prioridad, perfiles),
  robustez ante JSON malformado. Reviewer + Mariana (`qa_runs/mariana-20260707/`).
- **WS-5** `ef2d8cc` — subtítulos de cues sobre el motor final + ventana adaptativa (ya no 1.5 s fija).
- **WS-6** `5c6eefc` (ADR 0027, reencuadra 0026) + `4d77e7e` (Escribano: CHANGELOG, formato-datos,
  guia-usuario, ux-patterns, ROADMAP).
- **Cinta E2E real** `9ac4a9a` — Playwright encadena Paso 5 (pack con coast + todas las curvas) y
  Paso 0→1→3→4 (compone el video con overlay+subtítulos), 100% desde la UI. Generó el entregable
  **`C:\Users\jose_\Downloads\Pruebas finales\2_estudio_coast_ADR0027.mp4`** (687 MB, 2026-07-08 09:38)
  con evidencia en `qa_runs/cinta-adr0027/` (screenshots del pack, overlay, video y 2 subtítulos:
  "inercia" en m950, "acelerador" en m1425 — el bug 317/393 ya no dice "inicio de acelerador" ahí).
- **Regla de cambio de marcha** `0d19159` — anotada en ROADMAP (decisión de diseño del PO 2026-07-08:
  estudio=referencia, en-vivo=RPM reales; única excepción a "nunca generar cues desde la vuelta del
  piloto"). Es la nota de follow-up del slot `gear`, no una implementación.

**Decisión del countdown (opción 3 acotada):** se puede apagar + prioridad como metadata, pero **sigue
oportunista** (no pelea por espacio en la cabida) — hacerlo pelear contradiría el diseño validado de
oído.

**Material de pruebas en esta PC:** `C:\Users\jose_\Downloads\Pruebas finales`.

## Siguiente acción

**El release ya está fundido a `master`. Lo que falta es proceso/revisión, no desarrollo:**

1. **PO: mirar/oír `2_estudio_reencuadre_ADR0028.mp4`** (en OneDrive/Videos y en `Pruebas finales`,
   ver arriba). El checkpoint de Mariana capturó screenshots pero el veredicto final sobre el
   audio/video es del PO, no de la IA.
2. **Decidir si cerrar #29 y #32** (ver nota arriba — están absorbidos, el sistema me bloqueó cerrarlos
   sin que los nombraras explícitamente).

**Deuda anotada (Reviewer WS-1, ya en ROADMAP):** (a) `throttle_on_window`/`full_throttle` en muestras
fijas, no normalizado por tasa de muestreo (mal a ≠50 Hz); (b) coast no se emite si hay frenada sin
`brake_release` (trail-braking al borde del segmento).

**Decisiones de juicio del PO pendientes (no bugs — QA de Mariana):** asimetría leyenda-cerrada /
cues-abierta; rango de prioridad 0-999 sin pista visual; columnas desbalanceadas con cues abierto;
¿el select de perfiles necesita salvaguarda anti-cambio-accidental?; modo-claro fuera de alcance (la app
fuerza dark global, `ng_app.py:17`).

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
