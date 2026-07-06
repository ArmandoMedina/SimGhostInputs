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

**Rama activa `feat/cues-frenada-universal` (sin push todavía):** rediseño del modelo de
cues de pace notes, commits `2f426ae` (código) + `ce01d72` (ADR 0026). Cierra dos
defectos que el PO reportó de oído sobre la cinta de estudio regenerada:
- **Metro 819** (frenada muda por competencia de gap) — el tono de frenada pasa a ser
  **universal y protegido**: suena en toda curva con `brake_start`, ningún gap lo tira.
- **Metro 4463** (3 bips sin frenada cerca) — el countdown pasa a **oportunista por
  cabida**: los 2 tics se colocan solo donde quepan contra TODA la línea de tiempo
  (tics de otras curvas incluidos), si no caben queda solo el tono de frenada.
- Además se retiró el **tono** de ápex del pack sonoro (el milestone sigue en datos, voz
  y matching). Detalle completo: [ADR 0026](docs/decisions/0026-cues-frenada-universal-countdown-oportunista.md).
Suite: 248 passed. **Bloqueado: el oído del PO sobre la cinta regenerada con este
rediseño** — el material real (`_DEMO_COMPLETO_SUBS.mp4`) no está en esta PC, así que no
se puede regenerar ni escuchar aquí. Falta también abrir el PR (push pendiente).

Contexto previo: `master` en **v2.2.0**, con el "pedo de los sonidos" (3 PRs: #25 `normalize=0`,
#26 [ADR 0024](docs/decisions/0024-sincronia-pace-notes.md) sincronía+gap global+sidecar,
#27 UI del Paso 5) y el countdown anclado del [ADR 0025](docs/decisions/0025-countdown-ancla-en-la-frenada.md)
(#28) ya mergeados — ambos quedan enmendados por el ADR 0026 de esta rama.

> **Pendiente fuera del repo:** la skill global `release-helper` (paso 2) aún dice "bump `pyproject.toml`";
> desde la #24 el bump va a `fantasma/__init__.py`. Actualizarla cuando el PO lo autorice.

## Siguiente acción

1. **Push de `feat/cues-frenada-universal` y abrir el PR** con el rediseño (819/4463/apex).
2. **Regenerar la cinta de estudio con este rediseño y conseguir el oído del PO** — bloqueado
   hasta que el material real (`_DEMO_COMPLETO_SUBS.mp4`) esté disponible en una PC con acceso
   a `qa_runs/charbel-20260706-cinta-estudio/` o equivalente.
3. Si la cinta le funciona: llevar al motor/UI los **upshifts de la referencia** y la
   **generación del `.srt`** (candidata Alta en ROADMAP; hoy son scripts de qa_runs).
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
