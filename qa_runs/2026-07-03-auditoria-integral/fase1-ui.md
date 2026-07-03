# Auditoría UI — fantasma/ui/ — v2.0.0-pre (rama codex/sgi-v2-merge)

**Fecha:** 2026-07-03  
**Rama:** codex/sgi-v2-merge  
**Área auditada:** `fantasma/ui/` (NiceGUI) + `tests/ui/`  
**Auditor:** Claude Sonnet 4.6

---

## Veredicto

**La migración a NiceGUI está funcional pero tiene fugas de disco graves y al menos dos rutas
que bloquean el event loop en operaciones pesadas. El flujo feliz está cubierto por tests;
los caminos de error y el comportamiento al navegar en medio de un render no lo están.**

---

## Conteo por severidad

| Severidad | Hallazgos |
|-----------|-----------|
| Crítico   | 2         |
| Mayor     | 5         |
| Menor     | 6         |
| **Total** | **13**    |

---

## Framework activo

El código ejecutable en producción es **NiceGUI**. Los archivos
`fantasma/ui/app.py`, `step0.py`–`step4.py` y `_helpers.py` son código Streamlit
legacy que coexiste en el mismo paquete pero ya no se referencia desde ningún
entry-point. Los `ng_*.py` son los archivos activos.

---

## Hallazgos — CRÍTICO

### C-01 — Archivos temporales de uploads nunca se borran

**Archivos:** `fantasma/ui/ng_helpers.py:106-112`, `ng_step1.py:148-149`, `ng_step1.py:158-159`, `ng_step4.py:148-151`

`_save_upload()` crea un `NamedTemporaryFile(delete=False, ...)`, escribe los bytes
y devuelve la ruta. Nunca borra el archivo. Los llamadores (Step 1 upload handlers y el
upload de sync en Step 4) no almacenan la ruta para limpieza posterior y tampoco
registran ningún atexit/finalizer.

Con CSVs de telemetría de 30–60 MB (como los del material de test), cada par de uploads
acumula 60–120 MB en el directorio temporal del sistema. Con sesiones repetidas (uso
normal de desarrollo), el disco se llena sin aviso. En PyInstaller native mode, el
directorio temporal del bundle tiene límites más estrictos.

**Impacto:** Llenado de disco acumulado. Sin test que lo detecte.

**Corrección mínima:** Envolver en un try/finally y llamar `os.unlink(path)` cuando
se garantice que los bytes ya fueron parseados y el objeto Lap reside en memoria; o
registrar las rutas en `AppState` y limpiarlas en `clear_drv()` / `clear_analysis()`.

---

### C-02 — `detect_corners()` bloquea el event loop en Step 3

**Archivo:** `fantasma/ui/ng_step3.py:49-57`

```python
if not corners:
    try:
        from fantasma.core.corners import detect_corners, extract_milestones
        _evs, _ = detect_corners(ref_lap)
        corners = extract_milestones(ref_lap, _evs)
        state.corners = corners
    except Exception:
        corners = []
```

Esta llamada ocurre en la función `async def render(state, navigate)` —
que corre en el event loop de asyncio — sin ningún `await run.io_bound(...)`.
`detect_corners()` sobre una vuelta de Nordschleife (>20 km, miles de muestras)
es CPU-intensivo y puede tardar varios segundos. Mientras corre, el event loop
de NiceGUI está congelado: no responde a clics del usuario, no actualiza la UI
y bloquea otras conexiones activas en modo servidor.

Por contraste, Step 2 usa `await run.io_bound(_do_compare)` correctamente.

**Impacto:** UI congelada al entrar al Paso 3 con datos cargados por primera vez.

**Corrección:** Envolver en `await run.io_bound(lambda: detect_corners_and_extract(ref_lap))`,
igual que Step 2 hace con `compare`.

---

## Hallazgos — MAYOR

### M-01 — Timers de render no se cancelan al navegar mid-render (Steps 3 y 4)

