# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

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

### Pendiente / Known issues
_(ninguno)_

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
- **`docs/decisions-sync-offset.md`**: documento que registra las 5 opciones evaluadas para la detección de offset (correlación de audio, FFT con numpy, OCR del velocímetro, timestamps de metadata y guía manual) con razonamiento de descarte para cada opción rechazada.

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
