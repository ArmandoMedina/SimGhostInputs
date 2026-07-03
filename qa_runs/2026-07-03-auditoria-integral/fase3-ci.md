# Fase 3 — Auditoria de CI y regla anti-bypass

**Fecha:** 2026-07-03
**Rama auditada:** `codex/sgi-v2-merge`
**Cuenta gh activa:** `Armandomedina9705` (lectura publica; no es la propietaria del repo)
**Cuenta propietaria:** `ArmandoMedina` (inactiva durante la auditoria)
**Ruleset consultado:** `gh api repos/ArmandoMedina/SimGhostInputs/rulesets/18321394`

---

## Veredicto

5 de 6 jobs utiles existen en el workflow; 5 de los 6 ya son required checks en el ruleset activo;
el unico muro faltante es `audit` (blast-radius §8 sobre el rango del PR), que es cosmético hoy
aunque ADR 0019 y el HANDOFF lo exigen como requerido. `visual-smoke` esta en el ruleset pero su
implementacion actual es import-smoke de NiceGUI, no regression visual Playwright — el muro
documentado no coincide con el muro real.

---

## Inventario de jobs en tests.yml vs. docs/flujo-de-trabajo.md

| Job (nombre exacto) | Que corre | Runner | Trigger | Documentado en flujo-de-trabajo.md |
|---|---|---|---|---|
| `lint` | `ruff check .` + `ruff format --check .` | ubuntu-latest | push + PR | Si (job 1) |
| `audit` | `tools/auditar-radius.ps1 -Range ...` (blast-radius §8 sobre rango del PR) | ubuntu-latest | **solo PR** | Si (job 3) |
| `docs-graph` | `tools/auditar.ps1 -Bloquea` (grafo product/ + engineering/) | ubuntu-latest | push + PR | Si (job 2) |
| `pytest` | pytest matrix 3.10 / 3.11 / 3.12 (--ignore=tests/ui/visual) | windows-latest | push + PR | Si (job 4) |
| `visual-smoke` | Import smoke de modulos ng_* (NiceGUI); **sin Playwright** | ubuntu-latest | push + PR | Si (job 5), pero docs dicen "screenshot Playwright" — DISCREPANCIA |
| `build-installer` | Bundle PyInstaller / Windows | windows-latest | **solo tags v*** | No documentado como job de CI de PR |

**Total jobs documentados:** 5 (lint, docs-graph, audit, pytest, visual-smoke)
**Total jobs reales:** 6 (los 5 + build-installer)
**Discrepancia conceptual:** flujo-de-trabajo.md linea 211 describe `visual-smoke` como "screenshot del Paso 0 contra baseline; truena si el layout se movio respecto al baseline". El yml solo verifica que los imports de `ng_app`, `ng_state`, `ng_helpers`, `ng_step0-4` y `hud_preview` no lanzan excepcion.

---

## Required checks — estado real del ruleset "Protect master" (id 18321394)

Ruleset activo desde 2026-06-30, enforcement: `active`, condicion: `~DEFAULT_BRANCH` (master).

| Job | Required check | Fuente |
|---|---|---|
| `lint` | **SI** | ruleset id 18321394 |
| `docs-graph` | **SI** | ruleset id 18321394 |
| `pytest (3.10)` | **SI** | ruleset id 18321394 |
| `pytest (3.11)` | **SI** | ruleset id 18321394 |
| `pytest (3.12)` | **SI** | ruleset id 18321394 |
| `visual-smoke` | **SI** | ruleset id 18321394 |
| `audit` | **NO** | ausente del ruleset — brecha critica |
| `build-installer` | N/A | solo corre en tags `v*`, fuera del scope de PR |

Reglas adicionales del ruleset: deletion bloqueado, non-fast-forward bloqueado, PR requerido
(0 reviewers, `squash` como unico merge method), strict status checks (la rama base debe estar
al dia antes de mergear).

---

## Hallazgos por severidad

### CRITICO

**C-1: `audit` no es required check — el muro de blast-radius §8 en PR es cosmético.**

El job `audit` corre `tools/auditar-radius.ps1` sobre el diff del PR (commits entre `origin/<base>` y
`HEAD`). Segun ADR 0019 y el comentario en tests.yml (linea 12), debe ser required para cerrar la
ventana que el hook local (`pre-push --no-verify` saltable) y `verificar.ps1` no cubren. Hoy un PR
puede mergear aunque `audit` salga rojo; el bypass de docs §8 que el hook local bloquea se puede
colar por la ruta PR si nadie lo nota.

**Accion del PO:** en GitHub UI ir a Settings > Rules > "Protect master" > editar > Required status
checks > agregar `audit`.

Comando de verificacion (cuenta ArmandoMedina):
```
gh api repos/ArmandoMedina/SimGhostInputs/rulesets/18321394
```
Debe aparecer `{"context":"audit","integration_id":15368}` en la lista.

---

### MEDIO

**M-1: `visual-smoke` en el ruleset pero su implementacion no es regression visual.**

El job esta marcado required y es util (atrapa errores de importacion de la UI v2.0). Sin embargo
la documentacion dice que es un "screenshot Playwright contra baseline" y en realidad es un
`python -c "from fantasma.ui import ng_app, ..."`. La nota en el yml lo aclara: "Playwright
completo contra NiceGUI se agrega en un PR posterior al merge." El problema es que `flujo-de-trabajo.md`
no refleja eso — promete un muro que no existe todavia.

