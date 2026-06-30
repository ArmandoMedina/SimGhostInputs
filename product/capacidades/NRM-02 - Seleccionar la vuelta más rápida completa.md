---
tipo: capacidad
clave: NRM-02
modulo: NRM
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# NRM-02 - Seleccionar la vuelta más rápida completa

## Módulo
- [[NRM - Normalización]]

## Propósito funcional
De entre las vueltas separadas de un outing, devolver la que tiene el menor tiempo de vuelta para usarla como referencia o como vuelta del piloto en la comparación.

## Actor principal
Sistema (paso de selección automática dentro del pipeline de normalización).

## Entradas funcionales
- Lista de objetos `Lap` ya separados por [[NRM-01 - Separar las vueltas de un outing]].

## Salidas funcionales
- El objeto `Lap` con el menor tiempo total de vuelta.

## Reglas de negocio
- La selección se basa en el tiempo de vuelta calculado a partir del canal `time` de cada vuelta.
- Entre vueltas de igual tiempo, se devuelve la primera encontrada.

## Criterios de aceptación
- Dado una lista de vueltas con distintas velocidades base (y por tanto distintos tiempos de vuelta), cuando se llama a `fastest_lap`, entonces se devuelve la vuelta con el tiempo más bajo.
- Dado que la vuelta rápida está en cualquier posición de la lista (no necesariamente la primera), cuando se llama a `fastest_lap`, entonces se identifica correctamente.

## Dependencias funcionales
- [[NRM-01 - Separar las vueltas de un outing]]

## Fuera de alcance
- Remuestreo por distancia (es [[NRM-03 - Remuestrear por distancia]]).

## Verificación
- Cubierta por `tests/core/test_normalize.py` (`test_fastest_lap_picks_lowest_time`).

## Relacionado con
- [[Normalización y comparación]]