**Archivos:** `fantasma/ui/ng_step3.py:221`, `ng_step4.py:536`

Cuando el usuario inicia un render y luego navega a otro paso, `navigate()` en
`ng_app.py:190` llama `content.clear()`, que destruye todos los elementos DOM
del paso actual (incluyendo `progress_bar`, `status_label`, `cancel_btn`).
Sin embargo, el `ui.timer(0.5, poll)` sigue vivo porque `job_holder` y el timer
pertenecen a la closure de `render()` anterior, inaccesible desde la nueva.

Cuando el timer dispara y `poll()` intenta llamar `progress_bar.set_value()` o
`progress_bar.delete()` sobre elementos ya eliminados, NiceGUI puede lanzar
excepciones internas. Cuando el job termina, el resultado se escribe correctamente
en `state.last_overlay` (ya que el state persiste), pero el usuario no recibe
ninguna notificación porque el área de resultado ya no existe en el DOM.

El problema está documentado indirectamente en `tests/ui/test_step3_render_guard.py:42-53`
(usa `_NoOpTimer` para evitar el RuntimeError en teardown de Windows).

**Impacto:** Timers fantasma acumulados por sesión; logs de error silenciosos; el
usuario que navega durante un render no sabe si terminó.

**Sin test:** No hay test que verifique el comportamiento de navegar mid-render.

**Corrección:** `navigate()` debe cancelar el timer activo antes de limpiar el
contenido. Exponer el timer actual en `AppState` o en una variable de módulo por
cliente para que `navigate()` pueda cancelarlo.

---

### M-02 — Generación de gráficas y lectura de imágenes bloquean el event loop (Step 2)

**Archivo:** `fantasma/ui/ng_step2.py:194-208`, `289-294`, `325-330`, `341-346`

Dos problemas distintos en la misma función `render()`:

1. `render_charts(trace, rows, ...)` (línea 200) es una llamada matplotlib bloqueante
   que corre directamente en el event loop sin `await run.io_bound(...)`. Para un
   Nordschleife con 70+ curvas puede tardar decenas de segundos.

2. La lectura de archivos de imagen (open/read en líneas 289-294, 325-330, 341-346)
   también ocurre en el event loop. Para múltiples PNGs de 400 px no es grave, pero
   suma al bloqueo total del renderizado.

Step 2 sí usa `run.io_bound` para el `compare()`, pero no para el paso posterior de
generación de gráficas.

**Impacto:** UI congelada durante la generación de gráficas; peor en Nordschleife.

**Corrección:** Envolver `render_charts(...)` en `await run.io_bound(...)`.

---

### M-03 — Directorio temporal de gráficas nunca eliminado

**Archivo:** `fantasma/ui/ng_step2.py:195`

```python
_out = tempfile.mkdtemp()
```

Se crea un directorio temporal nuevo en cada sesión de análisis (cada vez que
`state.charts_paths is None`). La ruta del directorio no se almacena en `AppState`,
solo se almacenan las rutas de los archivos individuales en `state.charts_paths`.
No hay limpieza al cerrar la app, al iniciar nueva sesión, ni en `clear_analysis()`.

Con renders recurrentes (flujo overlay o compose, donde el usuario puede hacer
múltiples análisis en una sesión), los directorios se acumulan indefinidamente.

**Impacto:** Fuga de disco adicional a C-01; en PyInstaller con tmp en el bundle,
puede causar fallo de arranque al reabrir la app.

**Corrección:** Guardar `_out` en `AppState` (p.ej. `state.charts_tmpdir`) y limpiar
en `clear_analysis()` con `shutil.rmtree(old_dir, ignore_errors=True)`.

---

### M-04 — `_pick_file()` y `_pick_folder()` bloquean el event loop

**Archivos:** `fantasma/ui/ng_helpers.py:131-164`, `ng_step3.py:83-92`, `ng_step4.py:81-91`, `ng_step4.py:101-112`, `ng_step4.py:364-373`

