---
tipo: capacidad
clave: CMP-02
modulo: CMP
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMP-02 - Métricas y flags por curva

## Módulo
- [[CMP - Comparación]]

## Propósito funcional
Para cada curva detectada, calcular las métricas de diferencia entre piloto y referencia: velocidad en el ápex, distancia de frenada, punto de gas al 100% y flags de comportamiento.

## Actor principal
Sistema (parte de `compare()`, ejecutada por curva tras el delta continuo).

## Entradas funcionales
- Trace de delta (salida de [[CMP-01 - Comparar dos vueltas por distancia]]).
- Lista de curvas con hitos (salida de [[COR-01 - Detectar curvas e hitos]]).

## Salidas funcionales
- `rows`: lista de dicts por curva con `d_vmin`, `d_brake_m`, `d_gas100_m`, `time_lost`, `flags`, y opcionalmente `ref_abs`, `drv_abs`, `ref_tcs`, `drv_tcs`.
- Solo aparecen los campos cuyo canal subyacente existe en ambas vueltas.

## Reglas de negocio
- `d_vmin` positivo significa que el piloto pasa el ápex más rápido que la referencia.
- Si no hay canal `gear`, el campo `vmin_gear` no aparece en la salida.
- Si no hay canal `glat` o `glong`, los campos dependientes de ellos no aparecen.
- El pipeline no crashea con ninguna combinación de los 32 subconjuntos de canales opcionales (glat, glong, gear, abs, tcs).

## Criterios de aceptación
- Dado que el piloto pasa el ápex más rápido que la referencia, cuando se calculan las métricas por curva, entonces `d_vmin` es positivo para esa curva.
- Dado que ninguna de las dos vueltas tiene canal de marcha, cuando se comparan, entonces el campo `vmin_gear` no aparece en las rows por curva.
- Dado que las vueltas carecen de un canal opcional (glat, glong, gear, abs o tcs), cuando se comparan, entonces los campos dependientes de ese canal no aparecen en la salida y el resto de métricas sí están presentes.

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[COR-01 - Detectar curvas e hitos]]

## Fuera de alcance
- Delta continuo (es [[CMP-01 - Comparar dos vueltas por distancia]]).
- Avisos globales de comparación inválida (es [[CMP-03 - Avisar de comparación inválida]]).

## Verificación
- Cubierta por `tests/core/test_compare.py` (`test_faster_apex_gives_positive_d_vmin`, `test_compare_without_gear_channel_does_not_crash`, `test_compare_without_glat_channel_does_not_crash`).
- Cobertura sistemática de las 32 combinaciones de canales opcionales: `tests/core/test_degradacion_canales.py` (`test_compare_degradacion_graceful`).

## Relacionado con
- [[Normalización y comparación]]
- [TEC-CMP-01 — Comparación por distancia](../../engineering/especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
