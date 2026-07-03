# Informe de síntesis — Auditoría integral pre-release v2.0.0

**Fecha:** 2026-07-03 · **Rama:** `codex/sgi-v2-merge` · **Sintetizador:** Claude Opus 4.8
**Insumos:** 21 reportes de auditores independientes (fase 0, 1, 2, 3 + decisión de retiro Streamlit).
**Alcance de este documento:** consolidar (dedupe), reconciliar contradicciones, recalibrar severidad
única, emitir los dos veredictos GO/NO-GO, ordenar paquetes de remediación y listar las decisiones del PO.

---

## 1. Veredictos

### (a) Merge a `master` — **GO CONDICIONADO**
Los gates deterministas están verdes (ruff, formato, 200/201 tests, grafo íntegro) y el drift documental
no bloquea el merge. **Condición:** el PR de release debe cargar **R1** (los críticos de código) — no se
debe mergear a la base de release un importer que corrompe datos en silencio (IMP-01) ni un CLI que
siempre devuelve exit 0 (CLI-01).

### (b) Tag `v2.0.0` + release — **NO-GO**
Bloquean el tag: R1 (7 críticos de código), R2 (seguridad `0.0.0.0` + spec con ruta absoluta),
R4 (bump de versión: `pyproject` sigue en 1.0.0 y no hay sección `[2.0.0]`), R5 (`audit` no es required
check todavía). R3 (retiro de Streamlit) es decisión del PO pero el análisis lo recomienda dentro de
este mismo PR: es el único punto honesto (major SemVer) para quitar una UI y matar el drift #1 antes de
enviarlo.

---

## 2. Reconciliación de contradicciones (gana la evidencia más directa)

| Tema | Postura A | Postura B | Ganador | Severidad final |
|---|---|---|---|---|
| Required checks en master | `fase3-adr0019`/`fase2-adrs`: lint, pytest, docs-graph NO requeridos | `fase3-ci`: verificado contra API GitHub (ruleset 18321394) — lint, docs-graph, pytest 3.10/11/12 y visual-smoke SÍ requeridos desde 2026-06-30; **solo falta `audit`** | **fase3-ci** (evidencia directa de la API) | MAYOR — solo `audit` pendiente (acción PO, 1 clic) |
| `visual-smoke` | `flujo-de-trabajo.md`: "screenshot Playwright contra baseline" | `fase3-ci`: el YML hace import-smoke de `ng_*`, sin Playwright | **fase3-ci** (leyó el YML) | MENOR — doc a corregir; el job es válido, no se toca el ruleset |
| Ruta absoluta en `SimGhostInputs.spec:8` | `fase1-cli` C3: CRÍTICO (no compila en otra máquina) | `fase1-seguridad` I-01: informativo (no es vuln) | Ambos correctos en su eje | MAYOR — no es seguridad; es bloqueador de build/higiene |
| Crash `ORECA sin Distance` | `fase1-charbel` C1: CRÍTICO | El pipeline lo maneja con mensaje accionable y exit 1 | Recalibrado | MENOR — es material de prueba, no bug de código |
| Cobertura 0% de `charts.py`/`report.py` | `fase1-suite`: CRÍTICO | `fase1-viz`: MAYOR | Recalibrado | MAYOR — deuda de test de salida determinista; no es bug de runtime |
| Crashes de `core` (fastest_lap vacío, dt=0) | `fase1-core`: CRÍTICO | — | Recalibrado | MAYOR — crash con traceback en input de borde raro; no corrompe datos |
| Conteo de tests | CHANGELOG 190 · ROADMAP 193 · HANDOFF 201 | `pytest --collect-only` = **201** | HANDOFF | MENOR — sincronizar a 201 |

---

## 3. Familia de drift Streamlit→NiceGUI (una familia, sus instancias)

Atraviesa 7 reportes. Raíz: la UI principal migró a NiceGUI (ADR 0018) pero Streamlit coexiste y la capa
de notas no cerró la transición. **Severidad de familia: CRÍTICO** (el doc de norte describe la tecnología
equivocada). Instancias consolidadas:

