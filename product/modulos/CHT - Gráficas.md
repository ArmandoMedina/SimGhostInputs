---
tipo: modulo
clave: CHT
dominio: Reportería
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CHT - Gráficas

## Dominio
- [[Reportería]]

## Propósito del módulo
Generar las gráficas de análisis del debrief: delta map, tiempo perdido por curva, diagrama G-G, vuelta completa multi-canal, detalle de curvas y zonas de frenada.

## Alcance
- Delta map: delta acumulado vs distancia con las mayores pérdidas anotadas.
- Barras horizontales de tiempo perdido por curva.
- Diagrama G-G (círculo de fricción): G-lat vs G-long de piloto y referencia.
- Vista multi-canal de la vuelta completa (todos los canales disponibles).
- Gráficas por curva: velocidad, gas, freno, volante, G-lat (top-N pérdidas).
- Zonas de frenada: zoom con velocidad, presión y G-long para las frenadas con mayor pérdida.

**No cubre:**
- Reporte Markdown y CSVs (es [[REP - Reporte y CSVs]]).
- HUD de video (es [[OVL - Render del overlay]]).

## Regla funcional
Si `matplotlib` no está instalado, el módulo devuelve una lista vacía sin lanzar excepción; las gráficas son un extra opcional que no bloquea el pipeline.

## Secuencia funcional
- **Módulo anterior:** [[CMP - Comparación]]
- **Módulo siguiente:** No aplica

## Capacidades
- [[CHT-01 - Generar gráficas de análisis]]

## Dependencias funcionales
- [[CMP - Comparación]]
- [[COR - Detección de curvas e hitos]]

## Relacionado con
- [[Reportería]]
