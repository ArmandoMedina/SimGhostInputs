# Auditoria integral de la suite de tests — Fase 1
**Fecha:** 2026-07-03
**Rama:** codex/sgi-v2-merge
**Python:** 3.11.4 — pytest 8.4.2 — Windows 11 Pro
**Referencia:** docs/decisions/0003-testing.md (6 tiers)

---

## 1. Resultado real de pytest

Dos runs consecutivos sobre los 201 tests colectados (~12 min cada uno):

| Run | Modo | Passed | Failed | Skipped | Tiempo |
| :-- | :--- | ------: | ------: | ------: | -----: |
| 1 | `-q --tb=no` | 200 | **1** | 0 | ~12 min |
| 2 | `-v --tb=short` | 200 | 0 | **1** | ~12 min |

El mismo test (`tests/ui/visual/test_e2e_playwright_wizard.py::test_pw_step3_overlay_render`) alterna entre FAIL y SKIP entre runs. Los 196 tests Tier 1-5 son verde estable en ambos runs.

### Conteo por archivo (coleccion)

| Archivo | Tests | Tier (ADR) |
| :------ | ----: | :--------- |
| tests/core/test_degradacion_canales.py | 32 | T1 |
| tests/core/test_compare.py | 15 | T1 |
| tests/viz/test_sync.py | 16 | T3 |
| tests/core/test_wear.py | 20 | T1 |
| tests/viz/test_pacenotes.py | 12 | T3 |
| tests/viz/test_compose.py | 10 | T3 |
| tests/test_cli.py | 8 | T1 |
| tests/importers/test_motec_csv.py | 8 | T2 |
| tests/ui/test_ng_step0.py | 6 | T4 |
| tests/ui/test_ng_state.py | 6 | T4 |
| tests/core/test_corners.py | 6 | T1 |
| tests/core/test_normalize.py | 5 | T1 |
| tests/ui/test_e2e_wizard.py | 5 | T5 |
| tests/ui/visual/test_e2e_playwright_wizard.py | 5 | T6 |
| tests/ui/test_paso1_estructura.py | 4 | T4 |
| tests/importers/test_generic_csv.py | 4 | T2 |
| tests/ui/test_app_smoke.py | 4 | T4 |
| tests/ui/test_step2_avisos.py | 4 | T4/T5* |
| tests/core/test_coaching.py | 3 | T1 |
| tests/ui/test_paso3_estructura.py | 3 | T4 |
| tests/ui/test_paso4_estructura.py | 3 | T4 |
| tests/viz/test_overlay.py | 7 | T3 |
| tests/viz/test_compose_encoder.py | 2 | T3 |
| tests/ui/test_ng_step1.py | 2 | T4 |
| tests/ui/test_ng_step2.py | 2 | T4 |
| tests/ui/test_ng_step3.py | 2 | T4 |
| tests/ui/test_ng_step4.py | 2 | T4 |
| tests/ui/visual/test_step0_visual.py | 2 | T6 |
| tests/ui/test_step3_render_guard.py | 1 | T5 |
| tests/ui/test_step4_ffmpeg.py | 1 | T5 |
| tests/test_main_gui.py | 1 | T4 |
| **TOTAL** | **201** | |

*test_step2_avisos.py esta marcado [T5] en el ADR pero usa Streamlit AppTest, no NiceGUI testing framework.

### Tier real vs ADR declarado

| Tier | ADR estima | Real | Estado |
| :--- | ---------: | ---: | :----- |
| T1 core/ + CLI | ~60 | 89 | OK (superado) |
| T2 importers/ | ~15 | 12 | OK |
| T3 viz/ helpers | ~25 | 47 | OK (superado) |
| T4 smoke/contrato | ~50 | 35* | OK (dentro del margen) |
| T5 NiceGUI testing | ~35 | **11** | **GAP — sub-poblado 3x** |
| T6 Playwright visual | ~8 | 7 | OK |

*T4 incluye test_step2_avisos que el ADR lista como T5 pero implementa con Streamlit AppTest.

---

## 2. Mapa de cobertura por modulo (por inspeccion — sin coverage tool instalado)