| # | Instancia | Fuente | Sev. instancia |
|---|---|---|---|
| D-1 | `PRODUCT_BRIEF.md` §6 dice "Streamlit"; es NiceGUI+pywebview (doc de norte) | ssot-b PB-01 | CRÍTICA |
| D-2 | `CONTRIBUTING.md §3` estructura `ui/` omite 8 archivos `ng_*` | ssot-a Drift-8; inventario §3-B | CRÍTICA |
| D-3 | `engineering/arquitectura.md:56` + `componentes/nicegui.md` dicen `storage.client`; el código usa `storage.user` | grafo GRAVE-2 | GRAVE (dato incorrecto) |
| D-4 | `README.md` tabla de deps omite `[ui-ng]`; `[full]` lo incluye en silencio | ssot-a Drift-1 | ALTA |
| D-5 | `guia-usuario.md` atribuye a `fantasma ui` (Streamlit) features que solo existen en NiceGUI (encoder, dark mode, botón sync) | ssot-a Drift-4/5 | ALTA |
| D-6 | `backlog.md` lista como diferido lo ya entregado (front escritorio, pace notes, drill-down) | grafo GRAVE-1; inventario §3-D | GRAVE |
| D-7 | `product/modulos/UI - Interfaz Streamlit.md` y `engineering/componentes/streamlit.md`: frontmatter `vigente` (deberían `obsoleto`) | adrs H-4; inventario §4 | MEDIA |
| D-8 | ADR 0010 header `Aceptada` pero sus enmiendas dicen "Parcialmente reemplazada por 0018"; ADR 0012 sin enmienda NiceGUI | adrs H-2/H-3 | MAYOR |
| D-9 | Skills con consejo `AppTest`/Streamlit desfasado: `ahiram:39`, `mariana:21`, `charbel:21` | skills P2 | ALTA |
| D-10 | UI-02/UI-03 citan tests NiceGUI que no cubren el criterio (`test_ng_step4.py`, `test_ng_step2.py`) | grafo GRAVE-3 | GRAVE |

El retiro de Streamlit (R3) cierra D-1..D-10 de un golpe: elimina la fuente del drift en vez de parchear
cada doc. Ver decisión PO-1.

---

## 4. Tabla maestra de hallazgos (deduplicada, severidad final recalibrada)

Leyenda paquete: R1 código-crítico · R2 seguridad/build · R3 retiro Streamlit+drift · R4 bitácora/versión
· R5 CI/required · R6 tests post · P post-release · O opcional.

### CRÍTICOS (7)

| ID | Área | Hallazgo (1 línea) | Fuente:línea | Paq. |
|---|---|---|---|---|
| C-01 | importers | Doble-append: 2 columnas al mismo canónico → canal con 2N muestras, datos desalineados en silencio | importers H-01 · `motec_csv.py:95-100,131-132` · `generic_csv.py:68-75` | R1 |
| C-02 | cli | `main()` ignora el retorno de `cmd_*` → exit-code siempre 0 aunque el comando falle (invalida CI/scripting) | cli C1 · `cli.py:679-684` | R1 |
| C-03 | viz | `_run_ffmpeg` manda stderr a DEVNULL → fallo de encoding VP9/ProRes opaco tras horas de render | viz H-01 · `overlay.py:627` | R1 |
| C-04 | viz | `asyncio.run()` dentro del event-loop de NiceGUI → voice pace notes crashea desde la UI principal | viz H-02 · `pacenotes.py:227` | R1 |
| C-05 | ui | Temp files de uploads con `delete=False` nunca se borran (60-120 MB/sesión, sin límite) | ui C-01 · `ng_helpers.py:106-112` | R1 |
| C-06 | ui | `detect_corners()` corre bloqueante en el event-loop en Paso 3 → congela toda la UI | ui C-02 · `ng_step3.py:49-57` | R1 |
| C-07 | docs | Familia drift Streamlit→NiceGUI (norte + estructura + storage backend) — ver §3 | ssot-b PB-01 + 9 más | R3 |

### MAYORES (recalibrados; 28)

