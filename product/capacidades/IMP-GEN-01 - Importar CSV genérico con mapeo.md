---
tipo: capacidad
clave: IMP-GEN-01
modulo: IMP-GEN
dominio: Importación de telemetría
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# IMP-GEN-01 - Importar CSV genérico con mapeo

## Módulo
- [[IMP-GEN - Importador CSV genérico]]

## Propósito funcional
Leer cualquier CSV de telemetría (SimHub, loggers genéricos) y devolver un objeto `Lap` con los canales canónicos disponibles, usando auto-detección de columnas o mapeo manual explícito.

## Actor principal
Sistema (llamado desde CLI o UI cuando el archivo no tiene estructura MoTeC).

## Entradas funcionales
- Ruta al archivo `.csv`.
- `column_map` opcional: diccionario que traduce nombres de columna del CSV a canales canónicos.

## Salidas funcionales
- Objeto `Lap` con los canales canónicos identificados (como mínimo time y dist).

## Reglas de negocio
- Los encabezados comunes de SimHub y otros loggers (SessionTime, LapDist, Speed_kmh, etc.) se detectan automáticamente sin configuración.
- Si se pasa `column_map`, sus asignaciones tienen prioridad sobre la auto-detección.
- Los valores vacíos o no numéricos se tratan como 0.0.

## Excepciones
- **Sin columnas de time o dist identificables:** se lanza `ValueError`; el sistema no puede normalizar sin distancia.

## Criterios de aceptación
- Dado que el CSV tiene encabezados típicos de SimHub (SessionTime, LapDist, Speed_kmh, Throttle_pct, Brake_pct), cuando se importa sin mapeo manual, entonces los canales time, dist, speed, throttle y brake se detectan y sus valores se parsean correctamente.
- Dado que el CSV tiene encabezados no estándar y se proporciona un `column_map` explícito, cuando se importa, entonces los valores se asignan a los canales canónicos indicados por el mapeo.
- Dado que el CSV carece de columna de distancia identificable, cuando se intenta importar, entonces se lanza `ValueError`.
- Dado que el CSV contiene valores vacíos o cadenas no numéricas, cuando se importa, entonces esos valores se asignan como 0.0 sin lanzar excepción.

## Dependencias funcionales
- No aplica

## Fuera de alcance
- Archivos con estructura de cabecera MoTeC i2 (es [[IMP-MTC-01 - Importar CSV de MoTeC i2]]).

## Relacionado con
- [[Importación de telemetría]]
