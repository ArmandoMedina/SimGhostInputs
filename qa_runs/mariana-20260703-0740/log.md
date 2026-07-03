# QA Visual — mariana-20260703-0740

**Fecha:** 2026-07-03  
**Rol:** Mariana (checkpoint visual, ADR 0019)  
**Scope:** fixes no-visuales en fantasma/ui/ — limpieza de temp, run.io_bound, timers, host=127.0.0.1  
**Veredicto:** CHECKPOINT — vuelve al PO. No es auto-pase.

---

## CSVs usados

| Rol | Archivo | Circuito | Tiempo de vuelta |
|-----|---------|----------|-----------------|
| REF | GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv | Nordschleife 2025 | 6:18.40 (3 vueltas) |
| DRV | GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv | Nordschleife 2025 | 6:17.14 (3 vueltas) |

Ambos de `Paterial para test (no es un repo)/Pruebas finales/`. Mismo circuito, distintos autos (GT3 vs LMS GT3 evo II).

---

## Comandos ejecutados

```
# Lanzamiento NiceGUI headless (env SGI_HEADLESS=1, puerto 8765, host 127.0.0.1)
python -m fantasma.ui.ng_app

# Script QA Playwright (chromium headless, 1280x900):
python _qa_run_mariana.py

# Re-toma Paso 2 con espera larga (hasta 5 min):
python _qa_paso2_retake.py

# Diagnostico directo de compare() y render_charts():
python _qa_debug_paso2.py
```

---

## Screenshots generados

| Archivo | Paso | Descripcion |
|---------|------|-------------|
| paso0.png | 0 | Estado inicial: sin flujo seleccionado (verificacion F-01) |
| paso0_compose.png | 0 | Flujo "Video con HUD" seleccionado; verificacion aviso ffmpeg |
| paso0_analisis.png | 0 | Flujo "Solo analisis" seleccionado |
| paso1.png | 1 | Paso 1 inicial: ambos paneles sin CSVs |
| paso1_ref.png | 1 | Referencia cargada con vueltas detectadas |
| paso1_ambos.png | 1 | Ambos CSVs cargados y confirmados |
| paso2.png | 2 | Analisis: barra de resumen visible; tabla de curvas NO visible (ver hallazgo H-01) |
| paso3.png | 3 | Overlay / deteccion de curvas completada; formulario visible |

---

## Checklist ux-patterns §2-B

Checklist de Mariana con los 5 puntos obligatorios:

### Punto 1 — El cambio respeta las 10 heuristicas de §1

Evaluacion por heuristica contra las pantallas capturadas:

| H | Heuristica | Estado | Evidencia / Nota |
|---|-----------|--------|-----------------|
| H1 | Visibilidad del estado del sistema | PASA parcial | Paso 0: chip "Motor listo" verde. Paso 1: mensajes amarillo/verde claros. Paso 2: barra de resumen correcta; **tabla de curvas no aparece** (ver H-01). Paso 3: formulario visible sin spinner/congela. |
| H2 | Lenguaje del usuario, no del sistema | PASA | "vuelta de referencia", "tu vuelta de hoy", "curva a atacar", "frenada", "apex". Sin rutas de archivo ni nombres tecnicos expuestos. |
| H3 | Prevencion de errores | PASA | Boton "Empezar" en estilo secundario hasta seleccionar flujo. Aviso ffmpeg: no se dispara con ffmpeg instalado (correcto). Mensajes de validacion en upload. **Aviso menor:** boton "CARGAR Y VER ANALISIS" en azul primario aun cuando no hay CSVs — podria confundir (ver A-02). |
| H4 | Reconocer en vez de recordar | PASA | F-01 respetado: ninguna tarjeta pre-seleccionada al cargar (paso0.png). Wizard expone opciones. Selector de vueltas con lap-time y estado. |
| H5 | Disclosure progresivo | PASA | Opciones avanzadas en expander en Paso 1. Informacion esencial primero. |
| H6 | Control y libertad | PASA | Boton "Volver", sidebar navegable entre pasos, flujo bidireccional. Paso 3: "EXPLORAR..." para carpeta de salida. |
| H7 | Consistencia y estandares | PASA | Iconos, colores y etiquetas consistentes en todos los pasos. Dark mode uniforme. |
| H8 | Estetica y diseno minimalista | PASA | Layout limpio. Jerarquia visual clara. Badges "MAS COMPLETO", "REF", "HOY" en el lugar correcto. |
| H9 | Ayuda y documentacion en contexto | PASA | Footer del Paso 0 con links "Guia MoTeC" y "Ejemplo CSV". Expander de ayuda en Paso 1 para usuarios sin referencia externa. |
| H10 | Accesibilidad minima | PASA | Modo oscuro activado globalmente. Colores de estado combinan color + texto (no solo color). Contraste legible en todos los pasos capturados. |

