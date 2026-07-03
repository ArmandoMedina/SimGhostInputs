# Decisión — ¿Retirar el código de Streamlit YA (pre-v2.0.0)?

**Fecha:** 2026-07-03
**Rama:** codex/sgi-v2-merge (pre-release v2.0.0)
**Pregunta del PO:** ¿Vale la pena YA eliminar todo el código de Streamlit?
**Autor:** Claude Opus 4.8 (análisis de decisión — no se editó código ni docs)

---

## Recomendación

**Eliminar Streamlit YA, dentro del PR de release v2.0.0 (antes del tag), no después.**

v2.0.0 es un major de SemVer: es el único punto honesto para quitar una UI. No hay
ninguna feature que se pierda (NiceGUI es un superconjunto), el "fallback" de Streamlit
es ilusorio para el usuario objetivo (el instalador v2 solo empaqueta NiceGUI; el
verdadero fallback es la CLI), y retirarlo ahora mata el drift documental —el dolor #1
medido hoy— **antes** de que se envíe a los usuarios, en vez de dejar que v2.0.0 salga
con dos UIs y docs contradictorias que obliguen a un v2.0.1 de limpieza.

Único matiz de secuencia: el retiro es una tarea; los **2 críticos de NiceGUI** que
encontró la auditoría de hoy (C-01 fuga de temp files, C-02 event loop bloqueado en Paso 3)
son otra. El retiro no depende de esos fixes —son bugs de NiceGUI que existen con o sin
Streamlit—, pero el release v2.0.0 no debería taggearse con ellos abiertos. Retirar
Streamlit y arreglar los 2 críticos son los dos entregables del mismo PR de release.

### Por qué NO "eliminar después de v2.0.0"

Porque quitar una UI **es** un cambio de major. Si se difiere, v2.0.0 sale mostrando
`fantasma ui` (Streamlit) como la interfaz principal en README, guía y CONTRIBUTING
—contradiciendo al ADR 0018— y se necesita otro tag para arreglarlo. El drift se envía.

### Por qué NO "mantener ambas con fecha de retiro"

La convivencia es exactamente la fuente del drift auditado hoy. No hay usuario que se
beneficie de Streamlit: el `.exe` v2 no lo incluye, y ningún dev necesita dos UIs para
el mismo wizard de 5 pasos. Mantener = pagar el costo de drift sin comprar nada.

---

## Los 3 datos duros que más pesan

1. **Cero gap de features — NiceGUI es superconjunto de Streamlit.** Los 5 pasos están
   portados y NiceGUI tiene *más*: drill-down/`corner_coaching` en Paso 2, auto-sync +
   encoder NVENC en Paso 4, los 3 flujos del Paso 0, preview reactiva del HUD, breadcrumb,
   y referencias a pacenotes en Paso 0/2 que **no existen** en los archivos Streamlit.
   Eliminar Streamlit no pierde ninguna funcionalidad.

2. **El retiro ya está autorizado por el ADR 0018 — no requiere ADR nuevo.** El ADR 0018
   dice literalmente: *"Streamlit se mantiene en paralelo hasta que la migración esté
   completa y probada — no se borra hasta que el nuevo UI pase todos los tests."* NiceGUI
   ya pasa (flujo feliz cubierto por tests NiceGUI + Playwright; CI verde con import smoke
   ng_*). La condición de borrado está cumplida. La ejecución es una **enmienda** a
   ADR 0010/0018 ("migración completa, Streamlit retirado"), no una decisión nueva.

3. **El "fallback" de Streamlit es ilusorio para el usuario objetivo, y el CI ya migró.**
   El instalador v2 (`build_installer.py`, job `build-installer`) empaqueta **solo**
   `[ui-ng,overlay,sync,xlsx]` — Streamlit no viaja en el `.exe`. El `visual-smoke` del CI
   ya se rebaselíneó a import smoke de NiceGUI; no queda baseline visual de Streamlit. Un
   usuario del campo no puede "volver a Streamlit". El verdadero rollback es la CLL
   (arquitectura "CLI primero"), que no se toca. Mantener Streamlit no compra rollback real.

---

## Censo real (lo que se tocaría)

### 1. Código Streamlit-only en `fantasma/ui/`

| Archivo | Líneas | Estado |
|---|---:|---|
| `app.py` (router) | 211 | Streamlit — no referenciado por ningún entry point v2 |
| `step0.py` | 176 | Streamlit |
| `step1.py` | 283 | Streamlit |
| `step2.py` | 323 | Streamlit |
| `step3.py` | 150 | Streamlit |
| `step4.py` | 431 | Streamlit |
| `_helpers.py` | 295 | Streamlit |
| **Total** | **1 869** | 7 archivos, todos importan `streamlit as st` a nivel de módulo |

Los archivos activos (`ng_app.py`, `ng_state.py`, `ng_helpers.py`, `ng_step0-4.py`,
2 435 líneas) se quedan. `__init__.py` está vacío y no importa los legacy, por eso hoy
no rompen — pero el auditor (m-02) marca el riesgo latente: cualquier import de conveniencia
de un módulo legacy lanza `ImportError` en un entorno solo-`[ui-ng]`.

