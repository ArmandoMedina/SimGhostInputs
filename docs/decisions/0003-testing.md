# Decisiones de diseño: estrategia de pruebas automatizadas

> **Estado: implementado y ampliado.** La estrategia original (4 tiers) está implementada
> y se extendió con dos capas nuevas para v2.0 (NiceGUI testing framework y Playwright E2E).
> Ver [§ Estado de implementación](#estado-de-implementación) al final para el inventario
> actualizado. La decisión razonada queda aquí para no improvisarla en el momento.

## Problema

El proyecto no tiene ningún test automatizado. Todo el QA es manual con telemetría
real, lo que tiene dos costes concretos ya observados:

- **Regresiones silenciosas.** El refactor 0.6.3 (split de la UI en módulos) dejó
  `app.py` con imports relativos que rompían el arranque de la UI; nadie lo detectó
  hasta ejecutarla a mano sesiones después. Un test que solo importara `app.py`
  lo habría atrapado al instante.
- **Bugs por entorno no cubierto.** El detector de NVENC daba falso positivo en
  equipos sin GPU NVIDIA usable (`Cannot load nvcuda.dll`) y no caía al fallback de
  CPU. Un test del helper habría fijado el contrato.

El ROADMAP lista "sin tests automáticos" como deuda técnica y pide **al menos tests
unitarios de `core/`** como requisito para la 1.0.

---

## Principios que condicionan el enfoque

Heredados de `CONTRIBUTING.md` §4:

1. **Motor sin datos.** El repo nunca incluye telemetría. Los tests usan **datos
   sintéticos** generados en memoria, no CSVs reales versionados.
2. **Determinista.** Mismo input → mismo output. Los tests no dependen de archivos
   externos, red, GPU ni del reloj.
3. **Núcleo sin dependencias.** `core/` e `importers/` son librería estándar pura;
   sus tests no deben necesitar matplotlib, ffmpeg ni streamlit.
4. **Degradación graceful.** Falta de canales opcionales (gear, glat, abs…) es un
   caso de primera clase, no un error — y por tanto algo que **hay que testear**.

---

## Qué se automatiza vs qué se prueba a mano (directiva)

La regla de oro: **automatiza la lógica determinista; prueba a mano lo que depende
del entorno, lo visual y lo subjetivo.** "Determinista" = misma entrada, misma
salida, sin GPU/ffmpeg/red/ojo humano.

| Parte del proyecto | Quién verifica | Por qué |
| :-- | :-- | :-- |
| `core/` (compare, normalize, corners, wear) | 🤖 Automática | Aritmética pura. Es el valor del producto. |
| `importers/` (motec_csv, generic_csv) | 🤖 Automática | Parsear texto → datos es determinista. |
| `viz/` **helpers puros** (`_build_filter`, `_nvenc_available`, aritmética de `sync`) | 🤖 Automática | Construir un comando o calcular un offset es determinista; **sin invocar ffmpeg**. |
| `ui/app.py` — arranque | 🤖 Smoke mínimo | Solo "¿levanta sin excepción?". |
| `ui/` — comportamiento funcional (clics, navegación, mensajes de error) | 🤖 NiceGUI testing | El framework interno simula eventos sin browser real. |
| `ui/` — apariencia visual (colores, alineación, contraste en dark mode) | 🤖 Playwright (solo laptop dev) | Requiere CSVs reales y Chromium; no corre en CI. |
| Render real de overlay (`.webm` se ve bien, alfa correcto) | 👤 Manual | Ojo humano sobre el resultado. |
| Composición ffmpeg + NVENC real, auto-sync con video real | 👤 Manual | Depende de GPU/drivers/video; el entorno manda. |

**El matiz clave:** la UI se parte en dos. *La lógica detrás* de la UI vive en `core/`
y **sí** se automatiza. *La presentación* tiene ahora dos niveles: el comportamiento
funcional (el wizard avanza, los mensajes aparecen) se cubre con el NiceGUI testing
framework; la apariencia visual (contrastes, posiciones, dark mode) se cubre con
Playwright solo en el laptop de desarrollo, donde existen los CSVs reales y un
Chromium instalado.

**Cómo decidir un caso nuevo (3 preguntas):**
1. ¿La respuesta correcta es un valor exacto (número, string, lista)? → 🤖 Automática.
2. ¿Necesito ver/oír/sentir si está bien? → 👤 Manual.
3. ¿Depende de GPU/ffmpeg/video/drivers/red? → 👤 Manual (o automatiza solo el
   pedazo determinista, como el comando que se construye).

El QA manual no desaparece: **se aligera**. Se deja de gastar tiempo verificando
matemáticas (lo hace la máquina) y se concentra en lo único que un humano puede
juzgar: lo visual y lo experiencial.

---

## Cuándo se corren y se añaden (regla operativa)

Lo de arriba dice *qué* y *cómo*; esta es la regla de *cuándo* (para que ninguna sesión
futura tenga que preguntarla):

- **Antes de cerrar un cambio de comportamiento, corre `pytest`.** Verde es condición
  para commitear/pushear; un rojo se **diagnostica**, no se silencia.
- **Si añades o cambias lógica determinista, el cambio incluye su test.** No es un paso
  "para después": el test es parte del cambio — es lo que permite auditar por
  verificación sin leer el código.
- **Si el escenario no existe, créalo;** si un bug se cuela, se blinda con un test de
  regresión (un bug que no se detecta vuelve — ver §Tests de regresión).
- **Si un test está mal o quedó desactualizado, corrígelo — pero primero entiende por
  qué falla.** Un rojo suele ser el test haciendo su trabajo (atrapando una regresión
  real). Ajustar un test para que pase sin entender el rojo es apagar la alarma de humo.

Esta regla vive también, en corto, en `CONTRIBUTING.md` §3 (la cara para contribuidores).

---

## Enfoque elegido

### Framework y estructura

- **pytest** — estándar de facto, fixtures simples, sin boilerplate.
- Nuevo extra opcional en `pyproject.toml`: `test = ["pytest>=8,<9"]`, instalable con
  `pip install -e ".[test]"`. Se mantiene fuera de `[full]` (es para desarrollo, no
  para el usuario final).
- Config mínima en `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests"]`).
- Carpeta `tests/` como espejo del paquete:

```
tests/
  conftest.py        # fixtures compartidas + el builder make_lap
  core/
    test_normalize.py
    test_compare.py
    test_corners.py
  importers/
    test_motec_csv.py
    fixtures/         # CSVs diminutos (10-20 filas), únicos datos versionados
  viz/
    test_compose.py   # solo helpers puros, sin invocar ffmpeg
  ui/
    test_app_smoke.py # arranque de la UI con streamlit.testing.AppTest
```

### Fixtures sintéticas: `make_lap`

La pieza central es un constructor `make_lap(...)` en `conftest.py` que arma una
`Lap` (el dataclass de `core/lap.py`: `channels` dict + `meta`) con un perfil de
velocidad controlado:

- Valles de velocidad ("curvas") en metros concretos → permite afirmar dónde debe
  detectar curvas el detector y cuánto tiempo se pierde.
- El tiempo se **integra a partir de distancia/velocidad**, así ir más lento cuesta
  más tiempo, igual que en pista real (clave para los tests de `compare`).
- Los canales opcionales se controlan por parámetro: quitar `gear` o `glat` del set
  prueba la degradación graceful sin tocar nada más.

Ventaja sobre versionar CSVs: legible, determinista, y los casos límite se expresan
como parámetros (`make_lap(channels=(...))`) en vez de como archivos opacos.

---

## Estrategia por capas (orden de prioridad = ROI descendente)

### Tier 1 — `core/` puro · **empezar aquí**

Es donde vive el valor del producto y no tiene I/O. Cobertura objetivo:

- `normalize.resample` — paso de rejilla correcto, longitud, interpolación lineal en
  rango, canales discretos (gear) sin fraccionar.
- `compare.delta_trace` — `delta_t` con signo correcto (piloto más lento = positivo),
  alineación por distancia; vueltas idénticas → delta ≈ 0.
