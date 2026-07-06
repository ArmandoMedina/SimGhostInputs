# Patrones de UX/UI y gate de calidad de interfaz

> **Para qué es este documento.** Así como el repo tiene convenciones de **código** (ruff, tests)
> y de **docs** (§8 de `CONTRIBUTING.md`), este es el estándar de **interfaz**: las heurísticas que
> la UI (`fantasma-ng`, NiceGUI) y el HUD deben cumplir, y **el gate que verifica que se cumplan
> antes de subir cambios** — análogo a "los tests deben pasar". Lo usa el rol **Mariana** (UX) como
> rúbrica, y se integra con las barreras de [`flujo-de-trabajo.md`](flujo-de-trabajo.md).
>
> **Principio rector (igual que en todo el repo): determinismo bloquea, juicio aconseja.** La
> calidad de UX tiene una parte **medible** (regresión de layout, contraste, elementos presentes,
> estados de carga) que **puede bloquear como un test**; y una parte **subjetiva** ("¿se ve
> profesional?, ¿el flujo se siente claro?") que **no** puede ser portero automático — es el
> checkpoint humano de Mariana que vuelve al PO. Forzar lo subjetivo como gate produce falsos
> rojos y se ignora; no medir lo objetivo deja pasar regresiones. El gate respeta esa frontera.

---

## 1. Heurísticas (la rúbrica)

Adaptación de las heurísticas de Nielsen al dominio (sim racing, análisis post-tanda, local-first).
Cada cambio de UI/HUD se evalúa contra esto.

1. **Visibilidad del estado del sistema.** El usuario siempre sabe qué pasa: progreso de render con
   %, qué encoder se usó (NVENC vs CPU) y cuánto tardó, qué vuelta/flujo está activo, qué paso sigue.
   *Hoy falla en:* no se reporta el encoder ni el tiempo de compose (C20).
2. **Lenguaje del usuario, no del sistema.** Vocabulario de pista: "frenada", "ápex", "tiempo
   perdido", "vuelta de referencia" — no "buffer", "tempfile", "exit code". *Regresión histórica:*
   mostrar la ruta de un tempfile en vez del nombre del archivo (ya corregido).
3. **Prevención de errores > mensajes de error.** Chequear prerrequisitos **antes** de dejar entrar
   a un flujo: ffmpeg presente para video (C19), columnas mapeables para CSV no-MoTeC (C07),
   referencia vs piloto distintos. Mejor desactivar/avisar que dejar fallar a mitad.
4. **Reconocer en vez de recordar.** El usuario no memoriza flags: el wizard de 5 pasos y los flujos
   predefinidos exponen las opciones. *Deuda:* capacidades del CLI no expuestas en UI (mapeo de
   columnas, comparar dos vueltas del mismo archivo, editar nombres de curva — C07/C10/C13).
5. **Disclosure progresivo.** Lo avanzado se esconde tras expanders; lo esencial primero. El Paso 0
   ya usa expander para la guía de export. *Riesgo:* pantallas demasiado densas de texto.
6. **Control y libertad del usuario.** Cancelar un render largo, volver a procesar otra vuelta sin
   recargar, navegar sin perder estado. *Ya cubierto* (Detener render, "Procesar otra vuelta").
7. **Consistencia y estándares.** Mismos iconos/colores/etiquetas en toda la app; salidas en
   formatos estándar (CSV/MD/PNG/WebM). El vocabulario de color del HUD debe coincidir con
   `hud-reference.md` (regla de consistencia §8).
8. **Estética y diseño minimalista.** Cada elemento gana su lugar; nada compite con la señal. En el
   HUD esto es crítico: legibilidad sobre el video, jerarquía piloto-vs-referencia (ADR 0005-0007).
9. **Ayuda y documentación en contexto.** Tooltips/captions donde se necesita la decisión, enlaces a
   la guía. La guía visual de export **está incompleta** (imágenes placeholder — C04).
10. **Accesibilidad mínima.** Contraste de texto legible (WCAG AA en lo posible), no depender solo
    del color para transmitir estado (el HUD ya combina color + forma/posición).

---

## 2. El gate de UX/UI (cómo se "aprueban las pruebas de UX")

Tres capas, de menor a mayor autoridad — igual que las barreras de código avisan temprano y
bloquean al final.

### Capa A — Determinista, **BLOQUEA** (en CI, como los tests)

Son verificables por máquina; si fallan, el cambio no debe subir (rojo en CI). Viven junto a la
suite, corren en `pytest`/`verificar.ps1` y en `.github/workflows/tests.yml`.

- **Smoke visual de layout (Playwright).** Screenshot de cada pantalla contra un baseline (Ubuntu =
  verdad canónica, ADR 0012), tolerancia generosa: atrapa "el layout se movió", no antialiasing.
  - *Hoy:* solo cubre el **Paso 0**. **Objetivo:** extender a Pasos 1-4 (con estado/datos
    sintéticos cargados por el harness), un baseline por pantalla.
- **Aserciones estructurales (fixture `user` de NiceGUI).** Sin pixeles: que los elementos esperados
  existan (los 3 flujos en el Paso 0, el botón primario de avance, la tabla de vueltas tras cargar,
  el progreso durante el render). Determinista y rápido.
- **Contraste de texto.** Chequeo automatizable de ratio de contraste de los estilos propios
  (los colores del HUD y del CSS de la UI) contra WCAG AA. Es aritmética sobre colores → bloquea.

### Capa B — Juicio, **ACONSEJA** (checkpoint de Mariana, vuelve al PO)

"¿Se ve profesional?", "¿el flujo se siente claro?", "¿el HUD es legible sobre ESTE video?" no son
deterministas. No bloquean por máquina: los dispara el hook de sesión **`mariana-stop`** al tocar
`fantasma/viz/` o `fantasma/ui/`, que **frena el cierre y obliga a mirar** (abrir `fantasma-ng` /
revisar el HUD) con esta **checklist**:

- [ ] El cambio respeta las 10 heurísticas de §1 (revisión rápida).
- [ ] La pantalla afectada se ve coherente con el resto (espaciado, tipografía, iconos).
- [ ] El HUD (si aplica) es legible sobre video real, con la jerarquía piloto/ref correcta.
- [ ] Ningún texto en jerga de sistema; vocabulario de pista.
- [ ] Estados visibles: carga, progreso, encoder/tiempo, errores claros.

El resultado de la checklist es **juicio del PO**, no un auto-pase — igual que el Reviewer de código
y el Escribano de docs proponen pero el contenido no bloquea lo irreversible.

### Capa C — Local, **AVISA** (temprano)

`verificar.ps1` corre el smoke visual y las aserciones estructurales NiceGUI en modo aviso antes del push (skipea
limpio si no hay Chromium), como ya hace con lint/formato/tests. El CI es el que bloquea.

> **Regla de oro del gate:** lo que se pueda medir (layout, contraste, presencia de elementos,
> visibilidad de estado) **se mide y bloquea**; lo que sea gusto/sensación **se mira y vuelve al
> PO**. Nunca un gate subjetivo automático.

---

## 3. Estado y plan de implementación

| Pieza del gate | Estado | Acción |
| :-- | :-- | :-- |
| Smoke visual Paso 0 | ✅ existe (ADR 0012); baseline regenerado en v0.14.0 por cambio F-01 | — |
| Smoke visual Pasos 1-4 | ⏸️ diferido | los tests NiceGUI cubren la estructura; Playwright requiere inyectar estado en browser (no trivial). Diferido post-v1.0 |
| Aserciones estructurales NiceGUI | ✅ Pasos 0-4 cubiertos (`tests/ui/`) — 41 tests NiceGUI (`fixture user`) en verde | — |
| Contraste WCAG | ⏸️ diferido post-v1.0 | Bajo riesgo: paleta reducida, colores revisados a ojo |
| Checklist Mariana | ✅ hook formalizado con los 5 puntos de §2-B (v0.14.0) | — |
| Integración en `verificar.ps1`/CI | ✅ (visual + tests NiceGUI vía pytest) | — |

> La decisión de tratar el gate de UX con la dualidad determinismo/juicio se asienta en un ADR
> (ver `docs/decisions/`). Los hallazgos de UX concretos por pantalla se documentan tras el
> diagnóstico con capturas, cruzados con [`casos-de-uso.md`](casos-de-uso.md).

---

## 4. Patrones específicos de NiceGUI (agregados en v2.0)

La UI principal de v2.0 migró de Streamlit a **NiceGUI** ([ADR 0018](decisions/0018-framework-ui-nicegui.md), enmienda al [ADR 0010](decisions/0010-framework-ui-streamlit.md)). NiceGUI es reactivo y asíncrono, así que impone patrones distintos a los de Streamlit (rerun completo del script). Estos son los que el código de `fantasma/ui/ng_*.py` sigue y que cualquier cambio nuevo debe respetar.

1. **Operaciones en background (render async).** Para operaciones largas (componer video, generar overlay) **no** se bloquea el event loop con `asyncio.sleep` en un loop. Se usa un objeto `RenderJob` (`ng_helpers.py`) que corre `fn` en un thread daemon (`start_bg_render`), y en la UI un `ui.timer(0.5, poll)` hace polling del job: lee `job.n/job.total` para actualizar la barra de progreso y, cuando `job.done`, cancela el timer y refresca la UI con el resultado. El `RenderJob` también expone `cancel()` (un `threading.Event`) para el botón «Detener». Patrón vivo en `ng_step4.py::_start_compose`.

2. **Forward-declaration de elementos UI.** En NiceGUI los handlers (closures) se definen **antes** de que existan los elementos que manipulan; el closure captura el nombre, no el valor. Patrón: declarar `ref_status = None  # noqa: F841` (y `drv_status`, `load_err`, etc.), definir los handlers que usan `ref_status`, y **más abajo** hacer la asignación real `ref_status = ui.label(...)`. El `# noqa: F841` es necesario porque ruff no ve que la variable se reasigna dentro de un closure — **no es dead code**, es la forma correcta en NiceGUI. Ejemplo en `ng_step1.py`.

3. **Diálogos de archivo nativos (`native=True`).** `_pick_file()` y `_pick_folder()` (`ng_helpers.py`) abren el selector nativo del OS vía Tkinter (`filedialog`). Solo funcionan de forma fiable en modo `native=True` (ventana pywebview, que es como arranca `fantasma-ng` en `ng_app.py::run`); en modo browser/desarrollo el selector puede fallar o abrir una ventana separada extraña. Ambos helpers atrapan cualquier excepción y devuelven `""`. Las operaciones potencialmente lentas (leer overlay, componer preview) se envuelven con `await run.io_bound(...)` para no bloquear el event loop.

   *Excepción — upload de CSV en Paso 1:* los dos paneles de carga de `ng_step1.py` usan `ui.upload` (componente nativo del browser, `<input type="file">`) en lugar de `_pick_file()`. Esta ruta funciona en modo browser y en `native=True` por igual; no invoca Tkinter.

4. **Colores de texto: clases Tailwind, no vars CSS inline.** Los colores de estado usan clases Tailwind (`text-gray-400`, `text-red-400`, `text-yellow-400`, `text-green-400`) en lugar de `.style("color:var(--X)")` inline. Las vars CSS inline no se resuelven de forma fiable bajo el modo oscuro de Quasar en pywebview.

5. **Corrección F-01 (NiceGUI) — pendiente.** El selector de flujo del Paso 0 (`ng_step0.py`) no debe mostrar ningún flujo como «✓ Seleccionado» al cargar la app. Hoy `is_selected = state.flow_key == flow_key` compara contra `flow_key`, que tiene un default (`_DEFAULT_FLOW = "compose"`), por lo que la tarjeta por defecto aparece pre-seleccionada aunque el usuario no haya elegido nada. El estado ya tiene el booleano `flow_chosen` (separado de `flow_key`) para distinguir «default cargado» de «usuario eligió explícitamente»; la corrección es que el Paso 0 use `flow_chosen` para decidir el marcado. Registrado para corrección en v2.0.x. Es el equivalente NiceGUI del F-01 ya resuelto en Streamlit (ver §5, v0.14.0).

---

## 5. Registro de cambios de patrón por versión

Historial de decisiones de UX que alteraron el layout o el flujo de la UI — para que el baseline visual tenga contexto al regenerarse.

### feat/cues-frenada-universal (Unreleased)

**Leyenda de tonos del Paso 5 — el tono de ápex desaparece solo, sin tocar la UI:**
- La leyenda (patrón ya documentado más abajo en "feat/pacenotes-ui-paso5") se deriva de `PLAN_CUES`/`DEFAULT_FREQS`; al retirarse `apex` de `PLAN_CUES` como cue sonoro ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md)) la leyenda deja de listarlo sin cambiar una línea de `ng_step5.py` — el DRY de esa tabla paga solo.
- El resto del rediseño (tono de frenada universal y protegido, countdown oportunista por cabida) vive entero en el motor (`fantasma/viz/pacenotes.py`); no hay cambio de layout ni de componentes en el Paso 5. Ver el ADR para el porqué.

