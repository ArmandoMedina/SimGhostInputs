# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **`fantasma ui`**: interfaz gráfica local basada en Streamlit (localhost, sin hosting). Extra `[ui]`: `pip install 'fantasma-inputs[ui]'`.
  - **5 pasos** (0–4): Inicio · Importar · Comparar · Overlay · Componer.
  - **3 flujos predefinidos** elegibles en el Paso 0: *📊 Solo análisis* (0→1→2), *🎬 Solo overlay* (0→1→3), *🎥 Video con HUD* (0→1→3→4, default). Los pasos fuera del flujo elegido quedan accesibles como opcionales desde el sidebar.
  - **Selector de flujo en Paso 0**: tarjetas visuales con descripción y lista de entregables; navegación flow-aware — el botón "Siguiente" y el breadcrumb del sidebar se adaptan al flujo elegido.
  - **Guía de exportación Sim To MoTeC** en el Paso 0 (colapsada por defecto), con placeholders para imágenes/GIFs.
  - **Tabla de selección de vueltas** con `st.data_editor` + checkboxes: columna "Estado" con `🏆 Más rápida` / `✓ Completa` / `⚠️ Incompleta`; pre-selección automática de la vuelta más rápida. Referencia y piloto son single-select; el overlay de toda la sesión se activa en el Paso 3.
  - **Carga en caché por `file_id`**: el archivo se parsea una sola vez; interactuar con widgets no re-procesa el archivo.
  - **Tiempos en M:SS.ss** en todos los indicadores.
  - **Sidebar como breadcrumbs**: ▶️ (actual) / ✅ (completado) / ○ (en flujo) / · (opcional); los pasos sin datos quedan deshabilitados.
  - **Botones "Ir al Paso N →"** flow-aware al pie de cada paso.
  - **Auto-comparación** al llegar al Paso 2 (flag `needs_compare`); solo se activa en flujos de análisis.
  - **Editor inline de curvas**: `st.data_editor` para nombrar curvas sin editar JSON a mano.
  - **Overlay de toda la sesión** (Paso 3): checkbox "Generar para todas las vueltas completas del archivo" — usa las vueltas completas detectadas directamente, sin necesidad de pre-seleccionarlas en el Paso 1.
  - **Badge pre-release v0.x** en README + bloque de aviso `[!WARNING]` de desarrollo activo.
- **`fantasma compose`**: subcomando que compone el overlay sobre el video de grabación usando ffmpeg. Parámetros: `--video`, `--overlay`, `--position`, `--offset`, `--scale`, `-o`.
- **`fantasma overlay --all-laps`**: renderiza todas las vueltas completas del archivo del piloto (una por subcarpeta `lap_NN/`); con fallback por longitud (≥ 90 % del máximo) cuando ninguna vuelta tiene `is_complete=True`.
- **Badges en README**: Ko-fi "Buy me a Lap" y AGPL-3.0.

### Cambiado
- **Overlay HUD rediseñado (HUD-A)**: reemplaza las barras instantáneas (Pillow) por 3 paneles de líneas rodantes (matplotlib) con ventana deslizante de ±320 m / +200 m alrededor del cursor. Franja superior con GAP, ΔV, índice de deslizamiento y contador de ABS.
- **Branding → SimGhostInputs**: strings de marca en `setup.ps1`, `report.py` y README; nombre técnico del paquete (`fantasma-inputs`) y comando CLI (`fantasma`) sin cambios.
- **Codificación de color ABS/TCS en overlay**: freno ámbar / gas violeta cuando la electrónica interviene; versiones apagadas en la referencia para distinguir jerarquía visual.
- **Steering coloreado por G lateral relativo**: amarillo (P75–P90) y naranja (>P90) calibrados contra percentiles de la referencia.
- **`compare.py`**: `_samples` importado al tope del módulo en vez de dentro de la función.
- **`cli.py`**: eliminados imports locales duplicados de `detect_corners`/`extract_milestones` (ya estaban en el tope del módulo).

### Añadido
- **Indicadores de desgaste de goma** (`wear.py`): índice de deslizamiento, activaciones de ABS/TCS, temperatura media, combustible usado. Visibles en HUD y en `report.md`.
- **`setup.ps1`**: instalación interactiva para Windows — paquete Python + winget para ffmpeg, GitHub CLI, VLC y Kdenlive.
- **Grupos de dependencias opcionales** en `pyproject.toml`: `pip install -e ".[xlsx|overlay|charts|ui|full]"`.

### Corregido
- **CSV genérico**: `GUESS` dict extendido con variantes `_pct`, `_deg`, `_m`, `_s`, `_kmh` — cubre exports de SimHub, jocmaster y otros loggers sin necesidad de `--map`.
- **`fantasma overlay --all-laps`**: fallback cuando `is_complete=False` en todas las vueltas; usa las vueltas ≥ 90 % de la longitud máxima.
- **`numpy`**: añadido a los extras `overlay` y `full` en `pyproject.toml`.
- **`report.md`**: URL y nombre de marca corregidos.
- **`motec_csv.py`**: eliminado bloque `if "beacon markers": pass` que era código muerto.

### Eliminado
- Archivos de configuración de desarrollo (`.claude/`, `CLAUDE.md`) retirados del seguimiento de git (siguen disponibles localmente vía `.gitignore`).
- `drv_selected_laps` del session_state de la UI — el overlay multi-vuelta ahora opera directamente sobre las vueltas completas del archivo.

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
