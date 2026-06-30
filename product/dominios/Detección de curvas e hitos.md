---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Detección de curvas e hitos

## Producto
- Fantasma

## Propósito
Identificar automáticamente **dónde están las curvas** y los hitos de manejo dentro de cada una (frenada, turn-in, ápex, gas), para que el análisis sea por curva y el piloto pueda priorizar las que más tiempo cuestan.

## Alcance
- Detección de curvas por mínimo de velocidad (V-Min) y de "kinks" por G-lat.
- Extracción de hitos: inicio/fin de frenada, lift, turn-in, ápex, inicio de gas, gas pleno.
- Salida estructurada por curva (id, hitos, dirección, pendiente, overlap de trail-brake).

**Fuera de alcance:** nombres reales de las curvas por circuito (track packs, futuros); la comparación entre vueltas (es [[Normalización y comparación]]).

## Módulos
- COR — Detección de curvas e hitos

## Relacionado con
- [[Normalización y comparación]]
- [TEC-COR-01 — Detección de curvas](../../engineering/especificaciones/TEC-COR-01%20-%20Deteccion%20de%20curvas%20e%20hitos.md)
