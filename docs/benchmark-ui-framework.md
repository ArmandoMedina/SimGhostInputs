# Benchmark — Framework UI para v2.0

> Por qué **NiceGUI (ventana nativa) + nicegui-pack + Inno Setup** y no las alternativas.
> Alimenta [ADR 0018](decisions/0018-framework-ui-nicegui.md) (enmienda al [ADR 0010](decisions/0010-framework-ui-streamlit.md)).

**Fecha de actualización:** 2026-07-01
**Contexto:** SimGhostInputs v1.0 usa Streamlit. La migración está decidida en dirección. El PO
confirma el criterio determinante: **la UI debe darle al usuario una experiencia de app de
escritorio** (una ventana propia que se abre y se cierra como cualquier programa de Windows),
con tecnologías web (HTML/CSS) bajo el capó. Esto se logra con `ui.run(native=True)`, que abre
una ventana **pywebview** usando el motor web embebido del sistema — el usuario no ve `localhost`,
no ve pestañas de browser, no ve terminal. El código sigue siendo web por dentro, así que el
mismo `.exe` corre igual en macOS y Linux (donde el modo `native=False` sirve como alternativa
para dev y para plataformas sin webkit2gtk).

> **Nota de reconciliación (2026-07-01):** una versión anterior de este benchmark fijaba
> `native=False` (abrir el browser del sistema) como criterio innegociable y descartaba
> `native=True`. El PO revisó esa premisa: para el usuario zero-técnico, abrir el browser del
> sistema crea confusión (pestañas, servidor colgado en segundo plano, no sabe cómo cerrar). La
> decisión correcta es `native=True` — combina HTML/CSS multiplataforma con la UX de una app de
> escritorio de Windows. Este documento ya refleja esa decisión.

Los objetivos por orden de prioridad:

1. **Experiencia de app de escritorio (pywebview nativo) — web bajo el capó.** El `.exe` abre
   una ventana propia con `ui.run(native=True)`; la UI la renderiza el motor web embebido del OS.
   Sin browser visible, sin `localhost` a la vista, sin ventana Flutter. Como el motor es web,
   el mismo código es multiplataforma (`native=False` cubre dev/macOS/Linux).
2. **Instalación doble-click en Windows — sin Python, sin terminal, sin PS1.**
   Un `.exe` descargable. Esto es el dolor #2 de ADR 0010 y es **innegociable para v2.0**.
3. **Sin techo de personalización UI** — preview reactiva del HUD, sliders con imagen en
   tiempo real, layouts arbitrarios, componentes custom.

Las deps científicas que el `.exe` debe incluir: `numpy`, `Pillow`, `matplotlib`, `scipy`,
`openpyxl`, `pandas`. El core (`fantasma/core/`, `fantasma/overlay/`, etc.) no se toca en
ningún escenario — solo la capa UI (`fantasma/ui/`).

---

## Criterio de entrada: experiencia de app de escritorio (pywebview nativo), web bajo el capó

El criterio combina dos exigencias: (a) el usuario final ve una **ventana de app de escritorio**
propia (no una pestaña de browser ni una terminal) y (b) por dentro es **web** (HTML/CSS), para
no reescribir la UI en un toolkit nativo y conservar la portabilidad. Con esa lente:

| Candidato | Modo de renderizado | Cumple criterio |
|:--|:--|:--|
| **NiceGUI** `native=True` | Ventana **pywebview** (motor web embebido del OS); HTML/CSS bajo el capó | SI — decisión tomada |
| NiceGUI `native=False` | `localhost` + browser del sistema | Parcial — útil solo para dev/macOS/Linux, no es la entrega final |
| **Streamlit** | `localhost` + browser del sistema | NO — sin ventana propia ni ruta oficial a `.exe` |
| **FastAPI + frontend custom** | `localhost` + browser del sistema | NO — igual que Streamlit y hay que escribir el front |
| Electron | Chromium bundleado, ventana propia | Parcial — logra la ventana pero suma un runtime JS pesado |
| Tauri | WebView nativo del OS | Parcial — Linux frágil sin webkit2gtk; añade Rust + Node |
| pywebview solo | WebView nativo del OS | Parcial — daría la ventana pero habría que construir toda la UI a mano |
| Flet | Flutter nativo | NO — no es web UI (widgets Flutter tipados) |
| Gradio | `localhost` + browser del sistema | NO — sin ventana propia; orientado a ML demos |

