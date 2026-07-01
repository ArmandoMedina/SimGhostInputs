---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Coaching de voz

## Producto
- Fantasma

## Propósito
Entregar salida de audio sincronizada a los metros de la vuelta para coaching en tiempo real durante las sesiones en pista. Permite al piloto escuchar señales de frenada, vértice y aceleración sin apartar la vista del circuito.

## Alcance
- Packs de audio (tonos WAV o voz TTS) indexados por distancia en la vuelta, listos para CrewChief.
- Señales posicionales por hito de curva: frenada, turn-in, ápex, gas.
- Plan anti-saturación que acota cuántas señales suenan por curva.

**Fuera de alcance:** el análisis que produce los metros y las pérdidas por curva (es [[Detección de curvas e hitos]] y [[Normalización y comparación]]); el coaching adaptativo en tiempo real vía UDP (será `fantasma-live`, repo separado).

## Módulos
- [[PAC - Pace Notes CrewChief]]

## Relacionado con
- [[PAC - Pace Notes CrewChief]]
- [[Análisis Post-Tanda]]
- [[Detección de curvas e hitos]]
