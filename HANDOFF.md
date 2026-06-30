# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## En una frase

Motor **offline** de análisis de telemetría sim racing (importar CSV de MoTeC → comparar vueltas por
distancia → reporte + overlay de video). Objetivo de fondo: cortar la **v1.0** (estabilizar, testear,
documentar, validar en AMS2 el pipeline que ya existe). **Nada en vuelo ahora** — punto de partida
limpio sobre v0.13.0.

## Estado actual (qué está hecho y validado)

- **v0.14.0** (2026-06-30). **126 tests verdes**. Pipeline offline completo: importar → comparar →
  overlay → componer. UI Streamlit ([ADR 0010](docs/decisions/0010-framework-ui-streamlit.md)).
- **QA de AMS2 cerrado (requisito de v1.0):** validado en 4 circuitos (Barcelona NC, Interlagos,
  Nordschleife 2025, Nürburgring GP) y clases más allá de GT3 (Hypercar, Fórmula F3, Prototipo/LMP2).
  El canal de distancia ahora es requisito duro con aviso temprano ([ADR 0017](docs/decisions/0017-distancia-canal-requerido.md)).
- Metodología de `project-starter` adoptada por completo: estructura `product/` + `engineering/`
  poblada con contenido real ([ADR 0015](docs/decisions/0015-estructura-product-engineering.md)),
  casting de asientos formalizado, y gate determinista del grafo de docs
  (`tools/auditar.ps1`, [ADR 0016](docs/decisions/0016-gate-grafo-documentacion.md)).
- Capa de barreras viva: `ruff`+CI (v0.10.0), doc-gate §8 + roles (v0.11.0), Mariana cableada
  ([ADR 0011](docs/decisions/0011-cablear-mariana-no-charbel.md)), smoke visual Playwright
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
pytest                            # suite (125+)
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

> El QA de AMS2 (≥3 circuitos) ya quedó cerrado en v0.14.0. De los requisitos de v1.0 quedan dos.

1. **`setup.ps1` en Windows 11 limpio** — Fase 0 (SSH a la PC potente `SERVER`) ✓; pendiente
   **Fase 1: VM limpia de Windows con Hyper-V** para probar la instalación desde cero.
2. **Estabilizar la API interna de `core/`** — sin cambios breaking entre parches (revisión, no código nuevo).
3. **Pulir HUD:** DESLIZ vs GASTO se confunden (misma franja). _Prioridad baja._
4. **Confirmar con video 60 fps real** que el overlay no desincroniza (sin repro hasta hoy). _Prioridad baja._

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