pytest-cov no esta instalado (`--cov` devuelve error 4 "unrecognized argument").

### Modulos SIN ningun test directo

| Modulo | Funciones publicas | Testeable sin GPU/ffmpeg | Severidad |
| :----- | :---------------- | :----------------------: | :-------- |
| `fantasma/viz/charts.py` | `plot_corner`, `plot_delta_map`, `plot_time_loss_bar`, `plot_gg_diagram`, `plot_full_lap`, `plot_brake_zones`, `render_charts` (7 fns) | Si (requiere matplotlib; si no instalado devuelve None) | CRITICO |
| `fantasma/viz/report.py` | `write_outputs`, `render_markdown` (2 fns) | Si — stdlib pura (csv, os), sin dependencias | CRITICO |
| `fantasma/viz/hud_preview.py` | `compose_preview_frame` | No (ffmpeg + PIL) | BAJO (correctamente manual) |
| `fantasma/importers/_util.py` | `detect_delimiter`, `pfloat` | Si — stdlib pura | MEDIO (ejercido indirectamente via motec/generic) |
| `fantasma/ui/ng_helpers.py` | `_fmt_lap`, `_sync_quality_label`, `_best_lap_index`, `_lap_options`, `_load_laps`, `start_bg_render` | Parcialmente | MEDIO |
| `fantasma/viz/_overlay_worker.py` | Entry point de subprocess | No (subprocess spawn) | BAJO (correctamente manual) |

### Modulos con tests pero con zonas no cubiertas

| Modulo | Zona sin cubrir | Impacto |
| :----- | :-------------- | :------ |
| `viz/overlay.py` | `_HUDFigure`, `_render_chunk`, `_run_ffmpeg`, `render_overlay` (logica principal) | Alto — solo se testean los helpers puros; el render real es 0% |
| `viz/overlay.py` | Fallback serial cuando un worker falla (`failed` list en `_render_parallel`) | Medio — el test round-robin no cubre el caso de worker con returncode != 0 |
| `viz/compose.py` | `compose_video` con NVENC exitoso (returncode=0 en la segunda llamada sin crear el archivo) | Bajo |
| `ui/app.py` (Streamlit) | Paso 3 (render de overlay real), navegacion completa | Medio |
| `core/corners.py` | Circuitos con multiples kinks, curvas muy juntas, sin throttle/brake | Medio |
| `core/normalize.py` | `split_laps` con canal `lap_number` continuo (no enteros); vueltas de longitud 0 | Bajo |

### Modulos bien cubiertos

- `core/compare.py`: 15 tests unitarios + 32 parametrizados de degradacion = excelente
- `core/wear.py`: 20 tests; cubre slip, assist_count, wear_budget con umbrales y None
- `viz/sync.py`: 16 tests; cubre _rank_candidates, zona gris, _read_wav_mono
- `viz/pacenotes.py`: 12 tests; cubre generacion WAV, metadata, eventos vacios
- `viz/compose.py`: 10 tests; helpers puros bien cubiertos
- `importers/motec_csv.py`: 8 tests con fixture miniCSV; cubre separador `;`

---

## 3. Calidad de los tests

### 3.1 Test FLAKY — severidad ALTA

`tests/ui/visual/test_e2e_playwright_wizard.py::test_pw_step3_overlay_render`

- Run 1 (-q): **FAILED** (no skip, failure real)
- Run 2 (-v): **SKIPPED** con "render timeout — Nordschleife es una vuelta larga"
- Causa: `_do_step1()` sube dos CSVs reales (~31 MB + ~59 MB) via Playwright. Si el servidor NiceGUI no levanta rapido o la subida supera el timeout de 90 s, el `wait_for_selector` de Playwright lanza un error NO atrapado por el guard de `PlaywrightTimeoutError` (que solo rodea el wait del render, no el upload). El test falla en vez de skipear.
- Impacto: genera ruido en CI; enmascara si hay un fallo real de regresion en overlay.
- Recomendacion: envolver `_do_step1()` en un try/except PlaywrightTimeoutError con `pytest.skip` apropiado.