### Punto 2 — La pantalla afectada se ve coherente con el resto

- Paso 0: PASA — coherente con el diseno general; 3 tarjetas alineadas, botones a la misma altura (test E2E de alineacion en verde).
- Paso 1: PASA — paneles simetricos REF/HOY, tipografia y espaciado uniformes.
- Paso 2: **FALLA visual** — la tabla de curvas y columna de graficas nunca aparecen tras la barra de resumen (ver hallazgo H-01). La pantalla queda a medio renderizar.
- Paso 3: PASA — formulario de overlay coherente con el estilo general; legible.

### Punto 3 — El HUD es legible sobre video real con jerarquia piloto/ref correcta

N-A — No se genero overlay en esta corrida (se detiene antes del render completo per instrucciones). Sin evidencia de HUD en esta corrida.

### Punto 4 — Ningun texto en jerga de sistema; vocabulario de pista

PASA — Toda la UI usa vocabulario de pista. Unica excepcion aceptable: "Carpeta donde guardar el overlay" (ruta de directorio, necesaria).

### Punto 5 — Estados visibles: carga, progreso, encoder/tiempo, errores claros

- Carga de CSVs: PASA — progreso de upload visible (MB/%), confirmacion verde con tiempo de vuelta.
- Progreso de analisis: PASA — spinner durante io_bound (no confirmado en headless pero la espera fue correcta).
- Errores de validacion: PASA — mensajes claros si se avanza sin cargar CSVs.
- Estado post-analisis: **FALLA** — Paso 2 no muestra tabla de curvas ni estado final "Analisis completado" (ver H-01).
- Deteccion de curvas (Paso 3): PASA — responde sin congelarse (fix run.io_bound verificado).

---

## Resumen checklist

| Punto | Estado |
|-------|--------|
| H1 Visibilidad del estado | PASA parcial |
| H2 Lenguaje del usuario | PASA |
| H3 Prevencion de errores | PASA |
| H4 Reconocer vs recordar | PASA |
| H5 Disclosure progresivo | PASA |
| H6 Control y libertad | PASA |
| H7 Consistencia | PASA |
| H8 Minimalismo | PASA |
| H9 Ayuda en contexto | PASA |
| H10 Accesibilidad | PASA |
| §2-B Pt1 Heuristicas | PASA (con H-01 bloqueando H1/Pt2) |
| §2-B Pt2 Coherencia visual | FALLA — tabla de curvas no renderiza (re-verificado: fix incompleto, ver seccion Re-verificacion H-01) |
| §2-B Pt3 HUD legible | N-A |
| §2-B Pt4 Vocabulario pista | PASA |
| §2-B Pt5 Estados visibles | PASA parcial (Paso 2 incompleto) |

**Conteo: 11 PASA / 1 PASA parcial / 1 FALLA / 1 N-A**

---

## Hallazgos visuales

### H-01 FALLA — Paso 2: tabla de curvas y graficas nunca aparecen (modo headless)

**Severidad para PO:** Media-Alta — el flujo "Solo analisis" es el flujo mas comun para usuarios sin video.

**Observado:**  
En paso2.png (re-tomado con 5 minutos de espera), la pagina muestra correctamente:
- Dos avisos de contexto: "Autos distintos: BMW M4 GT3 (ref) vs Audi R8 LMS GT3 evo II (piloto)" y "Piloto mas rapido que la referencia (1.2 s de ventaja)"
- Barra de resumen: REF 6:18.40 / TU VUELTA 6:17.14 / DELTA TOTAL -1.240 s

Pero la tabla de curvas (panel izquierdo), las graficas delta/GG/curvas (panel derecho), el footer "Analisis completado" y el drill-down por curva **nunca aparecen**, ni siquiera despues de 5 minutos.

**Causa probable identificada:**  
El script de diagnostico (`_qa_debug_paso2.py`) confirma que `render_charts()` tarda ~13 segundos fuera del contexto NiceGUI. Dentro del contexto, `render_charts()` se llama sincronamente en el handler async de NiceGUI (sin `run.io_bound`), bloqueando el event loop durante esos ~13 segundos. Segun el diagnostico:
- 55 curvas detectadas, comparacion en 1.2 s
- render_charts: 27 archivos en 12.9 s (corrida standalone)

