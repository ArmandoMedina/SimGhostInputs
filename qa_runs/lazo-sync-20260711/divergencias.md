# Reporte de divergencia del motor — SGI vs Jidoka (lazo labs↔Jidoka)

- **Fecha:** 2026-07-11
- **Jidoka de referencia:** 0.10.1-beta (la versión a la que SGI convergió, ADR 0034/0035).
- **Método:** se leyeron ambos árboles y se comparó pieza por pieza el motor. Clasificación
  por `Get-FileHash -Algorithm SHA256` (idéntica = mismo hash) + lectura del diff para nombrar
  *en qué* difiere.

> **Regla del cliente que este reporte hace visible:** la **mecánica** (lógica de
> verificar/auditar/hooks/gate) converge e idéntica; la **estética/instancia** (comandos con
> layout propio, skills con nombre de persona, ley, `product/`, ADRs, HANDOFF) NUNCA se
> sobrescribe. La divergencia se **detecta y se preserva**, no se pisa.

## Tabla de comparación

| Pieza en Jidoka | Equivalente en SGI | Clasificación | En qué difiere |
|---|---|---|---|
| `tools/verificar.ps1` | `tools/verificar.ps1` | **diverge-dominio** | SGI es un **pipeline no-mistakes de stack Python**: corre `ruff check`, `ruff format --check`, `pytest` y cobertura de tests (AVISAN), y BLOQUEA por doc-gate + auditor del grafo. Jidoka es solo el Andon del doc-gate (blast-radius). Además SGI **carece del parámetro `-Cambiados`** (inyección de lista de archivos sin git) que Jidoka sí tiene — esta es la costura que impide portar `probar-gate.ps1` (ver lección). Ambos comparten falla-cerrado (exit 2). |
| `tools/auditar.ps1` | `tools/auditar.ps1` | **diverge-dominio** | SGI audita `product/ + engineering/` (tiene carpeta `engineering/`, ADR 0015) y referencia la sección 8 de `CONTRIBUTING`; Jidoka escanea `product/ + docs/ + kanban/ + doctrina/ + kit/`. Misma lógica de auditor (frontmatter, wikilinks, criterios Gherkin, modulación por estado); difieren los **árboles-destino** por el layout de cada instancia. |
| `tools/probar-hooks.ps1` | `tools/probar-hooks.ps1` | **idéntica** | Byte-idéntico (self-test de los hooks). |
| `tools/probar-auditor.ps1` | `tools/probar-auditor.ps1` | **idéntica** | Byte-idéntico (self-test del auditor). |
| `tools/probar-gate.ps1` | *ausente* | **ausente-en-SGI** | SGI no lo tiene: no pudo portarse porque su `verificar.ps1` no acepta `-Cambiados` (ADR 0035, "pendiente diferido a sesión humana"). Ítem de **convergencia/bajada** (ver `leccion-probar-gate-convergencia.md`). |
| `tools/estado-motor.ps1` | `tools/estado-motor.ps1` | **idéntica** (recién sembrada) | Ausente hasta hoy; **copiada byte-idéntica desde Jidoka por este lazo**. Es aviso de divergencia del motor, no muro. |
| `.claude/settings.json` | `.claude/settings.json` | **idéntica** | Byte-idéntico (cableado de hooks del método). |
| `.claude/hooks/andon-stop.ps1` | idem | **idéntica** | Byte-idéntico. |
| `.claude/hooks/gemba-stop.ps1` | idem | **idéntica** | Byte-idéntico (neutral; filtra `rol: revisor-visual`, ADR 0034). |
| `.claude/hooks/no-memorias-pretooluse.ps1` | idem | **idéntica** | Byte-idéntico. |
| `.claude/hooks/review-stop.ps1` | idem | **idéntica** | Byte-idéntico (data-driven, lee `revisa: true`). |
| `.claude/commands/jidoka/*` (arranca, cierra, desatendido, gemba, planea, que-sigue) | `.claude/commands/*` (mismos nombres, **sin subcarpeta `jidoka/`**) | **diverge-estética** | Mismo set de comandos, **layout distinto**: SGI los tiene en la raíz de `commands/` (sin namespace `jidoka/`). El contenido además referencia las personas y rutas propias de SGI (`/arranca` re-homologado, ADR 0035). Estética/instancia: nunca se pisa. |
| `.claude/skills/*` (arquitecto-doc, escribano, revisor-visual, validador — **nombres de asiento neutral**) | `.claude/skills/*` (ahiram, armando, charbel, mariana, escribano — **nombres de persona**) | **diverge-estética** | El casting de SGI usa nombres de persona; Jidoka usa el asiento neutral. El mapeo es explícito (ADR 0035): ahiram→desarrollador, armando→arquitecto-doc, charbel→validador, mariana→revisor-visual, escribano→escribano. La autoridad la da la ley (tokens de rol genéricos), no el nombre. Estética/casting: nunca se pisa. |
| `.githooks/pre-push` | `.githooks/pre-push` | **diverge-dominio** | SGI usa `#!/usr/bin/env bash` con **fallback** si `powershell.exe` no está y **sale 0 siempre** (modo aviso puro, "avisa temprano, bloquea al final"); Jidoka usa `#!/bin/sh` y `exit $?` (propaga el veredicto local). Diferencia de política del hook local; el muro real en ambos es el required check del CI. |
| `.github/workflows/andon.yml` | `.github/workflows/tests.yml` (+ `release.yml`, `installer.yml`) | **diverge-dominio** | SGI no tiene `andon.yml`: su CI equivalente es `tests.yml`, partido en jobs `lint` (ruff), `audit` (blast-radius, `auditar-radius.ps1`), `docs-graph` (`auditar.ps1 -Bloquea`) y `pytest` — todos marcados como required checks server-side. Es el mismo rol (barrera determinista sobre el artefacto) instanciado para el stack Python de SGI. `release.yml`/`installer.yml` son producto de SGI (no motor de método). |