### 3.2 Mocks que mockean lo que prueban — severidad BAJA

`test_render_parallel_collect_round_robin` (tests/viz/test_overlay.py):

El test es solido: simula tres workers con distintos tiempos de terminacion y verifica que el collect round-robin los recolecta a todos. Lo que NO cubre: el caso en que un worker termina con `returncode != 0` (el fallback serial en la lista `failed`). El assert solo verifica `collected_done[-1] == n_frames`, que puede dar green aunque el fallback serial nunca se invoque.

### 3.3 Asserts triviales — severidad BAJA

Cuatro tests en test_ng_step1.py, test_ng_step2.py, test_ng_step3.py, test_ng_step4.py son smoke minimos (solo verifican heading visible + guard de estado vacio). Son aceptables como smoke pero no verifican comportamiento funcional relevante del paso.

`test_paso3_estructura.py::test_paso3_sidebar_activo_en_nav3` verifica que el sidebar tiene el emoji especifico `"▶"` — si el emoji cambia, el test falla por razon cosmética. Fragilidad baja pero presente.

### 3.4 Clasificacion incorrecta en el ADR — severidad MEDIA

`test_step2_avisos.py` esta documentado en el ADR como `[T5] wizard: avisos en Paso 2 (NiceGUI testing)` pero usa `streamlit.testing.v1.AppTest` (no NiceGUI testing framework). Esto distorsiona el conteo real de Tier 5.

Los tests de estructura del Paso 1/3/4 (`test_paso*.py`) tambien usan Streamlit AppTest — son tests de la UI legacy Streamlit (app.py), no de la UI NiceGUI (ng_app.py). Deben mantenerse mientras app.py exista, pero su clasificacion en el ADR no es precisa.

### 3.5 Dependencia de CSVs reales en T5 — severidad MEDIA

`test_e2e_wizard.py` tiene 5 tests; 4 de los 5 usan `@_SKIP_CSVS` que los salta en entornos sin los CSVs de Nordschleife. En CI (sin los CSVs) solo `test_e2e_step0_select_flow_overlay` corre — el 80% del archivo T5 queda inactivo en CI. El ADR dice que T5 "corre en CI" pero la implementacion real depende de archivos locales para 4 de los 5 tests mas importantes del wizard.

### 3.6 _SharedState — fragilidad de estado compartido — severidad BAJA

`_SharedState` en test_e2e_wizard.py usa un dict de clase (`cls._shared`) compartido entre instancias. Cada test llama `.reset()` antes de usar el estado, lo que es correcto. Sin embargo, `test_e2e_step0_select_flow_overlay` no llama `.reset()` y podria ver estado residual de un run anterior si el orden de tests cambia. No es problema hoy porque pytest corre en orden de recoleccion, pero es una deuda de fragildiad.

### 3.7 Pillow DeprecationWarning — severidad MUY BAJA

`test_step0_visual.py` usa `img.getdata()` (deprecated en Pillow 14, eliminado en 2027-10-15). Los tests pasan con warnings hoy; fallaran en Pillow 14 sin cambios.

---

## 4. Los 6 tiers del ADR: estado real

| Tier | Definicion ADR | Estado | Observacion |
| :--- | :------------- | :----- | :---------- |
| T1 — core/ puro | Matematica del motor, determinista | **EXCELENTE** | 89 tests; 32 parametrizados de degradacion; cubre todos los casos edge documentados |
| T2 — importers/ | Parseo CSV, fixture miniCSV | **BIEN** | 12 tests; cubre separador `;`, encoding, columnas ausentes |
| T3 — viz/ helpers puros | Sin ffmpeg ni matplotlib | **BIEN** | 47 tests; sync, compose, pacenotes, overlay helpers bien cubiertos; GAP en charts.py y report.py |
| T4 — smoke y contrato UI | Importacion, firmas, AST | **BIEN** | 35 tests; cubre Streamlit + NiceGUI smoke; discrepancia de clasificacion con T5 |
| T5 — NiceGUI testing | Comportamiento funcional del wizard | **GAP CRITICO** | Solo 11 tests reales (ADR dice ~35); 4 de 5 tests E2E dependen de CSVs locales (skip en CI) |
| T6 — Playwright visual | Apariencia, colores, alineacion | **BIEN** | 7 tests; 1 flaky (test_pw_step3_overlay_render); visuals de alineacion y contraste correctos |