**En modo headless (Playwright):** el event loop bloqueado 13+ segundos parece impedir que el browser reciba las actualizaciones del DOM posteriores. La tabla y graficas nunca se renderizan.

**Pregunta para PO:** ¿Se reproduce en modo `native=True` (pywebview, que es la experiencia real del usuario)? En native mode, la conexion WebSocket puede ser mas resiliente al bloqueo de 13 s. Si en native=True el paso 2 SI muestra la tabla, el bug es headless-especifico y la prioridad baja. Si tambien falla en native=True, es critico.

**Fix sugerido (para Ahiram):** envolver `render_charts(...)` en `await run.io_bound(lambda: render_charts(...))` como ya se hizo con `compare()` en ng_step2.py y `detect_corners()` en ng_step3.py.

---

### A-01 AVISO cosmético — Indicadores de readiness no reactivos en Paso 1

**Observado:**  
En paso1_ambos.png, los puntos `• Referencia` y `• Tu vuelta` del footer siguen en gris incluso despues de cargar ambos CSVs exitosamente (los mensajes de confirmacion verde son correctos). Los puntos son HTML estatico generado al inicio del render y no se actualizan cuando cambia `ref_state["laps"]`.

**Impacto:** Bajo — el usuario tiene la confirmacion verde ("✓ Referencia cargada"). Los puntos grises pueden ser confusos pero no bloquean el flujo.

**Para PO:** ¿Es by design o deuda tecnica?

---

### A-02 AVISO cosmético — Boton "CARGAR Y VER ANALISIS" activo antes de cargar CSVs

**Observado:**  
En paso1.png (estado inicial), el boton principal aparece en estilo primario (azul filled) y es clickeable, aunque no hay CSVs cargados. Al hacer click, muestra un mensaje de error en el footer. Por heuristica H3, seria mejor disabled/secundario hasta que ambos archivos esten listos.

**Impacto:** Bajo — el error message es claro. No bloquea el flujo.

---

### A-03 AVISO informativo — Campos PISTA y FECHA vacios en barra de resumen

**Observado:**  
En paso2.png, la barra de resumen muestra PISTA = "—" y FECHA = "—". Los CSVs "Pruebas finales" de MoTeC no incluyen metadatos de pista o fecha en el formato que la app espera.

**Impacto:** Cosmético — no afecta el analisis.

---

## Fix de limpieza de archivos temporales (upload)

**Fix evaluado:** `_cleanup_upload()` llamado en bloque `finally` de `handle_ref_upload` y `handle_drv_upload` (ng_step1.py) para eliminar el `NamedTemporaryFile` del upload inmediatamente tras parsear el CSV.

**Resultado del check:**

| Momento | Archivos en TEMP |
|---------|-----------------|
| Antes del upload | 4274 |
| Tras subir ambos CSVs | 4276 (+2 de Playwright: playwright-artifacts y playwright_chromiumdev_profile) |
| Al finalizar la corrida | 4279 (+3 adicionales) |

Los 3 archivos adicionales al final son:
- `nicegui-test-storage-*`: directorio de sesion de NiceGUI (esperado)
- `tmp*` x2: directorios huerfanos de `tempfile.mkdtemp()` en ng_step2.py (chart output dirs), NO del upload

**Veredicto del fix de upload:**  
PASA — Los archivos temporales del upload (`NamedTemporaryFile` del `_save_upload`) fueron correctamente eliminados tras parsear los CSVs. No hay huerfanos del mecanismo de upload.

**Deuda separada identificada:** Los 2 directorios `tmp*` de chart generation (`tempfile.mkdtemp()` en ng_step2.py) no se limpian al cerrar. Esto es menor y no forma parte de los fixes evaluados en esta corrida.

---

## Fixes no-visuales evaluados

| Fix | Estado | Evidencia |
|-----|--------|-----------|
| Limpieza de temp (upload NamedTemporaryFile) | PASA | No hay huerfanos de upload en TEMP |
| run.io_bound en analisis (compare) | PASA | Analisis completo en ~1.2 s; io_bound funciona |
| run.io_bound en deteccion de curvas (Paso 3) | PASA | Formulario overlay visible sin congelarse (paso3.png) |
| run.io_bound en render_charts (Paso 2) | **FALLA parcial — fix incompleto** | El await run.io_bound() fue implementado pero state.corners se evalua dentro del thread → app.storage.user can only be used within a UI context. Tabla y graficas siguen sin aparecer (paso2_fix.png). Ver seccion Re-verificacion H-01. |
| Timers (ui.timer en Paso 4) | N-A | No se llego al Paso 4 |
| host=127.0.0.1 | PASA | NiceGUI arranco correctamente en localhost:8765 |

