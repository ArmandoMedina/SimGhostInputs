# 👻 SimGhostInputs

[![Estado](https://img.shields.io/badge/estado-pre--release%20v0.2-orange)](CHANGELOG.md)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20Lap-FF5E5B?logo=ko-fi&logoColor=white)](https://ko.fi/armandomedina2255)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

> [!WARNING]
> **Proyecto en desarrollo activo — versión 0.x (pre-release).**
> El motor CLI está validado con telemetría real, pero la interfaz gráfica (`fantasma ui`) y el flujo de video completo (`fantasma compose`) están en pruebas.
> La API interna puede cambiar sin aviso entre versiones 0.x. No se garantiza estabilidad hasta v1.0.

**Compara tus inputs contra una vuelta de referencia, por distancia, no por tiempo.**

SimGhostInputs es una herramienta abierta para sim racers que quieren estudiar su conducción con datos claros, visuales y accionables. Convierte telemetrías exportadas desde distintas fuentes —CSV, Excel, MoTeC u otros formatos compatibles— en un formato común que permite comparar una vuelta del piloto contra una vuelta de referencia.

El objetivo **no** es distribuir vueltas de referencia pagadas, privadas o de terceros. Cada usuario carga sus propios archivos de telemetría y se asegura de tener derecho a usarlos. El software solamente proporciona el motor de conversión, normalización, comparación y visualización.

> Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

Por eso el código se publica bajo **AGPL-3.0-or-later**: puedes usar, estudiar, modificar y compartir el software (incluso comercialmente), pero si distribuyes una versión modificada o la ofreces como servicio en red, debes publicar tu código fuente bajo la misma licencia.

## Qué hace

- Importa telemetría desde **CSV exportado de MoTeC i2** (y el mismo formato en `.xlsx`), o CSV genérico con mapeo de columnas.
- Separa las vueltas de un *outing* (por beacons, número de vuelta o reinicio de distancia) y elige la más rápida.
- Normaliza todo a un formato interno estándar: **distancia de vuelta con metro 0 en meta**, remuestreo configurable (5 m por defecto).
- Detecta curvas e hitos automáticamente: frenada, turn-in, release, ápex (V-Min), gas, gas 100%, G lateral máxima, pendiente.
- Compara piloto vs referencia **por distancia**: delta de tiempo continuo, Δ V-Min, Δ metro de frenada, tiempo perdido por curva.
- Calcula indicadores de desgaste de goma: índice de deslizamiento (slip rueda vs velocidad real), activaciones de ABS/TCS por curva, temperatura media de gomas y combustible consumido.
- Genera reporte en Markdown + CSVs de salida listos para graficar.

## Qué NO incluye

Vueltas de referencia pagadas, telemetrías privadas de coaches o proveedores, setups comerciales, bases de datos propietarias. **Trae tus propios datos.**

## Instalación

**Windows (recomendado):** ejecuta el script de setup incluido — instala el paquete, las dependencias Python y las herramientas del sistema en un paso:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
# o con todo incluido (openpyxl + Pillow + matplotlib):
powershell -ExecutionPolicy Bypass -File setup.ps1 -Full
```

**Manual:**

```
pip install -e .                          # núcleo (sin dependencias externas)
pip install -e ".[xlsx]"                  # + leer archivos .xlsx de MoTeC i2
pip install -e ".[overlay]"               # + fantasma overlay (HUD de video)
pip install -e ".[charts]"                # + fantasma compare con gráficas
pip install -e ".[ui]"                    # + fantasma ui (interfaz gráfica local)
pip install -e ".[full]"                  # todo lo anterior
```

### Dependencias completas

| Dependencia | Tipo | Para qué | Cómo instalar |
| :-- | :-- | :-- | :-- |
| `openpyxl` | Python opcional | Leer `.xlsx` exportados de MoTeC i2 | `pip install openpyxl` |
| `matplotlib` | Python opcional | `fantasma overlay` — HUD animado; `fantasma compare` — gráficas ghost | `pip install matplotlib` |
| `Pillow` | Python opcional | `fantasma overlay` — renderizado de frames auxiliares | `pip install Pillow` |
| `streamlit` + `pandas` | Python opcional | `fantasma ui` — interfaz gráfica local | `pip install 'fantasma-inputs[ui]'` |
| `ffmpeg` | Sistema opcional | Codificar `.webm`/`.mov` con canal alfa y `fantasma compose` | `winget install Gyan.FFmpeg` |
| `gh` (GitHub CLI) | Sistema opcional | Publicar y gestionar el repositorio en GitHub | `winget install GitHub.cli` |

### Herramientas recomendadas para el flujo de video

No son dependencias del paquete, pero completan el flujo de análisis con video:

| Herramienta | Para qué | Cómo instalar (Windows) |
| :-- | :-- | :-- |
| **[VLC](https://www.videolan.org/vlc/)** | Previsualizar `overlay.webm` con alfa antes de editar | `winget install VideoLAN.VLC` |
| **[Kdenlive](https://kdenlive.org/)** | Editor open source (GPL) para superponer el HUD sobre tu grabación | `winget install KDE.Kdenlive` |
| **[DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve)** | Alternativa profesional gratuita (no open source) | Descarga manual |

El `setup.ps1` incluido pregunta si instalar VLC y Kdenlive junto con el resto.

## Uso rápido

```
# interfaz gráfica local (abre el navegador automáticamente)
fantasma ui

# ver las vueltas que contiene un archivo
fantasma laps "mi_export_motec.csv"

# detectar curvas de la vuelta más rápida
fantasma detect "referencia.csv" -o salida/

# comparar tu vuelta contra la referencia
fantasma compare --reference "referencia.csv" --driver "mi_vuelta.csv" -o salida/

# video HUD transparente para superponer sobre tu grabación
fantasma overlay --reference "referencia.csv" --driver "mi_vuelta.csv" -o salida/

# componer el overlay sobre tu grabación y obtener el video final
fantasma compose --video "grabacion.mp4" --overlay "salida/overlay.webm" -o "resultado.mp4"
```

Salida de `compare`:
- `report.md` — el debrief: dónde pierdes, cuánto y en qué fase de cada curva.
- `delta_map.png` — delta acumulado de la vuelta completa con tus mayores pérdidas anotadas.
- `curva_<ID>.png` — gráficas ghost (velocidad/gas/freno, tú vs referencia) de las curvas donde más pierdes.
- `delta.csv` / `corners_compare.csv` — los datos, listos para graficar otra cosa.

Salida de `overlay`:
- `overlay.mov` — video HUD **con canal alfa** (ProRes 4444) sincronizado con el tiempo de tu vuelta. Arrástralo como pista superior en tu editor sobre la grabación real y alinea el segundo 0 con tu cruce de meta. También `--format webm` (VP9 con alfa, mucho más ligero) o `--format png` (frames sueltos).

  El HUD incluye tres paneles (gas / freno / volante) con codificación de color por estado:

  | Canal | Color piloto | Color referencia |
  | :-- | :-- | :-- |
  | Gas / Freno — normal | verde / rojo | gris |
  | Gas / Freno — **TCS activo** | violeta vívido | violeta apagado |
  | Gas / Freno — **ABS activo** | ámbar vívido | ámbar apagado |
  | Volante — carga lateral media (P75–P90 ref) | amarillo | amarillo apagado |
  | Volante — carga lateral alta (> P90 ref) | naranja | naranja apagado |

  Los umbrales de G lateral del volante son **relativos a la vuelta de referencia**: el percentil 75 y 90 del `|G-lat|` de esa vuelta definen qué es "trabajando" y "al límite" para ese auto y pista, sin necesidad de ajuste manual.

  La franja de datos muestra: GAP acumulado · ΔV en el metro actual · índice de deslizamiento (proxy de desgaste) · activaciones de ABS por segmento.

Documentación completa en [`docs/`](docs/): [guía de usuario](docs/guia-usuario.md) · [formato de datos](docs/formato-datos.md) · [cómo contribuir](CONTRIBUTING.md).

## Nombres de curvas (opcional)

El reporte usa IDs genéricos (`C01`, `C02`...) salvo que le des un archivo de curvas:

```
# 1. genera las curvas de TU referencia
fantasma detect "referencia.csv" -o salida/
# 2. edita salida/corners_detected.json y añade "name" a cada curva
#    (y ajusta "tolerances" si quieres avisos más o menos sensibles)
# 3. úsalo en las comparaciones
fantasma compare --reference referencia.csv --driver mi_vuelta.csv --corners salida/corners_detected.json
```

Los nombres de curvas y sus metros son datos de la comunidad: comparte tu "track pack" JSON con otros pilotos del mismo circuito.

## Cómo capturar telemetría

| Sim | Ruta recomendada |
| :-- | :-- |
| AMS2 | [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) (shared memory → `.ld`) → exportar CSV desde MoTeC i2 |
| GT7 | [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) (UDP → `.ld`) → CSV desde i2 |
| ACC / AC / rF2 / LMU | Cualquier logger que genere `.ld` de MoTeC → CSV desde i2 |
| Otros | CSV genérico con `--map` (ver `fantasma compare --help`) |

En el roadmap: lectura directa de `.ld` (sin pasar por i2) e iRacing `.ibt`.

## Licencia

[AGPL-3.0-or-later](LICENSE). © Colaboradores de SimGhostInputs.
