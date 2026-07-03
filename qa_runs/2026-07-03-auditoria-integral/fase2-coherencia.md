# Auditoría de coherencia de bitácoras — SimGhostInputs v2.0.0 pre-release

**Fecha:** 2026-07-03  
**Rama:** `codex/sgi-v2-merge`  
**Fuentes cruzadas:** CHANGELOG.md, ROADMAP.md, HANDOFF.md, `git log master..HEAD` (59 commits), pyproject.toml  
**Tests reales (pytest --collect-only):** 201

---

## Veredicto

**APROBADA CON BLOQUEOS** — la rama está bien estructurada pero hay 1 contradicción crítica entre ROADMAP y código/CHANGELOG, 1 prerrequisito de release sin completar (version bump), y faltas de coherencia menores. Ningún hallazgo invalida el trabajo realizado; todos son corregibles en < 1 hora.

---

## Conteo por severidad

| Severidad | Cantidad |
|-----------|----------|
| CRÍTICO   | 1        |
| ALTO      | 2        |
| MEDIO     | 3        |
| BAJO      | 3        |
| **Total** | **9**    |

---

## Hallazgos detallados

### CRÍTICO

**C-01 — ROADMAP contradice CHANGELOG y el código sobre la preview del HUD en Paso 4**

ROADMAP §"Post-v2.0 — pendiente de iniciar" lista "Previsualización del HUD en Paso 4" como un feature **diferido**, con el texto explícito "No bloqueó v1.0 ni v2.0" y "Por qué se difiere: trabajo de UX más que de motor." Sin embargo:

- CHANGELOG §Unreleased la declara como implementada: "Preview reactiva del HUD en Paso 4 (`viz/hud_preview.py`): actualización en tiempo real al cambiar posición, escala y overlay."
- El archivo `fantasma/viz/hud_preview.py` existe en disco (creado en commit `21b88c3 feat(ui): migrar UI a NiceGUI v2.0`).
- El commit `c873e00 docs(roadmap): limpia seccion v2.0 ya enviada al CHANGELOG` limpió el ROADMAP pero no eliminó ni marcó como hecho este ítem.

**Impacto:** quien lea el ROADMAP antes del merge creerá que la preview del HUD no existe. Es la contradicción más grave del audit.

**Acción requerida:** eliminar o marcar `[x]` el ítem en ROADMAP §"Post-v2.0".

---

### ALTO

**A-01 — `pyproject.toml` en `version = "1.0.0"`, sin sección `[2.0.0]` en CHANGELOG**

`pyproject.toml` todavía dice `version = "1.0.0"`. El CHANGELOG no tiene sección `[2.0.0]` — todo el contenido v2.0 vive en `§Unreleased`. Esto es estado pre-release esperado, pero es un prerrequisito bloqueante: el `skill release-helper` (indicado como siguiente acción en HANDOFF) falla si no se hace el bump antes del tag.

**Acción requerida (en el ritual de release, no antes del merge):** `pyproject.toml version → 2.0.0`, renombrar `§Unreleased` a `[2.0.0] - 2026-07-0X`.

---

**A-02 — Conteo de tests inconsistente en 3 de 4 fuentes**

| Fuente | Número declarado | Correcto |
|--------|-----------------|----------|
| CHANGELOG §Cambiado (Unreleased) | "190 tests" | NO |
| ROADMAP §Estado actual | "193 tests verdes" | NO |
| HANDOFF §Estado actual | "201 tests verdes" | SÍ |
| pytest --collect-only (actual) | **201** | — |

La discrepancia se debe a que §Cambiado fue escrito antes de que §Optimizado y §Añadido (ambos 2026-07-02) sumaran tests adicionales; el total no se actualizó en §Cambiado. ROADMAP refleja el conteo del commit `55bebfd`. Solo el HANDOFF está al día.

**Acción requerida:** actualizar el número en CHANGELOG §Cambiado y en ROADMAP §Estado antes del tag.

---

### MEDIO

**M-01 — Doble `### Corregido` en §Unreleased**

Dentro de `## [Unreleased]` existen dos bloques con el heading `### Corregido` (el primero sobre `ng_step2.py`/`ui.download`, el segundo sobre `ng_state.py`/`clear_drv` y los bugs visuales). Keep a Changelog exige una sola entrada por categoría por versión. Un parser automático leería solo la primera.

**Acción requerida:** fusionar ambos `### Corregido` en uno.

---

**M-02 — Commit `b7a50ef` sin entrada en CHANGELOG**

El commit `b7a50ef chore: spec de PyInstaller, preview de icono y formato en gen_icon` agrega tres artefactos relevantes para el release:
- `SimGhostInputs.spec` — spec de PyInstaller (fichero de build para el exe)
- `docs/icon_preview.png` — preview del icono de la app
- Mejora de `tools/gen_icon.py`

El CHANGELOG menciona el packaging (build_installer.py, installer.iss) en commits anteriores, pero estos nuevos artefactos de la misma área (PyInstaller) no tienen entrada. Es el único commit feat/chore de área técnica sin cobertura.

**Acción requerida:** añadir entrada en §Añadido o §Cambiado bajo "Empaquetado Windows".

---

**M-03 — ROADMAP §Estado actual con conteo de tests y contexto desactualizado**

