---
tipo: modulo
clave: NRM
dominio: Normalización y comparación
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# NRM - Normalización

## Dominio
- [[Normalización y comparación]]

## Propósito del módulo
Separar las vueltas de un outing, seleccionar la más rápida completa y remuestrear los canales a una rejilla uniforme de distancia, dejando los datos listos para comparación y detección de curvas.

## Alcance
- Separación de vueltas por canal `lap_number` o beacons, con re-referenciado del tiempo a 0 en cada vuelta.
- Selección de la vuelta con menor tiempo (`fastest_lap`).
- Remuestreo a rejilla uniforme de distancia con paso configurable: interpolación lineal para canales continuos, hold (valor anterior) para canales discretos como `gear`.

**No cubre:**
- Comparación piloto vs referencia (es [[CMP - Comparación]]).
- Detección de dónde están las curvas (es [[COR - Detección de curvas e hitos]]).

## Regla funcional
El índice maestro de toda la cadena de procesamiento es la distancia, no el tiempo; el remuestreo por distancia es obligatorio antes de cualquier comparación o detección de curvas.

## Secuencia funcional
- **Módulo anterior:** [[IMP-MTC - Importador MoTeC]] / [[IMP-GEN - Importador CSV genérico]]
- **Módulo siguiente:** [[CMP - Comparación]] y [[COR - Detección de curvas e hitos]]

## Capacidades
- [[NRM-01 - Separar las vueltas de un outing]]
- [[NRM-02 - Seleccionar la vuelta más rápida completa]]
- [[NRM-03 - Remuestrear por distancia]]

## Dependencias funcionales
- [[IMP-MTC - Importador MoTeC]]
- [[IMP-GEN - Importador CSV genérico]]

## Relacionado con
- [[Normalización y comparación]]