### feat/flujo-solo-pacenotes (Unreleased)

**Nuevo flujo "Solo Pace Notes" — 4ª tarjeta en el Paso 0:**
- El Paso 0 pasa de un grid de 3 a 4 columnas; la tarjeta 🔔 "Solo Pace Notes" enruta al usuario por Importar (1) → Análisis (2) → Pace Notes (5), saltando overlay (3) y compose (4).
- El sidebar muestra los pasos 3 y 4 como "· paso opcional fuera del flujo elegido" cuando se elige este flujo.
- Heurística cubierta: **Visibilidad del estado del sistema** (§1.1) — el usuario ve exactamente qué pasos componen su flujo sin necesidad de consultar la guía.
- Patrón reusable: flujo = subconjunto ordenado de pasos; el sidebar los refleja con la misma lógica `_step_done` ajustando qué pasos son "en-flujo" vs opcionales.

**Fix del guard del Paso 5 — panel ② siempre visible:**
- Antes: el guard ocultaba todo el Paso 5 si `state.rows` o `state.corners` eran None.
- Ahora: el aviso "falta el análisis" vive solo dentro del panel ① (generar pack nuevo); el panel ② ("Aplicar sonido a un video existente") es visible siempre.
- Mensaje reescrito: distingue "para generar un pack nuevo, corre el Análisis (Paso 2)" vs "si ya tienes pack+video, usa el panel ②".
- Heurística cubierta: **Prevención de errores** (§1.3) — se elimina el bloqueo excesivo que impedía usar panel ② cuando el usuario ya tenía un pack generado en una sesión anterior o en otra herramienta.

