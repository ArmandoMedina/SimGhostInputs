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

**El plan de 3 PRs del "pedo de los sonidos" está COMPLETO y mergeado (6-jul):**
- **PR 1** #25 `fix(viz)` `normalize=0` — cues audibles sobre el motor.
- **PR 2** #26 `feat(viz)` motor + [ADR 0024](docs/decisions/0024-sincronia-pace-notes.md):
  anticipación por tiempo (3.5 s, clamp [60, 350] m), gap global, descarte de cues d≤0,
  brake 1000 Hz, `top=0` = todas las curvas, sidecar `<video>.sync.json`. E2e real en
  `qa_runs/charbel-20260705-pr2-e2e/`.
- **PR 3** #27 `feat(ui)` — leyenda de tonos, checkbox "todas las curvas", caption
  "Falta: …", aviso ✓/⚠ de sidecar, breadcrumbs por flujo, y dos fixes sistémicos de
  NiceGUI (`navigate()` sin await; `e.value` inexistente en `update:model-value` →
  reglas en `ux-patterns.md`). Evidencia: `qa_runs/mariana-20260705-paso5/`.
  Nota git: nació encima de la rama del PR 2 (squash) → hubo que
  `git rebase --onto origin/master` antes de mergear.

**Validación del PO (en curso):** sincronía confirmada A OÍDO ("los cambios de marcha se
escuchan perfectamente sincronizados") sobre la **cinta de estudio**
`C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO_SUBS.mp4` — su video + 174 sonidos TODOS
de la referencia (101 cues coaching + 73 upshifts a 1500 Hz) + subtítulos por sonido
(`.srt` incrustado mov_text, apagable). Scripts reproducibles en
`qa_runs/charbel-20260706-cinta-estudio/`. **Regla de producto (ROADMAP): los cues salen
SIEMPRE de la referencia; la vuelta del piloto solo mapea dist→tiempo al video.**
Veredicto del PO sobre los subtítulos: "están chingones… ya vi los problemas" (plural).
**Problema 1 (ATENDIDO, [ADR 0025](docs/decisions/0025-countdown-ancla-en-la-frenada.md)):**
"metro 4463 salen los 3 bips y no hay ni cerca ninguna frenada… el 3 debe ser el ya" —
el countdown ahora se ancla en la frenada: 2 tics de aviso + el tono de frenada exacto
donde frena la referencia (verificado en C13: tics 4408/4545, "¡ya!" en 4682). Cinta
regenerada (`_DEMO_COMPLETO_SUBS.mp4`, 203 sonidos, 161 rótulos) — **pendiente su oído**.
**El resto de la lista de problemas sigue pendiente de recibir.**

Contexto previo: `master` en **v2.2.0** con tres tandas mergeadas hoy:
1. **Flujo "Solo Pace Notes"** (#21) + release **v2.2.0** (#22, con `Setup.exe` + zip portable adjuntos).
2. **Automatización release→installer en CI** (#23, [ADR 0022](docs/decisions/0022-ci-release-installer.md)): al publicar un release se compila y adjunta el instalador solo (aplica desde el próximo release).
3. **Fuente única de versión** (#24, [ADR 0023](docs/decisions/0023-fuente-unica-de-version.md)): SSOT = literal `__version__` en `fantasma/__init__.py`; `pyproject` lo deriva con `dynamic`; el badge del footer y `build_installer.py` lo leen. **Bumpear la versión = editar `fantasma/__init__.py`.**

> **Pendiente fuera del repo:** la skill global `release-helper` (paso 2) aún dice "bump `pyproject.toml`";
> con la #24 el bump va a `fantasma/__init__.py`. Actualizarla cuando el PO lo autorice.
>
> Cambio local sin commitear (esta actualización del HANDOFF): `master` exige PR — lo recoge el próximo PR.

## Siguiente acción

1. **Recibir del PO el resto de los problemas** que vio en la cinta de estudio
   (`_DEMO_COMPLETO_SUBS.mp4` regenerada con el ADR 0025) y su veredicto de oído sobre el
   countdown nuevo — probable ajuste de `min_gap_m`/máx por curva ("faltan curvas").
2. Si la cinta de estudio le funciona: llevar al motor/UI los **upshifts de la
   referencia** y la **generación del `.srt`** (candidata Alta en ROADMAP; hoy son
   scripts de qa_runs).
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
