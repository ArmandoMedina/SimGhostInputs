# Benchmark — Framework UI para v2.0

> Por qué **NiceGUI (browser mode) + nicegui-pack + Inno Setup** y no las alternativas.
> Alimenta [ADR 0018](decisions/0018-framework-ui-nicegui.md) (enmienda al [ADR 0010](decisions/0010-framework-ui-streamlit.md)).

**Fecha de actualización:** 2026-06-30
**Contexto:** SimGhostInputs v1.0 usa Streamlit. La migración está decidida en dirección. El PO
confirma criterio determinante actualizado: **la UI debe correr en el browser del usuario**
(Chrome, Edge o Firefox instalado en su máquina), no en una ventana nativa empaquetada. Razón:
el browser es el denominador cross-platform común entre Windows, macOS y Linux; una ventana
pywebview en Linux depende de webkit2gtk que no siempre está.

Los objetivos por orden de prioridad:

1. **UI web en el browser del usuario — cross-platform.** El `.exe` levanta un servidor local
   y abre el browser. No pywebview, no Chromium bundleado, no ventana Flutter.
2. **Instalación doble-click en Windows — sin Python, sin terminal, sin PS1.**
   Un `.exe` descargable. Esto es el dolor #2 de ADR 0010 y es **innegociable para v2.0**.
3. **Sin techo de personalización UI** — preview reactiva del HUD, sliders con imagen en
   tiempo real, layouts arbitrarios, componentes custom.

Las deps científicas que el `.exe` debe incluir: `numpy`, `Pillow`, `matplotlib`, `scipy`,
`openpyxl`, `pandas`. El core (`fantasma/core/`, `fantasma/overlay/`, etc.) no se toca en
ningún escenario — solo la capa UI (`fantasma/ui/`).

---

## Criterio de entrada: web-based en el browser del usuario

Este criterio elimina de plano varios candidatos:

| Candidato | Modo de renderizado | Cumple criterio |
|:--|:--|:--|
| **NiceGUI** (modo default `native=False`) | `localhost` en el browser del usuario | SI |
| **Streamlit** | `localhost` en el browser del usuario | SI |
| **FastAPI + frontend custom** | `localhost` en el browser del usuario | SI |
| Electron | Chromium bundleado, ventana propia | NO — no usa el browser del usuario |
| NiceGUI `native=True` | Ventana pywebview (WebView nativo del OS) | NO — mismo problema que Electron/Tauri |
| Tauri | WebView nativo del OS | NO — Linux frágil sin webkit2gtk |
| pywebview | WebView nativo del OS | NO — Linux frágil |
| Flet | Flutter nativo | NO — no es web UI |
| Gradio | `localhost` en el browser del usuario | SI — pero orientado a ML demos, descartado |

**Nota importante:** NiceGUI tiene dos modos. `ui.run(native=False)` (default) abre el browser
del usuario — pasa el criterio. `ui.run(native=True)` abre una ventana pywebview — NO pasa el
criterio. Este benchmark recomienda **exclusivamente el modo `native=False`**.

---

## Parte 1 — Frameworks UI

| Framework | Browser del usuario | Personalización UI | Licencia | Costo migración desde Streamlit | Testabilidad | Activo (jun 2026) |
|:--|:--|:--|:--|:--|:--|:--|
| **NiceGUI** | SI — `localhost` default | Sin techo — Vue.js, HTML/CSS/JS, `ui.interactive_image` reactivo | **MIT** | Medio (3/5) — Python-first, modelo mental cercano a Streamlit | `user` fixture (pytest sin browser) + `screen` (Selenium) | v3.14.0 (30-jun-2026) |
| **Streamlit** (baseline) | SI | Limitado — slider per-tick requiere custom component React/Svelte | Apache 2.0 | 0 (ya está) | `AppTest` oficial | v1.45+ |
| **Flet** | NO — ventana Flutter nativa | Sin HTML/CSS | Apache 2.0 | Alto (4/5) — paradigma Flutter | Sin pytest fixture documentado | v0.85.3 pre-1.0, API en flujo |
| **Gradio** | SI | Limitado — orientado a demos ML | Apache 2.0 | Medio-alto (3.5/5) | Sin framework propio | Activo |
| **FastAPI + frontend custom** | SI | Total (hay que escribirlo) | MIT | Muy alto (5/5) — requiere HTML/CSS/JS desde cero | pytest-httpx + Playwright | Activo |

