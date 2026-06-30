---
tipo: capacidad
clave: REP-02
modulo: REP
dominio: Reportería
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# REP-02 - Exportar CSVs (delta, corners_compare)

## Módulo
- [[REP - Reporte y CSVs]]

## Propósito funcional
Exportar los resultados del análisis como archivos CSV estructurados para consumo externo o análisis posterior.

## Actor principal
Sistema (parte de `write_outputs()`; se genera junto con el reporte).

## Entradas funcionales
- `trace`: lista de dicts con el delta continuo por punto de distancia.
- `corner_rows`: lista de dicts con métricas por curva.
- Directorio de salida.

## Salidas funcionales
- `delta.csv`: una fila por punto de distancia con todos los campos del trace.
- `corners_compare.csv`: una fila por curva con todos los campos de las métricas.
- Directorio de salida creado automáticamente si no existe.

## Reglas de negocio
- Los encabezados de cada CSV se infieren dinámicamente de las claves del primer elemento (unión de todas las claves presentes en las rows para `corners_compare.csv`).
- Si `trace` está vacío, `delta.csv` no se escribe.
- Si `corner_rows` está vacío, `corners_compare.csv` no se escribe.
- El esquema exacto de columnas es dueño de `docs/formato-datos.md`.

## Criterios de aceptación
- Dado el trace y las rows de `compare()`, cuando se llama a `write_outputs`, entonces se crean `delta.csv` y `corners_compare.csv` en el directorio de salida con los encabezados correspondientes a los campos disponibles.
- Dado que el directorio de salida no existe, cuando se llama a `write_outputs`, entonces el directorio se crea automáticamente antes de escribir los archivos.

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[CMP-02 - Métricas y flags por curva]]

## Fuera de alcance
- Reporte Markdown (es [[REP-01 - Generar reporte Markdown]]).

## Relacionado con
- [[Reportería]]

> **Nota:** No existe test unitario dedicado a esta capacidad. Los criterios se derivan de la inspección de `fantasma/viz/report.py` (`write_outputs`).
