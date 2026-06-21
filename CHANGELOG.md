# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **`fantasma wear` — medidor de desgaste de goma acumulable** (implementa el ADR 0004): nuevo comando CLI y función pura `wear_budget` en `core/wear.py`. Acumula el `slip_index` de las vueltas de un stint, da estado (`ok`/`yellow`/`red`/`burst`) y estima cuántas vueltas faltan para el reventón, estilo medidor de gasolina. Umbrales configurables (`--yellow`/`--red`/`--burst`, default 30/40/50 — a calibrar con datos reales). El número es un proxy en unidades arbitrarias, no % físico.
- **ADR — registro de decisiones numerado** (`docs/decisions/`): se impone la estructura `NNNN-titulo.md` con plantilla (`0000-plantilla.md`) e índice (`README.md`). Se migran los decision-docs planos previos a `0001-sync-offset`, `0002-crewchief-pacenotes`, `0003-testing` (con sus referencias actualizadas en ROADMAP/CHANGELOG/CONTRIBUTING). Nuevo **ADR 0004 — desgaste de llanta acumulable** (medidor tipo gasolina): reusar `slip_index` como rate por vuelta, acumularlo en el stint, umbrales configurables y vueltas estimadas a cambio (**Aceptada**). Nuevo **ADR 0005 — indicadores de estado del HUD se leen en el cursor, no por ventana** (**Aceptada**): guardarraíl para las luces ABS/TC y DESLIZ.

### Corregido
- **Overlay — indicadores ABS/TC ahora son luces instantáneas, no conteo por ventana**: el texto "ABS"/"TC" de la franja mostraba un conteo de activaciones acumulado sobre los ~520 m visibles, así que no "prendía y apagaba" con la activación real. Ahora cada luz lee el flag del piloto **en el cursor** (`_flag_recent_grid` en `viz/overlay.py`) y se enciende en su color (ABS ámbar, TC violeta) cuando está activo, con retención corta (`HOLD_M = 8 m`) para no parpadear a 30/60 fps. Se añade además la luz **TC** que antes no existía como texto.
- **Overlay — espaciado de la franja de datos**: se separa la etiqueta «MARCHA» del número de marcha (estaban pegados) y se acerca «km/h» a «m» (sobraba aire entre ambos).
- **Overlay — DESLIZ ahora es deslizamiento reciente, no promedio de pantalla** (ADR 0005): antes promediaba el slip de toda la ventana visible (520 m, incluyendo 200 m **por delante** del cursor); ahora promedia solo una ventana corta detrás del cursor (`SLIP_WIN_M = 40 m`).
- **Overlay — ABS/TC de la referencia más visibles + luz apagada en gris**: se subió el brillo de las líneas de asistencia de la referencia (`_RABS`, `_RTCS`), que casi no se veían, y el estado *apagado* de las luces ABS/TC pasó a gris (`_DIM`) para que el on/off contraste sin depender de esos colores.

### Pendiente / Known issues
_(ninguno)_

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