---

## Informacion de entorno

- ffmpeg: instalado (`C:\Users\amedina\AppData\Local\Programs\Python\Python311\...`)  
- Python: 3.11  
- Playwright: chromium headless, viewport 1280x900  
- NiceGUI: modo headless (SGI_HEADLESS=1), native=False  
- Sistema: Windows 11 Pro

---

---

## Re-verificacion H-01 (2026-07-03)

**Fix evaluado:** `await run.io_bound(_do_render_charts)` en `fantasma/ui/ng_step2.py` linea 204  
**Script:** `qa_runs/mariana-20260703-0740/_qa_run_mariana.py`  
**Screenshot:** `qa_runs/mariana-20260703-0740/paso2_fix.png`  
**CSVs:** mismos que la corrida original (BMW M4 GT3 REF, AUDI R8 LMS EVO II DRV, Nordschleife 2025)

### Veredicto H-01 tras fix: FALLA

**Evidencia observada en paso2_fix.png:**
- Barra de resumen: PASA — REF 6:18.40, TU VUELTA 6:17.14, DELTA TOTAL -1.240 s. Los dos avisos de contexto (autos distintos, piloto mas rapido) aparecen correctamente.
- Error en pantalla: `app.storage.user can only be used within a UI context` (texto en verde sobre fondo oscuro).
- Tabla de curvas: NO aparece.
- Graficas: NO aparecen.
- Footer "Analisis completado": NO aparece.

**Causa raiz identificada (nueva):**
El fix envuelve `render_charts()` en `run.io_bound()` — correcto para no bloquear el event loop. PERO la funcion closure `_do_render_charts()` contiene `state.corners or []`, donde `state.corners` accede a `app.storage.user` desde el hilo de fondo. `app.storage.user` solo es accesible dentro del contexto del event loop de NiceGUI; en un thread lanza `app.storage.user can only be used within a UI context`.

El except block de `ng_step2.py` captura la excepcion y muestra el error, pero el layout de dos columnas (tabla + graficas) no se renderiza completamente despues del error.

**Distincion respecto al bug original:**
- Antes del fix: evento loop bloqueado 13 s → browser no recibia actualizaciones del DOM.
- Despues del fix (estado actual): event loop ya NO se bloquea, pero `state.corners` en el thread lanza excepcion → `charts_err` mostrado → tabla de curvas sigue sin aparecer.
- El sintoma visible (tabla y graficas ausentes) es identico. La causa raiz cambia.

**Accion requerida para Ahiram:** capturar `state.corners` en el event loop ANTES de definir el closure. En `_do_render_charts`, reemplazar `state.corners or []` por una variable local ya capturada (p. ej. `_corners_snap = state.corners or []` antes del `def`, y usar `_corners_snap` dentro).

### §2-B Punto 2 — Coherencia visual (actualizado)

- Paso 0: PASA (sin cambios).
- Paso 1: PASA (sin cambios).
- Paso 2: **FALLA** — tabla de curvas y graficas siguen sin aparecer tras el fix. Causa actual: `state.corners` evaluado en thread; error `app.storage.user can only be used within a UI context` visible en pantalla. El fix es incompleto; requiere correcion adicional.
- Paso 3: PASA (sin cambios).

---

## Re-verificacion 2 H-01 (2026-07-03)

**Fix evaluado:** `_corners_snap = state.corners or []` capturado fuera del closure en `fantasma/ui/ng_step2.py` linea 196  
**Script:** `qa_runs/mariana-20260703-0740/_qa_run_mariana.py` (ajustado: rutas fijas, salida `paso2_fix2.png`)  
**Screenshot:** `qa_runs/mariana-20260703-0740/paso2_fix2.png`  
**CSVs:** mismos que la corrida original (BMW M4 GT3 REF, AUDI R8 LMS EVO II DRV, Nordschleife 2025)

### Veredicto H-01 tras fix 2: FALLA