### Por qué NiceGUI gana entre los frameworks

**Modelo stateful sobre WebSocket.** NiceGUI corre un servidor FastAPI con conexión WebSocket
persistente por sesión. Un slider llama a un handler Python que ejecuta `image.set_source(pil)`
y empuja el update al browser sin rerun completo. Este es el patrón exacto que necesita la
preview reactiva del HUD.

**Packaging oficial documentado.** `nicegui-pack` es un wrapper de PyInstaller mantenido por
el mismo equipo de NiceGUI. Con `ui.run(native=False, reload=False)` la app levanta el servidor
local, abre el browser del sistema automáticamente y sirve la UI en `http://localhost:PUERTO`.
El `.exe` generado embebe Python y todas las deps — sin Python instalado en la máquina.

**v3.0 ya salió.** La versión anterior de este benchmark dejaba como incertidumbre "NiceGUI v3.0
en progreso". Resuelto: v3.14.0 se publicó el 30-jun-2026. No hay riesgo de breaking change
pendiente.

**Flet descartado.** Ventana Flutter nativa — no usa el browser del usuario. v0.85.x pre-1.0.
Sin pytest fixture para UI. El costo de migración es mayor que NiceGUI sin ninguna ventaja sobre
el criterio #1.

**Gradio descartado.** Diseñado para demos de ML de una pantalla, no para wizards de 5 pasos
con estado compartido. El packaging como `.exe` es un workaround frágil con problemas
documentados. Techo de personalización similar al de Streamlit.

**FastAPI + custom descartado.** Requiere que el mantenedor (vibe-coder, no programador web)
escriba y sostenga HTML/CSS/JS. Ese es el costo que ADR 0010 ya rechazó explícitamente.

---

## Parte 2 — Las cuatro preguntas clave del PO sobre NiceGUI

### P1. PyInstaller con deps científicas: factibilidad y tamaño del bundle

**SI es posible.** `nicegui-pack` (wrapper oficial de PyInstaller) genera un `.exe` con Python
embebido que incluye todas las deps. La documentación oficial contempla numpy vía
`--hidden-import numpy`. No es un workaround — es la ruta de distribución primera clase.

**Tamaño real estimado con el stack de SimGhostInputs:**

| Componente | Tamaño en bundle |
|:--|:--|
| Python runtime | ~15–20 MB |
| NiceGUI + FastAPI + Uvicorn | ~15–25 MB |
| numpy | ~20–25 MB |
| matplotlib | ~25–35 MB |
| scipy | ~45–60 MB |
| Pillow | ~4–6 MB |
| pandas | ~15–20 MB |
| openpyxl | ~5–8 MB |
| **Total `--onefile` comprimido** | **~200–350 MB** |
| **Total `--onedir` (carpeta)** | **~400–600 MB en disco, startup más rápido** |

**Nota:** los 40–80 MB de la versión anterior de este benchmark se basaban en NiceGUI solo,
sin el stack científico. Con scipy el rango real sube a 200–350 MB. La comunidad reporta 130 MB
sin deps científicas y hasta 700 MB sin optimización con numpy + matplotlib + plotly.
**Verificar con spike en PC objetivo antes de comunicar el tamaño al usuario final.**

### P2. El .exe: browser del usuario o ventana propia

**El .exe puede hacer ambas cosas. Para cumplir el criterio del PO: usar `native=False`.**

```python
# CORRECTO — abre el browser del usuario (Chrome, Edge, Firefox)
ui.run(native=False, reload=False, port=8080)
# Internamente hace: webbrowser.open("http://localhost:8080")
```

```python
# INCORRECTO para este proyecto — abre ventana pywebview (WebView nativo del OS)
ui.run(native=True, reload=False)
```

