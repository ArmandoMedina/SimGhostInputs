# 👻 Fantasma Inputs

**Compara tus inputs contra una vuelta de referencia, por distancia, no por tiempo.**

Fantasma Inputs es una herramienta abierta para sim racers que quieren estudiar su conducción con datos claros, visuales y accionables. Convierte telemetrías exportadas desde distintas fuentes —CSV, Excel, MoTeC u otros formatos compatibles— en un formato común que permite comparar una vuelta del piloto contra una vuelta de referencia.

El objetivo **no** es distribuir vueltas de referencia pagadas, privadas o de terceros. Cada usuario carga sus propios archivos de telemetría y se asegura de tener derecho a usarlos. El software solamente proporciona el motor de conversión, normalización, comparación y visualización.

> Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

Por eso el código se publica bajo **AGPL-3.0-or-later**: puedes usar, estudiar, modificar y compartir el software (incluso comercialmente), pero si distribuyes una versión modificada o la ofreces como servicio en red, debes publicar tu código fuente bajo la misma licencia.

## Qué hace

- Importa telemetría desde **CSV exportado de MoTeC i2** (y el mismo formato en `.xlsx`), o CSV genérico con mapeo de columnas.
- Separa las vueltas de un *outing* (por beacons, número de vuelta o reinicio de distancia) y elige la más rápida.
- Normaliza todo a un formato interno estándar: **distancia de vuelta con metro 0 en meta**, remuestreo configurable (5 m por defecto).
- Detecta curvas e hitos automáticamente: frenada, turn-in, release, ápex (V-Min), gas, gas 100%, G lateral máxima, pendiente.
- Compara piloto vs referencia **por distancia**: delta de tiempo continuo, Δ V-Min, Δ metro de frenada, tiempo perdido por curva.
- Genera reporte en Markdown + CSVs de salida listos para graficar.

## Qué NO incluye

Vueltas de referencia pagadas, telemetrías privadas de coaches o proveedores, setups comerciales, bases de datos propietarias. **Trae tus propios datos.**

## Instalación

```
pip install -e .
# opcional, para leer .xlsx:
pip install openpyxl
```

## Uso rápido

```
# ver las vueltas que contiene un archivo
fantasma laps "mi_export_motec.csv"

# detectar curvas de la vuelta más rápida
fantasma detect "referencia.csv" -o salida/

# comparar tu vuelta contra la referencia
fantasma compare --reference "referencia.csv" --driver "mi_vuelta.csv" -o salida/
```

Salida de `compare`:
- `report.md` — el debrief: dónde pierdes, cuánto y en qué fase de cada curva.
- `delta.csv` — delta de tiempo y de canales cada N metros (para graficar).
- `corners_compare.csv` — tabla por curva.

## Cómo capturar telemetría

| Sim | Ruta recomendada |
| :-- | :-- |
| AMS2 | [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) (shared memory → `.ld`) → exportar CSV desde MoTeC i2 |
| GT7 | [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) (UDP → `.ld`) → CSV desde i2 |
| ACC / AC / rF2 / LMU | Cualquier logger que genere `.ld` de MoTeC → CSV desde i2 |
| Otros | CSV genérico con `--map` (ver `fantasma compare --help`) |

En el roadmap: lectura directa de `.ld` (sin pasar por i2) e iRacing `.ibt`.

## Licencia

[AGPL-3.0-or-later](LICENSE). © Colaboradores de Fantasma Inputs.