| ID | Área | Hallazgo | Fuente:línea | Paq. |
|---|---|---|---|---|
| M-01 | seguridad | NiceGUI/Streamlit en `0.0.0.0` sin auth; path de salida sin sanear (escritura arbitraria LAN) | seguridad M-01 · `ng_app.py:284-292`, `main.py:5`, `cli.py:243` | R2 |
| M-02 | cli/build | `SimGhostInputs.spec` con ruta absoluta `C:\Users\amedina\...` → no compila en otra máquina | cli C3 / seguridad I-01 · `spec:8` | R2 |
| M-03 | cli/release | `pyproject.toml version = "1.0.0"` contradice v2.0.0 (installer, tag, `pip show`) | cli C2 · `pyproject.toml:7` | R4 |
| M-04 | core | `fastest_lap([])` revienta con `ValueError` (todas las vueltas < 10 muestras) | core C-01 · `normalize.py:44` | P |
| M-05 | core | `detect_corners` `ZeroDivisionError` si dt=0 (1 muestra o timestamps constantes) | core C-02 · `corners.py:53-54` | P |
| M-06 | core | `delta_at` cuantiza sin interpolar → error sistémico en `time_lost` (hasta 5 m/~0.18 s) | core M-01 · `compare.py:360-362` | P |
| M-07 | core | `_fmt_signed` con `.replace("+","+")` no-op → doble/nula codificación de signo | core M-02 · `compare.py:102` | P |
| M-08 | core | Duplicación literal de detección de bloques de frenada en 2 sitios | core M-04 · `corners.py:109-116`/`compare.py:333-338` | O |
| M-09 | importers | `IndexError` sin manejar en fila truncada en la columna dist | importers H-02 · `motec_csv.py:127-129` | P |
| M-10 | importers | `StopIteration` sin manejar en CSV vacío | importers H-03 · `generic_csv.py:64` | P |
| M-11 | importers | Fila truncada → `0.0` silencioso para time/dist sin marcar fila mala (rompe monotonía) | importers H-04 · `motec_csv.py:118-122` | P |
| M-12 | importers | `source_file` inconsistente (basename vs ruta completa) entre importers | importers H-05 · `generic_csv.py:61`/`motec_csv.py:145` | P |
| M-13 | importers | Un token inválido en beacons descarta TODOS los beacons → mal corte de vueltas | importers H-06 · `motec_csv.py:141-144` | P |
| M-14 | importers | `wb.active` None en XLSX vacío → `AttributeError` cruda | importers H-07 · `motec_csv.py:73-75` | P |
| M-15 | viz | `hud_preview` "ffmpeg" hardcodeado sin `shutil.which` → `FileNotFoundError` confuso en Windows | viz H-03 · `hud_preview.py:20` | P |
| M-16 | viz | `frames_dir` no se limpia si el encoding falla (~3.6 GB huérfanos) | viz H-04 · `overlay.py:803-806` | P |
| M-17 | viz | `compose.py` rama sin progress descarta stderr de ffmpeg | viz H-05 · `compose.py:340` | P |
| M-18 | viz/charts | `TypeError` al desempaquetar corner sin `segment_m`/`range_m` (mismo patrón en core m-02) | viz H-06 · `charts.py:53` | P |
| M-19 | viz/tests | `charts.py` y `report.py`: 0% cobertura (salida visual/reporte primaria, determinista) | viz H-07/H-08; suite C1/C2; grafo MEDIO-1 | R6 |
| M-20 | ui | Timers de render no se cancelan al navegar mid-render (Steps 3 y 4) | ui M-01 · `ng_step3.py:221`/`ng_step4.py:536` | P |
| M-21 | ui | `render_charts` y lectura de imágenes bloquean el event-loop en Paso 2 | ui M-02 · `ng_step2.py:194-208` | P |
| M-22 | ui | `tempfile.mkdtemp()` de gráficas nunca eliminado (fuga adicional a C-05) | ui M-03 · `ng_step2.py:195` | P |
| M-23 | ui | `_pick_file/_pick_folder` (tkinter) bloquean el event-loop | ui M-04 · `ng_helpers.py:131-164` | P |
| M-24 | ui | `_best_lap_index` cae a la vuelta 0 en silencio si ninguna es completa | ui M-05 · `ng_helpers.py:83-88` | P |
| M-25 | cli | `--all-laps --format prores` produce `overlay_all.webm` (extensión incorrecta) | cli M1 · `cli.py:188-190` | P |
| M-26 | cli | `--auto-sync` llama `input()` en rama ambiguous → bloquea CI/UI | cli M2 · `cli.py:298` | P |
| M-27 | docs | ADR 0010 header `Aceptada` vs enmiendas; ADR 0012 sin enmienda NiceGUI | adrs H-2/H-3 | R3 |
| M-28 | ci | `audit` (blast-radius §8) no es required check → muro cosmético en PR | ci C-1; adr0019 H2 | R5 |

