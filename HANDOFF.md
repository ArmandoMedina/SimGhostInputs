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

## ⚠️ Pendiente inmediato (en vuelo)

**127 tests verdes, `verificar.ps1` limpio, `master` sin push.** Solo falta:

1. ⚠️ **QA visual de Step 0 (Mariana checkpoint):** el Paso 0 fue rediseñado en esta sesión
   (reorden de bloques, cards más cortas, hero strip con los 3 insumos). Antes de hacer push,
   abrir `fantasma ui` y confirmar que el layout se ve correcto. Juicio visual, no comparación
   contra baseline.
2. Correr la skill **`release-helper`** para cortar **v0.14.0** (el PO ya autorizó
   commit/push/versionamiento): bump en `pyproject.toml`, mover `CHANGELOG [Unreleased]`→`[0.14.0]`
   (el contenido **ya está redactado**), footer/estado de `ROADMAP`, badge del `README`, **tag
   anotado**, **push** y **GitHub release** (ojo al cambio de cuenta `gh` personal↔trabajo: el repo
   es público bajo la cuenta personal de Armando).
3. Verificar que el CI quede verde tras el push.

## Estado actual

- **`master` local, sin push.** 4 commits por encima de `origin/master`.
- **127 tests verdes.** Pipeline completo: importar → comparar → overlay → componer.
- **QA de AMS2 cerrado** (requisito v1.0): 4 circuitos, Hypercar/F3/LMP2. Canal de distancia
  exigido con aviso temprano ([ADR 0017](docs/decisions/0017-distancia-canal-requerido.md)).
- **Rama `codex/pruebas-codex`:** 2 de 3 commits integrados a master (cherry-pick). El tercero
  (skills/hooks para Codex) excluido: rutas absolutas hardcodeadas, duplica `.claude/hooks/`.
  Si se quiere soporte Codex en el futuro, merece decisión limpia (ADR o nota en flujo-de-trabajo).

## Qué falta para v1.0

> QA de AMS2 cerrado. Quedan dos requisitos.

1. **`setup.ps1` en Windows 11 limpio** — Fase 0 (SSH a `SERVER`) ✓; pendiente Fase 1: VM limpia
   con Hyper-V para probar instalación desde cero.
2. **Estabilizar la API interna de `core/`** — sin cambios breaking entre parches (revisión, no
   código nuevo).

Baja prioridad: pulir HUD (DESLIZ vs GASTO misma franja), confirmar overlay con video 60 fps real.

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
   `[System.IO.File]::WriteAllText(... utf8NoBOM)`; `.ps1` con acentos → guardar con BOM.

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