El `.exe` generado con `nicegui-pack --onedir app.py` más `ui.run(native=False)`:
1. El usuario hace doble-click en `SimGhostInputs.exe`
2. El proceso Python levanta el servidor FastAPI en `localhost:8080` (en background)
3. NiceGUI llama `webbrowser.open("http://localhost:8080")` — el browser del sistema se abre
   con la UI de SimGhostInputs
4. El usuario ve la app en una pestaña normal de su browser (Chrome, Edge, etc.)

**Caveat de UX a resolver:** cuando el usuario cierra el browser, el proceso Python sigue
corriendo en el background. Opciones para el cierre limpio:
- Icono en la bandeja del sistema (system tray) con opción "Cerrar SimGhostInputs" — patrón
  estándar en apps Electron/NiceGUI de escritorio
- Endpoint `/shutdown` que mata el proceso cuando se detecta cierre de la última pestaña
- Documentar al usuario: cerrar la ventana del browser no cierra el app; usar el ícono de
  la bandeja

Esto es un detalle de UX — no un bloqueador técnico.

### P3. Testing: equivalente a AppTest de Streamlit

**SI existe, y es la comparación más directa posible.**

NiceGUI incluye un plugin de pytest (`nicegui.testing.plugin`) con dos fixtures:

| Fixture NiceGUI | Equivalente Streamlit | Como funciona |
|:--|:--|:--|
| `user` | **AppTest** | Simula interacciones en Python. Sin browser real. Comparte el mismo event loop async. Velocidad de tests unitarios. |
| `screen` | Playwright smoke (ADR 0012) | Selenium headless. Para casos que requieren JS o CSS real. |

Ejemplo del fixture `user`:

```python
async def test_paso1_carga_archivo(user: User):
    await user.open('/')
    user.find('Cargar').click()
    await user.should_see('Paso 1 — Importar telemetría')
```

**Veredicto:** la cobertura de AppTest actual (lógica de flujos 0→4) se puede reproducir
directamente con el fixture `user`. El smoke visual con Playwright (ADR 0012) se puede mantener
o reemplazar con el fixture `screen`. La inversión en tests no se pierde.

### P4. Costo de reescritura: fantasma/ui/ — total vs adaptable

**La lógica de negocio se preserva. La capa de presentación se reescribe.**

| Archivo | Qué hay | Qué pasa en NiceGUI |
|:--|:--|:--|
| `app.py` (~212 líneas) | Routing, sidebar, navegación, CSS global | Reescritura total. La lógica de `_step_unlocked()` y `_step_done()` se conserva en Python. |
| `_helpers.py` (~296 líneas) | `_FLOWS`, `_STEPS`, helpers de archivo, background render | Parcialmente adaptable. `_FLOWS`, `_STEPS`, `_fmt_lap`, `_best_lap_index` son Python puro — se reusan. `st.session_state` → `app.storage.user` o dict global. `_start_bg_render`/`_render_widget` → `run.io_bound()` + `ui.timer()`. |
| `step0.py` (~110 líneas) | Hero, strip de 3 cards, selector de flujo | Reescritura del markup. La lógica (guardar `flow_key`, navegar) se reutiliza. |
| `step1.py` (~284 líneas) | File uploaders, lap table, mapeo de columnas, opciones avanzadas | Reescritura de presentación. `st.file_uploader` → `ui.upload`. `st.radio` → `ui.radio`. `st.expander` → `ui.expansion`. `st.data_editor` → `ui.aggrid`. Lógica de carga de laps: 100% reutilizable. |
| `step2.py` | Análisis, gráficas, tabla por curva | Reescritura de presentación. `st.pyplot`/`st.image` → `ui.image` con matplotlib renderizado a buffer. Lógica de `core/` intacta. |
| `step3.py` | Overlay render, progress bar, cancelar | Reescritura de presentación. Background render: threading + `st.rerun` → `run.io_bound()` + `ui.timer()`. Lógica de `core/overlay` intacta. |
| `step4.py` | Composición de video, progreso | Igual que paso 3. |