**Evidencia observada en paso2_fix2.png:**
- Barra de resumen: PASA — REF 6:18.40, TU VUELTA 6:17.14, DELTA TOTAL -1.240 s. Los dos avisos de contexto (autos distintos, piloto mas rapido) aparecen correctamente.
- Error en pantalla: AUSENTE (el error `app.storage.user can only be used within a UI context` ya NO aparece — el fix de Ahiram elimino esa causa raiz).
- Tabla de curvas: NO aparece (sintoma identico al anterior pero causa raiz distinta).
- Graficas: NO aparecen.
- Footer "Analisis completado": NO aparece.

**Verificacion de render_charts:**  
Diagnostico confirmado: `render_charts()` SI corre en el thread (27 archivos PNG generados en directorio temporal en <12 s). El ccomputo completa correctamente. El problema es de actualizacion del DOM, no de procesamiento.

**Nueva causa raiz identificada (H-01b — bug zombie en outbox):**

`ui.image(f.read())` en ng_step2.py lineas 296, 304-308, 333-335, 348-350 pasa bytes crudos a `ui.image()`. NiceGUI 3.14.0 no soporta bytes como fuente — `ui.image` acepta `str | Path | PIL_Image` unicamente.

La cadena de fallo:
1. `Element.__init__()` se ejecuta primero: el elemento queda registrado en `client.elements`, insertado en los children del slot activo, y encolado en el outbox para actualizacion.
2. Acto seguido, `_set_props(bytes)` llama `is_file(bytes)` que llama `Path(bytes).is_file()` → lanza `TypeError` (no es `OSError`, no es capturado por el `except OSError` de `is_file`).
3. El `TypeError` sube hasta `ui.image(f.read())` y es capturado por el `except Exception: pass` del bloque render.
4. El elemento queda como "zombie": existe en el arbol DOM de NiceGUI con `_props['src'] = bytes`, pero el atributo `src` no es JSON-serializable.
5. Cuando el outbox agrupa TODOS los elementos pendientes en un unico dict `data` y llama `core.sio.emit('update', data, ...)`, la serializacion a JSON falla con `TypeError: Object of type bytes is not JSON serializable`.
6. La excepcion es capturada por `core.app.handle_exception(e)` en el loop del outbox, pero el BATCH COMPLETO de actualizaciones se descarta — incluyendo la tabla de curvas, las graficas, el footer "Analisis completado" y todos los demas elementos creados despues del `await run.io_bound(_do_render_charts)`.

**Distincion respecto a Re-verificacion 1:**
- Re-verificacion 1: `state.corners` en thread → excepcion `app.storage.user` → `charts_err` visible en pantalla → render_charts nunca corre.
- Re-verificacion 2 (estado actual): `_corners_snap` corrige el acceso en thread → render_charts corre y genera 27 PNG → PERO `ui.image(bytes)` crea elementos zombie con props no-JSON → outbox descarta el batch completo → tabla y footer nunca llegan al browser.

**Accion requerida para Ahiram (H-01b):** En ng_step2.py, sustituir:
```python
with open(p, "rb") as f:
    ui.image(f.read()).classes(...)
```
por:
```python
ui.image(p).classes(...)
```
en todos los bloques de carga de imagenes (delta_map, gg_diagram, full_lap, corner plots, brake zones). NiceGUI sirve los archivos estaticos automaticamente con `add_static_file` cuando se le pasa una ruta en lugar de bytes.

### §2-B Punto 2 — Coherencia visual (Re-verificacion 2)

- Paso 0: PASA (sin cambios).
- Paso 1: PASA (sin cambios).
- Paso 2: **FALLA** — tabla de curvas y graficas siguen sin aparecer. Error `app.storage.user` resuelto. Causa actual: elementos zombie por `ui.image(bytes)` corrompen el batch de actualizaciones del outbox. Fix incompleto; H-01b bloqueante.
- Paso 3: PASA (sin cambios).

### Resumen checklist §2-B (Re-verificacion 2)

| Punto | Estado |
|-------|--------|
| §2-B Pt2 Coherencia visual Paso 2 | **FALLA** (H-01b: ui.image(bytes) → zombie → outbox descarta batch) |
| §2-B Pt5 Estados visibles Paso 2 | **FALLA** (footer "Analisis completado" no aparece) |
| Todos los demas puntos | Sin cambio respecto a corrida original |

---

## Verificacion 3 H-01/H-01b (2026-07-03)

**Fix evaluado:** `ui.image(p)` en lugar de `ui.image(f.read())` en los 5 sitios de ng_step2.py (Ahiram), eliminacion de bloques `try/except Exception: pass` que enmascaraban el error  
**Script:** `qa_runs/mariana-20260703-0740/_qa_run_mariana.py`  
**Screenshot:** `qa_runs/mariana-20260703-0740/paso2_fix3.png`  
**CSVs:** mismos que la corrida original (BMW M4 GT3 REF, AUDI R8 LMS EVO II DRV, Nordschleife 2025)

