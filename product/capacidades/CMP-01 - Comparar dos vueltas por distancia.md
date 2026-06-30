---
tipo: capacidad
clave: CMP-01
modulo: CMP
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMP-01 - Comparar dos vueltas por distancia

## Módulo
- [[CMP - Comparación]]

## Propósito funcional
Comparar metro a metro la vuelta del piloto contra la de referencia y producir el trace de delta acumulado con todos los canales disponibles en cada punto de distancia.

## Actor principal
Sistema (núcleo del pipeline de análisis).

## Entradas funcionales
- Vuelta de referencia (objeto `Lap` remuestreado).
- Vuelta del piloto (objeto `Lap` remuestreado).
- Paso de rejilla en metros.

## Salidas funcionales
- `trace`: lista de dicts con `dist`, `delta_t` y los canales de referencia y piloto disponibles (`ref_speed`, `drv_speed`, etc.).
- `summary` con `ref_laptime`, `drv_laptime`, `total_delta`, `corners` y `avisos`.

## Reglas de negocio
- El delta es positivo cuando el piloto es más lento que la referencia.
- Vueltas idénticas producen delta nulo en todo punto.
- Solo los canales presentes en ambas vueltas aparecen en el trace; los ausentes no se inventan.

## Criterios de aceptación
- Dado dos vueltas idénticas (misma velocidad en todo punto), cuando se comparan, entonces el delta acumulado es 0 en cada punto del trace.
- Dado que el piloto es más lento que la referencia en todo punto, cuando se comparan, entonces el delta acumulado final (`total_delta`) es positivo.
- Dado que se ejecuta `compare()`, cuando termina, entonces el summary contiene `ref_laptime`, `drv_laptime`, `total_delta` y el número de curvas detectadas.

## Dependencias funcionales
- [[NRM-03 - Remuestrear por distancia]]
- [[COR-01 - Detectar curvas e hitos]]

## Fuera de alcance
- Métricas por curva y flags (es [[CMP-02 - Métricas y flags por curva]]).
- Avisos de comparación inválida (es [[CMP-03 - Avisar de comparación inválida]]).

## Verificación
- Cubierta por `tests/core/test_compare.py` (`test_identical_laps_have_zero_delta`, `test_slower_driver_loses_time_positive_delta`, `test_summary_counts_corners_and_laptimes`).

## Relacionado con
- [[Normalización y comparación]]
- [TEC-CMP-01 — Comparación por distancia](../../engineering/especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