**Resumen:**
- `core/` completo: **0% de cambio** (ADR 0010 honrado)
- Lógica Python de la UI (flujos, validaciones, llamadas a core): **~30–40% reutilizable**
- Capa de presentación (widgets, layout, CSS): **100% reescritura** — pero es la parte thin
- Background render + progreso: **reescritura con patrón equivalente**, más limpio en NiceGUI
- Tests: **AppTest → fixture `user`**, traducción directa

**Estimación de esfuerzo:** 2–4 sesiones de vibe-coding. El mayor riesgo no es la cantidad de
código sino aprender el modelo mental de NiceGUI (event-driven vs rerun).

---

## Parte 3 — Empaquetadores e instaladores

| Herramienta | Qué hace | Con NiceGUI | Bundle size | Licencia |
|:--|:--|:--|:--|:--|
| **PyInstaller / nicegui-pack** | Empaqueta Python + deps en `.exe` o carpeta | Primera clase — `nicegui-pack` es PyInstaller oficial | 200–350 MB (ver P1) | GPL con excepción de bootloader — el `.exe` generado NO hereda GPL |
| **Inno Setup** | Toma la carpeta de PyInstaller y genera un instalador `.exe` profesional | Independiente del framework | +50–100 KB sobre el bundle | Freeware |
| **Nuitka** | Compila Python a C nativo antes de empaquetar | Alternativa a PyInstaller | ~10–30% menor | Apache 2.0 |
| **Tauri + sidecar** | Frontend Rust/WebView + Python sidecar | El sidecar sigue siendo PyInstaller | Sin ahorro neto sobre PyInstaller solo | MIT / Apache 2.0 |

### La combinación ganadora: nicegui-pack + Inno Setup

**nicegui-pack** genera el `.exe` con Python embebido. El usuario no instala Python.
`nicegui-pack --onedir app.py` produce una carpeta — preferir sobre `--onefile` (startup más
rápido porque no descomprime).

**Inno Setup** toma esa carpeta y construye un instalador profesional de Windows:
- Acceso directo en el Escritorio y en el Menú Inicio
- Aparece en "Agregar o quitar programas" con opción de desinstalar
- Se genera con ~60 líneas de script `.iss`

La experiencia del usuario final: descarga `SimGhostInputs-v2.0-Setup.exe`, doble-click, "Siguiente" tres veces, el ícono aparece en el Escritorio. Doble-click en el ícono → se abre su browser con la app.

**Por qué no Nuitka ahora.** Compilar el stack científico tarda 30–60 minutos. Para ciclos de
release frecuentes, eso mata el flujo. Reevaluar si hay reportes de false positives de antivirus.

**Por qué no Tauri + sidecar.** Si el sidecar lleva numpy + scipy + PIL + matplotlib, pesa
200–350 MB igual que PyInstaller solo — no hay ahorro neto. Añade Rust + Node.js + Tauri CLI
al toolchain. Sin contrapartida.

---

## Veredicto

**NiceGUI (modo `native=False`) + nicegui-pack + Inno Setup.**

- **Objetivo #1 (browser del usuario):** `ui.run(native=False)` → el `.exe` levanta el servidor
  y abre el browser del usuario automáticamente. Cross-platform por diseño.
- **Objetivo #2 (doble-click):** nicegui-pack → carpeta con Python embebido. Inno Setup →
  instalador estándar de Windows. Sin terminal, sin Python, sin PS1.
- **Objetivo #3 (sin techo UI):** NiceGUI permite Vue.js, HTML/CSS/JS, `ui.interactive_image`
  para el HUD reactivo.

Beneficios secundarios:
- MIT — sin fricción de licencia con AGPL-3.0
- Testing: fixture `user` (= AppTest) + `screen` (= Playwright smoke)
- `core/` no se toca — solo `fantasma/ui/`
- NiceGUI v3.14.0 estable a la fecha de este benchmark

---

## Lo que se descartó y por qué

**Streamlit** — Sin ruta oficial a `.exe`. El dolor de instalación queda sin resolver. El
slider per-tick para la preview del HUD requiere un custom component React/Svelte — mismo
costo que migrar a NiceGUI pero sin resolver la distribución.

**Flet** — Ventana Flutter nativa, no usa el browser del usuario. v0.85.x pre-1.0 con API en
flujo. Sin pytest fixture. Costo de migración mayor sin ventaja alguna sobre NiceGUI.

