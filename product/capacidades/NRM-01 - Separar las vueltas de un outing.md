---
tipo: capacidad
clave: NRM-01
modulo: NRM
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# NRM-01 - Separar las vueltas de un outing

## Módulo
- [[NRM - Normalización]]

## Propósito funcional
Dividir el outing completo (telemetría de toda la sesión) en vueltas individuales, re-referenciando el tiempo de cada una a 0.

## Actor principal
Sistema (paso inicial de normalización después de importar).

## Entradas funcionales
- Objeto `Lap` con canal `lap_number` (o beacons de vuelta) que abarca toda la sesión.

## Salidas funcionales
- Lista de objetos `Lap`, uno por vuelta, con el tiempo re-referenciado a 0 en cada una.

## Reglas de negocio
- La separación usa el canal `lap_number` como criterio primario.
- El tiempo de cada vuelta se re-referencia a 0 (el primer punto de la vuelta es t=0).

## Criterios de aceptación
- Dado que un outing tiene 3 vueltas marcadas por valores distintos de `lap_number`, cuando se ejecuta `split_laps`, entonces se obtienen exactamente 3 objetos `Lap` independientes.
- Dado que las vueltas se han separado, cuando se revisa el tiempo del primer punto de cada vuelta, entonces es 0.0 en todas ellas.

## Dependencias funcionales
- [[IMP-MTC-01 - Importar CSV de MoTeC i2]] o [[IMP-GEN-01 - Importar CSV genérico con mapeo]]

## Fuera de alcance
- Selección de la vuelta más rápida (es [[NRM-02 - Seleccionar la vuelta más rápida completa]]).
- Remuestreo por distancia (es [[NRM-03 - Remuestrear por distancia]]).

## Relacionado con
- [[Normalización y comparación]]