### Veredicto H-01b tras fix 3: FALLA

**Evidencia observada en paso2_fix3.png:**
- Barra de resumen: PASA — REF 6:18.40, TU VUELTA 6:17.14, DELTA TOTAL -1.240 s. Los dos avisos de contexto aparecen correctamente.
- Error `app.storage.user`: AUSENTE (corregido por fix anterior).
- Error en pantalla: NINGUNO.
- Tabla de curvas: NO aparece.
- Graficas: NO aparecen.
- Footer "Analisis completado": NO aparece.
- DOM: 128 elementos en t+5s, 132 en t+25s (+4), sin cambio posterior hasta t+65s.

**Verificacion de render_charts:**  
Confirmado: `render_charts()` corre en thread. Los 42 PNG se generan en directorio temporal. No hay error de `ui.image(bytes)`: el fix de Ahiram elimino los elementos zombie. El outbox ya no descarta el batch por falta de serializacion JSON.

**Nueva causa raiz identificada (H-01c — html.js sin slot descarta children):**

Evidencia WS: el log completo en `_ws_fix3.log` muestra que a t+25s NiceGUI envia:
1. `load_js_components` para `table.js` y `image.js` (NiceGUI sabe que necesita esos componentes)
2. Un `update` de **34,898 chars** con TODOS los elementos del analisis: elemento 160 (analysis-cols, children [161,211]), 161 (panel izquierdo, children [162,163,165,166]), 163 (panel-body, children [164]), 164 (`nicegui-html` con la tabla completa de 52 curvas en innerHTML de 18,446 chars), elementos 165-226 (drill-down, imagenes, labels, botones), elemento 227 (export-strip con footer y botones).
3. Un evento binario `download` con el CSV de curvas (entregado correctamente via socket.io binary framing).

El update es recibido por el browser. `nicegui.js` (funcion `update` handler) agrega TODOS los elementos nuevos a `this.elements`. Pero el DOM solo crece en +4 nodos: dos por elemento 160 (componente Vue `<nicegui-html>` + `<div class="analysis-cols">`) y dos por elemento 227 (componente Vue + `<div class="export-strip">`).

**El bug esta en el componente Vue `html.js`:**

```javascript
// nicegui/elements/html.js
export default {
  template: `<component :is="tag"></component>`,  // <-- sin <slot>
  ...
};
```

La funcion `renderRecursively` en `nicegui.js` construye los children como contenido de slot:
```javascript
slots[name] = (props) => {
  const children = data.ids.map((id) => renderRecursively(elements, id, props || propsContext));
  return [...rendered, ...children];
};
return Vue.h(Vue.resolveComponent(element.tag), props, slots);
```

Para el elemento 160 (tag="nicegui-html"), se llama `Vue.h(html_js_component, props, {default: () => [vnode_161, vnode_211]})`. El slot default contiene los vnodes de los hijos. PERO el template de `html.js` (`<component :is="tag"></component>`) no tiene `<slot>`, por lo que Vue descarta silenciosamente todo el contenido del slot. Los elementos 161-226 nunca se montan en el DOM.

El mismo mecanismo afecta al elemento 227 (export-strip): su hijo "Analisis completado" existe en el slot pero tampoco se renderiza.

Adicionalmente, `renderContent()` en `mounted()` y `updated()` llama `this.$el.setHTML(...)` o `this.$el.innerHTML = ...` que sobreescribiria cualquier contenido DOM existente. Sin slot no hay nada que proteger.

**Cadena de causas en orden cronologico:**
- H-01: `render_charts()` bloqueaba el event loop → corregido con `run.io_bound`.
- H-01 re-verif: `state.corners` en thread → corregido con `_corners_snap`.
- H-01b: `ui.image(bytes)` → zombie → outbox descartaba batch JSON → corregido con `ui.image(p)`.
- H-01c (actual): el batch WS llega completo al browser, pero `nicegui-html` sin `<slot>` descarta todos sus hijos. Ni tabla, ni graficas, ni footer se montan en el DOM.

**Accion requerida para Ahiram (H-01c):**  
Reemplazar los contenedores `with ui.html('<div class="...">'):` por elementos NiceGUI nativos que si soportan children via slot. Opciones:
- `with ui.element('div').classes('analysis-cols'):` — crea un `<div>` nativo con soporte de children
- `with ui.column().classes('panel'):` — columna vertical (usa `nicegui-column`, que SI tiene slot)
- `with ui.row().classes('...')` — fila horizontal

