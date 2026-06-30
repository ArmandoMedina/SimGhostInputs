---
tipo: especificacion_tecnica
clave: TEC-CMP-01
tecnologia: Python (core, sin deps)
estado: vigente
---

# TEC-CMP-01 — Comparación por distancia

## Contexto técnico
El metro de pista es el índice maestro, no el tiempo. Dos vueltas se remuestrean a una rejilla uniforme de distancia y se comparan muestra a muestra. Aritmética pura, sin LLM (principio del producto). Vive en `fantasma/core/compare.py`.

## Flujo técnico
1. `delta_trace(ref, drv, step=5.0)` — remuestrea ambas vueltas (`normalize.resample`) y produce una fila por metro de rejilla: `dist`, `delta_t = drv.time[i] - ref.time[i]`, y `ref_<ch>`/`drv_<ch>` por canal. **Delta positivo = piloto más lento.**
2. `_corner_metrics(corner, lap_data)` — dentro del `segment_m` de cada curva: `vmin` (valor y distancia), `brake_d`/`brake_pct` (último bloque ≥50%), `gas100_d` (primer ≥98% tras vmin).
3. `compare(ref, drv, step, corners)` → `(trace, corner_rows, summary)`.

## Métricas y flags por curva (`corner_rows`)
`id, name, apex_d, ref_vmin, drv_vmin, d_vmin` (positivo = piloto más rápido en curva), `time_lost` (delta al final menos al inicio del segmento), `ref/drv_brake_d, d_brake_m, d_gas100_m, ref/drv_slip, ref/drv_abs, flags`.

Flags: `"vmin"` si `|d_vmin| > tol.vmin_kmh` (default 5 km/h); `"frenada"` si `|d_brake_m| > tol.brake_start_m` (default 15 m). Se concatenan con `+`.

## Avisos automáticos (`summary["avisos"]`)
- Delta total > 50% del laptime de referencia → posible **circuito distinto**.
- Metadata de auto distinta → **autos distintos**.

## Estrategia de mantenimiento
- **Dónde vive:** `fantasma/core/compare.py` (Tier 1 de pruebas).
- Las columnas exactas de las salidas (`delta.csv`, `corners_compare.csv`) son dueño de [`../../docs/formato-datos.md`](../../docs/formato-datos.md) — aquí se enlaza, no se redefine.

## Vinculado con
- [[Normalización y comparación]]
- [TEC-COR-01 — Detección de curvas](TEC-COR-01%20-%20Deteccion%20de%20curvas%20e%20hitos.md)
