# Roadmap — SimGhostInputs

> Estado vivo del proyecto. Cada versión tiene su lista de cambios y su checklist de QA antes de publicarse. El criterio para cerrar una versión es que **todos** los puntos de QA estén verificados con telemetría real.

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md)

---

## Estado actual — v0.4.0 + [Unreleased]

El código en `master` incluye cambios sin versionar aún. El próximo release es **v0.5.0**.

---

## v0.5.0 — Estabilidad de UI y cierre del análisis offline
> _Estado: en progreso — pendiente QA_

Agrupa todos los fixes del bloque `[Unreleased]` más las correcciones de esta sesión de desarrollo.

### Cambios incluidos
- [x] `fix(ui)` Charts en Paso 2: caché en `session_state`, errores visibles fuera del spinner
- [x] `fix(__version__)` Corregido de `0.2.0` a `0.4.0` → `0.5.0` al cerrar este release
- [x] `feat(compose)` NVENC automático con fallback a libx264
- [x] `fix(overlay)` Render paralelo funciona en UI via `subprocess.Popen`
- [x] `feat(overlay)` ffmpeg progress en tiempo real con `-progress pipe:1`
- [x] `feat(overlay)` VP9 multithreading con `-row-mt 1 -threads N`
- [x] `fix(sync)` `RuntimeError` cuando correlación z < 3.0σ
- [x] `fix(overlay)` Canales opcionales ausentes son `None`, no zeros

### QA antes de publicar v0.5.0

**Flujo de análisis (CLI)**
- [ ] `fantasma laps archivo.csv` — detecta vueltas y muestra tiempos correctamente
- [ ] `fantasma detect referencia.csv -o salida/` — genera `corners_detected.json` sin errores
- [ ] `fantasma compare --reference ref.csv --driver piloto.csv -o salida/` — genera los 5+ charts y `report.md`
- [ ] Verificar que los charts se generan aunque falten canales opcionales (glat, glong, gear)
- [ ] `fantasma compare` con CSV sin columna de marcha — no crashea, overlay muestra «N»

**Charts en UI (Paso 2) — el fix principal de esta versión**
- [ ] Cargar ref + piloto → ir al Paso 2 → las 5 gráficas aparecen sin interacción adicional
- [ ] Hacer scroll / interactuar con cualquier widget en Paso 2 → las gráficas siguen visibles (no desaparecen)
- [ ] Presionar «Recalcular» → spinner → nuevas gráficas reemplazan las anteriores
- [ ] Instalar sin matplotlib → aparece `st.info()` visible (no spinner vacío)
- [ ] Simular error en `render_charts` → aparece `st.error()` visible tras cerrar el spinner

**Overlay (CLI)**
- [ ] `fantasma overlay --reference ref.csv --driver piloto.csv -o salida/` — genera `overlay.webm`
- [ ] Barra de progreso refleja avance real de ffmpeg (no se congela al 99%)
- [ ] `fantasma overlay --all-laps` — genera subcarpetas `lap_00/`, `lap_01/`...
- [ ] Abrir `overlay.webm` en VLC — canal alfa visible, HUD animado correctamente

**Compose (CLI)**
- [ ] `fantasma compose --video grabacion.mp4 --overlay overlay.webm -o resultado.mp4` — genera video final
- [ ] Con GPU NVIDIA disponible: log confirma uso de `h264_nvenc`
- [ ] Sin GPU NVIDIA: fallback a `libx264` sin errores
- [ ] `fantasma compose --auto-sync` con video que corresponde a la vuelta — detecta offset
- [ ] `fantasma compose --auto-sync` con video que NO corresponde — lanza `RuntimeError` claro
- [ ] `fantasma compose --auto-sync` con video completo Nordschleife (~6 min) — documentar comportamiento real y bugs encontrados (insumo para v0.9.0)

**UI completa (Paso 0 → 4)**
- [ ] Flujo «📊 Solo análisis» (0→1→2): completa sin errores
- [ ] Flujo «🎬 Solo overlay» (0→1→3): completa sin errores
- [ ] Flujo «🎥 Video con HUD» (0→1→3→4): completa sin errores
- [ ] Botón «Detectar offset» en Paso 4: se prerellena el campo «Retraso del HUD»

---

## v0.6.0 — Histórico entre sesiones
> _Estado: por construir_

