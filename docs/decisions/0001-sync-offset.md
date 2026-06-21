# Decisiones de diseño: auto-detección del offset de sincronía

## Problema

Cuando el usuario graba una sesión de simracing y genera el overlay HUD con sus telemetrías,
necesita alinear temporalmente el overlay con el video: determinar cuántos segundos pasan desde
que empieza el video hasta que comienza la vuelta telemetrada.

El usuario no pudo sincronizar su video manualmente (intentó 13 s de delay — el HUD aparecía
completamente desfasado). La causa raíz fue que el offset real (~1.93 s) era difícil de estimar
a ojo, y la interfaz de Kdenlive ocultaba la complejidad del cálculo `blank − in`.

---

## Opciones evaluadas

### Opción 1 — Correlación de audio con scipy ✅ ELEGIDA

**Cómo funciona:**
1. FFmpeg extrae el audio del video como WAV mono 8 kHz.
2. Se calcula el espectrograma del audio y se promedia la energía en la banda 150–500 Hz
   (frecuencias dominantes del motor de 6 cilindros en línea del BMW M4 GT3).
3. La telemetría (RPM × peso 3.0 + velocidad × peso 1.5) se resamplea a 2 Hz y se normaliza.
4. `scipy.signal.correlate` en modo `full` da la correlación cruzada entre ambas señales.
5. El lag en el pico de correlación = offset en segundos.

**Precisión:** ±0.5 s (resolución de la correlación = 1 / _CORR_HZ = 0.5 s/muestra).

**Ventajas:**
- Funciona sin ninguna intervención manual.
- Independiente del sim, el logger y la grabadora.
- Reproducible: cualquier usuario con los mismos archivos obtiene el mismo resultado.
- Scipy no es una dependencia pesada; ya es un extra opcional (`[sync]`).

**Limitaciones:**
- Requiere audio en el video (no funciona con capturas mudas).
- La señal de audio puede ser ruidosa si hay overlay de sonido (música, voz en off).
- Precisión de 0.5 s: suficiente para uso práctico; una diferencia de 0.5 s a 150 km/h = 21 m.

**Dependencias:** `scipy>=1.11`, `numpy>=1.24`, `ffmpeg` en PATH.

---

### Opción 2 — Correlación FFT solo con numpy ❌ DESCARTADA

**Cómo funcionaría:** `numpy.fft.fft` + producto de espectros en frecuencia (correlación via FFT).

**Por qué se descartó:**
- Más portátil (numpy ya es dependencia de `[overlay]`), pero la implementación manual
  de la correlación espectral es más propensa a errores de normalización y detección de pico.
- `scipy.signal.correlate` ya usa FFT internamente para arrays grandes y está bien testeada.
- La diferencia de portabilidad no justifica la pérdida de robustez.

**Cuándo reconsiderar:** Si scipy supera 5 MB de instalación en sistemas embebidos / CI ultra-ligero.

---

### Opción 3 — OCR del velocímetro del sim en el video ❌ DESCARTADA

**Cómo funcionaría:** Detectar la región del velocímetro con OpenCV, extraer el número con
`tesseract` o `easyocr`, comparar la curva de velocidad OCR con la telemetría.

**Por qué se descartó:**
- Requiere `tesseract` + bindings Python (o `easyocr` + torch), ~1 GB de dependencias.
- Sensible a la resolución, el skin del HUD del sim, la compresión del video y las fuentes.
- Altamente dependiente del sim: cada juego posiciona el velocímetro diferente.
- El filtro de banda de audio da exactamente la misma información con 1/100 del esfuerzo.

**Cuándo reconsiderar:** Si el video no tiene audio (screen capture sin sonido del sim)
y la telemetría no tiene RPM ni velocidad (caso muy improbable).

---

### Opción 4 — Comparación de timestamps reales ❌ DESCARTADA

**Cómo funcionaría:** Leer `creation_time` del metadata del video (via `ffprobe -show_entries
format_tags=creation_time`) y compararlo con el timestamp de inicio de sesión del logger de
telemetría.

**Por qué se descartó:**
- `creation_time` no es fiable: muchas grabadoras (OBS, GeForce Experience, ShadowPlay)
  no escriben el timestamp de creación en el container MP4/MKV, o lo escriben en UTC sin
  corrección de zona horaria.
- El logger de telemetría (Sim To MoTeC) tampoco exporta el timestamp absoluto de inicio
  de sesión en el CSV; solo hay tiempo relativo desde el primer sample.
- Si ambos tienen el timestamp, funciona; pero en la práctica < 30 % de los casos.

**Cuándo reconsiderar:** Si el importer de telemetría expone un timestamp de inicio de
sesión en UTC y el video fue grabado con una cámara que escribe metadata GPS o NTP.

---

### Opción 5 — Guía manual con los campos HUD de referencia ❌ DESCARTADA como default

**Cómo funcionaría:** El HUD ya muestra marcha, velocidad (km/h) y distancia (m). El usuario
puede pausar el video en un punto reconocible (curva específica, frenada fuerte) y comparar
con la telemetría para estimar el offset.

**Por qué no es el método primario:**
- Requiere intervención manual y conocimiento del trazado.
- El usuario que motivó esta feature no pudo sincronizar ni con esta información disponible.
- La correlación de audio es más precisa y no requiere conocimiento previo del circuito.

**Cuándo es útil (fallback):** Si el video no tiene audio, si scipy no está instalado, o si
la correlación devuelve un resultado que parece incorrecto visualmente. Los campos marcha +
velocidad + distancia en el HUD fueron añadidos explícitamente para facilitar este fallback.

---

## Implementación elegida

- **Módulo:** `fantasma/viz/sync.py` — función `auto_sync(video_path, drv_lap) -> float`
- **CLI:** `fantasma compose --auto-sync --driver <tele.csv>` — calcula y aplica el offset
- **UI:** Paso 4 → expander "Detectar sincronía automáticamente" → pre-rellena el campo "Retraso del HUD"
- **Extra:** `pip install 'fantasma-inputs[sync]'` (scipy + numpy)
- **Full:** incluido en `pip install 'fantasma-inputs[full]'`

## Validación

Probado con:
- Video: grabación real de sesión AMS2, BMW M4 GT3, Nordschleife, ~70 min
- Telemetría: MoTeC CSV exportado de Sim To MoTeC (jocmaster logger)
- Offset real determinado por correlación: **1.933 s**
- Verificación visual: video de 60 s compuesto con ese offset → confirmado "perfecto" por el usuario
- El usuario no pudo encontrar el offset correcto manualmente; la correlación lo encontró automáticamente

## Limitaciones conocidas

- Resolución de 0.5 s (determinada por `_CORR_HZ = 2 Hz`). Subir a 4 Hz duplicaría la RAM usada
  por la correlación pero daría precisión de 0.25 s.
- La ventana de búsqueda es ±300 s. Si el video tiene más de 10 minutos de preámbulo antes de la
  vuelta, se puede ampliar con `_SEARCH_SEC`.
- Si el sim no exporta RPM ni velocidad (caso muy raro), la correlación falla con un mensaje claro.
