---
tipo: modulo
clave: REP
dominio: Reportería
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# REP - Reporte y CSVs

## Dominio
- [[Reportería]]

## Propósito del módulo
Materializar los resultados del análisis como un reporte Markdown legible por el piloto y como CSVs estructurados para análisis externo.

## Alcance
- Reporte Markdown (`report.md`) con tabla de tiempos de vuelta, top-5 de pérdidas por curva, tabla completa por curva, avisos del motor y desgaste si está disponible.
- CSV de delta continuo (`delta.csv`) con todos los campos del trace.
- CSV de métricas por curva (`corners_compare.csv`) con todas las columnas disponibles.
- Creación automática del directorio de salida.

**No cubre:**
- Gráficas de análisis (es [[CHT - Gráficas]]).
- HUD de video (es [[OVL - Render del overlay]]).

## Regla funcional
El reporte Markdown y los CSVs son la única fuente de verdad persistente del análisis; el detalle del esquema de salida es dueño de `docs/formato-datos.md` — esta nota enlaza, no duplica.

## Secuencia funcional
- **Módulo anterior:** [[CMP - Comparación]]
- **Módulo siguiente:** No aplica

## Capacidades
- [[REP-01 - Generar reporte Markdown]]
- [[REP-02 - Exportar CSVs (delta, corners_compare)]]

## Dependencias funcionales
- [[CMP - Comparación]]
- [[WER - Desgaste acumulable]]

## Relacionado con
- [[Reportería]]
