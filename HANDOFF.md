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

**2026-07-08 noche — fix `gear` vs `coast` cerrado, pusheado y cinta E2E verde. Listo para el PO.**
El PO reportó 5 problemas de audio/subtítulos sobre `2_estudio_coast_ADR0027.mp4` (plan
`~/.claude/plans/squishy-herding-pearl.md`): prioridades reordenadas, countdown a 0.75s uniforme,
tabla de frecuencias nueva, cue `gear` (cambio de marcha, solo subtítulo) implementado end-to-end —
todo eso ya commiteado en sesiones previas (`8b5b8cc`..`bfaee58`). Al probar con la UI real, activar
`gear` desalojaba **todos** los `coast` de la vuelta (mismo pool de cabida global) — bug real, no de
test. Fix en `3eb6688` + `32b4d2b` (pusheados a origin): `plan_tone_events` resuelve la cabida en dos
pools independientes (sonoro/mudo); mismo fix aplicado al timeline de `brake_tic`. Code review
(8 ángulos) + pytest completo verde. ADR 0028 enmendado, `formato-datos.md` corregido.

La cinta E2E (Playwright, Flujo A+B) se corrió 6 veces; la 5ª murió en un timeout de UI ajeno al fix
(clic en "Ir al Paso 4" tras generar overlay, `test_e2e_cinta_estudio_subtitulada.py:384` — no se
repitió en el rerun, probable flake de timing con Nordschleife/máquina cargada, no bloquea). La
**6ª (`1 passed in 825.87s`) pasó completa**: `coast_entries` y `gear_entries` confirmados en
`metadata.json`, subtítulo "cambio de marcha" capturado en el frame del metro **1754** (el reclamo
original del PO era ~1745). Entregable: **`2_estudio_reencuadre_ADR0028.mp4`** (~974 MB, overlay a
0.5x) en `C:\Users\jose_\Downloads\Pruebas finales\` y copiado a
`C:\Users\jose_\OneDrive\Videos\2_estudio_reencuadre_ADR0028.mp4`. Evidencia en
`qa_runs/cinta-adr0028/` (8 capturas: pasos del wizard + 3 frames de subtítulo — inercia m950,
acelerador m1425, cambio de marcha m1754).

**Siguiente paso real: el PO mira/oye la cinta nueva** y da el veredicto de oído/ojo sobre countdown
más rápido, turn_in en más curvas, tonos ya no confundibles, overlay 0.5x y el subtítulo de cambio de
marcha — es juicio subjetivo, no lo cierra la IA sola (mismo patrón que con la cinta ADR0027).

**Release "cues configurables" — PR #35 abierto, en revisión del PO.** El rediseño completo (WS-1 a
WS-6 del plan) está hecho, pusheado y con **PR paraguas abierto**: [#35](https://github.com/ArmandoMedina/SimGhostInputs/pull/35)
`feat/cues-configurables` → `master`, absorbe #29 y #32. Todo en la rama, nada fundido — **el merge lo
dispara el PO**.

**Plan persistido:** `~/.claude/plans/tender-hugging-whale.md` — detalle de cada workstream (todos
cerrados).

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

**El código y las docs del release están cerrados. Lo que falta es de proceso/revisión, no desarrollo:**

1. **PO: mirar/oír `2_estudio_reencuadre_ADR0028.mp4`** (en OneDrive/Videos y en `Pruebas finales`,
   ver arriba) — reemplaza a `2_estudio_coast_ADR0027.mp4` como la cinta vigente. El checkpoint de
   Mariana capturó screenshots pero el veredicto final sobre el audio/video es del PO, no de la IA.
2. **PR #35 tiene conflicto de merge con `master`** (`mergeStateStatus: DIRTY`, `mergeable: CONFLICTING`)
   — `master` avanzó con 2 PRs fundidos después de que esta rama arrancó (#31 botones legibles, #34
   cobertura report/charts). Conflictan: `CHANGELOG.md`, `ROADMAP.md`, `docs/guia-usuario.md`,
   `docs/ux-patterns.md`, `fantasma/ui/ng_app.py`, `fantasma/ui/ng_step5.py`, y archivos nuevos de test
   sin conflicto real (`tests/ui/conftest.py` vs `tests/ui/test_ci_flaky_filter.py`,
   `tests/viz/test_charts.py`, `tests/viz/test_report.py` — estos últimos son adds paralelos, no debería
   haber choque de contenido). Hay que traer `master` a la rama (merge o rebase) y resolver antes de
   poder fundir.
3. **CI nunca corrió sobre esta rama/PR — confirmado, no es lag.** `gh api .../actions/runs`: la última
   corrida en todo el repo es del 2026-07-07T00:18Z. Probé con un push de control (el commit de este
   mismo HANDOFF, `8e358a1`) y **tampoco disparó** `tests.yml`, pese a que Actions está `enabled`/`active`,
   el repo es público (sin límite de minutos) y el YAML es válido (`push: branches: [master]` +
   `pull_request: branches: [master]` — el PR #35 sí apunta a `master`, debería calzar). Esto ya **no es
   de este release**, es un gap de plataforma/cuenta que afecta a todo el repo desde ayer — **el PO
   debe revisarlo** (¿límite de la cuenta? ¿outage de Actions? ¿algo cambió en permisos del repo?) antes
   de confiar en que el CI vaya a bloquear nada. **No fundir sin CI verde** (regla del propio flujo).
4. Tras resolver 2 y 3: barrido de Reviewer consolidado sobre el diff final del PR, luego el PO aprieta
   el merge.

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