Los handlers de los botones "Explorar..." son funciones `def` síncronas que llaman
`filedialog.askopenfilename()` / `filedialog.askdirectory()` de tkinter. Estas son
llamadas bloqueantes que suspenden el hilo hasta que el usuario cierra el diálogo.

En NiceGUI, un handler síncrono registrado con `on_click` no se descarga a un executor
automáticamente — se ejecuta en el contexto del event loop (como coroutine parcial).
Esto bloquea el asyncio loop durante todo el tiempo que el diálogo permanezca abierto.

En modo nativo (PyInstaller), el impacto es tolerable porque hay un solo usuario.
En modo servidor (SGI_HEADLESS=1, el modo de Playwright), bloquea todas las conexiones.

**Sin test:** No hay test en modo web que verifique que el botón "Explorar..." no
bloquea otras solicitudes.

**Corrección mínima:** Envolver la llamada en `await run.io_bound(lambda: _pick_file(...))`.

---

### M-05 — `_best_lap_index()` selecciona la vuelta 0 silenciosamente cuando ninguna es completa

**Archivo:** `fantasma/ui/ng_helpers.py:83-88`

```python
def _best_lap_index(laps):
    best_i, best_t = 0, float("inf")
    for i, l in enumerate(laps):
        if l.meta.get("is_complete") and l.laptime < best_t:
            best_t, best_i = l.laptime, i
    return best_i
```

Si ninguna vuelta tiene `is_complete=True` (caso típico en out-laps o sesiones
interrumpidas), el bucle nunca entra en la rama `if`, y `best_i` devuelve 0.
La vuelta 0 puede ser un out-lap de 3 minutos que nunca cruzó la meta. El usuario
no recibe aviso de que se seleccionó una vuelta incompleta.

Impacto directo: la vuelta seleccionada por defecto en Step 1 es la vuelta 0, que
puede ser inútil para análisis, y el análisis en Step 2 corre sin avisar que los
datos son de una vuelta incompleta.

**Sin test:** No hay test con un CSV en que todas las vueltas sean incompletas.

**Corrección:** Si `best_t == float("inf")` al salir del bucle, retornar el índice de
la vuelta con menor laptime (sin filtro de completitud) y emitir una advertencia en la UI.

---

## Hallazgos — MENOR

### m-01 — Rutas absolutas hardcodeadas en tests

**Archivos:** `tests/ui/test_e2e_wizard.py:37-40`, `tests/ui/visual/test_e2e_playwright_wizard.py:27-34`

```python
_MATERIAL = Path(r"C:\Repositorio personal\Paterial para test (no es un repo)")
```

Las rutas son absolutas a la máquina de desarrollo. Los tests se marcan con `skipif`
cuando los CSVs no existen, por lo que CI no falla. Pero ningún colaborador puede
ejecutar estos tests sin reproducir manualmente la estructura de directorios.

**Corrección:** Leer la ruta de una variable de entorno `SGI_TEST_MATERIAL` con
fallback al path hardcodeado.

---

### m-02 — Archivos Streamlit legacy coexisten con NiceGUI activo

**Archivos:** `fantasma/ui/app.py`, `step0.py`–`step4.py`, `_helpers.py`

Los seis archivos legacy importan `streamlit as st` en el nivel de módulo. Si streamlit
no está instalado (que es el caso en un entorno solo con `[ui-ng]`), cualquier
`import fantasma.ui` que cargue estos módulos lanzará `ImportError`. Actualmente
`fantasma/ui/__init__.py` está vacío y los archivos legacy no se importan
automáticamente, por lo que el riesgo es latente pero real si alguien añade
una importación de conveniencia.

También crean confusión sobre qué código es el activo para revisión y mantenimiento.

**Corrección:** Mover los archivos legacy a `fantasma/ui/_legacy_streamlit/` o borrarlos.

---

### m-03 — `storage_secret` hardcodeado