### MENORES (agrupados; ~30)

- **Bitácora/versión (R4):** doble `### Corregido` en Unreleased (coherencia M-01); commit `b7a50ef` sin
  entrada (coherencia M-02); conteo de tests 190/193→201 (coherencia A-02; inventario); ROADMAP "HUD Paso 4"
  como diferido pese a estar implementado (coherencia C-01) — recalibrado a MENOR de bitácora.
- **CLI/build (P/O):** import `os` duplicado (cli m1); help `--auto-sync` sin extra `[sync]` (cli m2); sin
  test de exit-code de `main()` (cli m3); `AppId` UUID placeholder (cli m4); `build_installer` asume CWD
  raíz (cli M4).
- **Docs SSOT (R3):** `samples()` devuelve tupla, no lista (ssot-b FD-01, ALTO→se corrige en doc);
  orden `km/h`/`metros` invertido en `hud-reference` (ssot-b HUD-01); 3er aviso ausente en `hud-reference`
  (HUD-02); `slip_index`/`slip_load` símbolos (glosario GLO-01/02); TCS vs TC (HUD-03/GLO-03); licencias
  NiceGUI/pywebview no listadas (ssot-a Drift-2); badge v1.0.0 (Drift-3).
- **viz/importers menores (P):** `charts.py` KeyError apex.d (viz H-09); PIL handle abierto Windows
  (viz H-10); mismatch sample_rate WAV ignorado (viz H-11); numpy import incondicional en `sync.py`
  (viz H-12); pfloat sin separador europeo (importers H-08); doble apertura archivo (H-09);
  `NotMotecFormat` no exportada (H-10); GUESS sin normalizar `()`/`-` (H-11); core m-01..m-05.
- **Charbel (datos, MENOR):** ORECA sin Distance (C1 recalibrado); delta grid vs laptime 20 ms (M1);
  stderr como NativeCommandError en PS 5.1 (M2); +1 corner a 20 Hz (m1); V-Min engañoso en kink C53 (m2).
- **Tests/suite (R6/P):** flaky `test_pw_step3_overlay_render` (suite A2); Tier 5 sub-poblado 3x (A1);
  `_util.py` sin test directo (M1); clasificación T5 de `test_step2_avisos` (M2); Pillow `getdata()` (B1).
- **Hooks/método (O):** ver §5 (decisiones PO — concurrencia, durabilidad de evidencia, markers).
- **Grafo/blast-radius (O):** viz all-or-nothing (falso positivo no-visual, skills CRÍTICO→decisión PO-3);
  5 filas §8 sin área ejecutable (deps, release, alcance, glosario, decisiones); `README.md` falta en
  `doc_avisa` de viz; `hud_preview.py` sin capacidad (grafo MEDIO-3).

**Conteo consolidado final: CRÍTICO 7 · MAYOR 28 · MENOR ~30 · Total ~65 hallazgos deduplicados**
(recalibrados desde ~190 hallazgos brutos entre los 21 reportes; el grueso de la reducción es la familia
de drift Streamlit→NiceGUI, que se contó como 1 crítico + 10 instancias en vez de ~25 hallazgos sueltos).

---

## 5. Paquetes de remediación (ordenados)

### DEBE arreglarse antes del release (bloquea el tag)

- **R1 — Críticos de código (Ahiram, MEDIANO).** C-01..C-06: doble-append importers, exit-code CLI,
  ffmpeg stderr en overlay, asyncio.run en pacenotes, fuga de temp files UI, event-loop bloqueado en
  Paso 3. Cada uno con test que hoy no existe.
- **R2 — Seguridad y build (Ahiram, CHICO).** M-01 `host="127.0.0.1"` en `ng_app.py`/`main.py`/`cli.py`;
  M-02 ruta dinámica de nicegui en `SimGhostInputs.spec:8`.
- **R3 — Retiro de Streamlit + cierre de drift (decisión PO-1; ejecuta Ahiram código + Escribano/Armando
  docs, GRANDE).** Borra 1 869 LOC + 19 tests AppTest; corrige C-07 y D-1..D-10; enmienda ADR 0010/0018.
  Es el paquete que mata el drift #1 antes de enviar v2.0.0.
