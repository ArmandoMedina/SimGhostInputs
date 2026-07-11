# QA run - Actualizar nucleo Jidoka 0.10.1-beta -> 0.13.0-beta

Fecha: 2026-07-11
Rama: jidoka/actualizar-nucleo-0.13
Repo: SimGhostInputs (SGI)

## Objetivo

Traer la mecanica generica de SGI a Jidoka 0.13.0-beta y corregir el bug del
sello (4 piezas code-first grabadas como semilla pristina), SIN sobreescribir las
customizaciones code-first de SGI (Python/ruff/pytest y el gate local).

## 1. Correccion del sello (pre-Actualizar)

Se eliminaron de `tools/jidoka-motor.json` -> `sembrado_hashes` las 4 claves cuyo
childHash==seedHash habrian sido clasificadas "el hijo no lo toco -> actualiza",
sobreescribiendo el gate code-first de SGI:

- tools/verificar.ps1
- tools/auditar.ps1
- tools/probar-hooks.ps1
- .githooks/pre-push

Con seedHash=null, -Actualizar las clasifica DIVERGE y las preserva.

## 2. Salida COMPLETA de -Actualizar

```
== Actualizar motor: hijo en Jidoka 0.10.1-beta -> Jidoka 0.13.0-beta ==
  [DIVERGE] tools/verificar.ps1 -> se dejo tools/verificar.ps1.jidoka-nuevo (revisa a mano)
  [DIVERGE] tools/auditar.ps1 -> se dejo tools/auditar.ps1.jidoka-nuevo (revisa a mano)
  [NUEVO]  tools/probar-gate.ps1
  [DIVERGE] tools/probar-hooks.ps1 -> se dejo tools/probar-hooks.ps1.jidoka-nuevo (revisa a mano)
  [ACTUALIZA] .claude/hooks/gemba-stop.ps1
  [NUEVO]  .claude/commands/jidoka/arranca.md
  [NUEVO]  .claude/commands/jidoka/cierra.md
  [NUEVO]  .claude/commands/jidoka/desatendido.md
  [NUEVO]  .claude/commands/jidoka/gemba.md
  [NUEVO]  .claude/commands/jidoka/planea.md
  [NUEVO]  .claude/commands/jidoka/que-sigue.md
  [NUEVO]  .claude/skills/arquitecto-doc/SKILL.md
  [DIVERGE] .claude/skills/escribano/SKILL.md -> se dejo .claude/skills/escribano/SKILL.md.jidoka-nuevo (revisa a mano)
  [NUEVO]  .claude/skills/revisor-visual/SKILL.md
  [NUEVO]  .claude/skills/validador/SKILL.md
  [DIVERGE] .githooks/pre-push -> se dejo .githooks/pre-push.jidoka-nuevo (revisa a mano)
  [NUEVO]  .github/workflows/andon.yml
  [NUEVO]  docs/guias/entorno-windows-powershell51.md
  [NUEVO]  kanban/ (auditoria, desatendido, estados, homologacion, jerarquia, lazo, README, roles, verificacion)
  [NUEVO]  andon/README.md
  [NUEVO]  doctrina/ (00-tesis .. 07-receta-de-traslado, citas-verificadas, README, decisiones/0001..0004 + README)
  [NUEVO]  kit/.jidoka/templates/ (adr, desatendido, plan-de-trabajo, PRODUCT_BRIEF, README, recursos, sprint-entrega, sprint-plan, producto/*)
  [NUEVO]  kit/.jidoka/disparos/README.md
  [NUEVO]  kit/.jidoka/qa_runs/README.md

== Motor: 8 al dia | 1 actualizado(s) | 59 nuevo(s) | 5 divergen ==
Divergencias (el hijo customizo estas piezas de mecanica; se preservaron):
  - tools/verificar.ps1
  - tools/auditar.ps1
  - tools/probar-hooks.ps1
  - .claude/skills/escribano/SKILL.md
  - .githooks/pre-push
Instancia (ley, product/, HANDOFF, ADRs) intacta: -Actualizar solo toca la mecanica.
```

## 3. Sidecars .jidoka-nuevo: BORRADOS (5)

No se adoptan las versiones genericas de Jidoka de las piezas code-first ahora.
La reconciliacion (via una costura verificar.local.ps1) esta DIFERIDA a post-1.0.

- .claude/skills/escribano/SKILL.md.jidoka-nuevo
- .githooks/pre-push.jidoka-nuevo
- tools/auditar.ps1.jidoka-nuevo
- tools/probar-hooks.ps1.jidoka-nuevo
- tools/verificar.ps1.jidoka-nuevo

## 4. Back-outs (piezas nuevas incompatibles)

### tools/probar-gate.ps1 -> BACK-OUT (borrado)

El probar-gate.ps1 de Jidoka invoca `verificar.ps1 -Cambiados <lista>`. El
verificar code-first de SGI NO soporta `-Cambiados` (solo -Base/-Manifiesto/-Repo):
ignora el splat y corre el pipeline completo (ruff+pytest) en cada caso, asi que
6 de 10 casos fallan. Evidencia:

