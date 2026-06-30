---
tipo: modulo
clave: IMP-MTC
dominio: Importación de telemetría
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# IMP-MTC - Importador MoTeC

## Dominio
- [[Importación de telemetría]]

## Propósito del módulo
Leer archivos CSV (y XLSX) exportados desde MoTeC i2 y convertirlos al modelo canónico `Lap`, traduciendo los nombres de columna MoTeC a los canales estándar del sistema.

## Alcance
- Detección del formato MoTeC i2 por estructura de cabecera.
- Mapeo de columnas MoTeC (`MOTEC_MAP`) a canales canónicos.
- Parsing de metadatos (Venue, Vehicle, Beacon Markers, source_file).
- Soporte de separador `,` y `;` (exportaciones europeas).
- Soporte de coma decimal en exportaciones con separador `;`.
- División del outing en vueltas por `lap_number` (delegada a `load_laps`).

**No cubre:**
- CSV genérico sin estructura de cabecera MoTeC (es [[IMP-GEN - Importador CSV genérico]]).
- Archivos `.ld` nativos de MoTeC (diferido a post-v1.0).

## Regla funcional
Todo archivo con estructura de cabecera MoTeC i2 debe mapearse íntegramente a canales canónicos; si la estructura no coincide, el sistema falla con `NotMotecFormat` antes de devolver datos parciales.

## Secuencia funcional
- **Módulo anterior:** No aplica
- **Módulo siguiente:** [[NRM - Normalización]]

## Capacidades
- [[IMP-MTC-01 - Importar CSV de MoTeC i2]]

## Dependencias funcionales
- No aplica

## Relacionado con
- [[Importación de telemetría]]
