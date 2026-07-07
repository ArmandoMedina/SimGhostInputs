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

**Sesión de merge + revisada (2026-07-06).** master avanzó a `f8835de` con **4 PRs fundidos**
esta sesión, tras revisar los 6 con Reviewers:
- **#33** — silencia el ERROR flaky de JS del simulador NiceGUI en CI (test infra).
- **#34** — cobertura de `viz/report.py` y `viz/charts.py` (cierra deuda ROADMAP Alta).
- **#30** — el mux del Paso 5 no leía `state.drv_name` fuera del contexto UI.
- **#31** — botones de acción legibles + inputs de ruta a ancho completo.

**Abiertos, con fix y CI verde, BLOQUEADOS por el oído del PO:**
- **#29 `feat/cues-frenada-universal`** (ADR 0026) — frenada universal+protegida (metro 819),
  countdown oportunista por cabida (metro 4463), fuera el tono de ápex. La revisada encontró
  y Ahiram arregló (`a321011`) un bug: el tic del countdown se **auto-rechazaba contra su
  propia frenada** en curvas < ~103 km/h; ahora la timeline de cabida excluye el propio grupo
  de la curva (2 tests nuevos). **Gate: validación auditiva** — el material `_DEMO_COMPLETO_SUBS.mp4`
  no está en esta PC, no se puede regenerar la cinta aquí.
- **#32 `feat/cue-subtitles`** (ADR 0027) — subtítulos que nombran cada cue, quemados en el
  video. Ahiram blindó (`a37491c`) un bug: con subtítulos ON y rutas relativas, el video final
  se perdía en el tmpdir (ahora `abspath` a video/overlay/output). **Gate: tras oír la cinta,
  el PO decide si los subtítulos se quedan o se ajustan** (color/tamaño/duración).

Ambos PRs quedan para **merge conjunto tras la validación auditiva**; el merge lo dispara el PO
(la barrera de auto-mode bloquea que la IA funda PRs de código sin aprobación humana — se
respeta la regla del merge conjunto).

Contexto previo: `master` venía en **v2.2.0** con el "pedo de los sonidos" (#25/#26/#27) y el
countdown anclado del [ADR 0025](docs/decisions/0025-countdown-ancla-en-la-frenada.md) (#28)
ya mergeados — enmendados por el ADR 0026 de #29.

> **Pendiente fuera del repo:** la skill global `release-helper` (paso 2) aún dice "bump `pyproject.toml`";
> desde la #24 el bump va a `fantasma/__init__.py`. Actualizarla cuando el PO lo autorice.

## Siguiente acción

1. **Validación auditiva del PO (gate de #29 y #32)** — regenerar la cinta con el código de #29
   (ya con el fix del countdown) y oírla: 819 suena en frenada, 4463 sin bips huérfanos,
   countdown 3-2-1 donde debe, sin ápex, y en curvas lentas los DOS tics del countdown. Bloqueado
   hasta que `_DEMO_COMPLETO_SUBS.mp4` esté en una PC con acceso al material.
2. **Merge conjunto de #29 + #32** tras (1). Lo dispara el PO (auto-mode bloquea que la IA funda
   PRs de código). Antes de fundir #29: pasarle una revisada final si se toca más; #32 ídem.
3. Si la cinta le funciona: llevar al motor/UI los **upshifts de la referencia** y la
   **generación del `.srt`** (candidata Alta en ROADMAP; hoy son scripts de qa_runs). Y el PO
   decide si los **subtítulos de #32** se quedan o se ajustan (color/tamaño/duración).
Si esta sesión murió a medias: verificar contra el código real qué quedó mergeado
(`git log`, `gh pr list`) y retomar aquí.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
