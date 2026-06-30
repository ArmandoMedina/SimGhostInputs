---
tipo: solucion
producto: Fantasma
estado: vigente
---

# Análisis Post-Tanda

## Propósito
Después de una sesión, el piloto quiere saber **dónde perdió tiempo y qué hizo diferente**. Importa el CSV de MoTeC i2, compara su vuelta contra una referencia metro a metro, y entrega un reporte accionable en minutos. Objetivo: del CSV al insight en menos de cinco minutos.

## Alcance
- Reporte narrativo en Markdown: dónde pierdes, cuánto y en qué fase de cada curva.
- Gráficas ghost (velocidad/gas/freno/volante superpuestos), diagrama G-G, mapa de delta.
- Tabla de curvas con tiempo perdido ordenado por impacto.

**Fuera de alcance:** overlay de video (es la otra solución); coaching en vivo; IA en el pipeline de comparación (aritmética pura).

## Dominios que integra
- [[Importación de telemetría]]
- [[Normalización y comparación]]
- [[Detección de curvas e hitos]]
- [[Desgaste de gomas]]
- [[Reportería]]
- [[Interfaz de usuario]]

## Flujo de valor
1. **Entrada:** CSV exportado de MoTeC i2 (o CSV genérico).
2. **Proceso:** normaliza por distancia, detecta curvas, compara piloto vs referencia.
3. **Salida:** `report.md`, `delta.csv`, `corners_compare.csv` + gráficas.

## Relacionado con
- [[Fantasma]]
- [[Overlay de Video]]
