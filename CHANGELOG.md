# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **`fantasma ui`**: interfaz gráfica local basada en Streamlit (localhost, sin hosting). Flujo de 4 pasos: Importar → Comparar → Overlay → Componer. Extra `[ui]`: `pip install 'fantasma-inputs[ui]'`.
  - Wizard progresivo con `st.stop()`: cada sección se desbloquea cuando la anterior está completa.
  - **Tabla de selección de vueltas** (referencia y piloto) con `st.data_editor` + checkboxes: muestra `🏆 Más rápida` / `✓ Completa` / `⚠️ Incompleta`; pre-marca la vuelta completa más rápida. La referencia es single-select; el piloto acepta múltiples (se usan todas en overlay `--all-laps`).
  - **Carga en caché por `file_id`**: el archivo se parsea una sola vez; marcar/desmarcar vueltas en la tabla no re-procesa el archivo.
  - **Tiempos en M:SS.ss** en todos los indicadores (en vez de segundos crudos).
  - **Sidebar como breadcrumbs**: botones ▶️ (paso actual) / ✅ (completado) / ○ (pendiente) con navegación programática; los pasos futuros quedan deshabilitados hasta tener datos.
  - **Botones "Ir al Paso N →"** al final de cada paso para no depender de la barra lateral.
  - **Editor inline de nombres de curvas**: `st.data_editor` permite nombrar curvas directamente en la UI sin editar JSON a mano.
  - Detección automática de vueltas al subir el archivo; columna "Estado" con emoji en la tabla.
- **`fantasma compose`**: nuevo subcomando que compone el overlay sobre el video de grabación usando ffmpeg. Parámetros: `--video`, `--overlay`, `--position`, `--offset` (delay en segundos), `--scale`, `-o`.
- **`fantasma overlay --all-laps`**: renderiza todas las vueltas completas del archivo del piloto (una por subcarpeta `lap_NN/`); con fallback por longitud (90 % del máximo) cuando ninguna vuelta tiene `is_complete=True`.
- **Badges en README**: Ko-fi "Buy me a Lap" y AGPL-3.0.

### Cambiado
- **Overlay HUD rediseñado (HUD-A)**: reemplaza las barras instantáneas (Pillow) por 3 paneles de líneas rodantes (matplotlib) con ventana deslizante de ±320m/+200m alrededor del cursor. Franja superior con GAP, ΔV, índice de deslizamiento y contador de ABS.
- **Branding → SimGhostInputs**: strings de marca en `setup.ps1`, `report.py` y README actualizados; nombre técnico del paquete (`fantasma-inputs`) y comando CLI (`fantasma`) sin cambios.

### Añadido
- **Codificación de color ABS/TCS en overlay**: freno ámbar / gas violeta cuando la electrónica interviene; versiones apagadas en la referencia para distinguir jerarquía visual.
- **Steering coloreado por G lateral relativo**: amarillo (P75–P90) y naranja (>P90) calibrados contra percentiles de la referencia; escala automática sin configuración manual.
- **Indicadores de desgaste de goma** (`wear.py`): índice de deslizamiento, activaciones de ABS/TCS, temperatura media, combustible usado. Visibles en HUD y en `report.md`.
- **`setup.ps1`**: instalación interactiva para Windows — paquete Python + winget para ffmpeg, GitHub CLI, VLC y Kdenlive.
- **Grupos de dependencias opcionales** en `pyproject.toml`: `pip install -e ".[xlsx|overlay|charts|ui|full]"`.

### Corregido
- **CSV genérico**: `GUESS` dict extendido con variantes `_pct`, `_deg`, `_m`, `_s`, `_kmh` — cubre exports de SimHub, jocmaster y otros loggers sin necesidad de `--map`.
- **`fantasma overlay --all-laps`**: fallback cuando `is_complete=False` en todas las vueltas (archivo sin beacon de meta); usa las vueltas ≥ 90 % de la longitud máxima.
- **`numpy`**: añadido a los extras `overlay` y `full` en `pyproject.toml` (era dependencia implícita de matplotlib).
- **`report.md`**: URL y nombre de marca corregidos en el pie del reporte generado.

### Eliminado
- Archivos de configuración de desarrollo (`.claude/`, `CLAUDE.md`) retirados del seguimiento de git (siguen disponibles localmente vía `.gitignore`).

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