- `compare._corner_metrics` y `compare.compare` — vmin, punto de frenada, flags de
  tolerancia; **y el caso sin `gear`/`glat`** (gap #1 del ROADMAP).
- `corners.detect_corners` / `extract_milestones` — nº de curvas e hitos sobre un
  trazado sintético de valles conocidos.
- `wear` — slip/assist con y sin canales de rueda.

### Tier 2 — `importers/` con CSVs fixture diminutos

Únicos datos versionados (10-20 filas, sin datos personales):

- MoTeC i2 CSV estándar, **separador `;`** (gap del ROADMAP), encoding `utf-8-sig`,
  columnas ausentes, `load_laps` de punta a punta.

### Tier 3 — helpers puros de `viz/` (sin invocar ffmpeg)

- `compose._build_filter` — afirmar que el filtro contiene `scale=iw*<f>` y el
  `setpts` solo con offset≠0. **Este test habría atrapado un bug de construcción de
  filtro como el de los asteriscos.**
- `compose._nvenc_available` — monkeypatch de `subprocess.run`: returncode≠0 → `False`,
  0 → `True`. Fija el contrato del fallback.
- `sync` — la aritmética de offset/z-score sobre señales sintéticas.

### Tier 4 — smoke y contrato de UI (barato, alto valor)

- Smoke de importación: verifica que los módulos de UI importan sin error. Atrapa
  `ImportError` de arranque antes de que llegue al usuario.
- Tests de contrato: verifican firmas de funciones, atributos de clases y constantes
  que otros módulos consumen (p. ej. `_FLOWS`, `_STEPS` en `ng_helpers`).
- Tests AST: parsean el código Python sin ejecutarlo para verificar invariantes
  estructurales críticos (p. ej. `test_main_gui.py` comprueba que `freeze_support()`
  está presente en el entry point de PyInstaller).

### Tier 5 — tests E2E con NiceGUI testing framework *(nuevo en v2.0)*

Usan `nicegui.testing` (`user`, `user.find()`, `user.should_see()`). Levantan la app
en un loop asyncio simulado — **sin servidor HTTP real ni browser** — pero pueden
hacer clics y verificar que el DOM reacciona.

- Comportamiento funcional del wizard: ¿avanza al paso correcto?, ¿muestra el mensaje
  de error esperado?, ¿el guard de doble clic funciona?
- Datos sintéticos inyectados vía monkeypatch de `AppState` — nunca CSVs reales.
- **Corre en CI** (igual que Tier 1–4).
- **No detecta bugs visuales** (colores, alineación, contraste) — solo comportamiento.

### Tier 6 — tests Playwright E2E visual *(nuevo en v2.0, solo laptop de desarrollo)*

Levantan un servidor NiceGUI real en el puerto 8765 (subprocess separado) y abren un
Chromium headless real.

- **Pueden detectar bugs visuales** que los otros tiers no ven: alineación de
  elementos (`bounding_box()`), contraste de colores (`getComputedStyle`), opacidad.
- Usan CSVs reales de telemetría (Nordschleife) para el flujo completo clic a clic.
- **No corren en CI** (requieren los CSVs de `Paterial para test` y Chromium instalado).
  El módulo se skip automáticamente si los archivos no existen en disco.
- Screenshots guardados en `qa_runs/playwright_e2e/` como evidencia para QA.

> **Regla del PO (método).** Todo entregable que el PO vaya a evaluar tiene que salir de la
> **UI real**, en modo **E2E clic-por-clic con Playwright** (Tier 6) — nunca de un script
> externo que reproduzca el resultado por otra vía. Un script que llama directo a `core`/`viz`
> y arma el video o el reporte por su cuenta no prueba que la UI lo genere igual; esas no son
> pruebas confiables para una decisión de aceptación. La automatización de Tier 1-5 sigue
> siendo el gate de regresión; la evidencia que revisa el PO es Tier 6 sobre la app real.

---

## Tests de regresión de los bugs ya encontrados

Cada bug corregido se blinda con un test que lo fija (filosofía: un bug que no se
detecta vuelve):

| Bug | Test que lo fija | Tier |
| :-- | :-- | :-- |
| UI no arrancaba (`ImportError` tras el split) | smoke de importación | 4 |
| NVENC falso positivo sin GPU | `test_nvenc_available_false_on_nonzero` | 3 |
| Construcción de filtro ffmpeg | `test_build_filter_scale_has_operator` | 3 |
| Degradación sin canales gear/glat | casos de `compare` sin gear/glat | 1 |
| `freeze_support()` ausente → crash PyInstaller en Windows | `tests/test_main_gui.py` (AST) | 4 |
| Doble clic en "Generar overlay" lanzaba dos renders | `test_step3_render_guard.py` | 5 |
| Botones de tarjeta desalineados verticalmente (flexbox) | `test_pw_step0_button_alignment` | 6 |
| Texto invisible en botón seleccionado (contraste dark mode) | `test_pw_step0_selected_button_visibility` | 6 |

---

## Integración continua

`.github/workflows/tests.yml` corre `pytest --ignore=tests/ui/visual` en cada push y
PR, sobre **Windows** (plataforma objetivo) con Python 3.10–3.12. Cubre Tier 1–5.

Los tests Playwright (Tier 6) están en el repo pero **no corren en CI** — el job
`visual-smoke` solo verifica que los módulos importan. Para correrlos: ejecutar
`pytest tests/ui/visual/` en el laptop de desarrollo donde existen los CSVs reales
y Chromium instalado (`playwright install chromium`).

## Alternativas consideradas

- **unittest (stdlib)** — descartado: más verboso, sin fixtures parametrizadas tan
  cómodas. pytest no añade peso porque es solo dependencia de desarrollo.
- **Versionar telemetría real recortada como fixtures** — descartado: viola el
  principio "motor sin datos" y es menos legible que `make_lap`. Se reserva solo para
  los CSVs diminutos de `importers/` (donde el objeto bajo prueba *es* el parseo).
- **Tests E2E que invoquen ffmpeg/matplotlib** — descartado como base: lentos, frágiles
  y dependientes del entorno. La robustez de `compose`/`overlay` se cubre testeando sus
  helpers puros; el render real se sigue validando en el QA manual con video real.

---

## Estado de implementación

**193 tests** verdes (2026-07-02). CI en GitHub Actions corre Tier 1–5 en cada push/PR.

```
tests/
  conftest.py                        # make_lap + lap_factory: Lap sintética determinista
  test_main_gui.py                   # [T4] AST: freeze_support() en entry point PyInstaller
  test_cli.py                        # [T1] CLI end-to-end sin GPU/ffmpeg

  core/
    test_normalize.py                # [T1] rejilla, interpolación, gear discreto, split
    test_compare.py                  # [T1] delta=0 idénticas; lento→delta+; sin gear/glat
    test_corners.py                  # [T1] curvas por valle; ValueError sin speed; sin glat
    test_wear.py                     # [T1] slip/assist con y sin canales de rueda
    test_coaching.py                 # [T1] coaching adaptativo
    test_degradacion_canales.py      # [T1] degradación graceful con canales ausentes

  importers/
    fixtures/motec_mini.csv          # único dato versionado (24 filas sintéticas)
    test_motec_csv.py                # [T2] mapeo, metadatos, beacons, separador ';'
    test_generic_csv.py              # [T2] GUESS, mapeo manual, valores inválidos

  viz/
    test_compose.py                  # [T3] _build_filter + _nvenc_available (sin ffmpeg)
    test_compose_encoder.py          # [T3] selección de encoder
    test_overlay.py                  # [T3] helpers de overlay sin render real
    test_sync.py                     # [T3] aritmética offset/z-score sin scipy
    test_pacenotes.py                # [T3] generador WAV de pace notes

  ui/
    conftest.py                      # parche Storage.clear() para teardown Windows
    conftest_ng.py                   # fixtures NiceGUI testing (user, lap_factory)
    test_app_smoke.py                # [T4] smoke de importación (omitido si falta NiceGUI)
    test_ng_step0.py                 # [T4] contrato de ng_step0 (_FLOWS, render)
    test_ng_step1.py                 # [T4] contrato de ng_step1 (handle_upload, firmas)
    test_ng_step2.py                 # [T4] contrato de ng_step2
    test_ng_step3.py                 # [T4] contrato de ng_step3
    test_ng_step4.py                 # [T4] contrato de ng_step4
    test_ng_state.py                 # [T4] AppState: atributos, clear_drv, clear_ref
    test_paso1_estructura.py         # [T4] estructura del Paso 1
    test_paso3_estructura.py         # [T4] estructura del Paso 3
    test_paso4_estructura.py         # [T4] estructura del Paso 4
    test_step2_avisos.py             # [T5] wizard: avisos en Paso 2 (NiceGUI testing)
    test_step4_ffmpeg.py             # [T5] wizard: ffmpeg guard en Paso 4
    test_step3_render_guard.py       # [T5] wizard: guard doble clic "Generar overlay"
    test_e2e_wizard.py               # [T5] wizard 5 pasos con datos reales (NiceGUI testing)

  ui/visual/
    conftest.py                      # servidor NiceGUI en subprocess + fixture pw_page
    test_step0_visual.py             # [T6] screenshot Paso 0 vs baseline (PIL diff)
    test_e2e_playwright_wizard.py    # [T6] flujo clic a clic + aserciones visuales
```

**Resumen por tier:**

| Tier | Qué prueba | Tests | Corre en CI |
| :--- | :--- | ---: | :---: |
| 1 — `core/` puro | Matemáticas del motor | ~60 | ✅ |
| 2 — `importers/` | Parseo de CSV | ~15 | ✅ |
| 3 — `viz/` helpers puros | Helpers de render sin ffmpeg | ~25 | ✅ |
| 4 — Smoke y contrato UI | Importación, firmas, AST | ~50 | ✅ |
| 5 — NiceGUI testing framework | Comportamiento funcional del wizard | ~35 | ✅ |
| 6 — Playwright visual | Apariencia, colores, alineación | ~8 | ❌ (solo dev) |
