# Decisión de diseño: Integración con CrewChief via Pace Notes

**Fecha:** 2026-06-14  
**Estado:** Aceptada · implementada (v2.0, Unreleased) · **enmendada 2026-07-09** (formato reconciliado con el fuente real de CrewChief V4)  
**Pregunta:** ¿Puede SimGhostInputs generar coaching de voz en tiempo real para el piloto sin construir un sistema de TTS propio desde cero?

> **Enmienda (2026-07-09) — el formato y el trigger descritos abajo tenían deriva; corregidos contra el código real de CrewChief V4.** La «Especificación técnica» original de este ADR se escribió desde la documentación y sin trazar el fuente. Al trazarlo (un asiento de telemetría auditó `CrewChiefV4/DriverTrainingService.cs`, repo `github.com/mrbelowski/CrewChiefV4`, branch `master`, commit `84fe63b`), tres cosas resultaron falsas:
> 1. **La estructura no es «un `metadata.json` por cue».** Es **un `metadata.json` por game/clase/pista** con un array `entries`; cada entry ES un cue (una posición en pista con sus WAV). Top-level real = **5 campos** (`description`, `gameEnumName`, `carClassName`, `trackName`, `entries`); por entry = **4 campos** (`description`, `distanceRoundTrack`, `recordingNames`, `fileNames`).
> 2. **El disparo es solo cruce de distancia.** No existe `shouldPlay()` en la ruta de pace notes, ni condición de velocidad/RPM/marcha/tiempo. Los campos `lapNumber`/`minimumSpeed`/`maximumSpeed`/`minimumYawAngle`/`maximumYawAngle`/`playAllInOrder` del ejemplo de abajo **no existen en `MetaDataEntry`**: CrewChief los descarta en silencio (son parte de nuestro superset parse-safe, **no** filtros funcionales).
> 3. **Faltaba una advertencia dura:** una entry con `recordingNames`/`fileNames` **vacías o de largo distinto revienta CrewChief en pista** (mata el hilo principal).
>
> El detalle, con citas por línea, está en la sección **[«Enmienda (2026-07-09) — reconciliación con el fuente real de CrewChief V4»](#enmienda-2026-07-09--reconciliación-con-el-fuente-real-de-crewchief-v4)** al final. **Lo que sigue vigente:** el mecanismo (pack JSON+WAV externo), el anclaje por `distanceRoundTrack` en metros desde meta, el formato WAV y toda la sección de arquitectura/tonos. Nuestro superset de ~10 campos por entry **parsea sin error** — no es el problema.

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
        [nuevo: fantasma pacenotes]
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

**Opción C:** Hacer que `fantasma pacenotes` pregunte al usuario el nombre o lo detecte del nombre de archivo de telemetría.

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

## Sistema de señales de audio — dos capas

### Fundamento fisiológico

El tiempo de reacción humano varía según el canal sensorial:
- Señal visual (HUD, pantalla): ~300 ms
- Señal de voz (frase hablada): ~250 ms — el cerebro procesa lenguaje antes de reaccionar
- Tono puro (beep): ~100–150 ms — respuesta refleja entrenada, sin procesamiento semántico

Los pilotos de rally explotan esto: el copiloto dice la nota y el piloto reacciona al patrón sonoro, no al significado. Con repetición, el tono se convierte en reflejo. En F1, algunos equipos usan pitidos para confirmación de cambios y puntos de frenada por la misma razón.

### Capa 1 — Tonos posicionales (núcleo, sin dependencias extra)

Tonos puros generados con numpy (ya dependencia del proyecto). Cada hito del `corners.json` tiene su metro exacto y su frecuencia asignada:

| Hito | Metro en `corners.json` | Frecuencia sugerida | Significado |
| :-- | :-- | :-- | :-- |
| Punto de frenada | `milestones.brake.d` | 880 Hz (agudo) | Frena ahora |
| Turn-in | `milestones.turn_in.d` | 660 Hz | Gira |
| Ápex (V-Min) | `milestones.apex.d` | 440 Hz (medio) | Ápex |
| Gas | `milestones.gas.d` | 220 Hz (grave) | Abre gas |
| Gas 100% | `milestones.gas_100.d` | 180 Hz (grave suave) | Gas completo |

El piloto aprende la escala: agudo = frena, grave = acelera. Intuitivo, sin memorizar.

**Generación del tono (sin dependencias nuevas):**
```python
import numpy as np, wave, struct

def generate_tone(freq_hz, duration_s, volume=0.8, sample_rate=24000):
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    # fade in/out de 10ms para evitar clicks
    fade = int(sample_rate * 0.01)
    envelope = np.ones(len(t))
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    samples = (np.sin(2 * np.pi * freq_hz * t) * envelope * volume * 32767).astype(np.int16)
    return samples  # → escribir como WAV 24kHz 16-bit mono
```

### Capa 2 — Voz contextual (opcional, requiere edge-tts)

Mensajes de voz que se disparan antes de llegar a la curva (100–200 m antes del punto de frenada) para dar contexto. Mientras el tono actúa como reflejo, la voz enseña.

| Cuándo | Qué dice | Para qué |
| :-- | :-- | :-- |
| 200 m antes del punto de frenada | *"Hatzenbach — frena antes"* | Preparación cognitiva |
| En el punto de frenada | tono 880 Hz | Reacción refleja |
| En el ápex | tono 440 Hz | Confirmación de posición |
| En el punto de gas | tono 220 Hz | Apertura de gas |

### Modos configurables

```
fantasma pacenotes --mode tones   # solo tonos (sin dependencias extra)
fantasma pacenotes --mode voice   # solo voz (requiere edge-tts)
fantasma pacenotes --mode both    # voz contextual + tonos en hitos exactos
```

Por defecto: `--mode tones` — máxima reacción, cero dependencias extra.

### Parámetros configurables completos

```
fantasma pacenotes \
  --corners corners.json \
  --compare salida/corners_compare.csv \
  --top 5 \                          # solo las N curvas con más pérdida
  --mode both \                      # tones | voice | both
  --lang es-MX \                     # solo relevante en mode voice o both
  --brake-freq   880 \               # Hz del tono de frenada
  --apex-freq    440 \               # Hz del tono de ápex
  --gas-freq     220 \               # Hz del tono de gas
  --tone-duration 0.12 \             # segundos por tono
  --volume 0.8 \                     # 0.0–1.0
  --milestones brake,apex,gas \      # qué hitos generar tono
  --output-dir "C:\Users\...\Documents\CrewChiefV4\pace_notes\ams2\nurburgring"
```

### Plan de implementación

**Dependencias:**
- Capa 1 (tonos): numpy — ya en el proyecto. **Sin dependencias nuevas.**
- Capa 2 (voz): `edge-tts` + ffmpeg para conversión WAV — ffmpeg ya existe

```toml
# pyproject.toml
[project.optional-dependencies]
voice = ["edge-tts"]          # pip install 'fantasma-inputs[voice]'
```

**Nuevo módulo:**
```
fantasma/
  viz/
    pacenotes.py   ← generate_tone(), generate_voice(), build_pack()
```

**Nuevo comando CLI:**
```
fantasma pacenotes --corners ... --compare ... --mode tones --top 5 --output-dir ...
```

---

## Enmienda (2026-07-09) — reconciliación con el fuente real de CrewChief V4

**Origen.** La «Especificación técnica» de arriba se redactó desde la documentación de CrewChief, no desde su código; por eso quedó como deuda registrada (#14) y no se tocaba porque, sin fuente con líneas, era indecidible. Ya no lo es: un asiento de telemetría trazó el código real. **Fuente citada:** `CrewChiefV4/DriverTrainingService.cs`, repo `github.com/mrbelowski/CrewChiefV4`, branch `master`, commit `84fe63b6e7d466022acd8bce3d00e044ded864a3`. Toda la feature de pace notes vive en ese archivo. Esto es corrección de deriva anclada a evidencia, no una decisión nueva — por eso va como enmienda in-place y no como ADR aparte.

### Estructura real del `metadata.json`

No hay «un `metadata.json` por cue». Hay **un `metadata.json` por game/clase-de-coche/pista**, con un array `entries`; **cada entry ES un cue** (una posición en pista con sus WAV).

- **Clase `MetaData`** (`DriverTrainingService.cs:355-361`) — **5 campos top-level**: `description`, `gameEnumName`, `carClassName`, `trackName`, `entries` (`List<MetaDataEntry>`). Solo `entries` participa en la reproducción; los otros cuatro son log/metadatos.
- **Clase `MetaDataEntry`** (`:411-416`) — **4 campos**: `description` (solo log), `distanceRoundTrack` (`int`, **la clave de disparo**), `recordingNames` (`List<String>`), `fileNames` (`List<String>`).

Nuestro emisor (`_write_metadata`/`_metadata_entry` en `fantasma/viz/pacenotes.py:1474`, `:1423`) ya produce esos 5 campos top-level correctos, y por entry emite un **superset** de ~10 campos (añade `lapNumber`, `minimumSpeed`, `maximumSpeed`, `minimumYawAngle`, `maximumYawAngle`, `playAllInOrder`).

### Los campos de más son parse-safe (no son el problema)

CrewChief deserializa con `JsonConvert.DeserializeObject<MetaData>` (Newtonsoft, `:69` y `:178`), **sin** `[JsonProperty]` y **sin** `JsonSerializerSettings`. Por defecto de Newtonsoft, `MissingMemberHandling.Ignore`: **los campos desconocidos se descartan en silencio** (y el match de nombres es case-insensitive). Nuestro superset **parsea sin error** — los 6 campos que CrewChief no conoce simplemente se ignoran. Conclusión que corrige el ejemplo original: `lapNumber`/`minimumSpeed`/`maximumSpeed`/`minimumYawAngle`/`maximumYawAngle`/`playAllInOrder` **no son filtros de disparo** (no existen en `MetaDataEntry`); la descripción original de `minimumSpeed`/`maximumSpeed` como «filtros opcionales para disparar solo si el coche va a cierta velocidad» es **incorrecta** — esos campos no hacen nada en CrewChief.

### Disparo: solo cruce de distancia (no hay `shouldPlay`, ni RPM/velocidad/tiempo)

El pseudocódigo `shouldPlay()` de la «Especificación técnica» **no corresponde a la ruta real**. El disparo ocurre en `checkDistanceAndPlayIfNeeded` (`:127-148`); la condición (`:133`) es el **cruce puro** de `distanceRoundTrack`:

```csharp
// DriverTrainingService.cs:133 — condición real de disparo
previousDistanceRoundTrack < entry.distanceRoundTrack
    && currentDistanceRoundTrack > entry.distanceRoundTrack
```

No hay condición de `lapNumber`, velocidad, RPM, marcha ni tiempo. **Implicación (confirma la Fase 5 / frontera estudio↔vivo):** un cue anclado a estado del motor —el cambio de marcha por RPM— **no cabe por construcción** en el pack: no existe campo donde anclarlo y el motor solo dispara por metro de pista. Esto es exactamente lo que decidió el **[ADR 0030](0030-modos-estudio-en-vivo-que-ancla-cada-cue.md)** (cues de POSICIÓN viajan en el pack; cues de ESTADO DEL COCHE no) — esa tesis queda **confirmada por el fuente**, no por autorreferencia. El cue de marcha sonoro pertenece a `fantasma-live`, fuera de este repo.

### Advertencia dura: listas de audio vacías o desalineadas = crash en pista

Este es el hallazgo operativo nuevo, y resuelve el «SIN verificar al 100 %» que el [ADR 0030](0030-modos-estudio-en-vivo-que-ancla-cada-cue.md) (consecuencias) dejó abierto sobre si el crash era alcanzable. **Lo es:**

- **Vector 1 — lista vacía.** `getRandomRecordingName` (`:433-437`) hace `recordingNames[Utilities.random.Next(recordingNames.Count)]`. Con `Count == 0`, `Random.Next(0)` devuelve `0` y `recordingNames[0]` lanza `ArgumentOutOfRangeException`. **No hay filtro** que descarte la entry muda antes: `loadPaceNotes` (`:80-94`) no la elimina, y **no hay `catch`** en la cadena hasta `CrewChief.cs::Run()` → **mata el hilo principal** de CrewChief en pista.
- **Vector 2 — listas desalineadas.** Si `recordingNames.Count != fileNames.Count`, el loop de carga revienta al indexar `fileNames[i]`.

**Regla que el pack DEBE cumplir:** por cada entry embarcada, `recordingNames` y `fileNames` **no vacías y del mismo largo**. Campos de más = seguros; listas vacías o desalineadas = crash.

**Deuda latente en nuestro emisor.** `_metadata_entry` con `filename=None` (cue mudo, p.ej. `gear`) deja `recordingNames`/`fileNames` en `[]` (`fantasma/viz/pacenotes.py:1432`). Hoy el pack **por defecto** no lleva esa entry porque `gear` sale con `enabled=False` (`DEFAULT_CONFIG`), pero un perfil de terceros que habilite un cue mudo produciría un pack que revienta CrewChief. El [ADR 0030](0030-modos-estudio-en-vivo-que-ancla-cada-cue.md) ya proscribe darle WAV a `gear`; esta enmienda añade el porqué de bajo nivel y generaliza la regla a **cualquier** entry muda. Arreglo cuando se toque el código (fuera del alcance de esta enmienda documental): no emitir la entry, o embarcar un WAV silencioso. La regla de formato queda anotada en `docs/formato-datos.md`.

## Referencias

- [Repositorio oficial GitLab (activo)](https://gitlab.com/mr_belowski/CrewChiefV4)
- **Fuente trazada (enmienda 2026-07-09):** `CrewChiefV4/DriverTrainingService.cs` @ `github.com/mrbelowski/CrewChiefV4`, branch `master`, commit `84fe63b6e7d466022acd8bce3d00e044ded864a3` — clases `MetaData` (:355-361) y `MetaDataEntry` (:411-416), disparo `checkDistanceAndPlayIfNeeded` (:127-148, cond. :133), `getRandomRecordingName` (:433-437), `loadPaceNotes` (:80-94), deserialización Newtonsoft (:69, :178)
- [Documentación oficial Pace Notes](https://mr_belowski.gitlab.io/CrewChiefV4/Speech_PaceNotes.html)
- `CrewChiefV4/sounds/pace_notes/RACE_ROOM/TC1/Macau/metadata.json` — ejemplo real de formato
- [crew-chief-autovoicepack](https://github.com/cktlco/crew-chief-autovoicepack) — referencia de formato WAV comunitaria
