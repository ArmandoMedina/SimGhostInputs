---
tipo: modulo
clave: PAC
dominio: Coaching de voz
producto: Fantasma
estado: vigente
prioridad: Should Have
---

# PAC - Pace Notes CrewChief

## Dominio
- [[Coaching de voz]]

## Propósito del módulo
Generar packs de audio (tonos WAV o voz TTS) para CrewChief, indexados por la distancia de cada curva en la vuelta, a partir del análisis post-tanda.

## Alcance
- Pack de tonos posicionales (modo `tones`, solo numpy): un WAV por hito de curva con su frecuencia y su metro exacto.
- Pack de voz contextual (modo `voice`, requiere edge-tts y ffmpeg): frases habladas antes de la curva según los flags del compare.
- `metadata.json` en el formato que CrewChief espera (`distanceRoundTrack`, `fileNames`, `recordingNames`) y `plan.json` con el plan de señales.
- Requiere un `corners.json` con los metros de cada hito y un `corners_compare.csv` con las pérdidas por curva.

**No cubre:**
- La detección de los hitos y sus metros (es [[COR - Detección de curvas e hitos]]).
- El cálculo de la pérdida por curva y los flags (es [[CMP - Comparación]]).

## Regla funcional
Cada señal de audio se ancla al metro exacto que el análisis ya calculó; el pack nunca inventa posiciones ni satura una curva con más señales de las que el piloto puede procesar.

## Secuencia funcional
- **Módulo anterior:** [[CMP - Comparación]]
- **Módulo siguiente:** No aplica

## Capacidades
- [[PAC-01 - Generar pack de pace notes CrewChief]]
- [[PAC-02 - Plan anti-saturacion de senales]]

## Dependencias funcionales
- [[COR - Detección de curvas e hitos]]
- [[CMP - Comparación]]

## Relacionado con
- [[Coaching de voz]]