**Nota importante:** NiceGUI tiene dos modos y aquí conviven los dos. `ui.run(native=True)` abre
una ventana pywebview — **es el modo de entrega del `.exe`** para el usuario final y la decisión
del PO. `ui.run(native=False)` sirve en `localhost` y abre el browser — se usa en desarrollo y
como alternativa en macOS/Linux. Mismo código, distinto modo de entrega.

---

## Parte 1 — Frameworks UI

| Framework | Browser del usuario | Personalización UI | Licencia | Costo migración desde Streamlit | Testabilidad | Activo (jun 2026) |
|:--|:--|:--|:--|:--|:--|:--|
| **NiceGUI** | NO — ventana pywebview (`native=True`); `localhost` en dev/macOS/Linux | Sin techo — Vue.js, HTML/CSS/JS, `ui.interactive_image` reactivo | **MIT** | Medio (3/5) — Python-first, modelo mental cercano a Streamlit | `user` fixture (pytest sin browser) + `screen` (Selenium) | v3.14.0 (30-jun-2026) |
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
el mismo equipo de NiceGUI. Con `ui.run(native=True, reload=False)` la app levanta el servidor
local y abre una ventana pywebview — el usuario no ve localhost, no ve browser, no ve terminal.
El `.exe` generado embebe Python y todas las deps — sin Python instalado en la maquina.

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

**El .exe puede hacer ambas cosas. Para cumplir el criterio del PO: usar `native=True`.**

```python
# CORRECTO — abre ventana pywebview (WebView nativo del OS); sin browser visible
ui.run(native=True, reload=False)
```

```python
# SOLO PARA DEV/macOS/Linux — abre el browser del sistema
ui.run(native=False, reload=False, port=8080)
# Internamente hace: webbrowser.open("http://localhost:8080")
```

El `.exe` generado con `nicegui-pack --onedir app.py` mas `ui.run(native=True)`:
1. El usuario hace doble-click en `SimGhostInputs.exe`
2. El proceso Python levanta el servidor FastAPI en `localhost:PUERTO` (en background)
3. NiceGUI abre una ventana **pywebview** — el motor web embebido del OS renderiza la UI
4. El usuario ve la app en una ventana propia (sin browser, sin pestaña, sin localhost a la vista)

**Caveat de UX a resolver:** pywebview abre la ventana inmediatamente pero la UI tarda ~1-2 s
en estar lista (servidor levantando). Opciones:
- Pantalla de carga (splash) mientras el servidor inicializa — soporte oficial en NiceGUI
- `ui.run(native=True, show=False)` y mostrar la ventana solo cuando la UI este lista
- En Linux: webkit2gtk es requisito; si no esta instalado, caer a `native=False` automaticamente

Esto es un detalle de UX — no un bloqueador tecnico.

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

La experiencia del usuario final: descarga `SimGhostInputs-v2.0-Setup.exe`, doble-click, "Siguiente" tres veces, el icono aparece en el Escritorio. Doble-click en el icono: se abre una ventana propia con la app (sin browser, sin terminal).

**Por qué no Nuitka ahora.** Compilar el stack científico tarda 30–60 minutos. Para ciclos de
release frecuentes, eso mata el flujo. Reevaluar si hay reportes de false positives de antivirus.

**Por qué no Tauri + sidecar.** Si el sidecar lleva numpy + scipy + PIL + matplotlib, pesa
200–350 MB igual que PyInstaller solo — no hay ahorro neto. Añade Rust + Node.js + Tauri CLI
al toolchain. Sin contrapartida.

---

## Veredicto

**NiceGUI (modo `native=True`) + nicegui-pack + Inno Setup.**

- **Objetivo #1 (ventana propia de escritorio, web bajo el capó):** `ui.run(native=True)` → el `.exe`
  abre una ventana pywebview con motor web embebido. Sin browser visible, sin localhost a la vista.
  Cross-platform: `native=False` cubre dev y macOS/Linux.
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

**NiceGUI native=False (como modo de entrega)** — Abre el browser del sistema. Para el usuario
zero-tecnico genera confusion: pestanas abiertas, proceso colgado en segundo plano, no sabe
como cerrar. Valido como modo de dev y como fallback en macOS/Linux sin webkit2gtk, pero NO
es la entrega final para Windows.

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
- Prototipo mínimo: `ui.run(native=True, reload=False)` — confirmar que abre ventana pywebview
- Correr `nicegui-pack --onedir` y medir bundle size real
- Verificar sistema tray o mecanismo de cierre del proceso

**Paso 1 — Skeleton (1 día)**
- Crear `fantasma/ui/ng_app.py` con `ui.run(native=True, reload=False)`
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