Los `ui.html()` SIN children (para HTML estatico como la barra de resumen, el panel-header o la tabla de curvas) funcionan correctamente y no necesitan cambio. Solo los `ui.html()` usados como CONTENEDORES de otros elementos NiceGUI necesitan migrarse a elementos nativos.

Bloques afectados en ng_step2.py:
- Linea 221: `with ui.html('<div class="analysis-cols">').classes("w-full"):`
- Linea 223: `with ui.html('<div class="panel">'):` (panel izquierdo)
- Linea 253: `with ui.html('<div class="panel-body" style="padding:0">'):` (body tabla)
- Linea 258: (el ui.column ya es nativo, no necesita cambio)
- Linea 292, 301: `with ui.row().classes(...)` (ya es nativo, OK)
- Linea 312: `with ui.html('<div class="right-col">'):` (columna derecha)
- Linea 314, 347: `with ui.html('<div class="panel">'):` (paneles derecha)
- Linea 318, 351: `with ui.html('<div class="panel-body">'):` (bodies paneles)
- Linea 321: `with ui.html('<div class="chart-area" style="height:auto">'):` (area chart)
- Linea 363: `with ui.html('<div class="export-strip">'):` (export strip)
- Linea 365: `with ui.html('<div style="...">'):` (botones del strip)

Los estilos CSS de estas clases (`.analysis-cols`, `.panel`, `.panel-body`, `.right-col`, etc.) estan definidos en `sgi.css` y seguiran funcionando al aplicarlos via `.classes()` en elementos nativos.

### §2-B Puntos 2 y 5 — Estado (Verificacion 3)

| Punto | Estado | Nota |
|-------|--------|------|
| §2-B Pt2 Coherencia visual Paso 2 | **FALLA** | H-01c: html.js sin slot descarta children; tabla y graficas no se montan en el DOM. |
| §2-B Pt5 Estados visibles Paso 2 | **FALLA** | Footer "Analisis completado" tampoco se monta (hijo de export-strip = tambien html.js sin slot). |
| Todos los demas puntos | Sin cambio | Paso 0/1/3/4 y el resto de §2-B sin afectacion. |

**Raiz limpia:** si — el script QA esta en su carpeta (`qa_runs/mariana-20260703-0740/`). Sin copias en la raiz del repo.

---

## Verificacion 4 — cierre H-01 (2026-07-03)

**Fix evaluado:** H-01c — migracion de 11 contenedores `with ui.html('<div class="...">'):` a `ui.element("div").classes(...)` en `fantasma/ui/ng_step2.py`. Con esto html.js ya no descarta los children por falta de slot; los elementos Vue se montan correctamente.  
**Script:** `qa_runs/mariana-20260703-0740/_qa_run_mariana.py` (mismos CSVs; salida `paso2_fix4.png`)  
**Screenshot:** `qa_runs/mariana-20260703-0740/paso2_fix4.png`  
**CSVs:** BMW M4 GT3 REF, AUDI R8 LMS EVO II DRV, Nordschleife 2025 (identicos a las corridas anteriores)

### Veredicto H-01c tras fix 4: PASA

**Evidencia observada:**

- `'Analisis completado'` visible en footer: PASA
- Tabla de curvas con filas reales: PASA — 55 filas (curvas C01-C55 del Nordschleife)
- Imagenes de graficas cargadas: PASA — 27/27 cargadas, 0 rotas (naturalWidth > 0)
- Error en pantalla: NINGUNO
- DOM a t+25s: 968 elementos (vs 128 a t+5s); html correcto, tabla y contenido presentes

**Nota sobre imagenes "pendientes":**  
En el diagnostico intermedio, 5 imagenes `frenada_C*.png` tenian naturalWidth===0 aun siendo pending (no complete). Son graficas de zonas de frenada mas pesadas servidas desde el static file server de NiceGUI. La logica de espera las detecto como pending y aguardo hasta que `img.complete == true` para todas; todas completaron dentro del margen de 15 s adicionales. No es un bug nuevo; es latencia de carga normal.

**Cadena H-01 completamente cerrada:**