**Archivo:** `fantasma/ui/ng_app.py:288`

```python
storage_secret="sgi-v2-secret",
```

Para una app single-user local está bien. Si alguna vez se despliega en red,
permite que cualquier cliente forge cookies de sesión. Debería leerse de
`os.environ.get("SGI_STORAGE_SECRET", "sgi-v2-secret")`.

---

### m-04 — Puerto 8765 hardcodeado sin fallback

**Archivos:** `fantasma/ui/ng_app.py:290`, `tests/ui/visual/conftest.py:7`

Si el puerto está ocupado, la app falla al arrancar sin mensaje explicativo.
El conftest visual no detecta el error de bind y espera 30 s antes de hacer skip.

**Corrección:** Leer `int(os.environ.get("SGI_PORT", 8765))`.

---

### m-05 — Comentario inconsistente en test_ng_state.py

**Archivo:** `tests/ui/test_ng_state.py:77`

```python
# Nota: drv_name no esta en la lista de clear_drv(); no se elimina.
```

El comentario es incorrecto. `clear_drv()` en `ng_state.py:218` sí incluye
`"drv_name"` en su lista. El test posterior `test_appstate_clear_drv_removes_drv_name`
(línea 109) lo verifica correctamente. Solo el comentario del test anterior es
una reliquia de una versión anterior del código.

---

### m-06 — `import pandas as _pd` dentro del cuerpo de render()

**Archivo:** `fantasma/ui/ng_step2.py:220`

El import dinámico dentro de la función async es válido en Python pero dificulta
el análisis estático de dependencias. Si pandas no está instalado, el error aparece
en la mitad del renderizado del Paso 2 (después de que el análisis ya completó),
en lugar de fallar temprano con un mensaje claro.

**Corrección:** Mover el import al nivel de módulo y envolver en try/except con
un mensaje al usuario equivalente al que ya existe para matplotlib (línea 202-203).

---

## Cobertura de tests vs hallazgos

| Hallazgo | Cubierto por test |
|----------|-------------------|
| C-01 Temp file leak | No |
| C-02 detect_corners en event loop | No |
| M-01 Timer orphan mid-render | No (documentado como limitación conocida) |
| M-02 render_charts en event loop | No |
| M-03 mkdtemp nunca limpiado | No |
| M-04 _pick_file bloquea | No |
| M-05 _best_lap_index silencioso | No |
| m-01 Rutas hardcodeadas | N/A (tests con skip) |
| m-02 Legacy Streamlit | N/A |
| m-03 storage_secret | N/A |
| m-04 Puerto hardcodeado | N/A |
| m-05 Comentario incorrecto | N/A |
| m-06 import pandas en render | No |

**Lo que sí está bien cubierto:**
- AppState: propiedades, clear_analysis(), clear_drv() — unit tests exhaustivos
- Guards de paso (sin datos, sin ffmpeg) — smoke tests para Steps 0-4
- Double-click guard en render Step 3 — test de regresión dedicado
- Flujo feliz E2E: selector de flujo, uploads, análisis, overlay — tests NiceGUI + Playwright
- Contraste visual y alineación de botones en Step 0 — Playwright visual tests
- Manejo de errores de usuario (mensajes, no stack traces) — cubierto implícitamente

---

## Los 3 hallazgos más graves

1. **C-01** — `ng_helpers.py:106-112`: uploads CSV crean temp files con `delete=False` que nunca se borran; 60-120 MB por sesión acumulados sin límite.
2. **C-02** — `ng_step3.py:49-57`: `detect_corners()` corre bloqueante en el event loop de asyncio al entrar al Paso 3, congelando toda la UI durante varios segundos.
3. **M-01** — `ng_step3.py:221` / `ng_step4.py:536`: `ui.timer` del render activo no se cancela al navegar; el timer sigue disparando sobre elementos DOM eliminados y el usuario no recibe confirmación del fin del render.
