# Contribuir a Fantasma Inputs

Gracias por el interés. La regla de la casa es la del README:

> Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

Al contribuir aceptas que tu código se publique bajo **AGPL-3.0-or-later**.

## Entorno de desarrollo

```
git clone <repo>
cd fantasma-inputs
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e .[xlsx]
pip install matplotlib pillow                     # para viz (opcional)
```

Smoke test sin datos privados: usa cualquier export de MoTeC i2 propio y corre
`fantasma laps`, `detect` y `compare` (puedes comparar una vuelta contra otra del mismo outing).

## Principios de diseño

1. **Motor sin datos.** El repo nunca incluye telemetrías, referencias ni setups. Los tests usan datos sintéticos o aportados por quien los corre.
2. **Comparación por distancia.** El metro de pista es el índice maestro, no el tiempo.
3. **Sin dependencias en el núcleo.** `fantasma/core` e `importers` son librería estándar pura. Las dependencias viven en extras opcionales (`viz` usa matplotlib/Pillow; `.xlsx` usa openpyxl) y deben degradar con gracia si faltan.
4. **Determinista.** Mismo archivo de entrada → misma salida, siempre. Nada de IA en el camino de los datos.

## Qué contribuciones valen más ahora

- **Importadores**: MoTeC `.ld` directo (sin pasar por i2 — formato binario, no copiar código de proyectos sin licencia), iRacing `.ibt`, logs de SimHub.
- **Track packs**: JSONs de nombres de curvas por circuito/trazado (`docs/formato-datos.md` describe el esquema). Van en un repo/carpeta de datos comunitarios, no en el motor.
- **Robustez del detector**: el emparejamiento de frenadas entre pilotos da artefactos cuando difieren >100m; ideas bienvenidas.
- **Empaquetado**: `.exe` con PyInstaller para usuarios sin Python.
- Traducción de la documentación (inglés).

## Pull requests

- Una cosa por PR, con descripción de qué problema resuelve.
- Código en el estilo del proyecto: Python estándar, docstrings en español, sin comentarios obvios.
- Si tocas el detector o el comparador, incluye en la descripción del PR un antes/después con datos reales tuyos (basta el `report.md`).

## Reportar problemas

Un issue con: el comando exacto, la salida completa del error, y —si puedes compartirlo— el archivo de telemetría o sus primeras ~30 filas. Nunca subas telemetría que no sea tuya.