**Riesgo:** una regresion visual de layout puede pasar el CI y el ruleset sin ser detectada hasta QA manual.

**Accion:** actualizar `flujo-de-trabajo.md` (seccion Paso 3, job 5) para decir que hoy es import-smoke
y que Playwright se agrega post-merge v2.0. No cambiar el ruleset — el job es valido como esta.

**M-2: HANDOFF describe como pendiente algo que ya esta hecho.**

HANDOFF.md linea "Accion pendiente del PO" lista: "Marcar `audit`, `docs-graph`, `lint` y `pytest`
como required checks." La realidad al 2026-07-03: `docs-graph`, `lint`, `pytest (3.10/3.11/3.12)` y
`visual-smoke` YA estan en el ruleset (actualizado 2026-06-30T12:29:50). Solo falta `audit`.

**Accion:** actualizar HANDOFF para reflejar solo el pendiente real (`audit`).

---

### BAJO

**B-1: Cuenta gh activa no es la propietaria del repo.**

La cuenta activa durante la auditoria es `Armandomedina9705`; la propietaria es `ArmandoMedina`
(inactiva). La API de rulesets funciono porque el repo es publico. Para el merge y el push a master
el HANDOFF ya indica `gh auth switch --user ArmandoMedina` — este paso sigue siendo correcto y
necesario.

**B-2: No hay CI runs recientes para `codex/sgi-v2-merge`.**

`gh run list --limit 10` no muestra ningun run de esta rama. El workflow solo dispara en
`push: branches: [master]` y `pull_request: branches: [master]`; como la rama no tiene PR abierto
contra master, no hay evidencia de CI en GitHub Actions. El HANDOFF afirma "CI en verde" basandose
en ejecucion local (`verificar.ps1`, 201 tests). Los ultimos runs publicos son de 2026-07-01
(feature/pacenotes: verde en todos los jobs; worktree-agent NiceGUI: rojo en `lint` por ruff check,
verde en pytest/visual-smoke/docs-graph). La afirmacion del HANDOFF no es falsificable desde CI
externo sin crear el PR.

---

## Recomendacion sobre visual-smoke como required check

**Veredicto: mantenerlo en el ruleset, con nota de upgrade pendiente.**

Razones:
1. El job actual (import smoke) es un muro util y determinista: si los modulos NiceGUI no importan,
   el PR no puede mergear. Eso es valor real.
2. Eliminarlo del ruleset abriria una ventana temporal de "no hay muro de UI en el CI" que es peor
   que tener un muro parcial.
3. Cuando se agregue Playwright real (PR posterior al merge), el job existente se reemplaza in-place
   y el ruleset sigue valido — cero cambios en la configuracion de GitHub.

Lo que SI debe hacerse: corregir la documentacion para no prometer regression visual cuando solo
se hace import smoke. El muro real de layout es QA manual (Mariana) hasta que Playwright entre.

---

## Estado de CI en los ultimos 10 runs (2026-07-01)

| PR / rama | Run ID | Resultado | Jobs fallidos |
|---|---|---|---|
| feature/pacenotes #14 | 28527274606 | **verde** | ninguno |
| worktree-agent NiceGUI #13 | 28527229087 | rojo | `lint` (ruff check) |
| worktree-agent NiceGUI #13 | 28526603118 | rojo | `lint` |
| worktree-agent NiceGUI #13 | 28525483071 | rojo | `lint` |
| worktree-agent NiceGUI #13 | 28525019288 | rojo | `lint` |
| worktree-agent NiceGUI #13 | 28522219936 | rojo | `lint` |
| feature/pacenotes #14 | 28522187589 | **verde** | ninguno |
| worktree-agent NiceGUI #13 | 28521681069 | rojo | `lint` |
| feature/pacenotes #14 | 28521679381 | **verde** | ninguno |
| feature/pacenotes #14 | 28520457750 | **verde** | ninguno |

El worktree-agent (rama de migracion NiceGUI) tuvo 6 intentos fallidos consecutivos en `lint`
(ruff check) antes de ser abandonado o corregido. El PR #14 (pacenotes) pasa consistentemente.
No hay runs de `codex/sgi-v2-merge`.

---

## Comandos exactos para el PO (cuenta ArmandoMedina)

```powershell
# 1. Verificar cuenta activa
gh auth status

# 2. Cambiar a la cuenta propietaria si es necesario
gh auth switch --user ArmandoMedina

# 3. Ver el ruleset actual
gh api repos/ArmandoMedina/SimGhostInputs/rulesets/18321394

# 4. Para agregar 'audit' como required check, usar la UI de GitHub:
#    github.com/ArmandoMedina/SimGhostInputs/rules/18321394
#    (la API de edicion de rulesets requiere PATCH con el body completo)
```

---

## Resumen ejecutivo

| Item | Estado |
|---|---|
| Ruleset activo en master | SI ("Protect master", enforcement: active) |
| lint required | SI |
| docs-graph required | SI |
| pytest (3.10/3.11/3.12) required | SI |
| visual-smoke required | SI (import smoke, no Playwright) |
| audit required | **NO — unica brecha critica** |
| Doc. de visual-smoke precisa | **NO — docs dicen Playwright, yml hace import-smoke** |
| HANDOFF pendiente preciso | **NO — lista 4 jobs como pendientes; solo 1 lo esta** |
| CI runs de codex/sgi-v2-merge | No verificables — no hay PR abierto contra master |