**Tooltips en todos los controles del Paso 5 + caption puente:**
- Todos los controles de los paneles ① y ② del Paso 5 incluyen `ui.tooltip(...)` que explican su función, el rango válido o el prerrequisito necesario.
- Caption puente entre paneles: «Primero genera el pack en ①; luego aplícalo a tu video en ②».
- Heurística cubierta: **Ayuda y documentación** (§1.9) — la guía contextual elimina la necesidad de consultar documentación externa para entender el flujo del Paso 5.
- Patrón reusable: `ui.tooltip("Texto explicativo")` adjunto a cada `ui.input`, `ui.select`, `ui.slider` y `ui.button`; `ui.caption("...")` para mensajes de flujo entre secciones de la misma pantalla.

### feat/pacenotes-ui (Unreleased)

**Loading states en carga de CSV (Paso 1) — patrón «spinner + label en columna reservada»:**
- Antes de llamar `run.io_bound(_load_laps)`, se muestra un spinner con `ui.spinner("dots")` y una etiqueta «Leyendo CSV...» en un `ui.column` reservado (`ref_loading_area` / `drv_loading_area`).
- Tras el `await`, la columna se limpia (`.clear()`) en el bloque `finally`, independientemente de éxito o error.
- Mientras se calcula la vuelta más rápida (lógica post-lectura), el estado muestra «Calculando vuelta rápida...» antes de escribir el resultado final.
- Heurística cubierta: **Visibilidad del estado del sistema** (§1.1).
- Patrón reusable: `area = ui.column()` como placeholder, `.clear()` antes de rellenar, `ui.spinner()` + `ui.label(texto)` con clases Tailwind.

