# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **`fantasma compose` — NVENC automático**: si el sistema tiene una GPU NVIDIA con `h264_nvenc` disponible, el compose usa GPU encoding en lugar de `libx264` CPU. En una RTX 2060, un video de 70 min pasa de horas a ~19 min (3.7× tiempo real). Fallback automático a `libx264` si no hay NVENC.

### Mejorado
- **`auto_sync` — validación de confianza**: si el pico de correlación audio/telemetría no supera 3σ sobre el ruido, lanza `RuntimeError` con mensaje claro. Antes devolvía un offset inventado sin aviso cuando el video no correspondía a la vuelta.
- **`fantasma overlay` — progreso de codificación ffmpeg en tiempo real**: la barra de progreso de la UI ya no se congela al 99% mientras ffmpeg codifica. `_run_ffmpeg()` lanza ffmpeg con `-progress pipe:1`, lee `frame=N` de stdout y llama el callback de progreso con el texto «Codificando video… frame N / total». Compatible con cualquier formato (webm/mov).
- **`fantasma overlay` — VP9 multithreading**: añadidos `-row-mt 1 -threads N` al comando VP9 de `libvpx-vp9`, donde N = `os.cpu_count()`. Aprovecha todos los cores disponibles durante la codificación. (VP9+alpha `yuva420p` no tiene encoder GPU disponible en ningún vendor, por lo que el multithreading CPU es el máximo rendimiento posible para este codec.)

### Corregido
- **`fantasma overlay` — marcha/glat/abs/tcs ausentes se detectan correctamente**: `_interp_lap` devolvía zeros para canales opcionales no presentes en el CSV; `drv_ch.get("gear")` nunca era `None` y la marcha aparecía siempre como «N». Ahora los canales opcionales ausentes son `None`: `_masked`, `_masked_g` y el renderizador de gear/speed los omiten limpiamente sin crashear.
- **`fantasma overlay` — render paralelo no funcionaba en UI**: el `ProcessPoolExecutor(mp_context="spawn")` fallaba silenciosamente bajo Streamlit — el proceso hijo intentaba reimportar `__main__` del servidor de Streamlit y crasheaba en cascada, forzando el fallback a render serial (1 core). Reemplazado por `subprocess.Popen([python, -m, fantasma.viz._overlay_worker])` con un worker script independiente que tiene su propio `__main__`, arranca limpio y no hereda estado del servidor. El fix es multiplataforma sin código condicional por OS: `subprocess` siempre crea un proceso fresco, lo que también elimina el riesgo de deadlock de `fork + matplotlib` en Linux/Mac.

### Corregido
- **Charts en UI (Paso 2) — gráficas no se mostraban**: la generación de gráficas se disparaba en cada rerun de Streamlit (cualquier interacción con un widget lo provoca) y los errores dentro de `st.spinner()` desaparecen cuando el spinner cierra. Solución: las rutas de los charts se cachean en `session_state["charts_paths"]`; se regeneran solo cuando corre una comparación nueva o se presiona «Recalcular». Los mensajes de error y de importación se muestran fuera del spinner para que persistan.
- **`__version__` desactualizado**: `fantasma/__init__.py` reportaba `0.2.0`; corregido a `0.4.0`.

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
