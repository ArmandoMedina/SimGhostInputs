# ADR 0019 — Adopción de la homologación con project-starter v0.5.0 (cierra la Fase 4)

- **Estado:** Aceptada · enmend. 2026-07-03
- **Fecha:** 2026-07-01
- **Relacionada con:** [ADR 0011](0011-cablear-mariana-no-charbel.md), [ADR 0016](0016-gate-grafo-documentacion.md)

## Contexto

El [ADR 0016](0016-gate-grafo-documentacion.md) dejó declarada la **Fase 4: backport a `project-starter`**. Esa pasada se ejecutó el 2026-07-01 en el starter (su release **v0.5.0 "la pasada de homologación"**, ADRs 0033–0037 del starter): lo que este repo maduró ascendió a la plantilla **como máquina, no como prosa** — y en el camino el starter generalizó y mejoró varias piezas que nacieron aquí. Este ADR registra la **vuelta**: qué adopta SGI de regreso.

Los dolores que motivaron cada pieza son de las sesiones de ESTE repo: el "probé clic por clic" sin rastro conviviendo con la UI rota a ojo; "¿por qué te tengo que decir yo dónde está el freno?"; "nada de memorias, todo al repo" repetido cuatro veces; la ruta del material de pruebas dictada tres veces; los PRs verdes con docs desfasadas (jobs no requeridos); los cortes por tokens y el resumen de compactación que mintió (`storage.user` vs `storage.client`).

## Decisión

Se adoptan de la v0.5.0 del starter, adaptadas a este repo (criterio, no copia):

1. **Matcher del manifiesto homologado** (starter ADR 0033): un patrón sin `/` solo casa la raíz; campos opcionales `excluye` y `mensaje`. Área nueva **`raiz`** en `tools/blast-radius.json`: los archivos sueltos en la raíz dejan de ser tierra de nadie.
2. **`tools/auditar-radius.ps1` + job `audit` en CI** (starter ADR 0034): el blast-radius §8 se audita sobre el **rango del PR** — cierra la ventana que ni el hook (working tree) ni `verificar.ps1` (push local, saltable) cubren. **Regla anti-bypass:** todo aviso local se asume bypaseable; los jobs `audit`, `docs-graph`, `lint` y `pytest` deben ser **required checks** en el ruleset de master.
3. **Evidencia de QA verificable** (starter ADR 0035): `mariana-stop` deja de conformarse con el marcador y exige artefactos en `qa_runs/` **posteriores** al cambio visual. Convención `qa_runs/<rol>-<fecha>/` con README; el bulto se ignora, la evidencia citada se commitea. Un veredicto sin artefacto no vale.
4. **Contexto inyectado** (starter ADR 0036): hook `no-memorias` (PreToolUse que deniega escrituras a la memoria de Claude), `/arranca` con las reglas duras (delega / ciclo del HANDOFF / plan persistido / desconfiar de resúmenes / QA con evidencia), `docs/recursos-del-proyecto.md` con los datos reales re-dictados, recetario `docs/entorno-windows-powershell51.md` con versión corta **embebida en los 5 SKILL.md**, y `templates/plan-de-trabajo.md`.
5. **Correcciones operativas en skills:** los skills **no** son `subagent_type` (se spawnea subagente general con el SKILL.md en el prompt); el skill `armando` redacta notas **copiando su template**, nunca de cero.

**Enmienda al ADR 0016:** su pendiente "Backport a `project-starter` en la Fase 4" queda **cumplido** (starter v0.5.0, ADR 0032 del starter).

## El camino que NO se toma (y por qué tienta)

- **Copiar el `doc-gate-stop` genérico del starter en lugar del `escribano-stop` propio.** Tienta por uniformidad total. Se descarta: el de SGI ya está adaptado al casting con nombres y a su mensaje; se homologa el **matcher y el contrato**, no el archivo byte a byte (criterio, no copia).
- **Cablear el hook `revision-visual-stop` del starter además de `mariana-stop`.** Se descarta: sería el mismo gate dos veces; aquí Mariana **es** ese hook — se le sube la exigencia de evidencia en su propio archivo.
- **Confiar en el marcador de Mariana como hasta ahora.** Tienta porque "ya había checkpoint". Se descarta: el marcador prueba que alguien escribió un hash, no que hubo corrida — y el caso real (UI rota con "pruebas hechas") lo demostró.

## Consecuencias

