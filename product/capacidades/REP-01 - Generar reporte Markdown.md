---
tipo: capacidad
clave: REP-01
modulo: REP
dominio: Reportería
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# REP-01 - Generar reporte Markdown

## Módulo
- [[REP - Reporte y CSVs]]

## Propósito funcional
Generar el archivo `report.md` con el debrief completo de la comparación: tiempos de vuelta, top-5 de tiempo perdido por curva, tabla completa por curva y avisos del motor.

## Actor principal
Sistema (llamado al finalizar `compare()`; se genera automáticamente con `fantasma compare`).

## Entradas funcionales
- `trace`: puntos de delta del recorrido.
- `corner_rows`: métricas por curva.
- `summary`: tiempos, total delta, avisos, y datos de desgaste si disponibles.
- `meta`: metadatos de sesión (Venue, Vehicle, etc.).

## Salidas funcionales
- Archivo `report.md` en el directorio de salida configurado.

## Reglas de negocio
- El reporte siempre incluye: tabla de tiempos (referencia, piloto, delta) y tabla por curva.
- El top-5 de pérdidas solo incluye curvas con `time_lost > 0`.
- Los avisos del summary se muestran como citas de advertencia (`> **Aviso:** ...`).
- Las filas de desgaste (slip_index, ABS, TCS, temperatura, combustible) solo aparecen si los datos están en el summary.
- El esquema exacto del Markdown es dueño de `docs/formato-datos.md`.

## Criterios de aceptación
- Dado el resultado de `compare()` con curvas y summary, cuando se genera el reporte, entonces `report.md` contiene la tabla de tiempos (referencia, piloto, delta), la tabla completa por curva y el top-5 de tiempo perdido.
- Dado que `summary["avisos"]` contiene mensajes, cuando se genera el reporte, entonces aparecen como citas de advertencia en el Markdown.
- Dado que los datos de desgaste (slip_index, ABS, TCS) están presentes en el summary, cuando se genera el reporte, entonces sus filas aparecen en la tabla resumen.

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[CMP-02 - Métricas y flags por curva]]

## Fuera de alcance
- CSVs de salida (es [[REP-02 - Exportar CSVs (delta, corners_compare)]]).
- Gráficas de análisis (es [[CHT-01 - Generar gráficas de análisis]]).

## Relacionado con
- [[Reportería]]

> **Nota:** No existe test unitario dedicado a esta capacidad. Los criterios se derivan directamente de la inspección de `fantasma/viz/report.py` (`render_markdown`).