**Botones deshabilitados por contexto (Paso 4 y Paso 5) — patrón «habilitar reactivo»:**
- El botón «Componer video» (Paso 4) inicia como deshabilitado y solo se activa cuando `video_input.value` y `overlay_input.value` son no vacíos.
- El botón «Aplicar sonido» (Paso 5) inicia deshabilitado y solo se activa cuando están rellenos el video, la carpeta del pack y `state.drv_lap is not None`.
- Los `on("update:model-value", ...)` en los campos disparan `_update_X_enabled()` que llama `.enable()` / `.disable()` en el botón.
- Heurística cubierta: **Prevención de errores** (§1.3).
- Patrón reusable: definir `btn = ui.button(...)`, luego `_update_enabled()` que evalúa condiciones y llama `.enable()/.disable()`, enlazar los campos de entrada con `on("update:model-value", ...)`.

**Detección de curvas diferida con botón deshabilitado (Paso 3) — patrón «disable-mientras-resuelve»:**
- Al entrar al Paso 3, si `state.corners` no está disponible el panel se renderiza inmediatamente (sin bloquear) y el botón «Generar overlay» se deshabilita mientras corre `await run.io_bound(_detect)`.
- Durante la espera aparece un spinner con «Analizando el trazado...» en `render_area`; al completar (o fallar, con lista vacía) se elimina el hint y el botón se reactiva.
- Heurística cubierta: **Visibilidad del estado del sistema** (§1.1) y **Prevención de errores** (§1.3): impide arrancar un render sin milestones si el usuario pulsa antes de que termine la detección.
- Patrón reusable: `btn.disable()` → mostrar spinner en área reservada → `await run.io_bound(fn)` → eliminar hint → `btn.enable()`. Diferente del patrón de polling (§4.1): aquí el botón que dispara la acción es el mismo que se bloquea, no un job en background con timer.

