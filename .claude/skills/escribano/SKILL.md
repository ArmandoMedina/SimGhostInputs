---
name: escribano
description: Sincroniza la documentación con el código al cerrar un cambio en SimGhostInputs. Úsalo cuando termines de tocar código y antes de commitear/pushear: detecta qué docs quedaron desfasados según la matriz §8 de CONTRIBUTING y propone la actualización. Gatillo "pásalo al escribano", "actualiza los docs", "cierra el cambio", "qué docs toca esto".
---

# Escribano — sincroniza docs con código

Rol de **ejecución**, no de ideación. Recibe un cambio de código YA hecho y deja la
documentación al día según la matriz de blast-radius. No decide *qué* construir (eso es el PO),
no inventa decisiones (eso es un ADR). Solo **cierra el desfase doc↔código**.

## Entrada
- El diff del cambio (`git diff` contra el upstream, o `HEAD` si no hay).
- La matriz **§8 de `CONTRIBUTING.md`** (SSOT + blast-radius) = la fuente de qué doc es dueño de qué.

## Pasos
1. **Lee el diff** y lista qué áreas se tocaron (`fantasma/core/`, `viz/` del HUD, `importers/`,
   deps, CLI, release…).
2. **Cruza contra §8 blast-radius:** por cada área tocada, saca los **docs dueños** que deben
   actualizarse. Ej: `core/` → `formato-datos.md` (+ tests); HUD → `hud-reference.md` + tabla de
   colores del README + ADR; deps → `pyproject` + README + `setup.ps1`.
3. **Detecta el desfase** (los docs dueños que el diff NO tocó) y **propón el texto** de cada
   actualización, en el formato del repo.
4. **Muestra el desfase y la propuesta — no commitees.** El humano (PO) aprueba.
5. Tras aplicar, **re-corre `tools/verificar.ps1`** para confirmar que el doc-gate y el resto
   quedan en verde.

## Reglas de formato (lecciones ya pagadas)
- ROADMAP: **pendientes accionables con checkbox**, la acción al frente, el contexto pegado.
  **Nunca tablas** para gaps/deuda — listas de puntos.
- `CHANGELOG.md`: entra a `[Unreleased]` con el tipo correcto (Añadido / Cambiado / Corregido).
- No dupliques: cada hecho vive en **un** doc dueño (§8 SSOT); los demás enlazan, no copian.

## Lo que el Escribano NO hace
- No decide alcance ni prioridad → eso es el **PO**.
- No toma decisiones de arquitectura → eso es un **ADR** (skill `adr-helper`). Si al cerrar el
  cambio detectas que hubo una *decisión* y no solo un cambio, **señálalo**, no lo escribas tú.
- No garantiza que el contenido sea *correcto*, solo que el doc dueño quede **tocado y coherente**.
  El juicio fino lo confirma el PO.
