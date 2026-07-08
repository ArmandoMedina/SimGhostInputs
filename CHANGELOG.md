# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **Cues como catálogo configurable con prioridad y perfiles compartibles** (`fantasma/viz/pacenotes.py`, `fantasma/viz/cue_profiles.py`, `fantasma/ui/ng_step5.py`; [ADR 0027](docs/decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md), enmienda a los ADR 0024, 0025 y 0026): el set de cues deja de ser una lista hardcodeada — `DEFAULT_CONFIG` da a cada tipo un `enabled` y una `priority` configurables desde el Paso 5, reproduciendo exactamente el comportamiento anterior (no-regresión). El **ápex vuelve al catálogo, apagado por defecto** (el 0026 lo había retirado por completo como sonido). Los perfiles se cargan, guardan e importan como **JSON portable** (`~/.simghostinputs/cue-profiles/`), con degradación con gracia ante JSON malformado o de terceros — nunca crashea el Paso 5.
- **Modelado del coast (inercia)** (`fantasma/core/corners.py`): nuevos milestones `coast_start`/`coast_end` para el tramo entre el fin de la frenada (o el lift) y el gas sostenido, cuando ni freno ni gas superan su umbral. Nuevo cue `coast` (apagado por defecto, con la opción «Solo curvas sin frenada»), que marca una sola vez en `coast_start`.
- **Subtítulos de cues quemados con ventana adaptativa** (`fantasma/viz/pacenotes.py::build_cue_ass`, `compose_video(..., burn_cue_subs=True)`, checkbox del Paso 4; absorbe la #32): rotula sobre el video, sincronizado con el tono, qué significa cada sonido —etiqueta con color por tipo más nombre de curva— más una leyenda; la duración de cada rótulo es adaptativa (dura hasta el siguiente cue) en vez de la ventana fija de 1.5 s de la propuesta original, que apagaba el rótulo antes de tiempo. Solo se rotulan los cues habilitados.

### Corregido
- **El "inicio de acelerador" anclaba en un roce fugaz de pedal, no en la aceleración real** (`fantasma/core/corners.py`; [ADR 0027](docs/decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md)): `throttle_on` ahora exige throttle sostenido durante varias muestras seguidas —mismo patrón que ya usaba `full_throttle`— así un roce de pedal fugaz deja de ganar el hito y el cue ancla en la aceleración real y sostenida. El tramo de coast recién nombrado cierra el hueco de modelado que causaba el desfase (el motor asumía "fin de frenada implica inicio de gas", sin nombrar la inercia entre medias).
- **Metro 819: no sonaba el tono de frenada** (`fantasma/viz/pacenotes.py`): el `brake` plano (prioridad 80) lo tiraba el gap global cuando un vecino de mayor prioridad (el tono de ápex o un tic de countdown) caía a menos de `min_gap_m` de distancia — la curva se quedaba sin su marca de frenada. Corregido con un tono de frenada **universal y protegido**: ninguna curva con `brake_start` se queda sin su tono, sin importar qué compita por el gap.
- **Metro 4463: sonaban 3 bips sin ninguna frenada cerca** (bug del countdown empaquetado del [ADR 0025](docs/decisions/0025-countdown-ancla-en-la-frenada.md)): el chequeo de solape comparaba solo las posiciones finales de los cues, no los tics **entre sí**, así que dos countdowns encadenados amontonaban sus tics en una zona sin frenada real. Corregido: cada tic se chequea contra toda la línea de tiempo, tics de otras curvas incluidos.

### Cambiado
- **Rediseño del modelo de cues de pace notes** (`fantasma/viz/pacenotes.py`, commit `2f426ae`; [ADR 0026](docs/decisions/0026-cues-frenada-universal-countdown-oportunista.md), enmienda a los ADR 0024 y 0025): el tono de inicio de frenada pasa a ser **universal y protegido** (suena en toda curva con `brake_start`, ningún gap lo descarta — protegido vs protegido se quedan ambos); el countdown de 2 tics de aviso pasa a ser **oportunista por cabida** (se coloca donde quepa contra toda la línea de tiempo, ya no hay gate de severidad por `time_lost`/`braking_issue`); y se **retira el tono de ápex** como cue sonoro (el milestone se conserva intacto en los datos, las notas de voz y el matching de curvas). Suite: 248 passed.

### Cambiado
- **El último tono del countdown ES el punto de frenada** ([ADR 0025](docs/decisions/0025-countdown-ancla-en-la-frenada.md), enmienda al 0024): el evento `brake_countdown` se ancla en la frenada con su anticipo como `lead_m`, y el pack lo expande en 2 tics de aviso (660/770 Hz, a `lead_m` y `lead_m/2` antes) más el tono de frenada (1000 Hz) exacto donde frena la referencia — "nada de 1,2,3, ya: el 3 debe ser el ya" (feedback del PO con dato: los 3 bips sonaban en el metro 4463 con la frenada real en 4682). Tics que caen antes de la meta o a <50 m de otro cue se omiten; el tono de frenada nunca se pierde. Leyenda del Paso 5 actualizada; 2 tests nuevos. Evidencia: `qa_runs/charbel-20260706-cinta-estudio/` (iteración 3).

### Añadido
- **Paso 5 legible + breadcrumbs por flujo** (`ng_step5.py`, `ng_step4.py`, `ng_helpers.py`): leyenda de tonos plegable derivada del motor (`PLAN_CUES`/`DEFAULT_FREQS`, con la aclaración de que los tonos marcan los puntos de la referencia); checkbox «Todas las curvas» (manda `top=0`); caption bajo «Aplicar sonido» que dice exactamente qué falta cuando está deshabilitado; aviso ✓/⚠ que coteja el sidecar `.sync.json` del video contra la vuelta cargada antes de apretar el botón; el Paso 4 escribe el `sync_info` al componer; y `render_breadcrumb(step, flow_key)` pinta solo los pasos del flujo activo (en "Solo Pace Notes": Inicio › Importar › Análisis › Pace Notes).
- **ADR 0024 — Sincronía de pace notes** (Aceptada): anticipación del countdown por tiempo (`countdown_s=3.5` a la velocidad de llegada, clamp [60, 350] m; fallback a los 120 m fijos sin `v`), gap mínimo global entre curvas (gana la prioridad), descarte de cues que caen antes de la meta, `brake` a 1000 Hz (distinguible del countdown), `top=0` = todas las curvas (pace notes de ritmo), y **sidecar de sincronía** `<video>.sync.json` que `compose_video` escribe y el mux del Paso 5 valida (error accionable si la vuelta cargada difiere > 0.1 s). Base: diagnóstico con datos reales en `qa_runs/charbel-20260705-desync/` que refuta la hipótesis de descalibración de distancia. 7 tests nuevos en `tests/viz/`.

### Corregido
- **El botón «🔔 Generar Pace Notes» del Paso 2 no hacía nada** (`ng_step2.py`): llamaba al `navigate(5)` async sin await, el coroutine se descartaba y la navegación moría en silencio — era el "no logré llegar a pace notes" del QA del PO. Mismo bug en «Procesar otra vuelta» del Paso 4 (limpiaba el estado pero no navegaba). Regla nueva en `ux-patterns.md`.
- **Handlers de valor rotos en toda la UI (bug sistémico de NiceGUI 3.x)**: los `.on("update:model-value", ...)` que leían `e.value` morían con AttributeError silencioso porque `GenericEventArguments` no trae `.value`. Estaban rotos de origen: los sliders de volumen del Paso 5 (el volumen elegido nunca aplicaba), el offset manual del Paso 4 (no se persistía al teclear), el selector «Curva a atacar» del Paso 2, el mapeo de columnas del Paso 1, el selector de formato del Paso 3 y el checkbox de pace notes del Paso 4. Además, incluso los refreshes `lambda _: ...` sobre ese evento iban **una acción atrás** (el evento DOM llega antes de que NiceGUI asigne `element.value`): el botón «Componer video» del Paso 4, la vista previa del HUD y el botón «Aplicar sonido» se habilitaban/actualizaban con una edición de retraso — destapado por la captura de Mariana. Todo convertido a `on_value_change`/bindings declarativos; regla nueva en `ux-patterns.md`.
- **Los botones «Explorar…» del panel ② del Paso 5 no refrescaban el botón «Aplicar sonido»** (`set_value` no dispara el evento DOM): ahora refrescan a mano el estado del botón y el aviso del sidecar.
- **Los cues de pace notes quedaban enterrados −6 dB bajo el audio del motor** (`viz/compose.py::_audio_mix_filter`): `amix` sin `normalize=0` divide cada entrada entre el número de inputs, atenuando motor y cues por igual (medido: mezcla a −23.3 dB vs −17.3 dB del original; tono máx. −7.2 dB). Con `normalize=0` las entradas se suman sin atenuar (cue −0.9 dB, motor intacto). Aplica al compose completo y al mux standalone del Paso 5. Requiere ffmpeg ≥ 4.4. Test de regresión `test_audio_mix_filter_no_normalize`; evidencia en `qa_runs/mariana-20260705-180356/` y diagnóstico del desync percibido en `qa_runs/charbel-20260705-desync/notas.md`.

### Añadido
- **CI de release: generación y publicación automática del instalador Windows** ([ADR 0022](docs/decisions/0022-ci-release-installer.md)): nuevo workflow `.github/workflows/release.yml` disparado por `on: release: types: [published]` que instala deps + Inno Setup (`choco install innosetup`), ejecuta `build_installer.py --inno` y sube `SimGhostInputs-vX.Y.Z-Setup.exe` (y un zip portable) como assets permanentes del release con `gh release upload --clobber`. El job `build-installer` de `tests.yml` (mal cableado, nunca corría) se elimina.

### Cambiado
- **Versión del instalador parametrizada** (`tools/build_installer.py`, `tools/installer.iss`): `build_installer.py` lee la versión del paquete con `importlib.metadata` y la pasa a ISCC vía `/DMyAppVersion=`; `installer.iss` usa `{#MyAppVersion}` en vez del literal `"2.0.0"` hardcodeado. Se habilita el icono (`docs/icon.ico`) en el instalador.
- **Versión unificada en `fantasma/__init__.py` (SSOT)** ([ADR 0023](docs/decisions/0023-fuente-unica-de-version.md)): `__version__` pasa a ser la fuente única de verdad. `pyproject.toml` la deriva con `dynamic = ["version"]` + `attr:`; el badge del footer de la UI (`ng_app.py`) y `tools/build_installer.py` la importan desde ahí en lugar de usar un literal manual o `importlib.metadata`. Elimina la raíz de los tres bugs consecutivos de badge desactualizado (v2.0→v2.1.0, v2.1→v2.1.1, v2.1→v2.2.0). Para bumpear: editar `fantasma/__init__.py`, no `pyproject.toml`.

## [2.2.0] - 2026-07-05

### Añadido
- **Flujo "Solo Pace Notes"** ([ADR 0021](docs/decisions/0021-flujo-solo-pacenotes.md)): nueva tarjeta en el Paso 0 que enruta directamente Importar(1)→Análisis(2)→Pace Notes(5), saltando overlay y compose. Para el caso de uso "tengo un video con overlay hecho y solo quiero pace notes". Aditivo: los flujos `analisis`, `overlay` y `compose` no se modifican.
- **Guía del Paso 5**: tooltips en los controles de ambos paneles y caption puente ①→②; el panel "Aplicar sonido a video existente" ya no se oculta al acceder al Paso 5 (el guard aplica solo al panel de generación). Los textos explican por qué se necesitan dos vueltas (la derivación de pace notes requiere `time_lost` de `compare()`).

### Corregido
- **El botón «Aplicar sonido» del Paso 5 no reflejaba su estado deshabilitado** (`ng_app.py`): el selector CSS apuntaba a `:disabled` pero Quasar aplica la clase `.disabled`; ahora se atenúa (opacity 0.4) cuando faltan el video o la carpeta del pack. Además, el `finally` del mux re-evalúa el estado real en vez de re-habilitar incondicionalmente.

## [2.1.1] - 2026-07-05

### Corregido
- **El badge de versión del footer mostraba «v2.0» tras el release 2.1.0** (`ng_app.py`): el literal del `version-badge` estaba desacoplado de `pyproject`; corregido a «v2.1». La deuda de unificar la versión del footer con una única fuente queda anotada en el ROADMAP.

## [2.1.0] - 2026-07-05

### Añadido
- **Paso 5 — Pace Notes en la UI** (`fantasma/ui/ng_step5.py`): nuevo paso del wizard que genera el pack de pace notes para CrewChief (tonos, voz o ambos) desde `state.rows` y `state.corners`. Incluye selector de modo/top-N/volumen/idioma y directorio de destino pre-rellenado vía `crewchief_pacenotes_dir()`. Se activa desde el botón «Generar Pace Notes» del Paso 2; el paso aparece en el sidebar «Salidas» junto a Overlay y Video.
- **Mux standalone de pace notes en video existente** (`ng_step5.py`, `viz/compose.py::mux_pace_notes_into_video`): panel en el Paso 5 para mezclar el audio del pack de pace notes en un video ya compuesto usando ffmpeg `-c:v copy` (sin re-encodear). Requiere la vuelta del piloto cargada para sincronizar los cues por distancia.
- **Pipeline autónomo overlay→compose** (`ng_step3.py`, `ng_step4.py`, `ng_state.py`): checkbox «Al terminar, componer automáticamente» en el Paso 3 (flujo compose). Al terminar el overlay, navega al Paso 4 y lanza la composición sin intervención. Notificación de escritorio (Web Notifications API con degradación a `ui.notify`) al terminar. Nuevo estado `auto_compose` y `pending_autocompose` en `AppState`.
- **Pace Notes opcionales en el video compuesto** (`ng_step4.py`, `viz/compose.py`): checkbox «Incluir pace notes en el video» en el Paso 4; mezcla los WAVs del pack en el audio del video final durante el compose. `compose_video()` acepta nuevos parámetros opcionales `pace_notes_dir`, `pace_notes_volume` y `lap`.
- **Loading states en carga de CSV** (`ng_step1.py`): spinner + «Leyendo CSV...» durante la carga del archivo y «Calculando vuelta rápida...» al seleccionar la mejor vuelta; la operación de I/O se mueve a `run.io_bound` para no bloquear el event loop.
- **Botón «Componer video» deshabilitado hasta completar entradas** (`ng_step4.py`): se deshabilita si faltan el video de grabación o el overlay; se reactiva en tiempo real al rellenar ambos campos.

### Cambiado
- **`SimGhostInputs.spec` fuera del versionado** (`.gitignore`): `nicegui-pack` lo regenera en cada build con la ruta absoluta local de nicegui, deshaciendo cualquier fix versionado — es artefacto de build, no fuente. La receta canónica de empaquetado es `tools/build_installer.py`.
- **Deuda del ADR 0018 medida**: bundle onedir real de v2.0.0 = 373 MB; exe 30.7 MB; instalador 104.7 MB. Smoke del exe empaquetado: arranca y responde HTTP 200 en `127.0.0.1:8765`.
- **Layout 2 columnas en Pasos 4 y 5** (`ng_step4.py`, `ng_step5.py`): Paso 4 separa controles de entradas (izquierda) de la vista previa del HUD (derecha); Paso 5 separa «Generación» (izquierda) de «Aplicar sonido» (derecha). Contenido de la página centrado con ancho máximo de 1 100 px.

### Corregido
- **Botón «Generar Pace Notes» del Paso 2 navegaba al Overlay (Paso 3) en vez del Paso 5**: `navigate(3)` corregido a `navigate(5)` en `ng_step2.py`.
- **Auto-compose no arrancaba si el video/overlay no estaban rellenos al entrar al Paso 4** (BUG1): al navegar al Paso 4 en modo `pending_autocompose`, si los campos no estaban ya rellenos el compose se disparaba sin datos y fallaba silenciosamente; ahora verifica que ambos campos estén presentes antes de arrancar.
- **Campo Venue del circuito no se leía correctamente** (`ng_step2.py`): el nombre de pista usaba solo `meta.get("track")`; ahora prefiere `meta.get("Venue")` (clave real del metadato AMS2) con fallback a `"track"`.
- **Inconsistencia de tokens de color** (`ng_step2.py`): textos mutados migrados de `.style("color:var(--muted)")` a clase Tailwind `text-gray-400`, coherente con el patrón del resto de pasos (ADR 0018).
- **`tools/installer.iss` compilaba solo en CI-teoría**: primer build real del instalador destapó rutas relativas resueltas contra `tools\` (faltaba `SourceDir=..`) y un custom message inexistente (`{cm:DesktopFolder}` → `{cm:CreateDesktopIcon}`). Con esto se generó y publicó `SimGhostInputs-v2.0.0-Setup.exe` (104.7 MB) como asset del release.
- **Remediación visual QA** (`ng_app.py`, `ng_step0..5.py`): especificidad CSS de botones de sidebar en dark mode (prefijo `.sgi-sidebar` supera el color primario de Quasar); chrome del q-uploader ocultado en zonas custom del Paso 1; jerarquía `btn-featured` vs `btn-secondary` con `!important`; acentos corregidos en textos de todos los pasos; nombre de pista con guiones bajos reemplazados por espacios; celda de fecha en resumen del Paso 2 oculta cuando está vacía.
- **Detección de curvas diferida en Paso 3** (`ng_step3.py`): el render del panel ya no bloquea mientras se detectan las curvas; se muestra «Analizando el trazado...» con spinner y se deshabilita «Generar overlay» hasta completar la detección (o fallar silenciosamente con lista vacía).
- **Guard de doble-clic en «Aplicar sonido» del Paso 5** (`ng_step5.py`): semáforo `_mux_state["running"]` evita lanzar dos procesos ffmpeg concurrentes al mismo archivo de salida.

## [2.0.0] - 2026-07-03

### Añadido
- **Homologación con project-starter v0.5.0** ([ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md), cierra la Fase 4 del ADR 0016): job `audit` en CI (`tools/auditar-radius.ps1` — blast-radius §8 sobre el rango del PR; regla anti-bypass: required checks o nada); matcher del manifiesto homologado (raíz-sin-slash, `excluye`, `mensaje`) y área `raiz`; **Mariana exige evidencia verificable en `qa_runs/`** (un veredicto sin artefacto no vale, convención `qa_runs/<rol>-<fecha>/`); hook `no-memorias` (PreToolUse); `/arranca` con reglas duras de sesión; `docs/recursos-del-proyecto.md`; recetario `docs/entorno-windows-powershell51.md` con versión corta en los 5 SKILL.md; `templates/plan-de-trabajo.md`; ciclo de vida explícito del HANDOFF.
- **CrewChief Pace Notes (MVP)**: nuevo comando `fantasma pacenotes` para generar `metadata.json` + WAVs desde `corners_detected.json` y `corners_compare.csv`. El modo base (`--mode tones`) crea tonos por hito de curva sin dependencias externas adicionales; el extra opcional `[voice]` añade `edge-tts` para frases de voz. Incluye tests unitarios del generador WAV y smoke CLI del pack.
- **Pace Notes — plan anti-saturación y preview en video**: `fantasma pacenotes` ahora escribe `plan.json` con las señales elegidas/omitidas por curva y usa un plan inteligente por defecto (máximo 3 eventos por curva, separación mínima entre sonidos, countdown compacto solo donde cabe). `fantasma compose` acepta `--pace-notes-dir` para mezclar esos WAVs con el audio del video y previsualizar cómo se sentirían en carrera, sincronizados por distancia usando `--driver`.
- **UI NiceGUI v2.0**: nuevo frontend de escritorio nativo (pywebview) que sustituye a Streamlit como UI principal. Entry point `fantasma-ng`. Módulos: `ng_app.py` (router), `ng_state.py` (AppState), `ng_helpers.py`, `ng_step0.py`–`ng_step4.py` (wizard de 5 pasos portado de Streamlit).
- **Preview reactiva del HUD en Paso 4** (`viz/hud_preview.py`): actualización en tiempo real al cambiar posición, escala y overlay.
- **Empaquetado Windows**: `tools/build_installer.py` (nicegui-pack) y `tools/installer.iss` (Inno Setup) para instalador doble-clic.
- **CI**: job `build-installer` (tags `v*`) y migración de `visual-smoke` a import smoke NiceGUI.
- `fantasma/viz/compose.py`: `compose_video()` devuelve dict `{"path", "encoder", "duration_s"}`. La UI NiceGUI Paso 4 muestra el encoder usado (h264_nvenc o libx264) y la duración del encode al terminar.
- `fantasma/core/compare.py`: aviso en `summary["avisos"]` cuando el piloto va más de 1 s más rápido que la referencia — indica posible inversión de `--reference` y `--driver`.
- UI NiceGUI Paso 1: hint colapsable "¿No tienes vuelta de referencia externa?" para el caso C10 (compararse contra sí mismo).
- **UX NiceGUI post-auditoría v2.0**: breadcrumb de navegación en todos los pasos; links "Guía MoTeC" y "Ejemplo CSV" en Paso 0 con dialogs; slider de escala con valor dinámico en tiempo real; sidebar con checkmark ✅ cuando el paso está completo; guard de ffmpeg en Paso 3 con instrucción de instalación por plataforma; CSS vars para colores de los paneles de Paso 4.
- **C19 — aviso proactivo de ffmpeg en Paso 0**: al seleccionar el flujo "Video con HUD" o "Solo overlay", la UI muestra inmediatamente un aviso si ffmpeg no está instalado — sin esperar al paso de render.

### Optimizado (2026-07-02 — render paralelo)
- **Collect round-robin en `_render_parallel`** (`overlay.py`): el loop de recolección de workers era secuencial — esperaba al worker 0 aunque los demás ya hubieran terminado. Reemplazado por polling concurrente (while+pending): cada pasada sondea todos los workers pendientes y procesa inmediatamente los que terminaron. Tiempo de pared = tiempo del worker más lento, independientemente de su posición en el orden de lanzamiento.
- **Pickle compacto por chunk** (`overlay.py`): cada subprocess de overlay recibía el tuple `base` completo con todos los arrays numpy (~1-5 MB por worker segun vuelta). Ahora cada worker recibe solo el slice de distancia que cubre su rango de frames, mas padding de ventana HUD (`W_BEFORE`/`W_AFTER`) y retención de luces ABS/TC (`HOLD_M`). En Nordschleife reduce el pkl de ~4-5 MB a ~1 MB por worker.
- **`tests/viz/test_overlay.py`**: añadido `test_render_parallel_collect_round_robin` — 3 workers que terminan en orden inverso al de lanzamiento; verifica que todos son recolectados sin bloqueo y que el contador de frames llega a `n_frames`.

### Añadido (2026-07-02 — tests de regresión visual)
- **`test_pw_step0_button_alignment`** y **`test_pw_step0_selected_button_visibility`** en `tests/ui/visual/test_e2e_playwright_wizard.py`: detectan bugs de alineación de botones y contraste de texto antes de que lleguen al exe empaquetado.
- **`tests/test_main_gui.py`**: test AST que verifica que `freeze_support()` está presente en el entry point de PyInstaller.
- **`tests/ui/test_step3_render_guard.py`**: test de regresión para el guard de doble-clic en "Generar overlay".

### Añadido (QA 2026-07-01)
- **QA con datos reales — 4 combinaciones auto-circuito ejecutadas**: Nordschleife BMW vs Audi (cross-car), Barcelona BMW vs Mercedes, Interlagos GT3 vs Hypercar (classes diferentes — aviso "piloto más rápido" +7.5 s), F3 vs LMP2 (fallo limpio por canal Distance ausente en CSV de ORECA). Edge cases documentados en `docs/casos-de-uso.md` C30–C35.
- **`docs/casos-de-uso.md` — C30–C35**: seis escenarios nuevos basados en el material real: circuito corto vs largo, cross-car dentro de clase, clases distintas (LMP2 vs GT3, Hypercar vs GT3), flujo headless sin video, dos sesiones del mismo piloto.
- **Tests e2e NiceGUI** (`tests/ui/test_e2e_wizard.py`): 5 tests end-to-end del wizard de 5 pasos con datos reales de Nordschleife. Usa `_SharedState` (dict en memoria, sin I/O a disco) para inyectar datos pre-calculados en AppState sin abrir el browser.
- **`tests/ui/conftest.py`**: `pytest_configure` que parchea `Storage.clear()` para ignorar `PermissionError` de teardown en Windows (archivo temporal bloqueado por proceso de overlay activo en paralelo).

### Cambiado
- `setup.ps1`: la instalación de GitHub CLI (`gh`) se mueve detrás del flag `-Dev`; el setup de usuario final no instala herramientas de desarrollo.
- Suite de tests ampliada a **190 tests**: nuevos e2e wizard (5), corrección import directo en `test_sync.py`.
- UI NiceGUI Paso 1: zona de carga de CSV migra de botón con diálogo nativo (tkinter) a componente `ui.upload` de NiceGUI — el picker pasa a ser un componente integrado en el browser con soporte de arrastre, compatible tanto en modo native=True como en modo browser.

### Corregido
- `fantasma/ui/ng_step2.py`: `ui.download().classes()` fallaba con `AttributeError` en entorno sin browser real — añadido None-check (`ui.download()` devuelve None sin conexión WebSocket activa).
- `fantasma/ui/ng_state.py`: `clear_drv()` ahora elimina `drv_name` al cambiar vuelta del piloto — el nombre del archivo quedaba huérfano de la sesión anterior.
- UI NiceGUI — `F-01`: la tarjeta del flujo por defecto ya no se muestra como "✓ Seleccionado" hasta que el usuario hace clic en ella explícitamente.
- **UI Paso 0 — alineación de botones**: `.flow-card` ahora usa `display:flex; flex-direction:column` con `margin-top:auto` en `.q-btn` — los botones "Elegir este" quedaban a diferentes alturas según la longitud del contenido de cada tarjeta.
- **UI Paso 0 — texto invisible en botón seleccionado**: removido `.props("flat")` de los botones de tarjeta; Quasar `flat` overrideaba el `color:white` de `.btn-featured`, haciendo el texto invisible en dark mode.
- **UI Paso 1 — botón CARGAR parece deshabilitado**: mismo fix que arriba — removido `.props("flat")` de `.btn-primary` en `ng_step1.py`.
- **Exe PyInstaller — crash al cerrar**: `main_gui.py` ahora incluye `multiprocessing.freeze_support()` dentro del guard `if __name__ == "__main__"` — sin esto, Windows lanzaba `PermissionError [WinError 5]` al cerrar el proceso worker.
- **Paso 3 — doble clic en "Generar overlay"**: el botón se deshabilita durante el render y se reactiva al terminar — antes era posible lanzar dos procesos de overlay simultáneos causando corrupción del archivo de salida.
- **Importers — doble-append de columnas duplicadas** (`generic_csv.py`, `motec_csv.py`): al invocar `load()` más de una vez en la misma sesión las columnas mapeadas se añadían dos veces al `DataFrame`, corrompiendo silenciosamente las comparaciones posteriores.
- **CLI — exit codes no propagados**: `fantasma compare`, `overlay` y `pacenotes` ignoraban el código de salida de los subprocesos; una falla interna devolvía exit 0 en lugar del código real.
- **`overlay.py` — ffmpeg sin diagnóstico de stderr**: los errores de ffmpeg se descartaban (`stderr=DEVNULL`); ahora se captura el stderr y se anexa al mensaje de error visible al usuario.
- **Pacenotes — asyncio en hilo de voz no seguro**: `asyncio.run()` desde el hilo de voz chocaba con el event loop de NiceGUI; reemplazado por `asyncio.new_event_loop()` en un hilo propio.
- **`hud_preview.py` — ffmpeg falla sin mensaje útil**: el preview del HUD reventaba sin indicar la causa; ahora muestra el stderr de ffmpeg al usuario.
- **UI — fuga de archivos temp de uploads** (`ng_helpers._save_upload`): usaba `NamedTemporaryFile(delete=False)` sin cleanup; los CSV subidos se acumulaban en el directorio temp del SO. `do_load()` ahora borra el temporal tras parsear.
- **UI Paso 3 — event loop congelado durante el render**: `ng_step3` llamaba `time.sleep()` en el hilo de UI de NiceGUI bloqueando el event loop; reemplazado por `await asyncio.sleep()`.
- **UI — timers de polling no cancelados al navegar**: los timers periódicos de los pasos 3 y 4 seguían corriendo al cambiar de paso, causando actualizaciones huérfanas en el componente abandonado; ahora se cancelan en el `on_cleanup`.
- **UI Paso 2 — cadena H-01 (QA visual con material real)**: tres bugs encadenados que dejaban las gráficas vacías al correr con datos reales: las llamadas de render bloqueaban el event loop de NiceGUI — migradas a `run.io_bound` con snapshots de `AppState` capturados fuera del thread antes de entrar; `ui.image` recibía `bytes` en lugar de ruta de archivo (elemento zombie que Vue descartaba junto con el batch DOM completo del paso); 11 contenedores `ui.html` sin atributo `slot` cuyos hijos Vue descartaba silenciosamente — migrados a `ui.element("div")`. Evidencia en `qa_runs/mariana-20260703-0740/`.

### Seguridad
- **UI solo en `127.0.0.1`** (`ng_app.py`): NiceGUI arranca con `host="127.0.0.1"` — el servidor no expone el puerto a la red local (ajuste equivalente aplicado a Streamlit mientras convive con NiceGUI).

### Añadido (2026-07-03 — auditoría integral pre-v2.0)
- **Auditoría integral pre-v2.0.0** completada: revisión end-to-end de código, tests, docs, gates y método de la rama `codex/sgi-v2-merge`. Informe y evidencia en `qa_runs/2026-07-03-auditoria-integral/`. **212 tests** verdes tras la remediación R1.

### Eliminado (2026-07-03)
- **UI Streamlit retirada** (`fantasma/ui/{app,step0-4,_helpers}.py` + 6 tests AppTest): la interfaz Streamlit se retira por completo. El subcomando `fantasma ui` y el extra `[ui]` (incluyendo su presencia en `[full]` y en el CI) han sido eliminados. La única UI es NiceGUI (`fantasma-ng`, extra `[ui-ng]`), que es superconjunto funcional de la Streamlit en todos los flujos del wizard. Decisión registrada en la enmienda 2026-07-03 del [ADR 0018](docs/decisions/0018-framework-ui-nicegui.md); censo de archivos en `qa_runs/2026-07-03-auditoria-integral/decision-retiro-streamlit.md`.

### Cambiado (2026-07-03)
- **Blast-radius de `viz`** — `hud-reference` pasa de `doc_bloquea` a `doc_avisa` ([ADR 0020](docs/decisions/0020-blast-radius-viz-hud-reference-avisa.md)): los cambios no-visuales en `fantasma/viz/` ya no bloquean el push por no tocar `hud-reference.md`; el gate avisa y pregunta si el cambio es visual.
- **`SimGhostInputs.spec`** — ruta de los recursos de NiceGUI ahora es dinámica (vía `importlib`); elimina la dependencia de la ruta exacta de la versión instalada.
- **`audit` como required check del ruleset de `master`** (ADR 0019): el job `audit` (blast-radius §8 sobre el rango del PR) queda como barrera dura — un PR con docs desfasadas no puede mergearse.

## [1.0.0] - 2026-06-30

**Hito — pipeline AMS2 completo, documentado y probado.** `setup.ps1` validado en instalación limpia de Windows 11 (Hyper-V VM). Alcance declarado: AMS2, pipeline offline (análisis + overlay + compose), interfaz gráfica de 5 pasos. 142 tests en verde.

### Añadido
- **Drill-down por curva en UI Paso 2**: la tabla de curvas ahora selecciona por defecto la mayor pérdida y muestra un panel accionable con síntesis y plan de ataque (frenada, pico de freno, V-Min, gas 100%, G lateral y marcha/RPM cuando existan). El cálculo vive en `corner_coaching(row, trace)` dentro de `core`, sin LLM ni red, y degrada con gracia cuando faltan canales opcionales. La pantalla se organiza en pestañas: curvas prioritarias primero, resumen de vuelta después y la vista completa de todos los canales en una pestaña propia. Con tests de núcleo (`tests/core/test_coaching.py`) y AppTest de Paso 2.
- **`verificar.ps1` — aviso de cobertura de tests**: al correr las barreras locales se informa cuántos tests cubre la suite en ese momento, para que el aviso de "pytest verde" incluya el número real de casos en verde.

## [0.15.0] - 2026-06-30

### Añadido
- **Gate de UX — AppTest Pasos 1, 3 y 4** (Capa A): aserciones estructurales completan la cobertura de los 5 pasos del wizard (Pasos 0 y 2 ya existían). 142 tests verdes.
- **Checklist de Mariana formalizada en el hook `mariana-stop`**: los 5 puntos del §2-B de `ux-patterns.md` ahora aparecen explícitamente en el mensaje de bloqueo para no depender de que el revisor tenga el doc abierto.

### Refactorizado
- **`core/` — API pública estabilizada:** `_samples` renombrado a `samples` (era parte de la API real); funciones internas de `wear.py` (`_slip_index`, `_assist_count`, `_tyre_temp_avg`) prefijadas con `_`; constante `CANONICAL` eliminada (muerta, la documentación vive en `formato-datos.md`); `core/__init__.py` ahora declara `__all__` explícitamente.

## [0.14.0] - 2026-06-30

### Añadido
- **UI — botón «Nueva sesión» en el sidebar** (F-23): limpia todo el estado y vuelve al Paso 0 sin recargar la pestaña. Evita que el usuario tenga que refrescar el navegador para empezar un análisis nuevo.
- **UI Paso 2 — descarga de tabla de curvas en CSV** (F-09): botón `⬇️ Descargar tabla de curvas (CSV)` al final del análisis para guardar el reporte de curvas localmente.
- **UI Paso 2 — estado vacío si no se detectan curvas** (F-10): aviso claro con instrucción de re-exportación cuando la vuelta no tiene longitud suficiente o le falta el canal de distancia.
- **UI Paso 0 — estado neutro del flujo por defecto** (F-01): el flujo pre-seleccionado al arrancar muestra "Por defecto — pulsa «Empezar» o elige otro flujo" hasta que el usuario confirma con un clic, diferenciando la selección implícita de la explícita.
- **Aviso temprano si el CSV no trae el canal de distancia** ([ADR 0017](docs/decisions/0017-distancia-canal-requerido.md)): en MoTeC i2 la casilla **«Include Distance Data»** es fácil de no marcar, y sin ese canal —el eje maestro de la comparación— no hay análisis posible. Ahora `fantasma laps` lo **avisa** (con la instrucción de re-exportar) y la **UI Paso 1 lo bloquea** (no deja avanzar el flujo) en vez de dejar que el usuario falle más adelante en `detect`/`compare`/`overlay`. Detectado en el QA de cierre de v1.0 con un export real del ORECA 07.

### Corregido
- **UI — `_step_done(0)` siempre devolvía `True`** (B-01): chequeaba `"flow_key"` (presente desde el inicio) en vez de `"flow_chosen"` (que solo existe tras acción explícita del usuario). El sidebar mostraba el Paso 0 como completado en frío.
- **UI — `_step_done(4)` siempre devolvía `False`** (B-02): comparaba el flag contra el literal `False` en lugar de comprobar `"last_compose_video" in st.session_state`. El paso nunca se marcaba ✅ aunque el video existiese.
- **UI Paso 1 — estado de análisis rancio al cambiar archivos** (B-03): al pulsar «Cargar» con archivos nuevos, `summary`, `trace`, `rows` y `charts_paths` de la sesión anterior no se borraban. El Paso 2 mostraba la comparación vieja. Ahora se limpian antes de procesar.
- **UI Paso 1 — sin guard para `ref_laps` vacío** (B-04): la referencia sin vueltas detectadas caía silenciosamente; ahora muestra `st.warning` con instrucción de re-exportación, simétrico con el guard que ya existía para el piloto.
- **UI — `_next_step_btn` mostraba «Completaste» cuando el paso no estaba en el flujo** (B-07): si el usuario visitaba el Paso 2 en el flujo «Solo overlay», `flow["next"].get(2)` devolvía `None` y se mostraba el mensaje de completado incorrectamente. Ahora detecta pasos fuera del flujo y muestra el botón al siguiente paso real.
- **UI Paso 2 — ejecución continuaba tras error de comparación** (B-08): faltaba `st.stop()` en el `except`, el código seguía corriendo y generaba errores en cascada.
- **UI Paso 4 — import de `sync_gray_zone_warning` sin manejo de error** (B-11): si el módulo no estaba disponible, la UI reventaba en lugar de degradar. Envuelto en `try/except ImportError`.
- **UI Paso 4 — ffmpeg check no detenía el render ni indicaba cómo instalar** (B-12): sin `st.stop()` el formulario seguía visible y la instrucción de instalación era genérica. Ahora detiene el render y detecta la plataforma (Windows, macOS, Linux) para dar el comando exacto.
- **UI Paso 4 — mensaje de sincronía resuelta no aparecía** (B-13): la condición para mostrar «sincronía detectada» no cubría el caso donde se resolvía manualmente una detección ambigua.
- **UI Paso 4 — `_mss()` definida dos veces en distinto scope** (B-14): causaba `UnboundLocalError` en ciertas rutas. Movida al nivel de módulo.
- **UI Paso 1 — etiqueta de expander del piloto** (F-06): decía «Cambiar vuelta» (igual que el de referencia); ahora dice «Cambiar vuelta del piloto» para distinguirlos visualmente.
- **UI Paso 2 — convención de signos ambigua en la tabla de curvas** (F-11): «Diferencia km/h positivo» y «Tiempo ganado/perdido positivo» tienen signos opuestos. Caption reescrito para hacerlo explícito.
- **UI Paso 3 y 4 — mensajes de éxito mostraban la ruta completa del archivo** (F-13): ahora muestran solo el nombre de archivo con `os.path.basename()`.
- **UI Paso 4 — botón de sincronía automática en columna derecha** (F-17): layout de dos columnas era contraintuitivo (resultado izquierda, botón derecha). Ahora botón ancho completo y resultado debajo.
- **UI Paso 4 — `st.warning` redundante en expander de sync manual** (F-20): el título del expander ya indica que es avanzado. Aviso duplicado eliminado.
- **UI Paso 4 — «duración completa» ambigua en la opción de compose** (F-22): reemplazado por «duración completa del overlay».
- **`detect_corners` reventaba con `KeyError('dist')` desnudo si faltaba el canal de distancia**: ahora degrada con gracia lanzando un `ValueError` con mensaje accionable (re-exportar incluyendo el canal Distance), igual que ya hacía con el canal `speed`. Como `compare` y `overlay` pasan por aquí, los tres heredan el aviso claro. Con test de regresión (`test_detect_requires_dist_channel`).
- **`fantasma compare` con un CSV de piloto sin distancia escapaba como `NoneType` genérico**: ahora valida temprano la distancia en referencia y piloto, igual que `detect`, y devuelve el mensaje accionable para re-exportar con `Distance`. Detectado con el export real del ORECA 07. Con test de regresión (`test_compare_avisa_driver_sin_distancia`).

### Pruebas
- Suite local: **127 tests en verde** tras todos los cambios de UI y validación de distancia.
- **QA de AMS2 en ≥3 circuitos cerrado (requisito de v1.0).** Validación sobre telemetría real en **4 circuitos** (Barcelona NC, Interlagos, Nordschleife 2025, Nürburgring GP) y **clases más allá de GT3** (Hypercar: Valkyrie/BMW Hybrid V8/Cadillac V-Series.R; Fórmula: F3; Prototipo/LMP2: ORECA 07): el pipeline de análisis (`laps`→`detect`→`compare`) procesa todas las clases sin errores de lógica, con degradación graceful de canales ausentes. Único hallazgo: el export del ORECA sin canal de distancia (corregido arriba).
- **QA extendido con material real externo:** matriz sobre 19 CSVs AMS2 del directorio de pruebas: `laps` importó todos, `detect` generó curvas para todos los CSV con distancia y `compare --no-charts` generó reportes por circuito/clase. También se validó un tramo corto de `overlay` + `compose` con video real.

### Documentación
- **UI Paso 0 — onboarding guiado por objetivo:** la pantalla inicial adopta un patrón de decisión progresiva: primero muestra referencia/piloto/salida, deja claro que se puede comparar el mismo CSV contra sí mismo y usa el GIF real de exportación de MoTeC i2 como ayuda contextual antes de la guía completa.
- **ADR 0017 — La distancia es un canal requerido; no se sintetiza desde la velocidad** (Aceptada): se exige el canal `dist` y se descarta derivarlo integrando `speed × dt`, porque dos vueltas derivarían ejes inconsistentes y romperían el alineado por metro del que depende todo el análisis. Se refuerza la guía de export en `guia-usuario.md`, `formato-datos.md` y la capacidad COR-01.

## [0.13.0] - 2026-06-30

### Añadido
- **Gate determinista del grafo de documentación — `tools/auditar.ps1`** ([ADR 0016](docs/decisions/0016-gate-grafo-documentacion.md), Fase 3.2): auditor que verifica la integridad de `product/`+`engineering/` sobre el artefacto (los `.md`), no sobre confiar en el agente. **BLOQUEA** frontmatter ausente/incompleto, wikilinks rotos y capacidades `vigente` sin criterios Gherkin; **avisa** capacidad vigente sin test citado y notas huérfanas. **Modulado por estado** (`en_definicion` solo exige frontmatter + enlaces). Lo corre `verificar.ps1` (local, bloquea como el doc-drift §8) y el CI (nuevo job `docs-graph`, infranqueable). **Sin archivos de auto-firma** (`.gate/`): un agente que declara "ya validé" no es verificación. La §8 de `CONTRIBUTING.md` se extiende como fuente única (filas SSOT de `product/`/`engineering/`/`templates/` + blast-radius).
- **UI Paso 4 — aviso temprano si falta ffmpeg** (caso C19): el paso de composición necesita ffmpeg; ahora avisa al entrar (con el comando de instalación) en vez de dejar fallar al apretar «Componer». Con test estructural (`test_step4_ffmpeg.py`).
- **UI Paso 2 — avisos globales de comparación visibles** (caso C12): los avisos del motor (`summary["avisos"]`: autos distintos, delta sospechosamente grande → posible circuito distinto) ahora se muestran como banner en el Paso 2 de la UI. Antes solo aparecían en el CLI/`report.md`, así que un usuario de la UI podía interpretar un reporte inválido como válido. Con test estructural (`test_step2_avisos.py`, capa A del gate de UX, [ADR 0014](docs/decisions/0014-gate-ux-ui.md)).
- **`setup.ps1 -Yes` — modo desatendido** ([ADR 0013](docs/decisions/0013-setup-modo-desatendido.md)): responde "sí" a todas las confirmaciones (sin `Read-Host`) y, tras instalar Python, resuelve su ruta en la misma sesión en vez de relanzar una terminal nueva (inservible en headless/CI). Habilita probar el instalador desatendido en CI y en la VM limpia. Combo recomendado: `setup.ps1 -Yes -SkipSystem`.

### Corregido
- **GPU NVENC se descartaba SIEMPRE → compose iba a CPU aun con GPU NVIDIA usable** (caso C17): el test de capacidad `_nvenc_available()` codificaba un frame de **64×64**, resolución que **NVENC rechaza** ("no capable devices" / "Invalid surface") aunque la GPU sirva — falso negativo que mandaba todo el `compose` a CPU. Ahora el test usa **320×240**. Verificado en el host (Xeon + GPU NVIDIA): `compose` con NVENC **77.8 s vs 119.7 s en CPU (~35 % más rápido)**. Detectado y validado corriendo el flujo real en la PC potente.
- **`fantasma compose` / CLI — `UnicodeEncodeError` en consola de Windows**: el aviso de sincronía incluye `σ` (calidad, "z=5.5 σ") y al imprimirlo en la consola Windows (cp1252) lanzaba `'charmap' codec can't encode character 'σ'`, abortando `compose`. Se añadió `_force_utf8_console()` que reconfigura `stdout`/`stderr` a UTF-8 al arrancar el CLI (silencioso si el stream no lo soporta). Detectado corriendo el flujo completo real en el host. Con test de regresión (`test_force_utf8_console_*`).
- **`setup.ps1 -Yes` — Python no se encontraba tras instalarlo en sesión headless**: el probe de PATH usaba rutas fijas (`Python312`) y el guard se saltaba por el stub de WindowsApps, así que en PowerShell Direct/CI el script instalaba Python pero no lo veía y salía con error. Ahora ignora el stub y **globea `Python3*`** en user y machine para localizar el ejecutable real y anteponerlo al PATH.
- **`setup.ps1` no corría en una instalación limpia de Windows 11** (dos bugs detectados probando el script en una VM virgen `sgi-win11-clean`):
  - El stub de `python.exe` de la Microsoft Store (en `WindowsApps`) engañaba a `Get-Command python`: el script creía que Python ya estaba y reventaba después al llamar `pip`. Ahora se ignora cualquier `python` cuya ruta contenga `WindowsApps`.
  - `winget install` sin `--source winget` abortaba con "multiple sources found" (exit `-1978335138`) cuando la Microsoft Store también expone el paquete. Se añadió `--source winget` a las cinco llamadas (Python, ffmpeg, gh, VLC, Kdenlive).

### Pruebas
- **Smoke de la UI (`test_app_smoke`) — timeout de AppTest subido a 30 s.** El default (3 s) daba falsos rojos por timeout cuando la máquina está cargada (visto en una corrida local). Un gate flaky pierde autoridad ([ADR 0014](docs/decisions/0014-gate-ux-ui.md)); el arranque real tarda < 1 s.

### Documentación
- **Estructura `product/` + `engineering/` (reclasificación a repo mixto, [ADR 0015](docs/decisions/0015-estructura-product-engineering.md)):** se adopta la jerarquía funcional del método (ecosistema→solución→dominio→módulo→capacidad) y la capa de ingeniería (arquitectura, especificaciones, modelos de datos, pruebas). _Fase 0:_ esqueleto + `templates/` (formatos canónicos) + `HANDOFF.md` (relevo de sesión). _Fase 1:_ `engineering/` poblado — `arquitectura.md`, `pruebas.md`, componentes (ffmpeg, Streamlit, MoTeC i2) y especificaciones/modelos de los algoritmos (comparación por distancia, detección de curvas, auto-sync, overlay/NVENC, modelo `Lap`, salidas). Enlazan a sus dueños SSOT (`formato-datos.md`, `hud-reference.md`, ADRs), no duplican. _Fase 2:_ `product/` poblado con contenido real — ecosistema `Fantasma`, 2 soluciones, 8 dominios (1:1 con el código), 12 módulos y 18 capacidades con criterios de aceptación Gherkin derivados de los tests, un proceso (pipeline) y el backlog de diferidos.
- **Casting de asientos formalizado en el repo ([ADR 0015](docs/decisions/0015-estructura-product-engineering.md), Fase 3.1):** `flujo-de-trabajo.md` §4 documenta los seis asientos (**Mau** orquestador, **Ahiram** desarrollador, **Armando** arquitecto-doc, **Charbel**, **Mariana**, **Escribano**), la distinción **asiento≠skill**, el antipatrón "Mau desarrollando" y la **convención 🎭** de anuncio de sustitución de asiento. Nueva skill `.claude/skills/armando/` (arquitecto-doc: jerarquía, wikilinks, ADRs). El §8 de `CONTRIBUTING.md` reconcilia el nombre del rol Architect → **Armando** y deja el **PO** como el humano.
- **README (instalación):** nota de que una instalación limpia de Windows no trae git → descargar el ZIP de GitHub; y se añade el extra `.[test]` (correr la suite con pytest) a la lista de instalación manual.
- **`docs/casos-de-uso.md`** — personas (hobby, liga, coach, creador, sim raro) y matriz de casos de uso evaluados contra lo que existe hoy (✅ cubierto · ⚠️ fricción · ❌ gap), con hallazgos priorizados. Es la lente de evaluación del producto y la UX.
- **`docs/ux-patterns.md`** — estándar de interfaz: 10 heurísticas (Nielsen adaptado al dominio) y el **gate de UX/UI** en tres capas (determinista bloquea · checkpoint Mariana aconseja · local avisa). Análogo a las convenciones de código y al §8 de docs.
- **ADR 0014 — Gate de UX/UI** (Aceptada): lo medible (layout/contraste/estructura) bloquea como los tests; lo subjetivo es checkpoint de Mariana que vuelve al PO. Extiende la línea del ADR 0012.

## [0.12.0] - 2026-06-28

### Corregido
- **`fantasma overlay` CLI — video .webm de 0 bytes (bug bloqueante)**: el callback de progreso del CLI estaba definido como `def progress(n, total):` sin el kwarg `status`, pero `overlay.py` lo invocaba con `progress(enc, n_frames, status="...")`. Eso lanzaba `TypeError`, capturado por el `except BaseException:` de overlay, que mataba ffmpeg y re-lanzaba: resultado webm vacío y exit 1. La UI no lo sufría porque su callback (`_helpers.py`) ya definía `def _cb(n, total, status=None):`. Corregido extrayendo `_overlay_progress(n, total, status=None)` a nivel de módulo en `cli.py` y usándolo en `cmd_overlay`.

### Añadido
- **Auto-sync — aviso de "zona gris" (correlación moderada)**: si el offset aceptado cae en `3σ ≤ z < 6.5σ`, se acepta pero se avisa ("correlación moderada: el video podría no corresponder a esta vuelta; verifica el inicio del HUD"). Cierra el hallazgo #3 del QA: un video de la misma pista y mismo auto pero de otra sesión/fecha (z=5.45) pasaba el mínimo de 3σ y, al ser un único candidato fuerte (el ratio de ambigüedad no dispara), se aceptaba en silencio y dejaba el HUD ~4 s corrido. No bloquea: solo avisa, en el CLI (`compose --auto-sync`, stderr) y en la UI (Paso 4). Un match robusto (z ≥ 6.5σ) no avisa. Función de decisión pura `sync_gray_zone_warning(z)` en `viz/sync.py`.
- **`compare` — aviso de delta sospechosamente grande**: si `abs(total_delta) > ref_laptime * 0.5`, `compare()` emite un aviso claro en `summary["avisos"]` ("delta sospechosamente grande — ¿mismos circuitos?"). Previene que una comparación ref+piloto de circuitos distintos produzca un reporte numéricamente plausible pero silenciosamente incorrecto (-280 s sobre una vuelta de ~378 s). El cálculo no se bloquea; solo avisa.
- **`compare` — aviso informativo de autos distintos**: si el metadato `Vehicle` está disponible en ambas vueltas y difiere, `compare()` emite un aviso informativo ("autos distintos: X (ref) vs Y (piloto)"). Si el metadato falta en alguna vuelta, la degradación es silenciosa (no avisa, no crashea). Los avisos se imprimen en stderr con `fantasma compare` y aparecen en el `report.md` generado.
- **Rol Mariana auto-cableado** (`mariana-stop`): al tocar `fantasma/viz/` o `fantasma/ui/`, el hook de sesión frena el cierre y manda hacer el QA visual (checkpoint que vuelve al PO). `escribano-stop` se extiende para vigilar `fantasma/ui/` → `docs/guia-usuario.md`. Charbel se mantiene declarado en la §8 sin hook (su asiento son los tests). Ver ADR 0011.

### Corregido
- **UI Paso 0:** los botones «Elegir este / Seleccionado» de las tarjetas de flujo quedaban desalineados entre columnas (cada uno al final de su contenido). Ahora se anclan a una línea base común.

### Pruebas
- **Smoke visual del Paso 0 con Playwright** (`tests/ui/visual/test_step0_visual.py`): captura un screenshot del Paso 0 de la UI Streamlit via Chromium headless y lo compara contra un baseline con tolerancia generosa (15 % de pixels pueden diferir > 12 %). Detecta regresiones de layout («el layout se movió», como el bug de botones desalineados del ADR 0011) sin fallar por antialiasing entre máquinas. Skipea limpiamente si playwright o Chromium no están instalados. Baseline provisional en `tests/ui/visual/baselines/step0.png`; la verdad canónica es el job `visual-smoke` del CI (ubuntu-latest, entorno consistente — ADR 0012). Nuevo job `visual-smoke` en `.github/workflows/tests.yml`; el job `pytest` excluye `tests/ui/visual/` para separar responsabilidades.
- **Test sistemático de degradación por canales ausentes** (`tests/core/test_degradacion_canales.py`): parametrizado sobre las 32 combinaciones de {glat, glong, gear, abs, tcs} presentes o ausentes; verifica que `compare()` no crashea, calcula laptimes y traza, y que cada campo derivado de un canal aparece si y solo si el canal está. Cierra el gap «Media» del ROADMAP. Suite total: 106 tests en verde.

### Documentación
- **Enmienda al ADR 0008 (2026-06-28) — zona gris de confianza en auto-sync.** Registra por qué `_MIN_SYNC_Z` (3σ) no basta (no distingue "video correcto" de "otra sesión en la misma pista"), por qué el ratio de ambigüedad tampoco (un único candidato fuerte), el umbral elegido `_STRONG_SYNC_Z = 6.5` con su justificación (separa el caso bueno 9.81 del malo 5.45 con margen) y los caminos descartados (subir el mínimo a 6σ → falsos rechazos; solo el ratio → no atrapa el caso; no hacer nada → el dolor actual). Actualiza `guia-usuario.md` y el gap del ROADMAP.
- **ADR 0012 — Playwright para smoke visual acotado de la UI Streamlit en v1.0** (Aceptada). Enmienda la restricción de testing del ADR 0010: con la migración del front a meses de distancia, un snapshot visual en CI (extra `[dev]`, dueño Mariana) paga su costo y atrapa los bugs de layout que AppTest no ve. La regla "no Playwright sobre Streamlit" del 0010 queda acotada a la lógica de flujo, no al smoke visual.
- **ADR 0011 — Cablear el rol Mariana (UX visual); Charbel se queda en los tests** (Aceptada). Registra por qué Mariana se cabla ahora (el bug visual fue el "cambio real que lo pide") y por qué Charbel no (redundante con los tests; cablearlo sería sobre-orquestar).
- **`flujo-de-trabajo.md` (orquestación):** regla dura nueva — la lectura voluminosa (transcripts, logs, dumps de búsqueda, archivos gordos) **siempre** se delega a un subagente que devuelve solo el hallazgo; el recurso escaso del orquestador es su propio contexto (Context Rot), aunque solo se quede con la conclusión. Añadida la lección del segundo caso real.
- Pulido de descubribilidad: `README.md` agrega puntero explícito a `docs/flujo-de-trabajo.md` como guía del sistema de trabajo (barreras, doc-gate, matriz de roles §8 y capa asistida por IA en `.claude/`).

## [0.11.0] — 2026-06-27

### Añadido
- **Sistema de roles sobre el flujo de trabajo** — validadores que disparan solos (sobre el plan de Claude Code, sin API), enrutados por la matriz §8:
  - **Doc-gate bloqueante** en `tools/verificar.ps1`: el doc-drift de la §8 (`core/` sin `formato-datos.md`, `viz/` sin `hud-reference.md`, barreras sin `flujo-de-trabajo.md`) ahora **bloquea el push** (exit 1), no solo avisa. lint/formato/tests siguen avisando.
  - **Hooks de sesión** (`.claude/hooks/` + `.claude/settings.json`): `escribano-stop` sincroniza los docs dueños al detectar doc-drift; `review-stop` dispara `/code-review` cuando hay código sin revisar.
  - **Skill `escribano`** (`.claude/skills/escribano/`): el rol que actualiza los docs dueños según la §8.
  - **Matriz §8 extendida** en `CONTRIBUTING.md` con la columna de roles (Charbel telemetría, Mariana UX, Reviewer, Escribano, PO, Architect).
  - `.claude/` ahora **viaja con el repo** (salvo `settings.local.json` y el marcador de review).
  - **Orquestación y model-routing** en `flujo-de-trabajo.md`: cuándo el orquestador delega a un subagente vs lo hace en sesión, cómo elegir el modelo (haiku/sonnet/opus) según la complejidad, y el **playbook** de operación (el PO habla; el orquestador detona los subagentes).
  - **Mariana** valida también `fantasma/ui/` (UI Streamlit), no solo `viz/` (HUD), en la §8.
- `docs/flujo-de-trabajo.md` documenta esta capa y se corrigió donde describía el doc-gate como solo-aviso.

## [0.10.0] — 2026-06-26

### Añadido
- **Linter/formatter `ruff`** como barrera determinista pre-push (benchmark en `docs/benchmark-linter.md`): config en `pyproject.toml` (reglas `F`+`I`, alta señal y bajo ruido), extra `[dev]`, y job `lint` en CI (`ruff check`). Atrapa imports/variables sin usar y nombres indefinidos antes de subir.
- **`tools/verificar.ps1`** — pipeline local de barreras en **modo aviso** (lint + formato + tests + doc-gate de CHANGELOG), inspirado en el patrón "no-mistakes". No bloquea; el CI sigue siendo la compuerta que sí bloquea.
- **Hook `pre-push`** (`.githooks/pre-push`) en modo aviso: dispara `tools/verificar.ps1` automáticamente antes de cada push. Se enciende una vez por clon con `git config core.hooksPath .githooks`.
- **`docs/flujo-de-trabajo.md`** — guía completa (desde cero) del sistema de barreras y del flujo explorar→commit→push: glosario, las piezas, paso a paso, dónde acaba la máquina (límite semántico), local vs nube, mapa del repo. Registrada como SSOT en `CONTRIBUTING.md` §8.
- **CONTRIBUTING §3 y §6**: especifican la **puesta a punto del clon** (instalar `[dev]` + `git config core.hooksPath .githooks`) y que **el CI debe quedar en verde para mergear** — para que saltarse las barreras solo sea posible **a propósito**, nunca por desconocimiento. La **branch protection** (que vuelve el CI bloqueante para colaboradores) queda apuntada en el ROADMAP.

### Cambiado
- Imports ordenados (`ruff I`) y un import sin usar eliminado en `fantasma/ui/step4.py` — fixes seguros de ruff aplicados al adoptar; **74 tests verdes** (comportamiento preservado).
- **Baseline de formato `ruff format`** aplicado a todo el repo (34 archivos; cambio mecánico y AST-equivalente, 74 tests verdes). El CI ahora gatea también `ruff format --check`.

### Documentación
- **ADR 0010 — Framework de UI: Streamlit en v1.0; front de escritorio custom diferido a v2.0** (Aceptada). Registra la decisión de facto nunca asentada: por qué Streamlit (reusa `core/`, sin front web que construir), qué se descartó (HTML desde cero ahora), y el gatillo para revisitar en v2.0 (limitantes de personalización + instalación doble-click). Fija las restricciones que mantienen barata la migración (mantener `core/` desacoplado; tests a prueba de migración).
- **ROADMAP §v2.0**: bloque de evaluación de migración del front + tarea de benchmark de herramientas (actuales y nuevas).
- **ROADMAP reorganizado y depurado** (de 357 a ~65 líneas): se quita ruido estructural (doble numeración de hitos divergente, checklists de QA de versiones ya publicadas, specs largas de features diferidas) conservando los requisitos de la v1.0 verificados y las notas vivas con puntero a su ADR.

---

## [0.9.0] — 2026-06-22

### Añadido
- **Desgaste acumulado de la vuelta en el HUD (campo `GASTO`)**: nuevo readout en el overlay que muestra la *carga de deslizamiento* acumulada de la vuelta (piloto vs `ref`), distinta del DESLIZ instantáneo. Función pura `core.wear.slip_load` (slip integrado sobre la distancia: cantidad extensiva y aditiva). Implementa los ADR 0004 (enmienda) y 0009.
- **Glosario** (`docs/glosario.md`): definición canónica de los términos del proyecto (métricas de desgaste, hitos de curva, términos de overlay y telemetría). Enlazado desde el README y registrado como SSOT de vocabulario en `CONTRIBUTING.md` §8. Aclara explícitamente que **DESLIZ** (intensidad instantánea) y el **desgaste acumulado** (cantidad) no son lo mismo.
- **Matriz de mantenimiento de docs** (`CONTRIBUTING.md` §8): qué documento es dueño de qué (SSOT) y qué docs tocar en cada tipo de cambio (blast radius), más la regla de consistencia de vocabulario.
- **Regla operativa de pruebas** (CONTRIBUTING §3 + ADR 0003): cuándo correr `pytest`, que el test es parte del cambio, y qué hacer si el escenario falta o un test falla.

### Cambiado
- **`fantasma wear` ahora acumula la carga de deslizamiento** (`slip_load`) en vez del promedio `slip_index`, para ser consistente con el acumulado del overlay (ADR 0009). Los umbrales `--yellow/--red/--burst` ya no traen valor por defecto: la carga escala con la longitud del circuito y se calibran con datos reales.

### Documentación
- **ADRs 0004 y 0005 enmendados** (desgaste acumulado en dos vistas: overlay = vuelta, gráficas = stint) y **ADR 0009 nuevo** (unidad: carga de deslizamiento, no el promedio).
- Sincronización doc↔código tras pasada de verificación (`formato-datos.md`, `hud-reference.md`): hito fantasma `exit` eliminado, columnas reales de los CSV, vocabulario de color del HUD.

---

## [0.8.0] — 2026-06-21

### Añadido
- **Auto-sync para video de varias vueltas — candidatos + selección del usuario** (ADR 0008): el `auto_sync` antes buscaba el offset solo en ±300 s y, con un video de carrera completa, pegaba el HUD sobre la vuelta equivocada **en silencio**. Ahora `sync.sync_candidates()` busca en **todo** el video, detecta un candidato por vuelta (rankeados por calidad) y marca si son ambiguos. En CLI `compose --auto-sync`, si es ambiguo, lista los candidatos (minuto del video + calidad) y pide elegir. En la **UI (Paso 4)** el selector es **bloqueante**: con varias vueltas, no se puede componer hasta elegir cuál es la tuya. `auto_sync` se mantiene (compat) como "toma el mejor candidato". Lógica de ranking/ambigüedad cubierta con 6 tests puros.

### Known issues
- El auto-sync multi-vuelta (ADR 0008) tiene la lógica de ranking testeada, pero el camino completo (audio real + CLI interactivo + gate de UI) está **pendiente de QA con video de carrera real**.

---

## [0.7.2] — 2026-06-21

### Añadido
- **`setup.ps1` instala Python solo si falta**: si no hay `python`, ofrece instalarlo vía winget. Como el PATH recién instalado no aplica a la terminal en curso, el script **abre una terminal nueva** (que sí hereda el PATH actualizado) y re-corre el setup, cerrando la anterior. Guarda anti-bucle (`-Relaunched`) para no reabrir indefinidamente; si tras reabrir sigue sin aparecer, pide reiniciar la PC.

### Corregido
- **`setup.ps1` — caracteres no-ASCII rompían el script en instalación limpia**: el archivo tenía `—` (em dash) y acentos; PowerShell 5.1 lee un `.ps1` sin BOM con la codepage del sistema (Windows-1252), corrompía esos caracteres y el parser fallaba con "falta cadena en el terminador". Convertido a **ASCII puro** para ser inmune al encoding en cualquier PC. Validado con el parser de PowerShell.

---

## [0.7.1] — 2026-06-21

### Corregido
- **`setup.ps1` — la detección de dependencias mentía en una instalación limpia**: las comprobaciones `python -c "import X"` estaban dentro de un `try/catch`, pero un ejecutable nativo que sale con código ≠ 0 **no lanza una excepción** que `catch` capture en PowerShell (reporta por `$LASTEXITCODE`). Resultado: en una máquina **sin** la dependencia, el script imprimía "ya instalado" y **no la instalaba** — fallaba justo en el caso que importa. Cambiado a comprobar `$LASTEXITCODE -eq 0` en openpyxl, Pillow y matplotlib. Validado en un venv limpio (`.[full]` instala todo desde cero, imports y CLI OK).

---

## [0.7.0] — 2026-06-21

### Añadido
- **`fantasma wear` — medidor de desgaste de goma acumulable** (implementa el ADR 0004): nuevo comando CLI y función pura `wear_budget` en `core/wear.py`. Acumula el `slip_index` de las vueltas de un stint, da estado (`ok`/`yellow`/`red`/`burst`) y estima cuántas vueltas faltan para el reventón, estilo medidor de gasolina. Umbrales configurables (`--yellow`/`--red`/`--burst`, default 30/40/50 — a calibrar con datos reales). El número es un proxy en unidades arbitrarias, no % físico.
- **ADR — registro de decisiones numerado** (`docs/decisions/`): se impone la estructura `NNNN-titulo.md` con plantilla (`0000-plantilla.md`) e índice (`README.md`). Se migran los decision-docs planos previos a `0001-sync-offset`, `0002-crewchief-pacenotes`, `0003-testing` (con sus referencias actualizadas en ROADMAP/CHANGELOG/CONTRIBUTING). Nuevo **ADR 0004 — desgaste de llanta acumulable** (medidor tipo gasolina): reusar `slip_index` como rate por vuelta, acumularlo en el stint, umbrales configurables y vueltas estimadas a cambio (**Aceptada**). Nuevo **ADR 0005 — indicadores de estado del HUD se leen en el cursor, no por ventana** (**Aceptada**): guardarraíl para las luces ABS/TC y DESLIZ. Nuevo **ADR 0006 — jerarquía visual del HUD** (**Aceptada**): grosor uniforme, piloto siempre encima de la referencia, y colores piloto/referencia distinguibles (la regla de color queda como deuda, dirección "opción B"). Nuevo **ADR 0007 — el HUD no lleva leyenda de colores** (**Aceptada**): se documentan en `hud-reference.md` (con imagen anotada pendiente), no en pantalla.

### Corregido
- **Overlay — indicadores ABS/TC ahora son luces instantáneas, no conteo por ventana**: el texto "ABS"/"TC" de la franja mostraba un conteo de activaciones acumulado sobre los ~520 m visibles, así que no "prendía y apagaba" con la activación real. Ahora cada luz lee el flag del piloto **en el cursor** (`_flag_recent_grid` en `viz/overlay.py`) y se enciende en su color (ABS ámbar, TC violeta) cuando está activo, con retención corta (`HOLD_M = 8 m`) para no parpadear a 30/60 fps. Se añade además la luz **TC** que antes no existía como texto.
- **Overlay — espaciado de la franja de datos**: se separa la etiqueta «MARCHA» del número de marcha (estaban pegados) y se acerca «km/h» a «m» (sobraba aire entre ambos).
- **Overlay — DESLIZ ahora es deslizamiento reciente, no promedio de pantalla** (ADR 0005): antes promediaba el slip de toda la ventana visible (520 m, incluyendo 200 m **por delante** del cursor); ahora promedia solo una ventana corta detrás del cursor (`SLIP_WIN_M = 40 m`).
- **Overlay — ABS/TC de la referencia más visibles + luz apagada en gris**: se subió el brillo de las líneas de asistencia de la referencia (`_RABS`, `_RTCS`), que casi no se veían, y el estado *apagado* de las luces ABS/TC pasó a gris (`_DIM`) para que el on/off contraste sin depender de esos colores.
- **Overlay — se quitan los rótulos `freno+ABS` y `gas+TCS` de la franja** (ADR 0007): eran una leyenda parcial (2 de ~10 colores) que implicaba completitud falsa y ocupaba espacio; la leyenda de colores vive en `hud-reference.md`.
- **Overlay — escala del panel de volante con más divisiones**: pasa de mostrar solo -20/0/20 a `-30/-20/-10/0/10/20/30`, igualando la densidad de escala de los paneles de gas y freno (0..100 en pasos de 20).

---

## [0.6.6] — 2026-06-17

### Añadido
- **Suite de pruebas automatizadas — pytest**: arranca la suite definida en `docs/decisions/0003-testing.md`. Nuevo extra `pip install -e ".[test]"` y config en `pyproject.toml`. **48 tests** verdes. Cubre: **Tier 1** `core/` puro (normalización, comparación con los signos confirmados del producto —piloto más lento = delta positivo, ápex más rápido = `d_vmin` positivo—, detección de curvas y desgaste, incluyendo degradación graceful sin `gear`/`glat`), **Tier 2** importadores MoTeC CSV y CSV genérico con fixtures sintéticos diminutos (auto-detección de columnas, mapeo manual, separador `;`, coma decimal), **Tier 3** helpers puros de `compose` (regresión del filtro ffmpeg y del falso positivo de NVENC) y de `sync` (señal de telemetría, detección de pausa por silencio, lectura de WAV) —todo sin invocar ffmpeg— y **Tier 4** smoke de la UI (`AppTest`: `app.py` arranca sin excepción —blinda el `ImportError` del refactor 0.6.3). Fixtures sintéticas deterministas vía `make_lap` (sin telemetría real). Documentada también la directiva «qué se automatiza vs qué se prueba a mano».
- **CI — GitHub Actions** (`.github/workflows/tests.yml`): corre `pytest` en cada push y PR a `master`, sobre **Windows** (plataforma objetivo) con Python 3.10, 3.11 y 3.12. Instala con extras `[test,ui,sync]` para ejercitar todas las capas; ffmpeg no es necesario porque ningún test lo invoca.

### Corregido
- **Importadores — soporte de separador `;` y coma decimal europea**: `motec_csv` y `generic_csv` detectan automáticamente el separador (coma por defecto, `;` si predomina en la primera línea) y parsean valores con coma decimal (`100,5` → `100.5`). Cubre los exports europeos de MoTeC i2 que antes fallaban con `NotMotecFormat`. Cierra el gap del ROADMAP. Lógica compartida en `importers/_util.py` (`detect_delimiter`, `pfloat`); no afecta a los CSV con coma estándar.

---

## [0.6.5] — 2026-06-16

### Añadido
- **UI Paso 4 (Componer) — autónomo, sin depender de los Pasos 1 ni 3**: el Paso 4 ya no requiere haber generado un overlay en la sesión ni haber importado telemetría. Solo necesita video + overlay; puede apuntar a un `overlay.webm` existente con «Explorar…». La telemetría sigue siendo útil pero opcional: habilita el sync automático por audio y el recorte exacto a la vuelta. El CSV que se sube en la sección de sincronía del propio Paso 4 ahora alimenta **ambos** (sync y recorte), no solo el sync — antes el recorte solo funcionaba con telemetría del Paso 1. Sin telemetría, se compone con offset manual y duración completa (modo legado de `compose_video`, ya soportado). Si el usuario llega desde el flujo de importar, el Paso 4 reutiliza la vuelta del Paso 1 sin volver a pedir el archivo.

### Mejorado
- **UI Paso 4 — copy explícito sobre qué telemetría subir**: la sección de sincronía dejaba dudas sobre si el CSV a subir era el del piloto o el de referencia. Ahora un aviso destacado, el label del uploader y el tooltip aclaran que debe ser **tu vuelta — la misma del video, no la de referencia** (el sync compara el audio de tu motor con tus RPM).

### Corregido
- **`ui/app.py` — `ImportError: attempted relative import with no known parent package` al lanzar `fantasma ui`**: el refactor 0.6.3 partió la UI en módulos (`step0`–`step4`, `_helpers`) pero `app.py` conservó imports relativos (`from ._helpers import …`, `from . import step0…`). Streamlit ejecuta `app.py` como script suelto (`__main__`), sin paquete padre, por lo que los imports relativos fallaban antes de renderizar nada. Cambiados a imports absolutos (`from fantasma.ui._helpers import …`, `from fantasma.ui import step0…`); los submódulos siguen resolviendo sus propios imports relativos dentro del paquete instalado. La UI no se había probado tras el split.
- **UI Paso 2 — el nombre de archivo mostraba el temporal (`tmp3sj8t8k1.csv`) en vez del real**: el upload se guarda en un `NamedTemporaryFile` y la cabecera de referencia/piloto mostraba el basename del temporal. Ahora `_cache_file` cachea también el nombre original del upload (`uploaded_file.name`), el Paso 1 lo guarda en `session_state` (`ref_name`/`drv_name`) y el Paso 2 lo muestra (con fallback al basename del path).
- **UI — el sidebar no se desbloqueaba al cancelar (o terminar) un render**: la barra de navegación se bloquea mientras corre un render (overlay/compose). Al cancelar, el flag `_render_active` se limpiaba *dentro* del paso (`_render_widget`), que corre **después** del sidebar en el mismo run, dejando los botones bloqueados hasta la siguiente interacción. Ahora el sidebar se bloquea según si el hilo sigue corriendo (`_render_busy = activo y no done`), liberándose en el mismo run en que el hilo marca `done`. Afecta a los Pasos 3 y 4 (lógica compartida en `app.py`).
- **`compose` — NVENC falso positivo en equipos sin GPU NVIDIA usable**: `_nvenc_available()` solo hacía `grep` de `-encoders`, que lista `h264_nvenc` aunque no funcione en runtime (`Cannot load nvcuda.dll`). El compose intentaba GPU, fallaba con exit -1 y no caía al fallback de CPU. Ahora hace un probe real (encode de 1 frame contra un source sintético) y solo usa NVENC si termina en 0; si no, usa `libx264`. Además, el path con progreso (UI) capturaba el `stderr` de ffmpeg en `DEVNULL`, dejando solo un código de salida críptico; ahora reporta las últimas líneas del error real.

---

## [0.6.4] — 2026-06-15

### Añadido
- **`CONTRIBUTING.md` — guía de contribución completa**: cómo reportar bugs (qué incluir, qué no subir), cómo proponer features (abrir issue primero), entorno de desarrollo paso a paso, principios de diseño del proyecto, convenciones de commits (Conventional Commits), proceso de PR y tabla de contribuciones bienvenidas vs fuera de scope.

---

## [0.6.3] — 2026-06-15

### Cambiado
- **`importers/motec_csv.py` — `MOTEC_MAP` movido desde `core/lap.py`**: el diccionario de traducción de nombres de canal MoTeC pertenece al importer que lo usa, no al modelo de datos central. `core/lap.py` queda como modelo puro sin conocimiento de proveedores externos.
- **`importers/__init__.py` — nueva función `load_laps(path, column_map)`**: combina `load()` + `split_laps()` en un único punto de entrada compartido. Elimina la duplicación entre CLI y UI que cada uno repetía este patrón por separado.
- **`cli.py` — `_load_lap` simplificado**: usa `importers.load_laps()`, devuelve `(laps, lap)` en lugar de `(outing, laps, lap)`. El `outing` no era necesario porque cada vuelta hereda los metadatos del outing vía `slice_time`.
- **`ui/app.py` — partido en módulos por paso** (de 1 237 líneas a ~100): la UI monolítica se dividió en `_helpers.py` (helpers y constantes compartidas) + `step0.py`–`step4.py` (un archivo por paso con su función `render()`). `app.py` queda como router puro: inicializa estado, renderiza el sidebar y delega en el paso activo.

---

## [0.6.2] — 2026-06-15

### Cambiado
- **Dependencias — cotas superiores en todos los extras**: se añaden límites de versión mayor (`<N`) a todas las dependencias opcionales (`openpyxl<4`, `Pillow<12`, `matplotlib<4`, `numpy<3`, `streamlit<2`, `pandas<3`, `scipy<2`). Evita que una versión mayor con breaking changes se instale automáticamente en instalaciones nuevas. Los entornos existentes no se ven afectados.

---

## [0.6.1] — 2026-06-14

### Corregido
- **UI Paso 3 — nombres de curvas no aparecían en el overlay con el flujo «Solo overlay»**: el flujo sin Paso 2 saltaba la auto-detección de corners que solo existía en el bloque de comparación. Paso 3 ahora auto-detecta corners desde la vuelta de referencia si no hay corners explícitos cargados (JSON o botón «Detectar curvas»). Diagnóstico confirmado: el rendering HUD sí funcionaba; el problema era que `corners_by_seg = []` porque `corners or []` era lista vacía.
- **UI Paso 3/4 — `StreamlitAPIException` al usar «Explorar…»**: Streamlit prohíbe modificar `session_state[widget_key]` después de que el widget fue instanciado en el mismo run. Corregido con patrón pending key: el picker guarda el valor en `_*_pending`, llama `st.rerun()`, y en el siguiente run el valor se aplica al widget key vía `pop()` antes de que `text_input()` se instancie. Afecta los 4 pickers (Paso 3: carpeta overlay; Paso 4: video, overlay, carpeta salida).
- **UI Paso 3/4 — pickers de archivo/carpeta no actualizaban el campo de texto**: tras seleccionar una ruta con «Explorar…», el campo `text_input` seguía mostrando el valor anterior. Causa: Streamlit ignora `value=` en rerenders posteriores al primero; el control del widget es exclusivo de `session_state[key]`. Corregido actualizando la clave del widget en session_state al seleccionar.
- **UI Paso 1/2 — corners de sesiones anteriores aparecían sin cargar JSON**: `session_state["corners"]` persiste entre vueltas si el usuario no usa «Procesar otra vuelta». Corregido con flag `corners_editable`: solo se usan corners de session_state si el usuario los generó o cargó explícitamente en la sesión actual. «Procesar otra vuelta» limpia ambos.
- **Overlay — botón Detener no cancelaba el render de frames**: `_render_parallel` usaba `p.wait()` bloqueante; el cancel event no se chequeaba hasta que el worker terminaba por sí solo (potencialmente minutos). Corregido con polling `p.poll()` + `time.sleep(0.5)` que llama `progress()` en cada tick. Si `progress()` lanza `RuntimeError("__CANCELLED__")`, `_kill_all()` mata todos los subprocesos activos. El cancel ahora actúa en ~0.5 s.

---

## [0.6.0] — 2026-06-14

### Añadido
- **UI — pasada exhaustiva de UX/copy**: cada campo, widget y sección tiene una explicación breve en lenguaje llano. Se añaden dos callouts prominentes al tope del Paso 4 («el video debe tener audio del motor» + «el output es un clip, no el video completo»). Las tarjetas de flujo del Paso 0 incluyen «Necesitas:» con los requisitos de cada flujo. Los selectores de formato/fps tienen ayuda contextual ampliada. El auto-sync pasa de expander colapsado a sección abierta y destacada como ruta recomendada. Se añade un bloque «Resumen de lo que se va a generar» antes del botón Componer.
- **`auto_sync` — detección de pausas de juego**: tras detectar el offset, verifica que no haya silencio prolongado (>3 s, energía <5% de la media) en la ventana de audio correspondiente a la vuelta. Si lo hay, lanza `RuntimeError` con el timestamp exacto de la pausa. Un video pausado durante la grabación desincroniza la telemetría y produce clips erróneos.
- **UI Paso 4 — badge de calidad de sync**: tras «Detectar offset» muestra label descriptivo («Excelente / Muy bueno / Bueno / Marginal»). Tras «Componer video» repite el badge si el compose provino de auto-sync.
- **UI Paso 4 — botón «Procesar otra vuelta»**: aparece tras un compose exitoso. Limpia el estado del piloto (vuelta, overlay, sync, gráficas) sin tocar la referencia ni el video cargado; regresa al Paso 1 con el video pre-cargado para el siguiente ciclo.
- **UI — render con cancelación y threading**: overlay (Paso 3) y compose (Paso 4) corren en hilo de fondo con barra de progreso en tiempo real. Aparece un botón **Detener** durante el render; al pulsarlo se cancela el proceso ffmpeg limpiamente. La barra de navegación del sidebar se bloquea durante el render; si el usuario cambia de paso, el render se cancela automáticamente con un aviso.
- **UI — selectores de archivo y carpeta nativos (tkinter)**: botones «Explorar…» junto a los campos de ruta en Paso 3 (carpeta de salida) y Paso 4 (video, overlay, carpeta de salida). Abre el explorador del SO sin copiar archivos — solo toma la ruta seleccionada.
- **UI Paso 3 — FPS fuera del expander**: el selector de FPS pasa a ser un radio button (24 / 30 / 60, default 30) en la página principal. El formato de salida solo aparece en el flujo «Solo overlay»; en «Video con HUD» siempre se usa `webm`.
- **UI Paso 4 — auto-sync como flujo principal**: el bloque de sincronía automática aparece directamente en la página (sin expander). La opción de offset manual pasa a un expander colapsado «Sincronizar manualmente (avanzado)» con instrucciones de cuándo y cómo usarlo.
- **UI Paso 4 — carpeta de salida del compose**: campo de carpeta con botón «Explorar…». Por defecto toma la carpeta del overlay recién generado. Nombre de archivo auto-generado (`<nombre_video>_composed.mp4`).

### Mejorado
- **`auto_sync` — retorna `(offset, z_score)`**: ahora devuelve una tupla en lugar de solo el offset. El z-score permite al caller evaluar la confianza de la sincronización. CLI imprime `offset + z`; UI muestra badge de calidad.

### Corregido
- **`compose_video` — barra de progreso mostraba «frame 0 / 39404999 (0%)»**: `_total_frames()` consultaba `nb_frames` del contenedor, que muchos encoders rellenan con un valor incorrecto. La función ahora siempre usa `fps × duración` vía ffprobe e ignora `nb_frames`.
- **`_run_ffmpeg` (overlay) y loop de progreso (compose) — proceso ffmpeg no se mataba al cancelar**: el bloque `finally` hacía `proc.wait()` en lugar de `proc.kill()`. Corregido con `except BaseException: proc.kill(); proc.wait(); raise`.

### Cambiado
- **UI Paso 1 — selección de vuelta**: checkboxes múltiples reemplazados por radio buttons. Una sola vuelta por diseño.
- **UI Paso 3 — overlay**: eliminado el checkbox «Generar para TODAS las vueltas». El overlay siempre se genera para la vuelta del Paso 1.
- **`fantasma compose` — output recortado a la vuelta**: cuando se provee telemetría, el output es un clip de exactamente la duración de la vuelta (seek rápido `-ss` + `-t laptime`).
- **UI Paso 4 — thresholds del badge de calidad de sync**: umbral «Excelente» bajado de z>10 a z>8 (z=9.7σ ahora muestra «Excelente»). Nuevos umbrales: Excelente z>8 · Muy bueno z>5 · Bueno z>3 · Marginal ≤3. El valor z numérico se omite del badge principal para no confundir con porcentajes.

---

## [0.5.0] — 2026-06-14

### Añadido
- **`fantasma compose` — NVENC automático**: si el sistema tiene una GPU NVIDIA con `h264_nvenc` disponible, el compose usa GPU encoding en lugar de `libx264` CPU. En una RTX 2060, un video de 70 min pasa de horas a ~19 min (3.7× tiempo real). Fallback automático a `libx264` si no hay NVENC.

### Mejorado
- **`fantasma compose` — progreso en tiempo real en UI**: la barra de progreso del Paso 4 ya no queda en blanco mientras ffmpeg compone. `compose_video()` acepta un callback `progress(n, total)` que lee `frame=N` de `-progress pipe:1`; la UI muestra «Componiendo… frame N / total (X%)». El CLI sin callback sigue usando `subprocess.run` sin cambios.
- **`auto_sync` — validación de confianza**: si el pico de correlación audio/telemetría no supera 3σ sobre el ruido, lanza `RuntimeError` con mensaje claro. Antes devolvía un offset inventado sin aviso cuando el video no correspondía a la vuelta.
- **`auto_sync` — check de duración mínima**: si el audio del video tiene menos de 30 s, lanza `RuntimeError` claro antes de intentar la correlación. Con muy pocas muestras el z-score era artificialmente alto (varianza ≈ 0 en `corr_w`) y se colaba un offset basura sin aviso — reproducible con cualquier video de <30 s independientemente de si correspondía o no a la vuelta.
- **`fantasma overlay` — progreso de codificación ffmpeg en tiempo real**: la barra de progreso de la UI ya no se congela al 99% mientras ffmpeg codifica. `_run_ffmpeg()` lanza ffmpeg con `-progress pipe:1`, lee `frame=N` de stdout y llama el callback de progreso con el texto «Codificando video… frame N / total». Compatible con cualquier formato (webm/mov).
- **`fantasma overlay` — VP9 multithreading**: añadidos `-row-mt 1 -threads N` al comando VP9 de `libvpx-vp9`, donde N = `os.cpu_count()`. Aprovecha todos los cores disponibles durante la codificación. (VP9+alpha `yuva420p` no tiene encoder GPU disponible en ningún vendor, por lo que el multithreading CPU es el máximo rendimiento posible para este codec.)

### Corregido
- **`fantasma overlay` — marcha/glat/abs/tcs ausentes se detectan correctamente**: `_interp_lap` devolvía zeros para canales opcionales no presentes en el CSV; `drv_ch.get("gear")` nunca era `None` y la marcha aparecía siempre como «N». Ahora los canales opcionales ausentes son `None`: `_masked`, `_masked_g` y el renderizador de gear/speed los omiten limpiamente sin crashear.
- **`fantasma overlay` — render paralelo no funcionaba en UI**: el `ProcessPoolExecutor(mp_context="spawn")` fallaba silenciosamente bajo Streamlit — el proceso hijo intentaba reimportar `__main__` del servidor de Streamlit y crasheaba en cascada, forzando el fallback a render serial (1 core). Reemplazado por `subprocess.Popen([python, -m, fantasma.viz._overlay_worker])` con un worker script independiente que tiene su propio `__main__`, arranca limpio y no hereda estado del servidor. El fix es multiplataforma sin código condicional por OS: `subprocess` siempre crea un proceso fresco, lo que también elimina el riesgo de deadlock de `fork + matplotlib` en Linux/Mac.
- **Charts en UI (Paso 2) — gráficas no se mostraban**: la generación de gráficas se disparaba en cada rerun de Streamlit (cualquier interacción con un widget lo provoca) y los errores dentro de `st.spinner()` desaparecen cuando el spinner cierra. Solución: las rutas de los charts se cachean en `session_state["charts_paths"]`; se regeneran solo cuando corre una comparación nueva. Los mensajes de error y de importación se muestran fuera del spinner para que persistan.
- **`__version__` desactualizado**: `fantasma/__init__.py` reportaba `0.2.0`; corregido a `0.4.0`.

### Cambiado
- **`fantasma overlay` — formato por defecto cambiado a `webm`**: el default era `prores` (contradecía la documentación y producía archivos de 4+ GB que colgaban ffmpeg en sessions largas). Ahora el default es `webm` (VP9 con canal alfa), coherente con la guía de usuario. Para calidad máxima en editores de video usar `--format prores` explícito.
- **`__version__` — fuente única de verdad**: `fantasma/__init__.py` ya no tiene la versión hardcodeada. La lee en runtime de `pyproject.toml` via `importlib.metadata.version("fantasma-inputs")`. Elimina el riesgo de que `pyproject.toml` y `__init__.py` queden desincronizados en cada release.

### Eliminado
- **UI Paso 2 — controles redundantes**: eliminados el slider de resolución de metros, el selector de número de curvas y el botón «Recalcular». El análisis corre siempre a máxima resolución (1 m) al entrar al paso; todas las curvas siempre aparecen en las gráficas. Los controles no aportaban valor real dado el tiempo de generación (~instantáneo en hardware objetivo).

---

## [0.4.0] — 2026-06-13

### Añadido
- **`plot_time_loss_bar`** (`compare -o`): gráfica de barras horizontales con el tiempo perdido o ganado por curva, ordenadas de mayor a menor pérdida. Verde = ganas, rojo = pierdes. Archivo: `time_loss_bar.png`.
- **`plot_gg_diagram`** (`compare -o`): diagrama G-G (círculo de fricción) — scatter de G-lat vs G-long del piloto superpuesto sobre la referencia. Muestra si el piloto está aprovechando el agarre disponible. Se genera solo cuando los canales `glat` y `glong` están presentes en el CSV. Archivo: `gg_diagram.png`.
- **`plot_full_lap`** (`compare -o`): vista multi-canal de la vuelta completa en un solo PNG horizontal (16:9). Incluye todos los canales disponibles: delta acumulado, velocidad, gas, freno, volante, marcha, G-lat, G-long. Útil para imprimir o compartir. Archivo: `full_lap.png`.
- **`plot_brake_zones`** (`compare -o`): zoom automático en las N zonas de frenada con mayor pérdida de tiempo. Muestra velocidad + presión de freno + G-long (si disponible) con marcadores del punto de frenada de referencia vs piloto. Archivos: `frenada_<id>.png`.
- **`plot_corner` — paneles de volante y G-lat**: los charts por curva (`curva_<id>.png`) ahora incluyen hasta 5 paneles — se agregan ángulo de volante (azul) y G-lat (amarillo) cuando los canales están presentes. Degradación graceful: si el CSV no tiene esos canales, los paneles no aparecen.

### Mejorado
- **`compare.delta_trace`**: incluye ahora `glat` y `glong` en el trace de comparación para alimentar el diagrama G-G y los paneles nuevos de curva/frenada.
- **`render_charts`**: genera automáticamente todos los nuevos charts además de los existentes (`delta_map`, per-corner). La firma y los parámetros no cambian — compatibilidad hacia atrás total.

---

## [0.3.0] — 2026-06-13

### Añadido
- **`fantasma compose --auto-sync`**: detecta automáticamente el offset temporal entre el video de grabación y el overlay de telemetría mediante correlación cruzada de audio. Extrae la energía espectral del motor (banda 150–500 Hz) del audio del video y la correlaciona contra RPM + velocidad de la telemetría. Precisión ~0.5 s. Extra opcional: `pip install 'fantasma-inputs[sync]'`. Parámetros: `--auto-sync --driver <tele.csv> [--lap-idx N] [--map col=canal]`.
- **UI Paso 4 — Detectar sincronía**: expander «Detectar sincronía automáticamente» en el Paso 4 de `fantasma ui`. Si hay una vuelta cargada del Paso 1 la usa directamente; si no, permite subir la telemetría. El offset detectado se pre-rellena en el campo «Retraso del HUD».
- **`docs/decisions/0001-sync-offset.md`**: documento que registra las 5 opciones evaluadas para la detección de offset (correlación de audio, FFT con numpy, OCR del velocímetro, timestamps de metadata y guía manual) con razonamiento de descarte para cada opción rechazada.

### Mejorado
- **`fantasma overlay` — render paralelo**: frames distribuidos en `N_cores − 1` procesos con `ProcessPoolExecutor`; cada worker crea su propio `_HUDFigure` independiente. En Xeon E5-2680 v4 (14c): ~37 min/vuelta → ~3 min/vuelta.
- **HUD — marcha, velocidad y distancia**: la franja de datos del overlay muestra ahora la marcha actual del piloto (1-6 / N / R), la velocidad en km/h y la distancia recorrida en la vuelta en metros. Útil para verificar sincronía visualmente comparando con el velocímetro y el odómetro del sim.

---

## [0.2.0] — 2026-06-13

### Añadido
- **`fantasma ui`**: interfaz gráfica local basada en Streamlit (localhost, sin hosting). Extra `[ui]`: `pip install 'fantasma-inputs[ui]'`.
  - **5 pasos** (0–4): Inicio · Importar · Comparar · Overlay · Componer.
  - **3 flujos predefinidos** elegibles en el Paso 0: *📊 Solo análisis* (0→1→2), *🎬 Solo overlay* (0→1→3), *🎥 Video con HUD* (0→1→3→4, default). Los pasos fuera del flujo elegido quedan accesibles como opcionales desde el sidebar.
  - **Selector de flujo en Paso 0**: tarjetas visuales con descripción y lista de entregables; navegación flow-aware — el botón "Siguiente" y el breadcrumb del sidebar se adaptan al flujo elegido.
  - **Guía de exportación Sim To MoTeC** en el Paso 0 (colapsada por defecto), con placeholders para imágenes/GIFs.
  - **Tabla de selección de vueltas** con `st.data_editor` + checkboxes: columna "Estado" con `🏆 Más rápida` / `✓ Completa` / `⚠️ Incompleta`; pre-selección automática de la vuelta más rápida.
  - **Carga en caché por `file_id`**: el archivo se parsea una sola vez; interactuar con widgets no re-procesa el archivo.
  - **Tiempos en M:SS.ss** en todos los indicadores.
  - **Sidebar como breadcrumbs**: ▶️ (actual) / ✅ (completado) / ○ (en flujo) / · (opcional); los pasos sin datos quedan deshabilitados.
  - **Botones "Ir al Paso N →"** flow-aware al pie de cada paso.
  - **Auto-comparación** al llegar al Paso 2 (flag `needs_compare`); solo se activa en flujos de análisis.
  - **Editor inline de curvas**: `st.data_editor` para nombrar curvas sin editar JSON a mano.
  - **Overlay de toda la sesión** (Paso 3): checkbox "Generar para todas las vueltas completas del archivo" — usa las vueltas completas detectadas directamente, sin pre-seleccionarlas en el Paso 1.
- **`fantasma compose`**: subcomando que compone el overlay sobre el video de grabación usando ffmpeg. Parámetros: `--video`, `--overlay`, `--position`, `--offset`, `--scale`, `-o`.
- **`fantasma overlay --all-laps`**: renderiza todas las vueltas completas del archivo del piloto (una por subcarpeta `lap_NN/`); con fallback por longitud (≥ 90 % del máximo) cuando ninguna vuelta tiene `is_complete=True`.
- **Indicadores de desgaste de goma** (`wear.py`): índice de deslizamiento, activaciones de ABS/TCS, temperatura media, combustible usado. Visibles en HUD y en `report.md`.
- **`setup.ps1`**: instalación interactiva para Windows — paquete Python + winget para ffmpeg, GitHub CLI, VLC y Kdenlive.
- **Grupos de dependencias opcionales** en `pyproject.toml`: `pip install -e ".[xlsx|overlay|charts|ui|full]"`.
- **Badges en README**: Ko-fi "Buy me a Lap", AGPL-3.0 y estado pre-release.

### Cambiado
- **Overlay HUD rediseñado (HUD-A)**: reemplaza las barras instantáneas (Pillow) por 3 paneles de líneas rodantes (matplotlib) con ventana deslizante de ±320 m / +200 m alrededor del cursor. Franja superior con GAP, ΔV, índice de deslizamiento y contador de ABS.
- **Codificación de color ABS/TCS en overlay**: freno ámbar / gas violeta cuando la electrónica interviene; versiones apagadas en la referencia para distinguir jerarquía visual.
- **Steering coloreado por G lateral relativo**: amarillo (P75–P90) y naranja (>P90) calibrados contra percentiles de la referencia.
- **Branding → SimGhostInputs**: strings de marca en `setup.ps1`, `report.py` y README; nombre técnico del paquete (`fantasma-inputs`) y comando CLI (`fantasma`) sin cambios.
- **`compare.py`**: `_samples` importado al tope del módulo en vez de dentro de la función.
- **`cli.py`**: eliminados imports locales duplicados de `detect_corners`/`extract_milestones`.

### Corregido
- **CSV genérico**: `GUESS` dict extendido con variantes `_pct`, `_deg`, `_m`, `_s`, `_kmh` — cubre exports de SimHub, jocmaster y otros loggers sin necesidad de `--map`.
- **`fantasma overlay --all-laps`**: fallback cuando `is_complete=False` en todas las vueltas; usa las vueltas ≥ 90 % de la longitud máxima.
- **`numpy`**: añadido a los extras `overlay` y `full` en `pyproject.toml`.
- **`report.md`**: URL y nombre de marca corregidos.
- **`motec_csv.py`**: eliminado bloque `if "beacon markers": pass` (código muerto).

### Eliminado
- Archivos de configuración de desarrollo (`.claude/`, `CLAUDE.md`) retirados del seguimiento de git (siguen disponibles localmente vía `.gitignore`).
- `drv_selected_laps` del session_state de la UI — el overlay multi-vuelta opera directamente sobre las vueltas completas del archivo.

---

## [0.1.0] — 2026-06-12

Primera versión funcional, validada con telemetría real de dos pilotos (BMW M4 GT3, Nordschleife, AMS2).

### Añadido
- Importador de CSV/XLSX exportado de MoTeC i2, e importador de CSV genérico con `--map`.
- Separación de vueltas por beacons, número de vuelta o reinicio de distancia; selección automática de la más rápida.
- Normalización por distancia de vuelta (metro 0 en meta) con remuestreo configurable.
- Detector de curvas (V-Min + kinks de alta G) e hitos por curva con segmentación anti-contaminación: frenada, turn-in, release, ápex, gas, gas 100%, overlap gas/freno, pendiente por altitud.
- Comparador piloto vs referencia: delta continuo por metro y tabla por curva con tolerancias y avisos.
- Reporte `report.md` + `delta.csv` + `corners_compare.csv`.
- Gráficas ghost (matplotlib, opcional): mapa de delta de vuelta completa y velocidad/gas/freno por curva.
- `fantasma overlay`: video HUD con canal alfa (ProRes 4444 / WebM VP9 / frames PNG) sincronizado con el tiempo de la vuelta del piloto, para superponer sobre la grabación real.
- CLI: `fantasma laps | detect | compare | overlay`.

### Limitaciones conocidas
- El emparejamiento de frenadas entre pilotos puede dar artefactos cuando difieren >100m.
- Asume el mismo trazado en ambas vueltas (diferencias de longitud <0.5% son tolerables).
- Sin lector directo de `.ld` (requiere export CSV desde MoTeC i2).