**Guard de running state en mux standalone (Paso 5) — patrón «no dos a la vez»:**
- `_mux_state = {"running": False}` actúa como semáforo: al entrar a `_apply_mux()` se comprueba; si ya está corriendo, la función retorna inmediatamente ignorando el doble-clic.
- Al terminar (éxito o error, en bloque `finally`), se pone `running = False` y se reactiva `apply_btn`.
- Heurística cubierta: **Prevención de errores** (§1.3): evita dos procesos ffmpeg escribiendo al mismo archivo de salida concurrentemente.
- Patrón reusable: `state = {"running": False}`, guard al inicio, `btn.disable()` mientras corre, `state["running"] = False; btn.enable()` en `finally`.

**Layout en 2 columnas para Pasos 4 y 5 (baseline visual v0.14.x):**
- Paso 4: columna izquierda con paneles de entradas ①–④; columna derecha con parámetros del HUD y vista previa ⑤ (sticky).
- Paso 5: columna izquierda con «① Generación de Pace Notes»; columna derecha con «② Aplicar sonido a video existente».
- Contenido de la página centrado con ancho máximo de 1 100 px (`max-width:1100px;margin:0 auto`).
- Referencia: cualquier regeneración de baseline Playwright para Pasos 4 y 5 debe partir de este layout de 2 columnas.

### feat/pacenotes-ui-paso5 (Unreleased)

**Breadcrumb por flujo — solo los pasos de tu ruta:**
- `render_breadcrumb(step, flow_key)` pinta únicamente los pasos de `_FLOWS[flow_key]["steps"]`: en "Solo Pace Notes" se ve Inicio › Importar › Análisis › Pace Notes (antes pintaba los 6 pasos fijos y mandaba al usuario hacia Overlay/Video, reporte del PO en QA 2026-07-05).
- Fallback seguro: sin `flow_key`, con clave desconocida, o si el paso actual no pertenece al flujo (navegación manual), pinta los 6.
- Heurística cubierta: **Correspondencia sistema-mundo real** (§1.2) — el mapa que ve el usuario es el camino que va a recorrer.
- Patrón reusable: los componentes de navegación derivan SIEMPRE de `_FLOWS` (fuente única), nunca de una lista fija propia.

**Leyenda de tonos en el Paso 5 — panel plegable derivado del motor:**
- `ui.expansion` con una tabla tono→"suena como" generada desde `PLAN_CUES` + `MILESTONE_LABELS` + `DEFAULT_FREQS` (DRY: si el motor cambia una frecuencia, la leyenda se actualiza sola).
- Incluye la aclaración clave: los tonos marcan los puntos de la vuelta de REFERENCIA; el desfase con lo que haces es el consejo, no un bug ([ADR 0024](decisions/0024-sincronia-pace-notes.md)).
- Heurística cubierta: **Reconocimiento antes que recuerdo** (§1.6) — 7 tipos de tono eran indistinguibles sin tabla.

**Caption "qué falta" bajo botón deshabilitado (Paso 5) — evolución del patrón «habilitar reactivo»:**
- El botón gris sin explicación fue reporte directo del PO: `_update_apply_enabled()` ahora además setea un `ui.label` amarillo con la lista exacta de lo que falta ("Falta: la vuelta del piloto (Paso 1), el video.").
- Heurística cubierta: **Visibilidad del estado del sistema** (§1.1). Patrón reusable: todo botón que se deshabilite por contexto lleva un caption adyacente que se actualiza en el mismo `_update_X_enabled()`.

**Aviso de sidecar video↔vuelta (Paso 5, panel ②):**
- Al elegir video, si existe `<video>.sync.json` (ADR 0024) se coteja contra `state.drv_lap`: ✓ verde si corresponde, ⚠ amarillo con instrucción ("carga esa vuelta en el Paso 1") si no. El error del mux ya no es la primera noticia.
- El criterio de comparación vive en `compose.sync_sidecar_mismatch` (fuente única): la UI solo formatea, así el aviso y el rechazo real del mux no pueden contradecirse.
- Heurística cubierta: **Prevención de errores** (§1.3), en su forma fuerte: avisar antes de que el usuario apriete el botón que va a fallar.

