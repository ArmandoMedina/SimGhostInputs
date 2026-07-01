# ADR 0019 — Adopción de la homologación con project-starter v0.5.0 (cierra la Fase 4)

- **Estado:** Aceptada
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
