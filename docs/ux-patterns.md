# Patrones de UX/UI y gate de calidad de interfaz

> **Para qué es este documento.** Así como el repo tiene convenciones de **código** (ruff, tests)
> y de **docs** (§8 de `CONTRIBUTING.md`), este es el estándar de **interfaz**: las heurísticas que
> la UI (`fantasma ui`, Streamlit) y el HUD deben cumplir, y **el gate que verifica que se cumplan
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
- **Aserciones estructurales (Streamlit AppTest).** Sin pixeles: que los elementos esperados
  existan (los 3 flujos en el Paso 0, el botón primario de avance, la tabla de vueltas tras cargar,
  el progreso durante el render). Determinista y rápido.
- **Contraste de texto.** Chequeo automatizable de ratio de contraste de los estilos propios
  (los colores del HUD y del CSS de la UI) contra WCAG AA. Es aritmética sobre colores → bloquea.

### Capa B — Juicio, **ACONSEJA** (checkpoint de Mariana, vuelve al PO)

"¿Se ve profesional?", "¿el flujo se siente claro?", "¿el HUD es legible sobre ESTE video?" no son
deterministas. No bloquean por máquina: los dispara el hook de sesión **`mariana-stop`** al tocar
`fantasma/viz/` o `fantasma/ui/`, que **frena el cierre y obliga a mirar** (abrir `fantasma ui` /
revisar el HUD) con esta **checklist**:

- [ ] El cambio respeta las 10 heurísticas de §1 (revisión rápida).
- [ ] La pantalla afectada se ve coherente con el resto (espaciado, tipografía, iconos).
- [ ] El HUD (si aplica) es legible sobre video real, con la jerarquía piloto/ref correcta.
- [ ] Ningún texto en jerga de sistema; vocabulario de pista.
- [ ] Estados visibles: carga, progreso, encoder/tiempo, errores claros.

El resultado de la checklist es **juicio del PO**, no un auto-pase — igual que el Reviewer de código
y el Escribano de docs proponen pero el contenido no bloquea lo irreversible.

### Capa C — Local, **AVISA** (temprano)

`verificar.ps1` corre el smoke visual y las aserciones AppTest en modo aviso antes del push (skipea
limpio si no hay Chromium), como ya hace con lint/formato/tests. El CI es el que bloquea.

> **Regla de oro del gate:** lo que se pueda medir (layout, contraste, presencia de elementos,
> visibilidad de estado) **se mide y bloquea**; lo que sea gusto/sensación **se mira y vuelve al
> PO**. Nunca un gate subjetivo automático.

---

## 3. Estado y plan de implementación

| Pieza del gate | Estado | Acción |
| :-- | :-- | :-- |
| Smoke visual Paso 0 | ✅ existe (ADR 0012); baseline regenerado en v0.14.0 por cambio F-01 | — |
| Smoke visual Pasos 1-4 | ⏸️ diferido | AppTest cubre la estructura; Playwright requiere inyectar estado en browser (no trivial). Diferido post-v1.0 |
| Aserciones AppTest | ✅ Pasos 0-4 cubiertos (`tests/ui/`) — 18 tests en verde (v0.14.0) | — |
| Contraste WCAG | ⏸️ diferido post-v1.0 | Bajo riesgo: paleta reducida, colores revisados a ojo |
| Checklist Mariana | ✅ hook formalizado con los 5 puntos de §2-B (v0.14.0) | — |
| Integración en `verificar.ps1`/CI | ✅ (visual + AppTest vía pytest) | — |

> La decisión de tratar el gate de UX con la dualidad determinismo/juicio se asienta en un ADR
> (ver `docs/decisions/`). Los hallazgos de UX concretos por pantalla se documentan tras el
> diagnóstico con capturas, cruzados con [`casos-de-uso.md`](casos-de-uso.md).

---

## 4. Patrones específicos de NiceGUI (agregados en v2.0)

La UI principal de v2.0 migró de Streamlit a **NiceGUI** ([ADR 0018](decisions/0018-framework-ui-nicegui.md), enmienda al [ADR 0010](decisions/0010-framework-ui-streamlit.md)). NiceGUI es reactivo y asíncrono, así que impone patrones distintos a los de Streamlit (rerun completo del script). Estos son los que el código de `fantasma/ui/ng_*.py` sigue y que cualquier cambio nuevo debe respetar.

1. **Operaciones en background (render async).** Para operaciones largas (componer video, generar overlay) **no** se bloquea el event loop con `asyncio.sleep` en un loop. Se usa un objeto `RenderJob` (`ng_helpers.py`) que corre `fn` en un thread daemon (`start_bg_render`), y en la UI un `ui.timer(0.5, poll)` hace polling del job: lee `job.n/job.total` para actualizar la barra de progreso y, cuando `job.done`, cancela el timer y refresca la UI con el resultado. El `RenderJob` también expone `cancel()` (un `threading.Event`) para el botón «Detener». Patrón vivo en `ng_step4.py::_start_compose`.

2. **Forward-declaration de elementos UI.** En NiceGUI los handlers (closures) se definen **antes** de que existan los elementos que manipulan; el closure captura el nombre, no el valor. Patrón: declarar `ref_status = None  # noqa: F841` (y `drv_status`, `load_err`, etc.), definir los handlers que usan `ref_status`, y **más abajo** hacer la asignación real `ref_status = ui.label(...)`. El `# noqa: F841` es necesario porque ruff no ve que la variable se reasigna dentro de un closure — **no es dead code**, es la forma correcta en NiceGUI. Ejemplo en `ng_step1.py`.

3. **Diálogos de archivo nativos (`native=True`).** `_pick_file()` y `_pick_folder()` (`ng_helpers.py`) abren el selector nativo del OS vía Tkinter (`filedialog`). Solo funcionan de forma fiable en modo `native=True` (ventana pywebview, que es como arranca `fantasma-ng` en `ng_app.py::run`); en modo browser/desarrollo el selector puede fallar o abrir una ventana separada extraña. Ambos helpers atrapan cualquier excepción y devuelven `""`. Las operaciones potencialmente lentas (leer overlay, componer preview) se envuelven con `await run.io_bound(...)` para no bloquear el event loop.

4. **Corrección F-01 (NiceGUI) — pendiente.** El selector de flujo del Paso 0 (`ng_step0.py`) no debe mostrar ningún flujo como «✓ Seleccionado» al cargar la app. Hoy `is_selected = state.flow_key == flow_key` compara contra `flow_key`, que tiene un default (`_DEFAULT_FLOW = "compose"`), por lo que la tarjeta por defecto aparece pre-seleccionada aunque el usuario no haya elegido nada. El estado ya tiene el booleano `flow_chosen` (separado de `flow_key`) para distinguir «default cargado» de «usuario eligió explícitamente»; la corrección es que el Paso 0 use `flow_chosen` para decidir el marcado. Registrado para corrección en v2.0.x. Es el equivalente NiceGUI del F-01 ya resuelto en Streamlit (ver §5, v0.14.0).

---

## 5. Registro de cambios de patrón por versión

Historial de decisiones de UX que alteraron el layout o el flujo de la UI — para que el baseline visual tenga contexto al regenerarse.

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
