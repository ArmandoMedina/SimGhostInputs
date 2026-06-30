# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## En una frase

Motor **offline** de análisis de telemetría sim racing (importar CSV de MoTeC → comparar vueltas por
distancia → reporte + overlay de video). Objetivo de fondo: cortar la **v1.0** (estabilizar, testear,
documentar, validar en AMS2 el pipeline que ya existe).

## Estado actual — v0.15.0 (2026-06-30)

**142 tests verdes, `master` en limpio.** v0.15.0 recién cortada.

- Pipeline completo: importar → comparar → overlay → componer. Happy path confirmado en QA manual.
- QA de AMS2 cerrado: 4 circuitos, Hypercar/F3/LMP2, canal de distancia requerido ([ADR 0017](docs/decisions/0017-distancia-canal-requerido.md)).
- UI/UX: gate completo — AppTest Pasos 0-4 (18 tests) + checklist Mariana formalizada en hook.
- API `core/` estabilizada: `__all__`, `_` prefijos consistentes, `CANONICAL` eliminada.
- Cobertura completa de blast-radius (8 áreas); skill de Ahiram + Oscar en el casting.

## Qué falta para v1.0

> Queda un solo requisito.

1. **`setup.ps1` en Windows 11 limpio** — Fase 0 (SSH a `SERVER`) ✓; pendiente Fase 1: VM limpia
   con Hyper-V para probar instalación desde cero.

Baja prioridad: pulir HUD (DESLIZ vs GASTO misma franja), confirmar overlay con video 60 fps real.

### QA extendido 2026-06-30

- Artefactos: `qa_runs/local-matrix-20260630-082708/` y `qa_runs/charbel-20260630/`.
- `pytest`: **127 passed** tras el fix.
- Matriz local: 19/19 CSVs importan con `laps`; 18/19 generan `corners_detected.json`; el único
  fallo esperado es el ORECA 07 sin canal `Distance`.
- `compare --no-charts`: reportes generados por circuito/clase; el caso ORECA ahora falla con
  mensaje claro en vez de `NoneType`.
- `overlay` + `compose`: Charbel validó un tramo corto con `2.mp4`, generando `overlay.webm` y
  `composed_2s.mp4` bajo `qa_runs/charbel-20260630/overlay_compose/`.
- UI: AppTest explícito (`test_app_smoke`, `test_step2_avisos`, `test_step4_ffmpeg`) y smoke visual
  Playwright pasan individualmente. Ojo: `pytest tests\ui tests\ui\visual` colectó solo el test
  visual en esta máquina; usar archivos explícitos o revisar discovery si se quiere ese comando
  como atajo.

## Cómo correr

```powershell
pip install -e ".[full]"          # entorno completo
fantasma --help                   # CLI
fantasma ui                       # UI Streamlit
pytest                            # suite (127)
./tools/verificar.ps1             # barreras locales (lint+formato+tests+doc-gate)
git config core.hooksPath .githooks   # una vez por clon: enciende pre-push
```

## Cosas que DEBES saber (o te tropiezas)

1. **`core/` e `importers/` son librería estándar pura** — sin matplotlib/scipy/openpyxl. Las deps
   viven en extras opcionales y degradan con gracia si faltan. No metas deps al núcleo.
2. **Determinista:** misma entrada → misma salida. Solo lo determinista se automatiza como barrera;
   lo visual/subjetivo es QA manual ([ADR 0003](docs/decisions/0003-testing.md)).
3. **El cambio incluye su test** si toca comportamiento (`core/`, `importers/`, helpers puros de `viz/`).
4. **Doc-gate §8 BLOQUEA** en local si tocas `core/` sin `formato-datos.md`, `viz/` sin
   `hud-reference.md`, o las barreras sin `flujo-de-trabajo.md`. Pásalo al escribano.
5. **Entorno PS 5.1:** mensajes de commit multilínea a git → `git commit -F archivo` con
   `[System.IO.File]::WriteAllText(... utf8NoBOM)`; `.ps1` con acentos → guardar con BOM. Ver `CLAUDE.md` global.

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
