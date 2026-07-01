---
tipo: capacidad
clave: PAC-01
modulo: PAC
dominio: Coaching de voz
producto: Fantasma
estado: vigente
prioridad: Should Have
---

# PAC-01 - Generar pack de pace notes CrewChief

## Módulo
- [[PAC - Pace Notes CrewChief]]

## Propósito funcional
Dado un `corners.json` y una vuelta de referencia analizada, generar el pack que CrewChief reproduce en pista: `metadata.json` más los WAVs de tonos ubicados en los metros de cada curva. Ofrece dos modos: `tones` (sin dependencias extra) y `voice` (voz TTS, requiere edge-tts).

## Actor principal
El CLI (`fantasma pacenotes`), ejecutado después de `fantasma compare`.

## Entradas funcionales
- `--corners`: `corners.json` generado por `fantasma detect`, con los metros de cada hito.
- `--compare`: `corners_compare.csv` generado por `fantasma compare`, con la pérdida de tiempo y los flags por curva.
- `--mode tones|voice|both` (default `tones`).
- `--top N`: solo las N curvas con mayor pérdida de tiempo (default 5).
- `--output-dir`: destino del pack (si se omite, se resuelve el directorio de CrewChief por nombre de pista).

## Salidas funcionales
- Un directorio con `metadata.json` (formato CrewChief) y WAVs numerados por distancia y variante (`<metro>_<variante>.wav`).
- `plan.json` con el plan de señales por curva.
- En modo `voice`, WAVs de frases habladas convertidas a 24 kHz mono.

## Reglas de negocio
- El modo `tones` no requiere dependencias más allá de numpy: genera un tono por hito con su frecuencia asignada (frenada aguda, ápex media, gas grave).
- El modo `voice` requiere edge-tts; si no está instalado, se lanza un error claro con la instrucción de instalación (`pip install 'fantasma-inputs[voice]'`).
- `--top N` limita la generación a las N curvas con mayor `time_lost`; solo se consideran curvas con pérdida mayor a 0.
- Cada entrada de `metadata.json` incluye `distanceRoundTrack`, `fileNames` y `recordingNames` con el metro exacto del hito.
- Los WAV se generan a 24 kHz, mono, formato aceptado por CrewChief.

## Excepciones
- **edge-tts ausente en `--mode voice`:** error claro con la instrucción de instalación.
- **ffmpeg ausente en `--mode voice`:** se avisa y se omiten las notas de voz; el pack se escribe sin ellas.

## Criterios de aceptación
- Dado un `corners.json` válido, cuando se ejecuta `fantasma pacenotes --mode tones`, entonces se crea un directorio con `metadata.json` y WAVs numerados por el metro de cada curva.
- Dado que edge-tts no está instalado, cuando se ejecuta `--mode voice`, entonces se muestra un error claro con la instrucción de instalación.
- Dado `--top 3`, cuando hay 10 curvas con pérdida, entonces solo se generan WAVs para las 3 curvas con mayor pérdida de tiempo.
- Dado un `corners.json`, cuando se genera el pack, entonces cada entrada de `metadata.json` incluye `distanceRoundTrack`, `fileNames` y `recordingNames`.

## Dependencias funcionales
- [[COR-01 - Detectar curvas e hitos]]
- [[CMP-02 - Métricas y flags por curva]]

## Fuera de alcance
- El plan anti-saturación de señales por curva (es [[PAC-02 - Plan anti-saturacion de senales]]).

## Verificación
- Cubierta por `tests/viz/test_pacenotes.py` (`test_build_tone_pack_creates_files`, `test_metadata_json_format`).

## Relacionado con
- [[Coaching de voz]]
