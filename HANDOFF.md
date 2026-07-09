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

**2026-07-09 — ciclo de deuda técnica "Media" del ROADMAP CERRADO y FUNDIDO a `master`
(squash `dd65f9b`, [PR #45](https://github.com/ArmandoMedina/SimGhostInputs/pull/45)).** Las 8 PRs
independientes del ciclo (#37–#44) se consolidaron en una rama de integración
(`integration/deuda-tecnica-media-2026-07`), se mergearon una por una con `--no-ff`, y la rama
resultante se squash-mergeó a `master` con CI 7/7 verde. Autorizado explícitamente por el usuario
(merge automático al pasar la suite completa, sin revisión humana adicional).

**Qué entró (8 ítems Media, un PR cada uno, todos absorbidos en `dd65f9b`):**
- **#37** `chore/pin-ruff-version` — `ruff==0.15.20` pineado (CI y local misma versión).
- **#38** `chore/dependency-lockfile` — `requirements-lock.txt` con `pip-compile` ([ADR 0029](docs/decisions/0029-lockfile-pip-compile.md)).
- **#39** `docs/cierre-deuda-documental` — cierre de deuda documental (enmiendas ADR 0028/0019, hook de concurrencia).
- **#40** `fix/corners-window-sample-rate` — ventanas de sostenimiento (`throttle_on`/`full_throttle`) normalizadas por `dt` real, no muestras fijas.
- **#41** `fix/hooks-error-handling` — quitado el `SilentlyContinue` ciego de los 3 hooks de sesión (ALTO-04).
- **#42** `fix/voice-pack-anti-saturacion` — `build_voice_pack` reusa el plan anti-saturación ([ADR 0024](docs/decisions/0024-sincronia-pace-notes.md), enmienda "notas de voz").
- **#43** `test/step5-mux-storage-user-real` — E2E que ejerce `app.storage.user` real en `run.io_bound`.
- **#44** `fix/step3-render-job-in-state` — job de render del Paso 3 vive en `state.active_overlay_job`.

**Resolución de conflictos (por unión, nunca "ours"/"theirs" a ciegas):** cada rama tocaba
`CHANGELOG.md` y `ROADMAP.md`; varias también `docs/decisions/README.md`, `pyproject.toml`,
`docs/flujo-de-trabajo.md`. Se conservaron TODAS las adiciones de ambos lados (checkboxes, entradas,
filas de ADR) — verificado archivo por archivo contra cada rama fuente antes de commitear.
Conflicto semántico notable en `pyproject.toml`: #37 pineaba ruff y #38 sumaba `pip-tools` —
la unión mantiene ambos.

**Fix extra destapado al consolidar (`ci: instalar extra [voice] en el job pytest`):** la CI de #42
estaba en ROJO (no "verde" como se creía) — sus tests de `build_voice_pack` importan `edge_tts` para
monkeypatchear `Communicate`, pero el job pytest instalaba `.[test,ui-ng,sync]` sin `[voice]`
(`ModuleNotFoundError` en CI; local sí lo tenía instalado, por eso pasaba). El código de producción
mantiene edge-tts opcional (`find_spec` + RuntimeError accionable); el fix solo lo agrega al entorno
de test, como ya asumía el comentario del propio test. Con eso, CI 7/7 verde.

**Verificación:** `ruff check` + `ruff format --check` limpios; `pytest` completo **381 passed, 11
skipped**; `tools/verificar.ps1` con grafo de docs íntegro (solo AVISOs no bloqueantes de
blast-radius); CI de GitHub **7/7 verde** (audit, docs-graph, lint, pytest 3.10/3.11/3.12,
visual-smoke) sobre la PR de integración antes del squash.

## Siguiente acción

Nada bloqueante del ciclo Media queda abierto. Deuda nueva anotada en `ROADMAP.md` durante el ciclo
(no bloquea): modo `"both"` sin gap cruzado tono↔voz (#42), y los 3 ítems del hook de concurrencia
(campo `tool_input.isolation`, el "3" sin medir, concurrencia vs. cupo acumulado — enmienda
2026-07-09 del [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).

**Limpieza pendiente (no la pude cerrar yo):** las 9 ramas remotas (8 + integración) quedaron
**borradas en remoto** y la rama de integración local también. Las 8 ramas **locales** originales
siguen existiendo porque están checked-out en worktrees de otras sesiones de agente
(`.claude/worktrees/agent-*` y, en el caso de `docs/cierre-deuda-documental`, el checkout principal
del repo); borrarlas exige desmontar esos worktrees y el clasificador de permisos lo bloqueó (podrían
tener trabajo sin commitear de otras sesiones, y no estaban nombrados en la tarea). Están 100%
absorbidas en `dd65f9b` — sin riesgo de perder nada; se pueden borrar cuando esas sesiones cierren
sus worktrees.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean.