Permite comparar el rendimiento en una misma curva a lo largo de varias tandas. El piloto puede ver si progresa, retrocede o tiene un techo de mejora en una curva específica.

### Cambios previstos
- [ ] Modelo de datos para almacenar resultados de sesiones (`SessionHistory`)
- [ ] `fantasma history add` — registra los resultados de un `compare` en el histórico local
- [ ] `fantasma history show --corner "Hatzenbach"` — evolución de V-Min y tiempo perdido en esa curva
- [ ] Gráfica de tendencia por curva: eje X = fechas de sesión, eje Y = tiempo perdido
- [ ] UI — Paso nuevo opcional «Histórico»: tabla + gráfica de tendencia por curva
- [ ] Almacenamiento: SQLite local (sin servidor, sin cloud) o directorio de JSONs — decidir

### QA antes de publicar v0.6.0
- [ ] Registrar 3 sesiones distintas y verificar que el histórico acumula correctamente
- [ ] `fantasma history show` sin sesiones previas — mensaje claro, sin crash
- [ ] Importar sesión antigua (CSV del piloto ya procesado) al histórico
- [ ] Gráfica de tendencia con una sola sesión — no crashea, mensaje informativo
- [ ] Migración: si el esquema de almacenamiento cambia entre versiones, migrar datos existentes

---

## v0.7.0 — Nuevos importadores
> _Estado: por construir_

Elimina la dependencia de MoTeC i2 como intermediario para algunos formatos.

### Cambios previstos
- [ ] Importador `.ld` nativo (formato binario MoTeC) — sin necesidad de exportar CSV desde i2
- [ ] Importador iRacing `.ibt` — lectura directa del archivo de telemetría de iRacing
- [ ] Ampliar `GUESS` dict en `generic_csv.py` para cubrir exports de SimHub y ACC CSV
- [ ] Ampliar `MOTEC_MAP` con variantes de columnas detectadas en ACC, iRacing y rF2 vía sim-to-motec
- [ ] Docs: guía de compatibilidad por sim (qué canales exporta cada uno, qué queda como None)

### QA antes de publicar v0.7.0
- [ ] Importar `.ld` de AMS2 directamente — mismo resultado que vía CSV exportado
- [ ] Importar `.ibt` de iRacing — detección de vueltas y canales básicos funcionan
- [ ] CSV de SimHub para AMS2 — auto-detectado sin `--map`
- [ ] CSV de ACC vía sim-to-motec — importado correctamente con degradación graceful en ABS/TCS
- [ ] Tabla de compatibilidad en README actualizada con estado real probado

---

## v1.0.0 — Primera versión estable
> _Estado: objetivo a largo plazo_

El criterio para v1.0 es que el pipeline offline esté completo, documentado y probado con más de un sim y más de un circuito. No es una versión con features nuevas — es una declaración de estabilidad de API.

### Requisitos para llamarla v1.0
- [ ] Todas las fases anteriores (v0.5, v0.6, v0.7) completadas y en producción
- [ ] API interna (`core/`) estabilizada — sin cambios breaking entre parches
- [ ] Docs completas: guía de usuario, referencia de HUD, formato de datos, cómo contribuir
- [ ] Probado con al menos 2 sims (AMS2 + uno más) y al menos 3 circuitos distintos
- [ ] `setup.ps1` probado en instalación limpia de Windows 11
- [ ] No hay `[Unreleased]` acumulado en CHANGELOG

---

## v0.8.0 — Coaching de voz via CrewChief Pace Notes
> _Estado: investigado y validado — pendiente implementación_

**Hallazgo clave (2026-06-14):** CrewChief tiene un sistema nativo llamado **Pace Notes** que reproduce archivos WAV en metros exactos de la pista. SimGhostInputs ya tiene esos metros en `corners.json`. La integración es generar los archivos correctos — sin modificar CrewChief, sin construir un sistema de voz propio.

Ver especificación completa: [`docs/decisions-crewchief-pacenotes.md`](docs/decisions-crewchief-pacenotes.md)

### Cómo funciona
1. `fantasma compare` genera el análisis: qué curvas, cuánto tiempo, qué problema específico
2. `fantasma pacenotess` lee ese análisis y genera:
   - Frases en español con edge-tts → MP3 → WAV (24kHz, 32-bit float)
   - `metadata.json` con el metro exacto de cada curva (del `corners.json` existente)