- **R4 — Bitácora y versión (Escribano/Armando, CHICO).** Bump `pyproject` a 2.0.0; renombrar Unreleased
  a `[2.0.0]`; fusionar doble `### Corregido`; conteo 201; entrada de `b7a50ef`; limpiar ROADMAP HUD Paso 4.
- **R5 — CI required + doc (PO 1 clic + Escribano, CHICO).** Agregar `audit` al ruleset 18321394; corregir
  `flujo-de-trabajo.md` (visual-smoke = import-smoke, no Playwright); actualizar HANDOFF (solo `audit`).

### Puede ir post-release

- **R6 — Cobertura de tests (Ahiram, MEDIANO).** `tests/viz/test_report.py` + `test_charts.py` (deterministas,
  bajo esfuerzo); refactor Tier 5 con datos sintéticos; guard flaky Playwright; tests de bordes de importers.
- **P — Mayores y menores de robustez (Ahiram, MEDIANO por lotes).** M-04..M-26 restantes: guards de
  crash en core/importers/viz, limpieza de temp dirs, `run.io_bound` en handlers UI, extensión ProRes,
  `--video-lap-idx` para `--auto-sync`. Priorizar los que evitan crash o dato silencioso malo.

### Opcional

- **O — Deuda de método y grafo.** DRY de detección de frenada; granularidad del blast-radius viz
  (decisión PO-3); 5 filas §8 sin área ejecutable; adelgazar solapes de docs; markers/concurrencia de hooks
  (decisiones PO-4/5); lockfile de dependencias (seguridad, recomendado para release).

---

## 6. Decisiones del PO (no las toma el sintetizador)

- **PO-1 — Retiro de Streamlit YA, dentro del PR de release.** El análisis (`decision-retiro-streamlit.md`)
  lo recomienda con datos: cero pérdida de features (NiceGUI es superconjunto), el `.exe` v2 ya no empaqueta
  Streamlit, el CI ya rebaselíneó a NiceGUI, y es el único punto SemVer honesto (major) para quitar una UI.
  Retirarlo mata el drift #1 antes de enviarlo; diferirlo envía la contradicción README↔ADR 0018 en v2.0.0.
  Es una **enmienda** a ADR 0010/0018, no un ADR nuevo. **Recomendación fuerte: aprobar.**
- **PO-2 — ADR/docstring para el patrón `d_offset`.** El render paralelo resta `d_offset` para convertir
  distancia a índice en arrays recortados (adrs D-1). No amerita ADR (es invariante de implementación, no
  elección de arquitectura); **sí** amerita docstring en `_render_chunk` para que un refactor no rompa la
  retención ABS/TC en chunks no-iniciales. Decidir: docstring (recomendado) vs nada.
- **PO-3 — Ajuste del blast-radius viz (falso positivo no-visual).** Mover `hud-reference.md` de
  `doc_bloquea` a `doc_avisa` con `mensaje` (skills P0). Caso vivido hoy: un refactor de perf en `overlay.py`
  bloqueó el push por un doc irrelevante. No abre huecos (el CI `audit` sigue siendo el muro duro).
- **PO-4 — Enmienda del ADR 0018 (spike sin acreditar).** El ADR exige 4 spikes previos (bundle size,
  bug --onefile Win 11 24H2, latencia PIL, AV false positives) pero no hay evidencia de que se cerraran; el
  código de producción ya existe (adrs H-1). Decidir: enmienda retrospectiva con resultados, o declarar
  pendientes los que no se hicieron (el CI de Inno Setup espera confirmación del bundle size).
- **PO-5 — Política de sesiones concurrentes.** El método no contempla dos sesiones en el mismo working
  tree/HANDOFF (adr0019 H3; incidente 73f5ac1). Decidir: worktree por sesión, dueño único del HANDOFF, o
  lock. Relacionado: durabilidad de la evidencia de QA (adr0019 H1 — hoy `qa_runs/*` está gitignored y la
  evidencia se pierde) y markers de hooks seteables sin hacer el trabajo (hooks MEDIO-01).
- **PO-6 — Contradicción template plan-de-trabajo (asentar).** `templates/plan-de-trabajo.md:8` manda a la
  vez "vive en el repo… se commitea" y "se borra (efímero)" (adr0019 M2). Decidir si el plan se versiona.

---

*Síntesis producida sin editar código ni docs del repo. Ejecutar los paquetes es decisión del PO.*
