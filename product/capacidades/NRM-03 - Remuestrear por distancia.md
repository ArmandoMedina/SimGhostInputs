---
tipo: capacidad
clave: NRM-03
modulo: NRM
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# NRM-03 - Remuestrear por distancia

## Módulo
- [[NRM - Normalización]]

## Propósito funcional
Convertir los canales de una vuelta a una rejilla uniforme de distancia con paso configurable, permitiendo la comparación metro a metro entre dos vueltas.

## Actor principal
Sistema (paso previo obligatorio a comparación y detección de curvas).

## Entradas funcionales
- Objeto `Lap` con canal `dist` (y demás canales a remuestrear).
- Paso de rejilla en metros (por defecto 5.0 m).

## Salidas funcionales
- Objeto `Lap` remuestreado con puntos equiespaciados cada `step` metros desde 0.
- `lap.meta["resample_step_m"]` con el paso usado.

## Reglas de negocio
- Canales continuos (speed, throttle, brake, etc.) se interpolan linealmente entre muestras.
- Canales discretos (gear) se remuestrean por hold: cada punto toma el valor de la muestra inmediatamente anterior, nunca un valor fraccionario.
- La rejilla comienza en 0 m.

## Criterios de aceptación
- Dado una vuelta de 1000 m y un paso de 5 m, cuando se remuestrea, entonces todos los puntos de la rejilla están exactamente a 5 m de distancia del anterior y `resample_step_m` queda en 5.0.
- Dado un canal continuo con dos muestras consecutivas, cuando se remuestrea a la mitad del intervalo, entonces el valor interpolado es el punto medio entre los dos extremos.
- Dado un canal de marcha con valores enteros, cuando se remuestrea, entonces todos los valores resultantes pertenecen al conjunto de valores originales y nunca aparece un valor fraccionario.

## Dependencias funcionales
- [[NRM-02 - Seleccionar la vuelta más rápida completa]]

## Fuera de alcance
- Interpolación no lineal o suavizado (no implementado por diseño).

## Relacionado con
- [[Normalización y comparación]]
