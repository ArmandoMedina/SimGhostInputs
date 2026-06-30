# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## En una frase

Motor **offline** de análisis de telemetría sim racing (importar CSV de MoTeC → comparar vueltas por
distancia → reporte + overlay de video). Objetivo de fondo: cortar la **v1.0** (estabilizar, testear,
documentar, validar en AMS2 el pipeline que ya existe). **En vuelo ahora:** adopción de la estructura
`product/` + `engineering/` del método ([ADR 0015](docs/decisions/0015-estructura-product-engineering.md))
— refactor **documental**, no toca el motor; todo reversible por git.

## Estado actual (qué está hecho y validado)

- **v0.12.0** (2026-06-28). **121 tests verdes** (Tier 1-4 + smoke visual de UI). Pipeline offline
  completo: importar → comparar → overlay → componer. UI Streamlit ([ADR 0010](docs/decisions/0010-framework-ui-streamlit.md)).
- Capa de método ya viva: barreras `ruff`+CI (v0.10.0), doc-gate §8 + roles (v0.11.0), Mariana
  cableada ([ADR 0011](docs/decisions/0011-cablear-mariana-no-charbel.md)), smoke visual Playwright
  ([ADR 0012](docs/decisions/0012-playwright-smoke-visual-ui.md)).

| Pieza | Qué hace | Código | Validación |
|---|---|---|---|
| Motor de comparación | delta por distancia, curvas, tiempo perdido | `fantasma/core/` | tests Tier 1-2 verdes |
| Importadores | MoTeC CSV/XLSX, CSV genérico | `fantasma/importers/` | tests + 1 circuito AMS2 real |
| Overlay / compose | HUD alfa + ffmpeg/NVENC | `fantasma/viz/` | QA manual; tests de compose/overlay |
| Sincronía | offset por correlación de audio | `fantasma/viz/sync.py` | tests; pendiente repro 60fps |
| UI | Streamlit, pasos 0-4 | `fantasma/ui/` | smoke visual Paso 0 |

## Cómo correr

```powershell
pip install -e ".[full]"          # entorno completo
fantasma --help                   # CLI
fantasma ui                       # UI Streamlit
pytest                            # suite (121+)
./tools/verificar.ps1             # barreras locales (lint+formato+tests+doc-gate)
git config core.hooksPath .githooks   # una vez por clon: enciende pre-push
```

## Cosas que DEBES saber (o te tropiezas)

1. **`core/` e `importers/` son librería estándar pura** — sin matplotlib/scipy/openpyxl. Las deps
   viven en extras opcionales y degradan con gracia si faltan. No metas deps al núcleo (PRODUCT_BRIEF §8).
2. **Determinista:** misma entrada → misma salida. Solo lo determinista se automatiza como barrera;
   lo visual/subjetivo es QA manual ([ADR 0003](docs/decisions/0003-testing.md)).
3. **El cambio incluye su test** si toca comportamiento (`core/`, `importers/`, helpers puros de `viz/`).
4. **Doc-gate §8 BLOQUEA** en local si tocas `core/` sin `formato-datos.md`, `viz/` sin
   `hud-reference.md`, o las barreras sin `flujo-de-trabajo.md`. Pásalo al escribano.
5. **Entorno PS 5.1:** mensajes de commit multilínea a git → `git commit -F archivo`; `.ps1` con
   acentos → guardar con BOM. Ver `CLAUDE.md` global.

## Qué falta (próximos pasos, en orden de valor)

1. **Terminar la adopción de la estructura (plan en curso):** Fase 1 `engineering/` → Fase 2
   `product/` → Fase 3 casting + gate determinista (`tools/auditar.ps1`, §8 extendida) → Fase 4
   backport a `project-starter`. Cada fase commiteable y verde.
2. **QA AMS2 en ≥3 circuitos** — 1/3 (Nordschleife ✓). Faltan Interlagos y México (clases distintas
   al GT3); falta conseguir esas 2 telemetrías.
3. **`setup.ps1` en Windows 11 limpio** — en curso; plan de VMs limpias vía SSH a la PC potente (SERVER).
4. **Pulir HUD:** DESLIZ vs GASTO se confunden (misma franja). _Prioridad baja._
5. **Confirmar con video 60 fps real** que el overlay no desincroniza (sin repro hasta hoy).

## Mapa rápido del repo

```
product/        QUÉ  — ecosistema/solución/dominio/módulo/capacidad (criterios de aceptación)
engineering/    CÓMO — arquitectura + especificaciones + modelos de datos + pruebas
fantasma/       el código (core, importers, viz, ui, cli)
tests/          la suite (cada test = un criterio); espejo de fantasma/
docs/decisions/ ADRs — el porqué de cada decisión
docs/flujo-de-trabajo.md  el sistema de barreras explorar→commit→push
CONTRIBUTING.md §8  el doc-gate (matriz SSOT + router de roles)
```

---

> **Regla de continuidad:** la única "memoria" confiable entre sesiones amnésicas es lo escrito en
> el repo. Mantén este archivo al día como parte de cerrar un cambio — el escribano puede recordártelo.