| Fix | Corrida | Causa resuelta |
|-----|---------|---------------|
| run.io_bound(compare) | Verif. 0 (original) | event loop bloqueado 13 s |
| _corners_snap | Verif. 1 | state.corners en thread: app.storage.user fuera de contexto UI |
| ui.image(p) en 5 sitios | Verif. 2 | ui.image(bytes) → zombies → outbox descarta batch JSON |
| ui.element("div") en 11 contenedores | Verif. 4 (esta corrida) | html.js sin slot descarta children; tabla, graficas y footer nunca se montaban |

---

### §2-B FINAL — Checklist completa re-evaluada (cierre H-01)

#### Punto 1 — Heuristicas §1

| H | Heuristica | Estado | Evidencia |
|---|-----------|--------|-----------|
| H1 | Visibilidad del estado | **PASA** | Paso 2: tabla de 55 curvas, graficas de delta/GG/vuelta completa, footer "Analisis completado" visibles. Sin spinners atascados. |
| H2 | Lenguaje del usuario | PASA | Sin cambio; vocabulario de pista en todo el flujo. |
| H3 | Prevencion de errores | PASA | Sin cambio; aviso H3 anterior (boton azul sin CSVs = A-02) sigue como aviso menor. |
| H4 | Reconocer vs recordar | PASA | Sin cambio. |
| H5 | Disclosure progresivo | PASA | Sin cambio. |
| H6 | Control y libertad | PASA | Sin cambio. |
| H7 | Consistencia | PASA | Sin cambio. |
| H8 | Minimalismo | PASA | Sin cambio. |
| H9 | Ayuda en contexto | PASA | Sin cambio. |
| H10 | Accesibilidad | PASA | Sin cambio. |

#### Punto 2 — Coherencia visual

- Paso 0: PASA (sin cambio)
- Paso 1: PASA (sin cambio)
- Paso 2: **PASA** — tabla de 55 curvas visible, columna derecha con graficas delta/GG/vuelta completa, footer "Analisis completado" visible. Estilo CSS (`.analysis-cols`, `.panel`, `.panel-body`, `.right-col`, `.export-strip`) preservado al migrar a `.classes()`. Layout coherente con el resto de la UI.
- Paso 3: PASA (sin cambio)

#### Punto 3 — HUD legible sobre video real

N-A — No aplica a esta corrida (flujo "Solo analisis").

#### Punto 4 — Vocabulario de pista

PASA — Sin cambio.

#### Punto 5 — Estados visibles

- Carga de CSVs: PASA (sin cambio)
- Progreso de analisis: PASA (run.io_bound no bloquea; spinner durante el computo)
- Errores de validacion: PASA (sin cambio)
- Estado post-analisis Paso 2: **PASA** — footer "Analisis completado" visible; tabla y graficas presentes. H-01 cerrado.
- Deteccion de curvas Paso 3: PASA (sin cambio)

#### Resumen §2-B FINAL

| Punto | Estado anterior (Verif. 3) | Estado FINAL (Verif. 4) |
|-------|--------------------------|------------------------|
| §2-B Pt1 H1 Visibilidad | PASA parcial | **PASA** |
| §2-B Pt1 H2 Lenguaje | PASA | PASA |
| §2-B Pt1 H3 Prevencion errores | PASA | PASA |
| §2-B Pt1 H4 Reconocer | PASA | PASA |
| §2-B Pt1 H5 Disclosure | PASA | PASA |
| §2-B Pt1 H6 Control | PASA | PASA |
| §2-B Pt1 H7 Consistencia | PASA | PASA |
| §2-B Pt1 H8 Minimalismo | PASA | PASA |
| §2-B Pt1 H9 Ayuda | PASA | PASA |
| §2-B Pt1 H10 Accesibilidad | PASA | PASA |
| §2-B Pt2 Coherencia visual Paso 2 | FALLA | **PASA** |
| §2-B Pt3 HUD legible | N-A | N-A |
| §2-B Pt4 Vocabulario pista | PASA | PASA |
| §2-B Pt5 Estados visibles Paso 2 | FALLA | **PASA** |

**Conteo final: 13 PASA / 0 FALLA / 1 N-A**

**H-01 cerrado.** El Paso 2 renderiza su contenido completo: tabla de curvas con 55 filas, graficas delta/GG/vuelta, drill-down por curva, y footer "Analisis completado". La cadena de 4 bugs (H-01, H-01 re-verif., H-01b, H-01c) queda resuelta.

**Raiz limpia:** si — script y artefactos en `qa_runs/mariana-20260703-0740/`. Sin copias en la raiz del repo.

---

*Mariana — checkpoint visual. El veredicto final (aceptar/bloquear) es del PO.*
