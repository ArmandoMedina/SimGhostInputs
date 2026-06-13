# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/). Versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Añadido
- **Codificación de color ABS/TCS en overlay**: freno ámbar / gas violeta cuando la electrónica interviene; versiones apagadas del mismo color en la referencia para distinguir jerarquía visual sin perder continuidad de línea.
- **Steering coloreado por G lateral relativo**: amarillo (P75–P90) y naranja (>P90) calibrados contra los percentiles de la vuelta de referencia; escala automática para cualquier auto y pista sin configuración manual.
- **Indicadores de desgaste de goma** (`wear.py`): índice de deslizamiento (slip tyre-speed vs vehicle-speed), activaciones de ABS/TCS por tramo, temperatura media de gomas, combustible usado. Visibles en la franja de datos del HUD y en `report.md`.
- **`setup.ps1`**: script de instalación interactivo para Windows — instala el paquete Python con los grupos de dependencias opcionales (`xlsx`, `overlay`, `charts`, `full`) y ofrece instalar via winget: ffmpeg, GitHub CLI, VLC y Kdenlive.
- **Grupos de dependencias opcionales** en `pyproject.toml`: `pip install -e ".[xlsx|overlay|charts|full]"` para instalar solo lo necesario.
- **Flujo de video documentado en la guía de usuario**: VLC para previsualizar el overlay con canal alfa; Kdenlive (GPL) como editor open source recomendado para sincronizar el HUD con la grabación; instrucciones de instalación con winget incluidas.

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