3. Los archivos se escriben en `Documents\CrewChiefV4\pace_notes\ams2\[pista]\`
4. El piloto activa las pace notes con un botón antes de salir del pit — CrewChief habla en el momento exacto

### Dos capas de audio (ver spec completa en `docs/decisions-crewchief-pacenotes.md`)

**Capa 1 — Tonos posicionales** (núcleo, sin dependencias nuevas)
Tonos puros generados con numpy. Cada hito del `corners.json` tiene su metro y su frecuencia:
- Punto de frenada → 880 Hz (agudo, urgente)
- Ápex → 440 Hz (medio)
- Gas → 220 Hz (grave, suave)

El piloto aprende la escala como reflejo entrenado. Reacción ~100ms vs ~300ms visual.

**Capa 2 — Voz contextual** (opcional, requiere edge-tts)
Frases 200m antes del punto de frenada para dar contexto. La voz enseña, el tono actúa.

**Modos:** `--mode tones` (default) | `--mode voice` | `--mode both`

### Cambios previstos
- [ ] Nuevo módulo `fantasma/viz/pacenotess.py`
  - `generate_tone(freq, duration, volume)` → WAV 24kHz con numpy (sin dependencias extra)
  - `generate_voice(text, lang)` → WAV via edge-tts + ffmpeg
  - `build_pack(rows, corners, outdir, config)` → metadata.json + todos los WAV
- [ ] Nuevo comando CLI `fantasma pacenotess --corners --compare --mode --top --output-dir`
- [ ] Parámetros de tono configurables: `--brake-freq`, `--apex-freq`, `--gas-freq`, `--tone-duration`, `--volume`
- [ ] Frases de voz basadas en flags de `compare.py` (`late_brake`, `early_gas`, `d_vmin`)
- [ ] Nueva dependencia opcional: `edge-tts` → `pip install 'fantasma-inputs[voice]'`
- [ ] Resolución del nombre de pista AMS2 — detectar del campo `Venue` del CSV o pedir al usuario

### QA antes de publicar v0.8.0
- [ ] `--mode tones`: genera metadata.json + WAV de tonos sin instalar edge-tts
- [ ] Tonos suenan en los metros correctos en una sesión real en Nordschleife
- [ ] Escala de frecuencias distinguible sin confusión: agudo ≠ medio ≠ grave
- [ ] `--mode voice`: genera frases coherentes con el problema detectado por curva
- [ ] `--mode both`: voz 200m antes + tono en metro exacto, sin solapamiento
- [ ] `--top 3`: solo las 3 curvas con más pérdida generan audio
- [ ] `--volume 0.3`: tonos audibles pero no intrusivos junto al audio del sim
- [ ] Sin `edge-tts` con `--mode voice`: error claro con instrucción de instalación
- [ ] Nombre de pista incorrecto: CrewChief no carga el pack — documentar cómo encontrar el nombre correcto
- [ ] WAV generados en formato aceptado por CrewChief: 24kHz, mono (verificar con ffprobe)

---

## v0.9.0 — Sincronización robusta y flujos múltiples en UI
> _Estado: por construir — requiere audit de v0.5.0_

**Decisión de arquitectura:** `compose` y `compare` procesan una vuelta por ejecución. La UI facilita encadenar múltiples flujos sin repetir el proceso manualmente.

### Contexto
El `auto_sync` actual produce un overlay o aborta con `RuntimeError` si z < 3.0σ, pero no informa al usuario qué tan bien sincronizado está ni por qué falló. Con vueltas largas (Nordschleife ~6 min) los casos de fallo son más frecuentes y menos obvios. Si el usuario pausó durante la vuelta, el offset calculado es inválido y el resultado silencioso es peor que un error.

### Cambios previstos

**Detección de pausa en la vuelta**
- [ ] Detectar discontinuidades en el audio del video durante la vuelta seleccionada (silencio/salto)
- [ ] Abortar con error claro: "Pausa detectada en X:XX — vuelta no sincronizable. Usa un video sin pausas."
- [ ] No intentar re-sincronizar post-pausa (telemetría y video divergen irrecuperablemente)

**Métrica de calidad de sync**
- [ ] Mostrar siempre el resultado de sync: `Sync quality: 94% (z=4.7σ, offset=+1.23s) ✓`
- [ ] Umbral mínimo configurable: `--min-sync-quality` (default: 3.0σ, equivalente al actual)
- [ ] Si cae bajo el umbral: error explícito con el valor obtenido vs el requerido
- [ ] En UI: badge de calidad de sync visible tras compose exitoso

**UI — flujos múltiples**
- [ ] Botón «Procesar otra vuelta» al finalizar un flujo — reinicia desde Paso 1 sin cerrar la app
- [ ] Lista de vueltas procesadas en la sesión actual: vuelta, archivo de salida, sync quality
- [ ] Scope de `compare` y `compose` acotado a una vuelta por ejecución (claridad en la UI)

### QA antes de publicar v0.9.0
- [ ] Video Nordschleife completo (~6 min): sync correcto, offset preciso, badge de calidad visible
- [ ] Video con pausa en el minuto 3: error claro con timestamp de la pausa detectada
- [ ] `--min-sync-quality 4.5`: video que pasa 3.0σ pero falla 4.5σ → error con valores mostrados
- [ ] Procesar 3 vueltas en secuencia desde UI sin cerrar: cada una genera su clip y su badge
- [ ] Lista de vueltas procesadas refleja los 3 clips con sus métricas de sync

---

## Fuera de este repositorio — fantasma-live
> _Repo separado, solo si Pace Notes no cubre el caso de uso_

Con la integración de Pace Notes (v0.8.0), el coaching planificado basado en análisis histórico queda cubierto en este repo. `fantasma-live` quedaría para coaching **adaptativo en tiempo real** — reacciones a eventos que no se pueden predecir de antemano (trompo, contacto, condiciones cambiantes de pista).

### Cuándo tiene sentido construirlo
Solo si después de usar Pace Notes el piloto necesita algo que éstas no pueden dar: coaching que reacciona a lo que pasa en esa vuelta específica, no a lo que pasó en sesiones anteriores.

### Fases tentativas (sujetas a revisión tras experiencia con v0.8.0)
| Fase | Objetivo |
| :-- | :-- |
| 3.1 | Listener UDP para AMS2 — captura telemetría en tiempo real a 60 Hz |
| 3.2 | Comparador en vivo — delta continuo por curva vs referencia |
| 3.3 | Motor de voz adaptativo — TTS con edge-tts, latencia <200ms |
| 3.4 | Modos de coaching — Aprendizaje / Qualy / Carrera |

---

## Gaps técnicos identificados

Cosas que están en el código pero no tienen cobertura de QA formal ni están documentadas:

| Gap | Descripción | Prioridad |
| :-- | :-- | :-- |
| Test de degradación por canales ausentes | No hay prueba sistemática de qué pasa cuando faltan glat, glong, gear, abs, tcs en distintas combinaciones | Alta |
| Comportamiento con vueltas muy cortas | ¿Qué pasa si el piloto sale de pista y la vuelta tiene solo 500 m? | Media |
| CSV con separador de punto y coma | `motec_csv.py` usa `csv.reader` con separador coma por defecto. Algunos exports europeos usan `;` | Media |
| Circuitos con vuelta que cruza la línea de meta más de una vez | Circuitos en 8 o con chicane en meta podrían romper la detección de vueltas | Media |
| Overlay con FPS distintos al de la grabación | Si el usuario elige 30 fps en el overlay pero graba a 60 fps, la composición puede quedar desincronizada | Alta |
| `fantasma compose` sin ffmpeg instalado | El error actual puede no ser claro para el usuario — mejorar mensaje | Baja |
| Versión mínima de Python no declarada | `pyproject.toml` debería declarar `requires-python` — testeado internamente en 3.10+ | Media |

---

## Deuda técnica conocida

| Item | Descripción |
| :-- | :-- |
| `__version__` en `__init__.py` | Debe actualizarse manualmente en cada release — candidato a automatizar con `bumpversion` o similar |
| `motec_csv.py` codificación | Lee con `utf-8-sig` — CSV generados por i2 en Windows pueden tener encoding distinto en setups no-inglés |
| Sin tests automáticos | No hay suite de tests. Todo el QA es manual con telemetría real. Para v1.0 debería haber al menos tests unitarios de `core/` |
| Docs en `docs/` referenciadas pero no escritas | El README menciona `docs/guia-usuario.md`, `docs/hud-reference.md`, `docs/formato-datos.md` — no existen aún |

---

_Última revisión: 2026-06-14 — añadida v0.9.0 sincronización robusta y flujos múltiples en UI; decisión: compose y compare acotados a una vuelta por ejecución_
