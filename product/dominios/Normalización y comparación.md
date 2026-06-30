---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Normalización y comparación

## Producto
- Fantasma

## Propósito
El corazón del motor: separar las vueltas de un outing, elegir la más rápida, remuestrear por **distancia** (no tiempo), y comparar piloto vs referencia metro a metro para producir el delta y las métricas por curva. Aritmética pura, sin IA.

## Alcance
- Separación de vueltas (beacons / `lap_number` / reinicio de distancia) y selección de la más rápida.
- Remuestreo a rejilla uniforme de distancia (interpolación lineal; hold para canales discretos).
- Delta continuo con signo (piloto más lento = positivo), métricas y flags por curva, avisos (circuito/auto distinto).

**Fuera de alcance:** la detección de dónde están las curvas (es [[Detección de curvas e hitos]]); la presentación del resultado (es [[Reportería]]).

## Módulos
- NRM — Normalización (split, fastest, resample)
- CMP — Comparación (delta, métricas por curva)

## Relacionado con
- [[Importación de telemetría]]
- [[Detección de curvas e hitos]]
- [TEC-CMP-01 — Comparación por distancia](../../engineering/especificaciones/TEC-CMP-01%20-%20Comparacion%20por%20distancia.md)
