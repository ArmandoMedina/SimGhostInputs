# Decisión de diseño: Integración con CrewChief via Pace Notes

**Fecha:** 2026-06-14  
**Estado:** Investigado y validado — pendiente implementación (v0.8.0)  
**Pregunta:** ¿Puede SimGhostInputs generar coaching de voz en tiempo real para el piloto sin construir un sistema de TTS propio desde cero?

---

## Contexto

El objetivo era evitar construir `fantasma-live` (listener UDP + TTS + lógica de coaching en tiempo real) si CrewChief ya resuelve el problema de la voz. La hipótesis: SimGhostInputs genera archivos de configuración que CrewChief lee, entregando al piloto mensajes de coaching basados en el análisis post-sesión durante la siguiente vuelta.

---

## Investigación realizada

Se analizó el repositorio oficial de CrewChief en GitLab (`mr_belowski/CrewChiefV4`, 8.541 commits) y se encontró el mecanismo exacto.

### Lo que NO funciona: Spotter Packs

Los spotter packs son paquetes de voz para mensajes estándar del copiloto (bandera azul, rival a la derecha, pit window open). No son configurables por posición de pista externamente — no sirven para el objetivo.

### Lo que SÍ funciona: Pace Notes

`DriverTrainingService.cs` implementa un sistema de **Pace Notes** diseñado originalmente para que el piloto grabe notas de voz durante práctica y las escuche en la siguiente sesión. El formato es completamente abierto: JSON + WAV. Un programa externo puede generar exactamente esos archivos.

---

## Especificación técnica

### Estructura de directorios

```
C:\Users\[usuario]\Documents\CrewChiefV4\pace_notes\
  └── ams2\
      └── [nombre-de-pista-exacto]\
          ├── metadata.json
          ├── 1500_0.wav
          ├── 3200_0.wav
          └── ...
```

El subdirectorio de clase de coche es opcional. Sin él, los mensajes funcionan con cualquier coche en esa pista.

### metadata.json — formato completo

```json
{
  "description": "Generado por SimGhostInputs v0.8.0",
  "gameEnumName": "AMS2",
  "carClassName": "GT3",
  "trackName": "[nombre exacto que AMS2 reporta]",
  "entries": [
    {
      "description": "Hatzenbach — frenar 30m antes, pierdes 0.4s",
      "distanceRoundTrack": 1847,
      "lapNumber": null,
      "minimumSpeed": null,
      "maximumSpeed": null,
      "minimumYawAngle": null,
      "maximumYawAngle": null,
      "recordingNames": ["1847_0.wav"],
      "fileNames": ["1847_0.wav"],
      "playAllInOrder": false
    }
  ]
}
```

**Campos relevantes:**
- `distanceRoundTrack`: metros desde la meta — el mismo valor que `corners.json` de SimGhostInputs usa para `milestones.brake.d` o `milestones.apex.d`
- `lapNumber`: `null` = todas las vueltas
- `minimumSpeed` / `maximumSpeed`: filtros opcionales para disparar solo si el coche va a cierta velocidad (útil para evitar mensajes en pitlane)
- `playAllInOrder: false`: selecciona aleatoriamente entre variantes del mismo mensaje

### Trigger de posición — cómo funciona internamente

```csharp
// DriverTrainingService.cs — shouldPlay()
return previousDistanceRoundTrack < this.distanceRoundTrack
    && currentDistanceRoundTrack > this.distanceRoundTrack
    && (this.lapNumber == null || this.lapNumber == lapNumber)
    && (this.minimumSpeed == null || speed >= this.minimumSpeed)
    && (this.maximumSpeed == null || speed < this.maximumSpeed);
```

Dispara cuando el coche cruza el metro exacto. Usa la misma unidad (metros desde meta) que SimGhostInputs ya tiene en `corners.json`.

### Formato de audio WAV

- Formato: **WAV 32-bit float PCM, mono, 24.000 Hz**
- Conversión desde cualquier TTS: `ffmpeg -i input.mp3 -ar 24000 -ac 1 -sample_fmt flt output.wav`
- edge-tts (ya en el stack planeado) exporta MP3/WAV directamente

---

## Cómo SimGhostInputs genera el pack

El flujo completo con lo que ya existe en el proyecto:

```
corners.json                 → posición en metros de cada curva (milestones.brake.d)
corners_compare.csv          → tiempo perdido + descripción del problema por curva
compare.py (rows)            → delta V-Min, delta frenada, flags por curva

                    ↓
        [nuevo: fantasma pacenotess]
                    ↓

Para cada curva con time_lost > umbral:
  1. Generar frase: "En [nombre], [problema específico]. Pierdes [X] segundos."
  2. TTS con edge-tts → MP3
  3. Convertir a WAV 24kHz 32-bit float con ffmpeg
  4. Guardar como [distancia]_0.wav
  5. Agregar entry al metadata.json

Escribir todo en:
  Documents\CrewChiefV4\pace_notes\ams2\[track]\
```

### Ejemplo de frase generada

| Problema detectado | Frase de coaching |
|---|---|
| `d_brake_m > 30` (frena tarde) | "En Hatzenbach. Frena 30 metros antes. Pierdes 0.4 segundos." |
| `d_vmin < -10` (lento en ápex) | "En Schwedenkreuz. Más velocidad mínima en el ápex. Diferencia de 15 kilómetros por hora." |
| `flags: early_gas` | "En Aremberg. Espera el ápex para abrir gas. Pierdes 0.2 segundos." |

---

## Bloqueadores

### Bloqueador 1 — Nombre exacto de pista en AMS2 (único real)

CrewChief usa el string exacto que AMS2 reporta en su shared memory API (`mTrackLocation`). Ese string no está documentado para AMS2 en el repo. Opciones para obtenerlo:

**Opción A (recomendada):** Leer el shared memory de AMS2 durante una sesión. El importador de SimGhostInputs ya lee telemetría de AMS2 — el campo `Venue` del metadato MoTeC contiene el nombre de la pista exportado. Si coincide con el que AMS2 reporta a CrewChief, ya lo tenemos.

**Opción B:** Ejecutar CrewChief una vez con AMS2 en pista y leer los logs en `Documents\CrewChiefV4\`. CrewChief loguea el nombre de pista recibido.

**Opción C:** Hacer que `fantasma pacenotess` pregunte al usuario el nombre o lo detecte del nombre de archivo de telemetría.

### Bloqueador 2 — Activación manual por el piloto (no bloqueador real)

Las pace notes no se activan solas al iniciar la sesión. El piloto debe presionar un botón asignado ("Start pace notes") o decir el comando de voz. Una vez activas, funcionan automáticamente. Solución: documentar que hay que asignar el botón una vez en la configuración de CrewChief.

---

## Impacto en la arquitectura del proyecto

Este feature pertenece a **este repositorio** (`fantasma-inputs`), no a `fantasma-live`:
- Es post-sesión: corre después del análisis, no durante la conducción
- Es un output del pipeline existente: igual que genera `report.md` o `overlay.webm`, genera un pack de pace notes
- No requiere listener UDP ni conexión en tiempo real
- No requiere GPU

`fantasma-live` sigue siendo relevante para coaching adaptativo en tiempo real (reacciones a eventos que no se pueden predecir). Las pace notes resuelven el coaching planificado basado en análisis histórico.

---

## Plan de implementación

### Dependencias nuevas
- `edge-tts` (es-MX o es-ES) — TTS en español, gratuito, sin API key
- `ffmpeg` — ya es dependencia del proyecto, se reutiliza para conversión WAV

### Nueva dependencia opcional en pyproject.toml
```toml
[project.optional-dependencies]
pacenotess = ["edge-tts"]
```

### Nuevo comando CLI
```
fantasma pacenotess \
  --corners corners.json \
  --compare salida/corners_compare.csv \
  --top 5 \
  --lang es-MX \
  --output-dir "C:\Users\...\Documents\CrewChiefV4\pace_notes\ams2\nurburgring"
```

### Nuevo módulo
```
fantasma/
  viz/
    pacenotess.py   ← nuevo: genera WAV + metadata.json para CrewChief
```

---

## Referencias

- [Repositorio oficial GitLab (activo)](https://gitlab.com/mr_belowski/CrewChiefV4)
- [Documentación oficial Pace Notes](https://mr_belowski.gitlab.io/CrewChiefV4/Speech_PaceNotes.html)
- `CrewChiefV4/DriverTrainingService.cs` — implementación completa del sistema
- `CrewChiefV4/sounds/pace_notes/RACE_ROOM/TC1/Macau/metadata.json` — ejemplo real de formato
- [crew-chief-autovoicepack](https://github.com/cktlco/crew-chief-autovoicepack) — referencia de formato WAV comunitaria
