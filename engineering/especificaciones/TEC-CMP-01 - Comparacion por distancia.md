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
1. `delta_trace(ref, drv, step=5.0)` — remuestrea ambas vueltas (`normalize.resample`) y produce una fila por metro de rejilla: `dist`, `delta_t = drv.time[i] - ref.time[i]`, y `ref_<ch>`/`drv_<ch>` por canal, incluyendo `rpm` cuando existe. **Delta positivo = piloto más lento.**
2. `_corner_metrics(corner, lap_data)` — dentro del `segment_m` de cada curva: `vmin` (valor y distancia), `brake_d`/`brake_pct` (último bloque ≥50%), `gas100_d` (primer ≥98% tras vmin).
3. `compare(ref, drv, step, corners)` → `(trace, corner_rows, summary)`.
4. `corner_coaching(row, trace)` — interpreta una curva desde `corner_rows` + `trace` y devuelve síntesis y acciones deterministas para el drill-down de Paso 2.

## Métricas y flags por curva (`corner_rows`)
`id, name, segment_start_m, segment_end_m, apex_d, ref_vmin, drv_vmin, drv_vmin_d, d_vmin` (positivo = piloto más rápido en curva), `time_lost` (delta al final menos al inicio del segmento), `ref/drv_brake_d`, `d_brake_m`, `ref/drv_gas100_d`, `d_gas100_m`, `ref/drv_slip`, `ref/drv_abs`, `flags`.

## Drill-down por curva (`corner_coaching`)
`corner_coaching(row, trace)` no cambia el cálculo base ni usa LLM. Devuelve un dict con:
- `status`: `loss`, `gain` o `neutral`.
- `summary`: frase corta con pérdida/ganancia y señales principales.
- `actions`: lista de acciones priorizadas.
- `braking`, `apex`, `throttle`, `lateral`, `gear`: secciones de métricas; quedan vacías si falta el canal necesario.

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