---

## 5. Skips y xfails

No hay ningun `@pytest.mark.xfail` en la suite (buen signo: ningun test conocido-roto silenciado).

Skips presentes (todos con razon documentada):

| Patron | Archivo(s) | Razon |
| :----- | :--------- | :---- |
| `pytest.importorskip("nicegui.testing")` | test_ng_step*.py, test_step3_render_guard.py, test_step4_ffmpeg.py | NiceGUI no instalado |
| `pytest.importorskip("streamlit")` | test_app_smoke.py, test_paso*.py, test_step2_avisos.py | Streamlit no instalado |
| `pytest.importorskip("playwright.sync_api")` | tests/ui/visual/*.py | Playwright no instalado |
| `pytest.importorskip("numpy")` | test_overlay.py, test_sync.py | numpy no instalado |
| `pytest.importorskip("scipy")` | test_sync.py (5 tests) | scipy no instalado |
| `@_SKIP_CSVS` (skipif) | test_e2e_wizard.py (4 tests) | CSVs reales ausentes |
| `pytestmark = skipif(_CSV_MISSING)` | test_e2e_playwright_wizard.py (modulo) | CSVs reales ausentes |

Todos los skips son correctos y necesarios. El problema no es que haya skips; es que el skip de CSVs reales en T5 deja el tier practicamente inactivo en CI.

---

## 6. Hallazgos por severidad

### CRITICO (bloquea cobertura de valor de producto)

**C1 — viz/charts.py: 0% cobertura, 7 funciones publicas no testeadas**
`render_charts`, `plot_corner`, `plot_delta_map`, `plot_time_loss_bar`, `plot_gg_diagram`, `plot_full_lap`, `plot_brake_zones` son el output visual principal del flujo "analisis". Son deterministas (misma entrada -> misma salida dado matplotlib disponible). Cualquier regression en el nombrado de archivos, en la logica de seleccion de canales opcionales, o en el manejo de corner_rows vacios pasaria desapercibida. El ADR del Tier 3 dice "sin invocar ffmpeg", pero charts.py no requiere ffmpeg — solo matplotlib — y matplotlib esta en el extra `[full]`. Este es el gap de cobertura mas grande de la suite.

**C2 — viz/report.py: 0% cobertura, funciones 100% deterministas sin dependencias**
`render_markdown` es una funcion de texto puro que genera el report.md de debrief: sin matplotlib, sin ffmpeg, sin subprocess. `write_outputs` usa stdlib csv y os. Ambas son testables con make_lap + un tmp_path. Una regression en la estructura del markdown (cambio de columnas en la tabla, aviso que no se imprime, formato de tiempo roto) seria invisible.

### ALTO (degradacion silenciosa posible)

**A1 — Tier 5 sub-poblado: 11 tests reales vs ~35 declarados en el ADR**
El ADR promete cobertura funcional del wizard con NiceGUI testing framework. Los 11 tests actuales cubren smoke (heading visible, guard de estado) pero no flujos funcionales como: avance automatico de paso al cargar archivos, mensajes de error ante CSV invalido, comportamiento del selector de vuelta rapida, cancelacion de render en progreso. El `test_step3_render_guard` (1 test) es el unico test funcional real de Tier 5.

**A2 — test_pw_step3_overlay_render flaky: FAIL en run 1, SKIP en run 2**
El test de render completo de Nordschleife no tiene guards para el fallo del upload (que no es el render). Cuando `_do_step1()` falla en la navegacion, el error es un Playwright TimeoutError no atrapado, lo que da FAILED en vez de SKIP. Esto genera falsos positivos en CI y enmascara si hay una regresion real en el render de overlay.

### MEDIO (calidad o cobertura degradada)

**M1 — fantasma/importers/_util.py: no tiene tests directos**
`detect_delimiter` y `pfloat` son funciones puras (stdlib, sin imports externos). Se ejercen indirectamente via test_motec_csv y test_generic_csv, pero no tienen tests de contratos propios. Un cambio en la logica de deteccion de separador (ej. umbral de conteo) o en la tolerancia de pfloat solo se detectaria si los tests de integracion de importers lo atrapan — y pueden no hacerlo si el CSV fixture usa el separador por defecto.

**M2 — Clasificacion T5 incorrecta para test_step2_avisos.py**
test_step2_avisos.py usa Streamlit AppTest pero el ADR lo lista como [T5 NiceGUI testing]. Esto infla artificialmente el tier 5 en documentacion pero no en ejecucion real.

**M3 — 4 de 5 tests E2E wizard dependen de CSVs locales (skip en CI)**
En un entorno CI limpio, test_e2e_wizard.py aporta 1 test. Los 4 tests mas valiosos (carga de archivos, comparacion, overlay con datos reales) estan skipados. La promesa del ADR ("T5 corre en CI") no se cumple para la mayoria de los tests de este tier.

**M4 — _render_parallel: fallback serial no testeado**
test_render_parallel_collect_round_robin solo verifica que `collected_done[-1] == n_frames`. Si un worker falla con returncode != 0, el fallback serial en `failed` list NO es verificado — el test daria green aunque el fallback nunca se ejecute o estuviera roto.

### BAJO (fragilidad puntual o cosmética)

**B1 — Pillow DeprecationWarning en test_step0_visual.py**
`img.getdata()` sera eliminado en Pillow 14 (2027-10-15). Warning documentado en la salida.

**B2 — Asserts de emoji en test_paso3_estructura.py**
`assert any("1" in l and "▶" in l for l in labels)` — cambiando el caracter del sidebar romperia el test por razon cosmética.

**B3 — _SharedState sin reset() en test_e2e_step0**
El primer test del archivo no llama `.reset()`. Si el orden de ejecucion cambia o se añade estado en un fixture de sesion, podria ver estado residual.

---

## 7. Los 3 gaps mas graves (resumen ejecutivo)

1. **viz/charts.py y viz/report.py tienen 0% cobertura** — son el output primario del flujo "analisis" (PNGs de debrief, report.md, CSV) y son 100% deterministas. Una regression pasa invisible.

2. **Tier 5 sub-poblado 3x vs lo declarado en el ADR, y el 80% de los tests E2E dependen de CSVs locales** — en CI el wizard NiceGUI tiene cobertura funcional casi nula mas alla del smoke.

3. **test_pw_step3_overlay_render es flaky (FAIL/SKIP no determinista)** — el test no guarda contra el fallo del upload en el paso previo, generando FAILs que no son regressions de overlay sino de timing/servidor.

---

## 8. Recomendaciones priorizadas

| Prioridad | Accion | Tier | Esfuerzo |
| :-------- | :----- | :--- | :------- |
| P1 | Añadir `tests/viz/test_report.py` con tests de `render_markdown` y `write_outputs` (tmp_path, make_lap, datos sinteticos) | T3 | Bajo (funciones puras) |
| P2 | Añadir `tests/viz/test_charts.py` con tests de `render_charts` con monkeypatch de matplotlib o usando matplotlib real en CI (`[full]` instalado) | T3 | Medio |
| P3 | Refactorizar `test_e2e_wizard.py` para inyectar datos sinteticos via `_SharedState` en los 4 tests con CSVs — equivalente a lo que hace `test_step3_render_guard.py` | T5 | Medio |
| P4 | Envolver `_do_step1()` en try/except PlaywrightTimeoutError con pytest.skip en `test_pw_step3_overlay_render` | T6 | Bajo |
| P5 | Instalar `pytest-cov` y ejecutar `--cov=fantasma --cov-report=term-missing` para obtener numeros exactos de cobertura por linea | Infra | Bajo |
| P6 | Corregir clasificacion de `test_step2_avisos.py` en el ADR (es T4 Streamlit, no T5 NiceGUI) | Docs | Minimo |

---

*Generado por auditoria automatizada — rama codex/sgi-v2-merge — 2026-07-03*
