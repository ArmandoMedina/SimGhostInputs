---
tipo: modulo
clave: CMP
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMP - Comparación

## Dominio
- [[Normalización y comparación]]

## Propósito del módulo
Comparar metro a metro la vuelta del piloto contra la de referencia, produciendo el delta continuo, las métricas por curva y avisos cuando la comparación no es válida.

## Alcance
- Delta continuo con signo (piloto más lento = delta positivo).
- Métricas por curva: d_vmin, d_brake_m, d_gas100_m, flags de comportamiento.
- Avisos automáticos: delta sospechosamente grande (posible circuito distinto), autos distintos.
- Degradación graceful: los campos que dependen de un canal ausente (gear, glat, glong, abs, tcs) no aparecen en la salida; los demás sí.

**No cubre:**
- Normalización y remuestreo (es [[NRM - Normalización]]).
- Presentación visual del resultado (es [[REP - Reporte y CSVs]] y [[CHT - Gráficas]]).

## Regla funcional
El delta es positivo cuando el piloto pierde tiempo respecto a la referencia; un campo dependiente de un canal ausente no debe aparecer ni con valor nulo en la salida.

## Secuencia funcional
- **Módulo anterior:** [[NRM - Normalización]]
- **Módulo siguiente:** [[REP - Reporte y CSVs]], [[CHT - Gráficas]], [[OVL - Render del overlay]]

## Capacidades
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[CMP-02 - Métricas y flags por curva]]
- [[CMP-03 - Avisar de comparación inválida]]

## Dependencias funcionales
- [[NRM - Normalización]]
- [[COR - Detección de curvas e hitos]]

## Relacionado con
- [[Normalización y comparación]]
- [TEC-CMP-01 — Comparación por distancia](../../engineering/especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