- **Se gana:** el gate §8 queda auditado de punta a punta (sesión → push → PR); el QA visual deja rastro verificable; las reglas que se repetían a mano ahora tienen diente (hook) o se inyectan solas (`/arranca`, SKILL.md); los recursos del proyecto dejan de re-dictarse.
- **Se pierde / costo:** un job más de CI (solo PRs, barato); los hooks de sesión suman ~1s al cierre; el matcher raíz-sin-slash es un cambio de semántica del manifiesto (los patrones existentes con `/` no se ven afectados).
- **Acción manual pendiente del PO:** marcar `audit`, `docs-graph`, `lint` y `pytest` como **required checks** en el ruleset de master — sin eso, el punto 2 es cosmético (la regla anti-bypass lo dice: un rojo no-requerido deja pasar el merge).
- **Asientos dueños:** Armando (estructura/gates), Mariana (evidencia visual), Mau (reglas de sesión).

## Enmienda (2026-07-03) — método bajo carga: plan efímero, concurrencia y durabilidad de evidencia

La auditoría integral pre-v2.0.0 encontró tres grietas del método que este ADR no cerraba
(`qa_runs/2026-07-03-auditoria-integral/informe.md`, decisiones PO-5 y PO-6;
`fase3-adr0019.md` H1/H3/M2; `fase3-hooks.md` CRITICO-01/02). El PO las resuelve así:

### (a) El plan de trabajo es EFÍMERO — vive en la sesión, no se versiona

`templates/plan-de-trabajo.md` mandaba dos cosas opuestas: *"vive en el repo… se commitea"*
**y** *"se borra (es efímero)"* (`fase3-adr0019.md` M2). La práctica ejecutó ese churn: un
commit añadía el plan y otro del mismo día lo retiraba.

**Decisión (PO, 2026-07-03):** el plan de trabajo **NO se versiona**. Vive en la sesión / el
task-tracker mientras la tarea corre. Al morir la tarea:

- si dejó una **decisión** (se eligió un camino sobre otro) → va a un **ADR**;
- si dejó **estado en vuelo** al morir la sesión → va al **HANDOFF**;
- el resultado liberable → CHANGELOG.

El plan como archivo no entra al repo (ni siquiera a `docs/planes/`). `templates/plan-de-trabajo.md`
queda corregido para reflejar esto (deja de mandar "vive en el repo").

### (b) Una sola sesión ESCRITORA a la vez sobre el working tree

El método no contemplaba concurrencia (`fase3-adr0019.md` H3). Hoy dos sesiones operaron el
mismo working tree: el commit `73f5ac1` de una sesión paralela dejó **ciegos** los Stop hooks
de la otra —al momento del Stop el working tree estaba limpio, así que review-stop,
escribano-stop y mariana-stop pasaron sin revisar ese código commiteado
(`fase3-hooks.md` CRITICO-01/02).

**Decisión (PO, 2026-07-03):** **una sola sesión escritora a la vez** sobre un mismo working
tree. Si el PO abre una segunda sesión, esta es **solo-lectura**, o trabaja en **otra rama /
worktree** (`git worktree`). Los hooks de sesión leen `git status` del working tree; dos
escritoras sobre el mismo árbol producen lost-update del HANDOFF y puntos ciegos en los
gates. El HANDOFF tiene **dueño único** por rama/árbol.

### (c) La evidencia de QA se commitea con `git add -f qa_runs/<corrida>/` al cerrar cada corrida

El punto 3 de este ADR y `qa_runs/README.md` ya mandaban commitear la evidencia citada, pero
en la práctica **0 artefactos** llegaron a git (`git ls-files qa_runs/` → solo el README);
la evidencia vivía solo en la laptop y el "visual PASS" pre-merge quedó **inauditable desde
la historia** (`fase3-adr0019.md` H1). El hook `mariana-stop` verifica el working tree, no el
commit, así que un artefacto satisface el gate y luego se pierde.

**Decisión (PO, 2026-07-03):** commitear la evidencia citada con
`git add -f qa_runs/<corrida>/<archivo>` (solo lo citado, no el bulto) se **eleva a paso
obligatorio del cierre** de cada corrida de QA/auditoría —no una recomendación—. Un veredicto
en HANDOFF/CHANGELOG debe **citar** su directorio de corrida y ese directorio debe existir en
git. Sin artefacto commiteado, el veredicto no vale (mismo principio "sin auto-firmas" del
ADR 0016, ahora durable).