### 2. Tests Streamlit-only (`tests/ui/`) — todos AppTest

| Archivo | Tests | Líneas |
|---|---:|---:|
| `test_app_smoke.py` | 4 | 66 |
| `test_paso1_estructura.py` | 4 | 83 |
| `test_paso3_estructura.py` | 3 | 57 |
| `test_paso4_estructura.py` | 3 | 56 |
| `test_step2_avisos.py` | 4 | 164 |
| `test_step4_ffmpeg.py` | 1 | 36 |
| **Total** | **19** | **462** |

Los 6 usan `from streamlit.testing.v1 import AppTest`. Los tests NiceGUI
(`test_ng_*`, `test_e2e_wizard.py`, `test_ng_state.py`, `test_step3_render_guard.py`,
`conftest_ng.py`) se quedan. **Ojo:** parte de la lógica de aviso probada en
`test_step2_avisos.py` y `test_step4_ffmpeg.py` vive en `core/` (p. ej. el aviso "piloto
más rápido") — antes de borrar, verificar que esa cobertura ya está replicada en un test
NiceGUI o de `core/`; si no, portar los casos, no perderlos.

### 3. Entry points / CLI

- **`fantasma/cli.py:231` `cmd_ui`** + subparser `ui` (línea 593): lanza
  `streamlit run .../ui/app.py`. Es el comando que README/guía anuncian como principal.
  Se retira o se repunta a NiceGUI (decidir: ¿`fantasma ui` pasa a abrir NiceGUI, o se
  deprecia a favor de `fantasma-ng`?).
- **`pyproject.toml [project.scripts]`**: `fantasma-ng = fantasma.ui.ng_app:run` se queda.
- **`main.py` / `main_gui.py`**: ya son NiceGUI puro. No se tocan.

### 4. Dependencias / extras (`pyproject.toml`)

- **`[ui]  = streamlit + pandas`** → eliminar (o convertir en alias de `[ui-ng]`).
- **`[full]`** → quitar `streamlit`; `pandas` se mantiene (lo usa `[ui-ng]`).
- **`[ui-ng]`** → sin cambios (queda como el único `[ui]`).

### 5. CI (`.github/workflows/tests.yml`)

- Job **`pytest`**: `pip install -e ".[test,ui,ui-ng,sync]"` → quitar `ui`; comentario
  "[ui] mantiene los tests Streamlit existentes" queda obsoleto. Al borrar los 19 AppTest,
  ya no se necesita Streamlit instalado.
- Job **`visual-smoke`**: ya es import smoke NiceGUI. Sin cambios.
- Job **`build-installer`**: ya instala solo `[ui-ng,...]`. Sin cambios.

### 6. Docs y grafo que atribuyen a Streamlit (drift a corregir)

**Ley del blast-radius (§8):** área **ui**, rol **Mariana**, `doc_bloquea:
docs/guia-usuario.md`. El retiro dispara el gate de docs — es parte del mismo PR, no un
follow-up.

- `README.md` (líneas 13, 28, 66, 80, 100, 106): anuncia `fantasma ui` (Streamlit) como
  la UI principal; tabla de deps lista `streamlit`. **Contradice al ADR 0018.**
- `docs/guia-usuario.md` (38, 144): documenta `fantasma ui` como el asistente.
- `CONTRIBUTING.md` (72 `fantasma ui`; línea de estructura *"ui/ interfaz Streamlit —
  app.py (router), step0-4.py…"*): §3 obsoleto (auditoría de hoy).
- `tools/blast-radius.json` (área ui): desc menciona "y legacy Streamlit"; ajustar y
  quitar el patrón `engineering/componentes/streamlit*`.
- **Grafo product/engineering** (dispara `docs-graph`): `product/modulos/UI - Interfaz
  Streamlit.md` (retirar/archivar), `engineering/componentes/streamlit.md` (retirar),
  y revisar wikilinks entrantes en `product/dominios/Interfaz de usuario.md`,
  `engineering/arquitectura.md`, `engineering/README.md`, `product/requerimientos/backlog.md`,
  `PRODUCT_BRIEF.md`.
- **Skills** (consejo AppTest desfasado, auditoría de hoy): `.claude/skills/mariana/SKILL.md`,
  `.claude/skills/charbel/SKILL.md`, `.claude/skills/ahiram/SKILL.md`.
- **ADRs de contexto** (no se borran; se enmiendan/anotan): `0003-testing.md` (AppTest →
  fixture `user`), `0012-playwright-smoke-visual-ui.md`, `0014-gate-ux-ui.md`.
- `docs/benchmark-ui-framework.md`, `docs/flujo-de-trabajo.md`, `docs/ux-patterns.md`,
  `docs/casos-de-uso.md`: revisar menciones (histórico vs instrucción vigente — el histórico
  puede quedarse con nota, lo vigente se actualiza).

---

## Riesgos: retirar YA (pre-tag) vs después

| Eje | Retirar YA (en el PR de release) | Retirar después de v2.0.0 |
|---|---|---|
| **Feature loss** | Ninguna (NiceGUI es superconjunto). | Ninguna, pero con más tiempo de drift. |
| **Tamaño de diff pre-release** | +~2 330 LOC borradas + edición de docs. Grande pero **mecánico** y localizado en área `ui`. Un major lo justifica. | Diff menor ahora; se paga completo en v2.0.1/v2.1. |
| **Smoke visual CI** | Sin impacto: baseline ya es NiceGUI; no hay baseline Streamlit que perder. | Igual. |
| **Rollback si NiceGUI falla en campo** | El `.exe` no incluye Streamlit → mantenerlo **no** da rollback real al usuario objetivo. Fallback verdadero = CLI (intacta). | Mismo — el fallback nunca fue real. Falsa sensación de seguridad. |
| **Blast-radius §8 / gate docs** | Se paga una vez, dentro del PR de release. | Se difiere y se envía la contradicción README↔ADR 0018 al release. |
| **ADR** | Enmienda a 0010/0018 ("migración completa, retirado"). Sin ADR nuevo. | Igual, pero la contradicción vive en el tag. |
| **Drift documental (dolor #1)** | Se elimina **antes** de enviar v2.0.0. | Se **envía** en v2.0.0 y se limpia después. |

**El único riesgo real de retirar YA** es que el PR de release crezca y arrastre la
corrección del grafo de docs bajo presión de tiempo. Se mitiga tratándolo como lo que es
—trabajo de área `ui` con dueño Mariana— y no taggeando hasta que `docs-graph`, `audit`,
`lint` y `pytest` estén verdes. Es el mismo muro que ya exige el ADR 0019; no es carga
extra, es el proceso.

---

## Beneficios de retirar (cuantificados)

- **−~1 869 LOC** de código de UI y **−19 tests** AppTest → menos superficie de
  mantenimiento y de revisión.
- **−1 dependencia pesada** (`streamlit`) del árbol de extras; `[full]` más liviano.
- **Fin del drift documental** entre "lo que anuncia `fantasma ui`" y "lo que corre el
  `.exe`" — el dolor #1 medido hoy, causado precisamente por la convivencia.
- **Menos confusión para agentes futuros:** hoy un agente que abre `fantasma/ui/` ve 7
  archivos Streamlit + 7 NiceGUI y no sabe cuál es el vivo sin leer el ADR 0018 (m-02 del
  auditor lo marca explícitamente). Un solo framework elimina la ambigüedad.
- **Coherencia de release:** v2.0.0 sale contando una sola historia (NiceGUI), como dice
  el ADR 0018, en vez de dos.

---

## Esbozo de ejecución (para el PR de release v2.0.0)

1. **Portar cobertura en riesgo:** confirmar que los avisos probados por `test_step2_avisos.py`
   y `test_step4_ffmpeg.py` ya están cubiertos por tests NiceGUI/`core/`; si no, portar los casos.
2. **Borrar código:** `fantasma/ui/{app,step0,step1,step2,step3,step4,_helpers}.py`.
3. **Borrar tests:** los 6 `test_app_smoke/test_paso*_estructura/test_step2_avisos/test_step4_ffmpeg`.
4. **CLI:** decidir destino de `cmd_ui`/subparser `ui` (retirar o repuntar a NiceGUI) y ajustar `cli.py`.
5. **pyproject:** eliminar `[ui]` (o alias a `[ui-ng]`), quitar `streamlit` de `[full]`.
6. **CI:** quitar `ui` del install de `pytest`; actualizar comentario.
7. **Docs bloqueantes (gate §8):** README, `docs/guia-usuario.md`, CONTRIBUTING §3,
   `tools/blast-radius.json`.
8. **Grafo:** retirar/archivar `product/modulos/UI - Interfaz Streamlit.md` y
   `engineering/componentes/streamlit.md`; reparar wikilinks entrantes; pasar `docs-graph`.
9. **Skills:** corregir consejo AppTest en `mariana/charbel/ahiram`.
10. **ADR:** enmendar 0010/0018 registrando "migración completa; Streamlit retirado en v2.0.0";
    anotar 0003/0012/0014.
11. **En paralelo (release-readiness de NiceGUI, no del retiro):** arreglar C-01 y C-02 de
    la auditoría UI de hoy antes de taggear.
12. **CHANGELOG:** entrada "Eliminado — UI Streamlit legacy (`fantasma ui`), reemplazada por
    NiceGUI (`fantasma-ng`)". Verdes los 4 required checks. Tag v2.0.0.

---

*Nota de honestidad: no ejecuté `pytest` ni instalé entornos; el censo se levantó por
lectura de código, ADRs 0010/0018, la auditoría `fase1-ui.md` de hoy, `pyproject.toml`,
el workflow de CI, `blast-radius.json` y las docs. Los conteos de líneas/tests son de
`wc -l` y `grep -c "def test_"` sobre el árbol de la rama.*