**Gradio** — Diseñado para demos de ML de una pantalla. Packaging frágil. Descartado.

**NiceGUI native=True** — Abre ventana pywebview. No pasa el criterio del PO de "browser del
usuario". En Linux depende de webkit2gtk que no siempre está. Descartado para este proyecto.

**Tauri + sidecar** — Sin ahorro de tamaño con el stack científico. Añade Rust + Node.js al
toolchain. Descartado.

**Nuitka** — Buena tecnología para cuando el antivirus sea un problema real. Hoy no lo es.
Reevaluar cuando haya reportes concretos de false positives.

**FastAPI + frontend custom** — El PO no quiere sostener HTML/CSS/JS. Descartado (igual que
en ADR 0010).

---

## Incertidumbres pendientes (spike antes de migrar)

| Incertidumbre | Cómo verificar | Impacto si falla |
|:--|:--|:--|
| Bundle size real con stack completo en Windows 11 | `nicegui-pack --onedir` en venv limpio; medir tamaño de carpeta | Solo comunicación al usuario; no bloquea la decisión |
| Bug de `--onefile` en Windows 11 con NiceGUI | Probar en VM limpia Windows 11 24H2 | Usar `--onedir` + Inno Setup en su lugar (preferido de todas formas) |
| Mecanismo de cierre del proceso cuando se cierra el browser | Prototipar icono en bandeja del sistema con pystray | Si es complejo, documentar al usuario como workaround |
| Latencia PIL per-tick en HUD preview | Prototipo: slider → composición PIL → `image.set_source()` → medir latencia percibida | Si >100 ms perceptible, procesar en `run.io_bound()` |
| AV false positives en el `.exe` de PyInstaller | Subir bundle a VirusTotal | Si hay flagging, evaluar firma de código o migrar a Nuitka |
| `ui.upload` con archivos grandes (CSVs 10–50 MB) | Probar upload en prototipo | Configurar `max_upload_size` en `ui.run()` |

---

## Plan de migración de alto nivel

La migración toca exclusivamente `fantasma/ui/`. El core no cambia.

**Paso 0 — Spike (1–2 días)**
- Crear venv limpio: `pip install nicegui numpy Pillow matplotlib scipy openpyxl pandas`
- Prototipo mínimo: `ui.run(native=False, reload=False)` — confirmar que abre el browser
- Correr `nicegui-pack --onedir` y medir bundle size real
- Verificar sistema tray o mecanismo de cierre del proceso

**Paso 1 — Skeleton (1 día)**
- Crear `fantasma/ui/ng_app.py` con `ui.run(native=False, reload=False)`
- Sidebar (`ui.left_drawer`) con navegación de 5 pasos
- Estado de sesión (`app.storage.user` o dict global)
- Mantener `fantasma/ui/app.py` (Streamlit) en paralelo hasta que la migración esté completa

**Paso 2 — Portar cada paso (3–5 días)**
- `step0.py` → selector de flujo con `ui.radio` / `ui.card`
- `step1.py` → file upload con `ui.upload`, tabla con `ui.aggrid` o `ui.table`
- `step2.py` → gráficas matplotlib con `ui.matplotlib` o `ui.image`
- `step3.py` → generación de overlay con `ui.spinner` + `run.io_bound()`
- `step4.py` → composición de video

**Paso 3 — HUD preview reactiva (2–3 días)**
- Slider de posición del HUD → `ui.slider` con handler Python
- Composición PIL en thread → `image.set_source(buffer)` por WebSocket
- Medir latencia y ajustar resolución de preview si es necesario

**Paso 4 — Empaquetado (1 día)**
- `nicegui-pack --onedir --name SimGhostInputs --icon icon.ico app.py`
- Script `.iss` de Inno Setup: shortcut, uninstaller, versión
- Probar el instalador en VM limpia (sin Python)

**Paso 5 — CI (0.5 días)**
- Job en `.github/workflows/release.yml` que corra en `windows-latest`
- Genera el instalador en cada tag y sube el artefacto al GitHub Release
