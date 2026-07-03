---
tipo: plan-de-trabajo
estado: en_curso
---

# Plan — Auditoría integral pre-release v2.0.0 (código + documentación + metodología IA)

> Contexto: la rama `codex/sgi-v2-merge` está declarada lista para mergear (201 tests verdes,
> CI verde). Antes del merge + tag v2.0.0, el PO pidió una auditoría integral con tres
> dimensiones obligadas — **código**, **documentación** y **metodología de trabajo con IA** —
> más lo que el orquestador juzgue necesario (se añadió: **seguridad ligera** por ser repo
> público AGPL, y **preparación de release**). Todo se ejecuta vía subagentes (Mau orquesta,
> no ejecuta). Modelos por regla de calibración del flujo: mecánico→haiku, juicio acotado→sonnet,
> trade-offs→opus.

## Objetivo

Un informe consolidado de auditoría en `qa_runs/2026-07-03-auditoria-integral/informe.md` con
hallazgos priorizados (crítico/mayor/menor) y veredicto GO/NO-GO para el merge a `master` +
v2.0.0. Los hallazgos accionables quedan en HANDOFF/ROADMAP; las decisiones destapadas, como
ADRs; nada vive solo en la sesión.

## Pasos (cada uno commiteable y verde)

### Fase 0 — Cerrar lo en vuelo (prerrequisito)
- [x] Reviewer sobre el commit `73f5ac1` (render paralelo, escrito por otra IA) — subagente
      sonnet en curso. Verificación: reporte con veredicto + pytest/ruff reales.
- [x] Escribano §8 sobre ese cambio — hecho: `docs/hud-reference.md` ya venía en el commit;
      avisos (ux-patterns, OVL/CHT/CMPO/SYN) revisados sin cambio necesario.
- [ ] Commitear HANDOFF.md pendiente + este plan. Verificación: `git status` limpio.

### Fase 1 — Auditoría de CÓDIGO (subagentes paralelos)
- [ ] A1. Review por área: `core/`, `importers/`, `viz/`, `ui/`, `cli.py` — 1 subagente
      sonnet c/u, foco bugs/correctitud/calidad/muertes silenciosas. Entregan hallazgos
      numerados con severidad y archivo:línea.
- [ ] A2. Charbel (telemetría): validar `core/`+`importers/` contra material real
      (`C:\Repositorio personal\Paterial para test (no es un repo)`) — parseo, canales,
      rangos físicos, determinismo. Subagente sonnet con SKILL.md de charbel.
- [ ] A3. Salud de la suite (201 tests): ¿prueban lo correcto?, gaps por módulo vs los 6
      tiers del ADR 0003, tests que pasarían aunque el código estuviera roto. Sonnet.
- [ ] A4. Seguridad ligera: inputs no confiables (CSV/XLSX), rutas, invocación de
      ffmpeg/subprocess, pickle entre procesos. Sonnet.

### Fase 2 — Auditoría de DOCUMENTACIÓN (subagentes paralelos)
- [ ] B1. Gates deterministas: correr `tools/verificar.ps1` y `tools/auditar.ps1` y reportar
      salida real. Haiku (mecánico).
- [ ] B2. Drift SSOT §8: cada doc dueño vs el código real — README, guia-usuario,
      formato-datos, hud-reference, glosario, CONTRIBUTING §3, PRODUCT_BRIEF. 2-3 subagentes
      sonnet repartidos.
- [ ] B3. ADRs: índice completo, contradicciones código↔ADR, decisiones enterradas sin ADR
      (candidata ya detectada: patrón `d_offset` en `_render_chunk`, señalada por el
      Escribano). Sonnet.
- [ ] B4. Grafo `product/`+`engineering/` más allá del gate: huérfanos, criterios vagos,
      capacidades vigentes sin test citado. Sonnet.
- [ ] B5. Coherencia CHANGELOG ↔ ROADMAP ↔ HANDOFF ↔ `git log` (¿todo lo commiteado está
      contado?, ¿todo lo contado existe?). Haiku/sonnet.

### Fase 3 — Auditoría de METODOLOGÍA de trabajo con IA
- [ ] C1. Hooks de sesión (`.claude/hooks/*.ps1`): ¿cumplen lo que el flujo promete?,
      ventanas de bypass — incluida la recién vivida: un commit de sesión paralela satisface
      el gate sin que el Reviewer de esta sesión haya pasado. Sonnet.
- [ ] C2. Skills/asientos (`.claude/skills/*/SKILL.md`): límites claros, consistencia con la
      §8 y el casting del flujo. Sonnet.
- [ ] C3. `tools/blast-radius.json` vs tabla §8: espejo fiel + falsos positivos (detectado:
      cambio no-visual en `viz/` exige `hud-reference`). Sonnet.
- [ ] C4. Cumplimiento ADR 0019 en la historia reciente: ciclo HANDOFF, evidencia en
      `qa_runs/`, planes persistidos, model-routing, delegación de git. **Opus** (juicio de
      método con trade-offs).
- [ ] C5. CI y regla anti-bypass: jobs vs required checks del ruleset (con `gh`), qué es muro
      real vs cosmético. Sonnet.

### Fase 4 — Síntesis y cierre
- [ ] D1. Consolidar todos los reportes en `qa_runs/2026-07-03-auditoria-integral/informe.md`
      con severidades, veredicto GO/NO-GO pre-merge y lista de correcciones. **Opus.**
- [ ] D2. Correcciones críticas/mayores que el PO apruebe → Ahiram (código) / Armando o
      Escribano (docs), cada una con su test/verificación y commit propio.
- [ ] D3. Actualizar HANDOFF, marcar este plan `estado: cerrado` y borrarlo al cerrar la
      tarea (la plantilla lo manda); decisiones destapadas → ADRs.

## Decisiones tomadas en el camino

- (pendiente) ¿ADR para el patrón `d_offset` de `_render_chunk`? — señalado por el Escribano;
  decide el PO con el informe.
- (pendiente) ¿Ajustar `blast-radius.json` para que cambios no visuales de `viz/` no exijan
  `hud-reference`? — depende del hallazgo C3.

## Para retomar en frío

- Rama: `codex/sgi-v2-merge`. Último estado: commit `73f5ac1` + HANDOFF y este plan (ver
  `git log --oneline -3`).
- Los reportes parciales de subagentes NO sobreviven la sesión: cada fase que termina se
  vuelca a `qa_runs/2026-07-03-auditoria-integral/` (un .md por fase) y se commitea.
- Comando de estado: `git status`, `pytest -q` (espera 201 verdes), `./tools/verificar.ps1`.
- NO tocar `master` ni mergear: eso sigue requiriendo autorización explícita del PO.
