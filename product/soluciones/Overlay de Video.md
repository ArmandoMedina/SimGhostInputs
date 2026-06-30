---
tipo: solucion
producto: Fantasma
estado: vigente
---

# Overlay de Video

## Propósito
Los datos solos no bastan: ver **qué hiciste en la frenada mientras ves el video** de esa frenada cambia la comprensión. Genera un HUD animado con canal alfa, sincronizado con la telemetría, y lo superpone sobre la grabación del sim — con los inputs del piloto y la referencia en simultáneo.

## Alcance
- Overlay `.webm` con canal alfa (HUD listo para cualquier editor).
- Composición automática con ffmpeg (NVENC si hay GPU NVIDIA), en un paso.
- Auto-sincronización por correlación de audio (sin contar segundos a mano).

**Fuera de alcance:** el reporte/gráficas (es la otra solución); edición de video; coaching en vivo.

## Dominios que integra
- [[Importación de telemetría]]
- [[Normalización y comparación]]
- [[Overlay y composición de video]]
- [[Sincronía audio-video]]
- [[Interfaz de usuario]]

## Flujo de valor
1. **Entrada:** telemetría del piloto + video grabado del sim.
2. **Proceso:** renderiza el HUD, detecta el offset por audio, compone.
3. **Salida:** overlay `.webm` y/o video final con el HUD integrado.

## Relacionado con
- [[Fantasma]]
- [[Análisis Post-Tanda]]
