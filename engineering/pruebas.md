---
tipo: pruebas
estado: vigente
---

# Pruebas — la verificación viva

Las pruebas son la otra mitad del método: la doc dice qué *debería* hacer el sistema; los tests
confirman que lo *hace*. **El criterio de aceptación de una capacidad se materializa como test** —
el test ES el criterio, ejecutable. Eso es lo que vuelve seguro dirigir código que no se lee línea
por línea.

> **Dueño de la decisión (SSOT):** el *porqué* y el enfoque detallado (qué se automatiza vs qué es
> manual, los Tiers, las alternativas descartadas) viven en [ADR 0003](../docs/decisions/0003-testing.md).
> Esta nota es la vista navegable; no duplica esa decisión, la enlaza. El *cuándo corre cada barrera*
> (local avisa, CI bloquea) vive en [`../docs/flujo-de-trabajo.md`](../docs/flujo-de-trabajo.md).

## La regla operativa

- **Antes de cerrar un cambio de comportamiento, corre `pytest`.** Verde es condición para
  commitear/pushear; un rojo se **diagnostica**, no se silencia.
- **Si añades o cambias lógica determinista, el cambio incluye su test** — no es "para después".
- **Si un bug se cuela, se blinda con un test de regresión** (un bug que no se detecta, vuelve).

## Qué se automatiza vs qué es QA manual (el límite semántico)

La regla de oro: **automatiza lo determinista (misma entrada → misma salida); prueba a mano lo que
depende del entorno, lo visual y lo subjetivo.** Ningún chequeo determinista garantiza que el HUD
"se vea bien" o que la sincronía "se sienta" bien — eso es juicio humano (QA con telemetría y video
reales). La máquina no lo reemplaza: lo **aligera**. Detalle y tabla de decisión en [ADR 0003](../docs/decisions/0003-testing.md).

## Estructura (espejo del paquete)

`tests/` espeja `fantasma/`. La pieza central es `make_lap()` en `conftest.py`: un constructor de
`Lap` sintética y determinista (perfil de velocidad controlado, canales opcionales por parámetro) —
nunca telemetría real (principio "motor sin datos").

| Capa | Cubre | Carpeta |
|---|---|---|
| **Tier 1** — `core/` puro | normalize, compare, corners, wear (aritmética: el valor del producto) | `tests/core/` |
| **Tier 2** — `importers/` | parseo CSV con fixtures diminutos (único dato versionado) | `tests/importers/` |
| **Tier 3** — helpers puros de `viz/` | `_build_filter`, `_nvenc_available`, aritmética de `sync` — **sin invocar ffmpeg** | `tests/viz/` |
| **Tier 4** — smoke de UI | tests estructurales NiceGUI (fixture `user`): la UI arranca y los elementos clave existen | `tests/ui/` |
| **Visual** — smoke de layout | screenshot del Paso 0 vs baseline (Playwright); dueño: Mariana | `tests/ui/visual/` ([ADR 0012](../docs/decisions/0012-playwright-smoke-visual-ui.md)) |

> El conteo vivo de tests y el estado de cobertura están en [`../HANDOFF.md`](../HANDOFF.md) y
> [`../ROADMAP.md`](../ROADMAP.md), no aquí (para no desincronizar).

## Cómo correr

```powershell
pip install -e ".[test,ui-ng,sync]"
pytest                       # toda la suite
./tools/verificar.ps1        # lint + formato + tests + doc-gate, en modo aviso
```

## Gate de UX/UI (la interfaz)

Lo medible de la UI (layout, contraste, estructura) **bloquea en CI** como los tests; lo subjetivo es
**checkpoint de Mariana** que vuelve al PO (no auto-pase). Decisión en [ADR 0014](../docs/decisions/0014-gate-ux-ui.md);
rúbrica en [`../docs/ux-patterns.md`](../docs/ux-patterns.md).

## Relacionado con
- [[arquitectura]]
- [ADR 0003 — Estrategia de pruebas](../docs/decisions/0003-testing.md)
- [Flujo de trabajo (barreras)](../docs/flujo-de-trabajo.md)
