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

**2026-07-09 — en curso: cierre de la deuda técnica "Media" del ROADMAP (8 ítems), con
autonomía del usuario para ejecutar y subir PRs. Ninguno se mergea a `master` sin revisión
conjunta.** Plan de sesión (efímero, no versionado — ADR 0019): `~/.claude/plans/memoized-percolating-sundae.md`.

**Hecho y ya en PR/commit:**
- **Ítem 2** (duplicación `detect_gear_shifts`) — cerrado por documentación: enmienda a
  [ADR 0028](docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md) +
  checkbox en ROADMAP. No era código, los dos patrones no son intercambiables.
- **Ítem 7** (lockfile) — [ADR 0029](docs/decisions/0029-lockfile-pip-compile.md) decide
  `pip-compile`; parte mecánica en **PR #38** (`chore/dependency-lockfile`).
- **Ítem 6** (pin de ruff) — **PR #37** (`chore/pin-ruff-version`).
- **PR #39** (`docs/cierre-deuda-documental`) agrupa los ítems 2 y 7 (ADR) más la
  documentación del hook nuevo (ver abajo) — incluye su propia autocrítica sin sesgo.
- **Nuevo:** tope determinista de agentes "pesados" concurrentes
  (`~/.claude/hooks/agent-concurrency-gate.ps1`, fuera del repo — ver
  [docs/recursos-del-proyecto.md](docs/recursos-del-proyecto.md) y la enmienda 2026-07-09 del
  [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)). Nace de un incidente
  real (ver abajo). **Solo probado con stdin sintético, no con una llamada `Agent` real** — 3
  ítems de deuda de seguimiento anotados en ROADMAP (verificar el campo real, el "3" no está
  medido, el hook topa concurrencia no cupo acumulado).

**Bloqueado — cupo de cuenta agotado, NO es pérdida de trabajo:** al lanzar 5 subagentes worktree
en paralelo (skill Ahiram) más el trabajo del hilo principal, la cuenta API alcanzó su
"session limit · resets 12pm (America/Mexico_City)" y los 5 fallaron a mitad de tarea. Verificado
con `git status` de solo lectura: **el diff de cada worktree sigue intacto en disco**, nada se
perdió. Pendiente retomar cada uno vía `SendMessage` a su `agentId` cuando el cupo se restablezca,
respetando el hook nuevo (máx. 3 lanzamientos "pesados" por ventana de 20 min):

| Worktree | PR (ítem ROADMAP) | Rama | Último estado conocido |
|---|---|---|---|
| `agent-a0a28563e63af334b` | PR-1 (ítem 1: `throttle_on_window`/`full_throttle` no normalizado por Hz) | `fix/corners-window-sample-rate` | Código+test+QA (`qa_runs/charbel-20260709-corners-window-sample-rate/`) listos; falta confirmar y abrir PR. |
| `agent-a8f9f011dc7cacabb` | PR-2 (ítem 3: `build_voice_pack` no reusa `plan_tone_events`) | `fix/voice-pack-anti-saturacion` | A medio fix: detectó que `build_pack` no pasa `min_gap_m`/`voice_lead_s` a `build_voice_pack`; falta terminar. |
| `agent-a392926305ba7eed5` | PR-3 (ítem 4: job de render Paso 3 fuera de `state`) | (worktree default, sin renombrar) | Código+tests listos; a medio escribir la entrada de CHANGELOG. |
| `agent-aaf8382b3bca3ae86` | PR-4 (ítem 5: test E2E `app.storage.user` real) | (worktree default, sin renombrar) | Test nuevo escrito; corriendo pytest completo al momento del corte. |
| `agent-ac86234f93ff486bf` | PR-7 (ítem 8: solo ALTO-04, quitar `SilentlyContinue` ciego en hooks) | `fix/hooks-error-handling` | Cambios en los 3 hooks hechos; reintentando un commit que no se había aplicado. |

**PRs abiertos, pendientes de revisión conjunta (no mergear sin el usuario):** #37, #38, #39.

## Siguiente acción

1. **Retomar los 5 worktrees de la tabla arriba** una vez pase el reset de cupo (12pm
   2026-07-09) — de 3 en 3 máximo (hook nuevo), verificar en el primero si el contador del hook
   realmente se mueve (confirma o refuta la deuda "campo no verificado" del ROADMAP).
2. **Abrir los PRs faltantes** (PR-1, PR-3, PR-4, PR-7) en cuanto cada worktree termine su
   verificación local (`pytest`, `ruff check`, `ruff format --check`).
3. **Revisión conjunta de los 7 PRs** con el usuario — ninguno se mergea antes de esa revisión.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean. Ítems Media aún sin PR: ver tabla
arriba (PR-1/2/3/4/7). Nuevo desde hoy: los 3 ítems de deuda sobre el hook de concurrencia
(campo `tool_input.isolation` sin verificar contra un caso real, tope de 3 sin medir, concurrencia
vs. cupo acumulado — detalle en la enmienda 2026-07-09 del ADR 0019).
