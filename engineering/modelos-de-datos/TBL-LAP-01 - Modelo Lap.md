---
tipo: modelo_datos
clave: TBL-LAP-01
tecnologia: dataclass Python (fantasma/core/lap.py)
estado: vigente
---

# TBL-LAP-01 — Modelo `Lap`

## Propósito
El contenedor central de una vuelta en memoria: a esto convierte **todo** importador. Es el modelo canónico sobre el que operan normalización, detección y comparación. `fantasma/core/lap.py`.

## Campos
| Campo | Tipo | Significado |
|---|---|---|
| `channels` | `dict[str, list[float]]` | nombre canónico → serie; todas las listas con la misma longitud |
| `meta` | `dict` | metadatos libres: `venue`, `vehicle`, `driver`, `beacons`, `lap_index`, `is_complete`, `resample_step_m`… |

> Los **canales canónicos** y su significado (unidades, convenciones de signo) son dueño de [`../../docs/formato-datos.md`](../../docs/formato-datos.md). Constante `CANONICAL` en el código: `time`, `dist`, `speed`, `throttle`, `brake`, `steering`, `gear`, `glat`, `glong`, `rpm`, `alt`. Solo `time` y `dist` son obligatorios.

## API (a nivel código)
- **Propiedades:** `laptime` (`t[-1] − t[0]`), `length` (`d[-1] − d[0]`).
- **Métodos:** `col(name)`, `has(name)`, `sample(i)` (dict del frame i), `slice_time(t0, t1)` (sub-vuelta con `time`/`dist` re-referenciados a 0).
- **Nota:** `is_complete` **no** es propiedad; vive en `meta["is_complete"]`.

## Administrado por
- [[arquitectura]] (núcleo `core/`, sin dependencias)

## Vinculado con
- [Formato de datos (canales canónicos)](../../docs/formato-datos.md)
- [TEC-CMP-01 — Comparación por distancia](../especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
