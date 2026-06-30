---
tipo: capacidad
clave: IMP-MTC-01
modulo: IMP-MTC
dominio: Importación de telemetría
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# IMP-MTC-01 - Importar CSV de MoTeC i2

## Módulo
- [[IMP-MTC - Importador MoTeC]]

## Propósito funcional
Leer un archivo CSV exportado por MoTeC i2 y devolver un objeto `Lap` con los canales canónicos del sistema, los metadatos de sesión y los beacons de vuelta.

## Actor principal
Sistema (llamado desde CLI o UI al cargar un archivo de referencia o piloto).

## Entradas funcionales
- Ruta al archivo `.csv` (o `.xlsx`) exportado por MoTeC i2.
- Separador auto-detectado (`,` o `;`).

## Salidas funcionales
- Objeto `Lap` con canales canónicos (time, dist, speed, throttle, brake, gear, glat, abs, entre otros disponibles).
- `lap.meta` con Venue, Vehicle, Beacon Markers (como lista de floats) y source_file.

## Reglas de negocio
- Los nombres de columna MoTeC se traducen a canales canónicos usando `MOTEC_MAP`; las columnas desconocidas se ignoran sin error.
- La detección de separador `;` y coma decimal es automática.
- Los Beacon Markers se parsean como lista de floats.
- `source_file` se añade al meta con solo el nombre del archivo (sin ruta).

## Excepciones
- **Archivo sin estructura MoTeC i2:** se lanza `NotMotecFormat` antes de devolver datos parciales.

## Criterios de aceptación
- Dado que se carga un CSV de MoTeC i2 válido con separador `,`, cuando se importa, entonces los canales canónicos (time, dist, speed, throttle, brake, gear, glat, abs) están presentes y el primer valor de speed se parsea correctamente.
- Dado que el CSV tiene metadatos de cabecera (Venue, Vehicle) y Beacon Markers, cuando se importa, entonces `lap.meta` contiene Venue, Vehicle, source_file y beacons como lista de floats.
- Dado que el archivo no tiene la estructura de cabecera de MoTeC i2, cuando se intenta importar, entonces se lanza `NotMotecFormat`.
- Dado que el CSV usa separador `;` y coma decimal europea, cuando se importa, entonces los valores numéricos se interpretan correctamente.

## Dependencias funcionales
- No aplica

## Fuera de alcance
- Archivos `.ld` nativos de MoTeC (diferidos a post-v1.0).
- División del outing en vueltas (es [[NRM-01 - Separar las vueltas de un outing]]).

## Relacionado con
- [[Importación de telemetría]]