**REGLA — valores de eventos en NiceGUI 3.x (bug sistémico corregido en este PR):**
- Los handlers registrados con `.on("update:model-value", handler)` reciben `GenericEventArguments`, que **NO tiene `.value`** (dataclass con `sender/client/args`): todo handler que leía `e.value` moría con AttributeError silencioso (el volumen del Paso 5, el offset del Paso 4, el selector de curva del Paso 2, el mapeo de columnas del Paso 1, el formato del Paso 3 y la visibilidad del panel de pace notes del Paso 4 estaban rotos de origen).
- Peor aún: incluso los handlers `lambda _: refresh()` sobre ese evento van **una acción atrás**, porque el evento DOM se despacha ANTES de que NiceGUI asigne `element.value` — el refresh lee el valor anterior (así se comportaba el botón «Aplicar sonido»: habilitado/deshabilitado con un retraso de una edición; lo destapó la captura de Mariana al esperar el aviso del sidecar que "nunca llegaba").
- **Patrón correcto:** para todo lo que dependa del valor usa `elemento.on_value_change(handler)` (recibe `ValueChangeEventArguments` con `.value` ya asignado al elemento) o binding declarativo (`bind_enabled_from`, `bind_visibility_from`). `.on("update:model-value", ...)` queda solo para eventos que NO leen valores (ni siquiera indirectamente).
- **Corolario:** `set_value()` programático (botones "Explorar…") no pasa por el DOM — sí dispara `on_value_change`, pero cualquier refresh manual extra tras `set_value` es inofensivo.

**REGLA — `navigate` es async; no lo llames desde un `def` sin await:**
- `on_click=lambda: navigate(N)` funciona (NiceGUI aguarda el coroutine retornado), pero `def handler(): navigate(N)` **descarta el coroutine y no navega** — así estaba roto el botón "🔔 Generar Pace Notes" del Paso 2 (el reporte "no logré llegar a pace notes" del PO) y "Procesar otra vuelta" del Paso 4.
- **Patrón correcto:** si el handler hace algo más que navegar, decláralo `async def` y `await navigate(N)`.

### Unreleased

**ng_app.py — modo oscuro activado globalmente (bugfix de contraste):**
- `ui.dark_mode(True)` en `main_page()` establece el tema oscuro de Quasar como comportamiento por defecto; sin esto pywebview renderizaba en modo claro con problemas de contraste.
- Colores de texto en `ng_step0–4.py` migrados de `style("color:var(--X)")` a clases Tailwind (ver patrón 4 de §4).

### v0.14.0 (2026-06-30)

**Paso 0 — Rediseño del onboarding y selector de flujo:**
- Hero strip de 3 items (Referencia / Piloto / Salida) sustituye al bloque de texto de intro.
- Tarjetas de flujo con `st.container(border=True, height=260)`: altura fija para alinear los botones de selección entre columnas (ADR 0011).
- Estado neutro para el flujo por defecto: `st.info("Por defecto…")` en vez de `st.success("✓ Seleccionado")` hasta que el usuario confirma explícitamente (F-01). Heurística: **reconocer vs recordar** — el usuario sabe que no eligió nada todavía.
- `st.info`/`st.note` con texto `sgi-note` (borde azul izquierdo) para la instrucción de "una vuelta por flujo / compararse contra sí mismo".

**Paso 2 — Tabla de curvas:**
- Caption de convención de signos reescrito para explicitar que `Diferencia km/h` (+) y `Tiempo ganado/perdido` (+) tienen sentidos opuestos (F-11). Heurística: **prevención de errores** — la ambigüedad anterior llevaba a interpretaciones invertidas.
- Estado vacío cuando `rows=[]` con `st.info` y pasos de diagnóstico (F-10).
- Drill-down por curva: selector default en la mayor pérdida, síntesis determinista y tabla de puntos clave. Heurística: **reconocer en vez de recordar** — el usuario no revisa todas las gráficas ni memoriza MoTeC; la UI convierte la fila más importante en acciones concretas.
- Layout por pestañas: `Curvas prioritarias` primero; `Resumen de vuelta` y `Vuelta completa` separan las gráficas densas del coaching por curva. Heurística: **disclosure progresivo** — la señal accionable aparece antes que el contexto exhaustivo.

**Sidebar:**
- Botón 🔄 Nueva sesión al pie (F-23). Heurística: **control y libertad** — el usuario puede reiniciar sin recargar la pestaña.
