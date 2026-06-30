---
tipo: modelo_datos
clave: TBL-OUT-01
tecnologia: archivos de salida (CSV, JSON, Markdown)
estado: vigente
---

# TBL-OUT-01 — Salidas (CSV y JSON)

## Propósito
Índice de ingeniería de los **archivos que el repo entrega**. El **esquema canónico** de cada salida es dueño de [`../../docs/formato-datos.md`](../../docs/formato-datos.md) (principio de salidas estándar: si SimGhostInputs desaparece, los archivos siguen siendo legibles). Esta nota da el mapa rápido y de dónde sale cada uno; **no redefine** las columnas.

## Salidas
| Archivo | Qué es | Lo produce |
|---|---|---|
| `report.md` | reporte narrativo: tabla resumen + "Top 5 dónde se va el tiempo" + tabla por curva | `viz/report.py` (`render_markdown`) |
| `delta.csv` | una fila por metro de rejilla: `dist`, `delta_t`, `ref_<ch>`/`drv_<ch>` | `viz/report.py` (`write_outputs`) |
| `corners_compare.csv` | una fila por curva: métricas y flags de comparación | `viz/report.py` (`write_outputs`) |
| `corners_detected.json` | `{ "corners": [ … ] }` con el dict de cada curva | `cli.py` (`cmd_detect`) |

> **Convención de signo (recordatorio, no fuente):** `delta_t` positivo = piloto pierde tiempo; `d_vmin` positivo = piloto más rápido en la curva. Detalle y columnas exactas en [`formato-datos.md`](../../docs/formato-datos.md).

## Administrado por
- [[arquitectura]]

## Vinculado con
- [Formato de datos (esquema de salidas)](../../docs/formato-datos.md)
- [TEC-CMP-01 — Comparación por distancia](../especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
