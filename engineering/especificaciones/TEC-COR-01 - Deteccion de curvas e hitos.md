---
tipo: especificacion_tecnica
clave: TEC-COR-01
tecnologia: Python (core, sin deps)
estado: vigente
---

# TEC-COR-01 — Detección de curvas e hitos

## Contexto técnico
Identifica dónde están las curvas y los hitos de manejo (frenada, ápex, gas) sobre la vuelta, para que la comparación sea por curva. `fantasma/core/corners.py`. El **resumen** del algoritmo es dueño de [`../../docs/formato-datos.md`](../../docs/formato-datos.md); esta nota da el detalle de implementación.

## Algoritmo
**`detect_corners(lap, vmin_window_s=1.2, vmin_prominence_kmh=3.0, kink_glat=2.2)`** detecta dos tipos de evento ordenados por distancia:
- **vmin** — mínimo local de velocidad: `v` es el menor de la ventana `±W` (W ≈ `1.2s/dt` muestras) y ambos extremos superan `v + 3 km/h`.
- **kink** — pico de `|G-lat| > 2.2 G` en ventana `±0.5s`, descartado si hay un vmin a < 80 m.

**`extract_milestones(lap, events, ...)`** segmenta cada curva (máx ±450 m antes / ±350 m después) y extrae hitos:
- `brake_start` (inicio del último bloque de freno con pico ≥50%), `brake_release` (freno < 2%), `lift` (si no hay frenada), `turn_in` (steering > 8°), `apex` (mínimo de velocidad), `throttle_on` (> 5% desde apex−0.6s), `full_throttle` (≥98% sostenido 15 muestras).

## Estructura del dict de curva
`id, kind, milestones, no_brake, segment_m [lo, hi], delta_s, direction, max_steering_deg, slope_pct, slope` y `overlap_m` (solo cuando el gas precede al `brake_release` = trail-brake real). Cada hito: `{d, t, v, gear?, ...}`.

## Estrategia de mantenimiento
- **Dónde vive:** `fantasma/core/corners.py` (Tier 1). Umbrales calibrados sobre telemetría AMS2; recalibrar requiere datos reales, no intuición.

## Vinculado con
- [[Detección de curvas e hitos]]
- [Formato de datos (esquema corners JSON)](../../docs/formato-datos.md)