El ROADMAP dice "193 tests verdes. QA completo (2026-07-02)" cuando el actual es 201 (diferencia de los tests añadidos por el commit `73f5ac1` y anteriores). La fecha del QA es correcta (2026-07-02), pero el número hace que el estado parezca desactualizado.

Menor que A-02 porque el ROADMAP es un documento de estado, no una fuente de verdad para releases.

---

### BAJO

**B-01 — Separador de fecha inconsistente en versiones antiguas del CHANGELOG**

Versiones 0.12.0 en adelante usan el formato `[X.Y.Z] - YYYY-MM-DD` (guion, correcto per Keep a Changelog). Versiones 0.11.0 hacia atrás usan `[X.Y.Z] — YYYY-MM-DD` (em dash). No afecta al §Unreleased ni a las versiones del release activo, pero rompe la uniformidad del archivo.

---

**B-02 — Número de tests en §Cambiado no se actualiza tras adiciones posteriores en el mismo §Unreleased**

§Cambiado dice "190 tests" (escrito antes de las secciones §Optimizado y §Añadido del mismo Unreleased). El lector rápido del §Cambiado obtiene un número desactualizado sin saber que las secciones posteriores del mismo Unreleased lo incrementan. No hay una línea de "total actual" al final del §Unreleased.

---

**B-03 — Varios commits de docs/chores sin entrada en CHANGELOG (aceptables pero documentados)**

Los siguientes commits no tienen entrada en CHANGELOG. Los commits de docs internos y mantenimiento de HANDOFF/ROADMAP son aceptablemente excluibles; se listan para que el PO decida:

- `0679592 docs: plan de auditoria integral pre-v2 y HANDOFF al dia`
- `9006528 docs: retira el plan de auditoria del repo`
- `c873e00 docs(roadmap): limpia seccion v2.0 ya enviada al CHANGELOG`
- `9bc834e docs(handoff): limpia HANDOFF al minimo`
- `55bebfd docs(adr): actualiza ADR 0003 con 6 tiers de pruebas`
- `1505ba6 chore(qa): documenta resultados QA v2.0 en laptop`
- `caa5f38 chore(lint): elimina import pytest sin usar`

Ninguno introduce lógica nueva. Son omisiones justificadas por convención.

---

## Preguntas del audit — resultado

### (1) ¿Todo lo commiteado está en CHANGELOG §Unreleased?

**Casi.** Los commits feat/fix/perf significativos están cubiertos. El único gap real es `b7a50ef` (M-02). Los commits docs/chores son aceptablemente omitidos.

### (2) ¿Todo lo que el CHANGELOG afirma existe en el código?

**Sí**, en los casos verificados:
- `fantasma/viz/hud_preview.py` — existe
- `tests/test_main_gui.py` — existe
- `tests/ui/test_step3_render_guard.py` — existe
- `test_render_parallel_collect_round_robin` en `tests/viz/test_overlay.py` — existe (línea 54)
- Job `build-installer` en `.github/workflows/tests.yml` — existe

### (3) ¿El ROADMAP refleja el estado real?

**Parcialmente.** Los ítems `[x]` de deuda técnica (collect round-robin, pickle overhead) son correctos. Pero el ítem "Previsualización del HUD en Paso 4" aparece como pendiente post-v2.0 cuando ya está implementado — ver C-01. El conteo de tests es stale (A-02, M-03).

### (4) ¿El HANDOFF está al día y sin historia acumulada?

**Sí.** El HANDOFF (leído el 2026-07-03) tiene: estado actual (suite: 201 tests, CI verde, optimizaciones cerradas), siguiente acción (merge con comandos exactos), acción pendiente del PO (required checks), y referencia al backlog. No acumula historia. Cumple su contrato de "se llena al cerrar, se limpia al abrir".

### (5) ¿La versión de pyproject.toml es coherente con el plan de release?

**Bloqueante pre-tag.** `pyproject.toml version = "1.0.0"` — debe subirse a `2.0.0` como parte del ritual de release. CHANGELOG no tiene `[2.0.0]` (todo en §Unreleased), que es el estado correcto *antes* del tag. Ver A-01.

### (6) ¿Hay fechas imposibles o duplicados en el CHANGELOG?

**No hay fechas imposibles.** El orden cronológico es consistente. Las versiones múltiples en la misma fecha (0.7.0/0.7.1/0.7.2 en 2026-06-21; 1.0.0/0.15.0/0.14.0/0.13.0 en 2026-06-30) son legítimas. El único problema de formato es el separador em dash vs hyphen en versiones antiguas (B-01). Hay un duplicado de heading `### Corregido` en §Unreleased (M-01), que es estructural, no de fechas.

---

## Resumen de acciones requeridas antes del tag v2.0.0

| Prioridad | Acción |
|-----------|--------|
| CRÍTICO   | Eliminar o marcar `[x]` "Previsualización del HUD en Paso 4" en ROADMAP §Post-v2.0 |
| ALTO (release) | Bump `pyproject.toml version` a `2.0.0`; renombrar §Unreleased a `[2.0.0]` en CHANGELOG |
| ALTO      | Actualizar conteo de tests a 201 en CHANGELOG §Cambiado y ROADMAP §Estado |
| MEDIO     | Fusionar los dos `### Corregido` en §Unreleased en uno |
| MEDIO     | Añadir entrada en CHANGELOG para `b7a50ef` (SimGhostInputs.spec, icon preview) |

---

*Auditoría generada por Claude Sonnet 4.6 — 2026-07-03*
