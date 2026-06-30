---
tipo: modulo
clave: IMP-GEN
dominio: Importación de telemetría
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# IMP-GEN - Importador CSV genérico

## Dominio
- [[Importación de telemetría]]

## Propósito del módulo
Leer cualquier CSV de telemetría (SimHub, loggers genéricos) y convertirlo al modelo canónico `Lap`, mediante auto-detección de nombres de columna o mapeo manual explícito.

## Alcance
- Auto-detección de nombres comunes de columnas (`GUESS`) sin configuración adicional.
- Mapeo manual vía `column_map` para archivos con encabezados no estándar.
- Tolerancia a valores vacíos o no numéricos (se tratan como 0.0).

**No cubre:**
- Archivos con estructura de cabecera MoTeC i2 (es [[IMP-MTC - Importador MoTeC]]).
- Separadores y codificaciones exóticas fuera del estándar UTF-8 (deuda técnica).

## Regla funcional
Si el archivo no tiene columnas identificables como `time` y `dist` (por auto-detección o `column_map`), el sistema falla con `ValueError` antes de devolver datos parciales.

## Secuencia funcional
- **Módulo anterior:** No aplica
- **Módulo siguiente:** [[NRM - Normalización]]

## Capacidades
- [[IMP-GEN-01 - Importar CSV genérico con mapeo]]

## Dependencias funcionales
- No aplica

## Relacionado con
- [[Importación de telemetría]]