```
== Prueba de humo del Andon (tools/verificar.ps1) ==
  [FALLA] limpio: cambio fuera de las areas cubiertas (ley real) (exit 1, esperaba 0)
  [PASA]  bloquea: ADR nuevo sin listar en el indice (ley real)
  [FALLA] pasa: ADR nuevo listado en el indice en el mismo cambio (ley real) (exit 1, esperaba 0)
  [FALLA] avisa: comando /jidoka:* nuevo sin CHANGELOG (area ritual, ley real) (exit 1, esperaba 0)
  [FALLA] bloquea: doc_bloquea faltante (manifiesto sintetico) (exit 0, esperaba 1)
  [FALLA] avisa: area tocada sin el grafo de producto (product_avisa sintetico) (la salida no contiene '[AVISO]')
  [PASA]  pasa: area tocada CON su nota de producto (product_avisa sintetico)
  [PASA]  falla cerrado: base de git inexistente (no aprueba a ciegas)
  [FALLA] fixture README: esperaba bloqueo (exit 1 + [BLOQUEA]); fue exit 0
  [PASA]  fixture README: ADR listado en el indice -> pasa (exit 0)
== 6 de 10 caso(s) fallidos. ==
```

DIFERIDO a refactor post-1.0 (junto a la reconciliacion verificar.local.ps1).

### .github/workflows/andon.yml -> BACK-OUT (borrado)

SGI ya tiene `.github/workflows/tests.yml` con un job `audit` (auditar-radius.ps1
sobre el rango del PR) y un job docs-graph (auditar.ps1 -Bloquea). andon.yml
duplicaria esa CI y ademas invoca `probar-gate.ps1` (que se saco). Se borra para
evitar CI duplicada/en conflicto.

## 5. gemba-stop.ps1: REVERTIDO a la version de SGI (VARA)

`gemba-stop.ps1` se clasifico [ACTUALIZA] (SGI no lo habia tocado; child==seed).
Pero su nueva version 0.13 exige evidencia GIT-TRACKEADA en qa_runs/, mientras el
`probar-hooks.ps1` code-first preservado de SGI escribe evidencia solo en disco.
Resultado: probar-hooks quedaba ROJO (1/10 fallando: "gemba-stop: DEJA cerrar con
evidencia fresca"). Para no dejar un self-test rojo (vara), se revirtio
gemba-stop.ps1 a la version de SGI (`git checkout master -- .claude/hooks/gemba-stop.ps1`,
hash 14E8FDDE...). El sello conserva el hash de Jidoka (A84A52A...), asi que la
proxima -Actualizar lo vera DIVERGE y lo preservara. Su convergencia va con el
mismo lote de reconciliacion de hooks post-1.0.

## 6. Verificacion EN VERDE (evidencia)

| Prueba | Resultado |
|---|---|
| pytest | 453 passed, 11 skipped in 32.76s (exit 0) |
| ruff check . | All checks passed! |
| ruff format --check . | 81 files already formatted |
| tools/probar-hooks.ps1 | Hooks sanos: 10/10 (exit 0) |
| tools/probar-auditor.ps1 | Auditor sano: 5/5 (exit 0) |
| tools/auditar.ps1 | Grafo de docs integro (exit 0) |
| tools/estado-motor.ps1 -Jidoka C:\Repositorios\jidoka | Tu motor 0.13.0-beta = Jidoka 0.13.0-beta -> [OK] al dia (exit 0) |

Nota estado-motor: compara SOLO la version del sello vs Jidoka/tools/version.txt
(no hashes por archivo). Reporta 0.13.0-beta al dia correctamente. Las
divergencias por-archivo se registran en el sello (child != hash de Jidoka) y las
surtira -Actualizar, no estado-motor.

## 7. Clasificacion final de piezas

- Preservadas (DIVERGE, code-first): tools/verificar.ps1, tools/auditar.ps1,
  tools/probar-hooks.ps1, .githooks/pre-push, .claude/skills/escribano/SKILL.md,
  .claude/hooks/gemba-stop.ps1 (revertida).
- Agregadas y conservadas: .claude/commands/jidoka/* (6), .claude/skills/
  {arquitecto-doc,revisor-visual,validador}, docs/guias/entorno-windows-powershell51.md,
  y los dirs de referencia kanban/, andon/, doctrina/, kit/.jidoka/{templates,disparos,qa_runs}/.
- Agregadas y back-out: tools/probar-gate.ps1 (incompatible con verificar code-first),
  .github/workflows/andon.yml (duplica CI de tests.yml).
- Al dia (8): settings.json, hooks andon-stop/no-memorias/review-stop, workflows
  installer/release/tests, auditar-radius, probar-auditor, reportar-leccion, guia
  reportar-leccion (segun el resumen del motor).