## Convergencia pendiente vs estética legítima

**Convergencia pendiente (mecánica que SGI debería *bajar* cuando exista la costura):**

- `verificar.ps1` **`-Cambiados`** + **`probar-gate.ps1`**: Jidoka ya resolvió inyectar la lista de
  archivos al gate y trae el self-test del gate. SGI no pudo portarlo porque exigía **editar su
  propio gate** (reservado a sesión humana, ADR 0035). Este es el ítem de bajada más claro: es una
  brecha real de método que ahora tiene mecanismo (ver `leccion-probar-gate-convergencia.md`).
- Cualquier arreglo futuro de la **lógica común** (auditor, hooks, self-tests) vive **una vez** en
  Jidoka y baja por `./tools/instalar.ps1 -Actualizar`. Las piezas hoy **idénticas** (hooks,
  `settings.json`, `probar-hooks`, `probar-auditor`, `estado-motor`) son las que ese `-Actualizar`
  puede re-sembrar sin conflicto.

**Estética/instancia legítima de SGI (nunca se toca):**

- El **casting de personas** (`ahiram/armando/charbel/mariana/escribano`) y el **layout de comandos**
  sin namespace `jidoka/`: son la piel de SGI. El asiento neutral vive en los tokens de la ley, no en
  el nombre de la carpeta.
- El **dominio del pipeline** de `verificar.ps1` (ruff/pytest/cobertura) y de `auditar.ps1`
  (`product/ + engineering/`), el `pre-push` en bash con fallback, y el CI multi-job `tests.yml` +
  `release.yml`/`installer.yml`: son la realidad de que SGI es una app Python con instalador Windows.
  Auto-`-Actualizar` que los pisara sería una regresión (perdería las barreras de stack).

La frontera es limpia: **lo idéntico converge y puede re-sembrarse; lo que diverge por dominio o
estética se detecta, se registra aquí, y se preserva.**

## Evidencia: `tools/estado-motor.ps1 -Jidoka C:\Repositorios\jidoka`

Salida cruda guardada en [`estado-motor.txt`](estado-motor.txt):

```
== Estado del motor Jidoka ==
  Tu motor: Jidoka 0.10.1-beta
  Jidoka actual: 0.11.0-beta
  [AVISO] Tu sello (0.10.1-beta) difiere de Jidoka (0.11.0-beta): probablemente estas atras.
          Baja la mecanica (desde el repo Jidoka, apuntando aca):
            ./tools/instalar.ps1 -Destino 'C:\Repositorios\SimGhostInputs' -Actualizar
          Corre en una rama -> revisa el diff -> PR (el diff ES la revision).
```

> **Nota honesta (requiere decisión humana).** El plan de este lazo esperaba que estado-motor dijera
> **"al dia"** porque ambos repos estaban en **0.10.1-beta**. Al momento de correrlo, el checkout de
> Jidoka está en una **rama paralela en-vuelo** (`lazo-sincronizacion-labs`) con `tools/version.txt`
> **sin commitear** ya subido a **0.11.0-beta**. Por eso el aviso dice "atrás" en vez de "al dia".
> Esto **no es un fallo del lazo — es el lazo funcionando**: detecta que existe una Jidoka más nueva
> y ofrece la bajada. El sello de SGI se mantiene honesto en **0.10.1-beta** (el punto de convergencia
> real de ADR 0035); cuando 0.11.0-beta se publique, la bajada se evalúa en rama con `-Actualizar`
> revisando el diff. **Decisión humana:** confirmar si SGI adopta 0.11.0-beta o espera a que se libere.
