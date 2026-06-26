# Roadmap — SimGhostInputs

> Estado vivo del proyecto. Cada versión tiene su lista de cambios y su checklist de QA antes de publicarse. El criterio para cerrar una versión es que **todos** los puntos de QA estén verificados con telemetría real.
>
> **Para retomar en frío** (dónde va y qué sigue): lee «Estado actual» y «▶️ Para la próxima sesión» aquí abajo. El **porqué** de cada decisión vive en [`docs/decisions/`](docs/decisions/README.md); qué documentos tocar al hacer un cambio, en [`CONTRIBUTING.md` §8](CONTRIBUTING.md#8-mantenimiento-de-documentación).

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md)

---

## Estado actual — v0.9.0

Último release: **v0.9.0** (2026-06-22) — campo **GASTO** en el HUD del overlay: desgaste acumulado *de la vuelta* (carga de deslizamiento, ADR 0009), distinto del DESLIZ instantáneo; `fantasma wear` migrado a la misma carga extensiva. Además: **glosario** del proyecto, **matriz de mantenimiento de docs** (CONTRIBUTING §8), ADRs 0004/0005 enmendados y 0009 nuevo, y regla operativa de pruebas. _GASTO pendiente de QA con video real._ Previo: **v0.8.0** (auto-sync multi-vuelta, ADR 0008), **v0.7.x** (`fantasma wear`, ADR 0004–0007, `setup.ps1`), **v0.6.6** (suite de tests + CI, requisito de "tests unitarios de `core/`" cubierto).

> **Nota de numeración:** los números de versión **reales** (CHANGELOG/tags, ahora en v0.9.0) y las etiquetas de *hito* del «camino a v1.0» de abajo (v0.5.0, 0.6.x, «v0.9.0»…) son **dos esquemas distintos que ya divergieron** — manda el CHANGELOG. Los hitos conceptuales se renumerarán cuando se retomen.

El **drill-down por curva** (antes hito «v0.10.0») se difiere a post-1.0. Eso reenfoca la 1.0: ya no es "construir una feature nueva primero", sino **estabilizar, testear, documentar y validar en AMS2 el pipeline offline que ya existe**. El camino a la 1.0 es ahora mayormente QA manual + cierre de release.

> **▶️ Para la próxima sesión (Armando):** revisar **meticulosamente el overlay y la UI** buscando detalles visuales y de usabilidad por pulir. Incluye verificar si hay desync real de FPS con un video de 60 fps (ver gaps técnicos — el análisis de código dice que NO debería desincronizar; falta confirmarlo con video real). Con eso + el QA de AMS2 (≥3 circuitos) + `setup.ps1` en Windows limpio, se corta la 1.0.

### Camino a v1.0 (AMS2)

| Versión | Foco | Estado |
| :-- | :-- | :-- |
| v0.5.0 | Estabilidad UI, NVENC, auto_sync robusto | ✅ publicado |
| 0.6.x | UI, NVENC real, sync robusto, suite de tests + CI | ✅ publicado |
| v0.9.0 | Sincronización robusta + flujos múltiples en UI | ✅ entregada en 0.6.x (extras descartados/diferidos) |
| v1.0.0 | Estabilizar, testear, documentar y validar el pipeline offline en AMS2 | objetivo |

El drill-down por curva (antes v0.10.0), v0.6.0 (histórico entre sesiones), v0.7.0 (importadores) y v0.8.0 (Pace Notes) quedan diferidos para después de v1.0. (Nota: los números 0.6.x/0.10.0 ya quedaron desfasados respecto a los releases reales; se renumerarán cuando se retomen.)

> **Orden de este documento:** primero las versiones del **camino a la 1.0** (en orden de entrega), luego las **diferidas a post-1.0**, y al final los temas **transversales** (gaps técnicos y deuda).

---

# ▶️ Camino a la v1.0

---

## v0.5.0 — Estabilidad de UI y cierre del análisis offline
> _Estado: publicado — 2026-06-14_

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

## v0.9.0 — Sincronización robusta y flujos múltiples en UI
> _Estado: **completa** — el contenido se entregó en la tanda 0.6.0. Los extras (umbral configurable, lista de vueltas) se descartan/difieren; ver abajo._

**Decisión de arquitectura:** `compose` y `compare` procesan una vuelta por ejecución. La UI facilita encadenar múltiples flujos sin repetir el proceso manualmente.

### Contexto
El `auto_sync` actual produce un overlay o aborta con `RuntimeError` si z < 3.0σ, pero no informa al usuario qué tan bien sincronizado está ni por qué falló. Con vueltas largas (Nordschleife ~6 min) los casos de fallo son más frecuentes y menos obvios. Si el usuario pausó durante la vuelta, el offset calculado es inválido y el resultado silencioso es peor que un error.

### Cambios previstos

**Detección de pausa en la vuelta** ✅ (en 0.6.0)
- [x] Detectar discontinuidades en el audio del video durante la vuelta seleccionada (silencio/salto) — `sync._detect_pause`
- [x] Abortar con error claro: "Pausa detectada en X:XX…" — `sync.auto_sync` lanza `RuntimeError` con timestamp
- [x] No intentar re-sincronizar post-pausa (telemetría y video divergen irrecuperablemente)

**Métrica de calidad de sync**
- [x] Mostrar el resultado de sync: CLI imprime offset + z σ; UI muestra badge de calidad
- [~] ~~Umbral mínimo configurable: `--min-sync-quality`~~ → **descartado**. El único caso que justificaría bajar el umbral (auto-sync rechaza un video legítimo, p. ej. coche eléctrico sin banda de motor) ya está cubierto por el **offset manual** existente (`step4.py` «Sincronizar manualmente»). Sería una perilla para un problema ya resuelto.
- [x] Si cae bajo el umbral: error explícito — `auto_sync` lanza si z < 3.0σ
- [x] En UI: badge de calidad de sync visible — `_sync_quality_label` (Excelente / Muy bueno / Bueno / Marginal)

**UI — flujos múltiples**
- [x] Botón «Procesar otra vuelta» al finalizar un flujo — reinicia desde Paso 1 sin cerrar la app
- [~] ~~Lista de vueltas procesadas en la sesión actual~~ → **diferido a post-v1.0** (comodidad, no corrección; ver abajo)
- [x] Scope de `compare` y `compose` acotado a una vuelta por ejecución (radio buttons, una vuelta por diseño)

### QA antes de publicar v0.9.0 (validación con video real — QA manual)
- [ ] Video Nordschleife completo (~6 min): sync correcto, offset preciso, badge de calidad visible
- [ ] Video con pausa en el minuto 3: error claro con timestamp de la pausa detectada

### Diferido a post-v1.0
- **Lista de vueltas procesadas en la sesión** (vuelta + archivo de salida + sync quality acumulados en una tabla): es conveniencia para quien procesa varias vueltas seguidas sin cerrar la app. El producto funciona sin ella; se separa para no bloquear la 1.0.

---

## v1.0.0 — Primera versión estable (AMS2)
> _Estado: objetivo a largo plazo_

El criterio para v1.0 es que el pipeline offline esté completo, documentado y probado. Alcance declarado: **AMS2 únicamente**. Importadores adicionales (iRacing, rF2, ACC) y features post-tanda avanzadas (drill-down por curva, histórico, pace notes) van después.

### Requisitos para llamarla v1.0
- [x] v0.9.0 completada y en producción (el drill-down se difiere a post-1.0)
- [x] Suite de tests automatizados de `core/` + CI (cumple el requisito de "tests unitarios de core/")
- [ ] API interna (`core/`) estabilizada — sin cambios breaking entre parches (revisión, no código nuevo)
- [x] Docs completas: guía de usuario, referencia de HUD, formato de datos, cómo contribuir, **glosario**. Repasadas y al día a **v0.9.0** (matriz de mantenimiento de docs en `CONTRIBUTING.md` §8); la referencia de HUD incluye **leyenda visual** (`docs/demo/hud-leyenda.png`) y el campo **GASTO**.
- [x] **Decidir si los gaps `Alta` bloquean la 1.0** → **NO bloquean** (2026-06-21). El FPS≠grabación se investigó y no reproduce desync (bajado a Baja). El único gap `Alta` que queda es `--format prores`, **ya mitigado** con el default `webm`: no afecta el uso normal, solo a quien pida prores explícitamente. Se difiere a post-1.0.
- [ ] 👤 Probado con AMS2 en al menos 3 circuitos distintos — **1/3: Nordschleife ✓** (carrera M4 GT3, 9 vueltas, 2026-06-21): el pipeline completo corrió con datos frescos (laps → wear → overlay) sin errores; el overlay confirmó frenadas más fuertes vs sesión previa. Sin conclusiones aún. **Faltan Interlagos y México**, que se eligieron para cubrir clases de auto distintas al GT3 ya probado (fórmula y prototipo) y así ejercitar el pipeline con perfiles de telemetría diferentes; falta conseguir esas 2 telemetrías.
- [ ] 👤 `setup.ps1` probado en instalación limpia de Windows 11 — **en curso** (Armando lo prueba en otra PC con el release v0.7.1).
- [ ] No hay `[Unreleased]` acumulado en CHANGELOG (cortar el release)

> **Hallazgo de QA a refinar (no bloquea 1.0):** el medidor de desgaste (ADR 0004) usa umbrales de **vida total de goma**, pero en el QA real las gomas no llegaron al amarillo porque **el tanque se acaba antes**. Si se repite, el espectro útil no es "vida restante" sino **degradación de rendimiento dentro del stint** / relativo al combustible. Recopilar más datos antes de rediseñar. Detalle en ADR 0004 §Consecuencias.
>
> **Decidido (2026-06-22):** el desgaste acumulado se muestra en **dos vistas** (enmienda ADR 0004/0005; unidad en ADR 0009). **(1) HUD del overlay** — acumulado *de la vuelta* (campo **GASTO**, carga de deslizamiento, piloto vs ref, *además* del DESLIZ instantáneo): **✅ implementado en v0.9.0**. **(2) Gráficas (Producto 1)** — acumulado de *stint* entre vueltas: **⏳ pendiente** (hoy solo en `fantasma wear`, CLI). Detectado al sacar el video del overlay: el DESLIZ se veía "reiniciar" por curva (es instantáneo por diseño) y faltaba el medidor acumulable en el HUD.

---

# ⏸️ Diferido — post-v1.0

> Fuera del alcance de la 1.0 (solo AMS2). Se retoman después de declarar estable el pipeline offline.

---

## v2.0 — Front de escritorio custom (evaluación)
> _Estado: a evaluar post-v1.0. Decisión de fondo registrada en [ADR 0010](docs/decisions/0010-framework-ui-streamlit.md)._

La UI de v1.0 es Streamlit (ADR 0010). Se difiere a v2.0 **evaluar** migrar a un front
custom, por dos límites reales de Streamlit detectados en desarrollo: **(1) personalización**
del front topada, y **(2) fricción de instalación** — Streamlit no es doble-click, exige
Python + terminal + `setup.ps1`. **No es una migración decidida: es una evaluación con gatillo.**

> **Restricción heredada del ADR 0010:** mantener `core/` **desacoplado** de la UI (eso mantiene
> plano el costo de migrar) y, durante v1.0, preferir tests **a prueba de migración** (AppTest de
> flujos + snapshot de imagen del HUD) sobre Playwright-sobre-Streamlit, que se tiraría al migrar.

### Qué evaluar antes de comprometerse
- [ ] 🔬 **Benchmark de herramientas** (usa la skill `benchmark-opciones`): comparar lo que ya
  usamos (Streamlit, `streamlit.testing.AppTest`) **y opciones nuevas** que sirvan para lo que se
  necesita —front testeable + personalizable + **instalación doble-click**—. Candidatos a comparar:
  - **Shell de escritorio empaquetado** (Tauri, pywebview, Electron) → da `.exe` de doble-click.
  - **Web-en-navegador con servidor local** (FastAPI + front JS) → se compara, pero **parte en
    desventaja**: no quita la fricción de instalación (ADR 0010, camino descartado).
  - **Escape hatches de Streamlit** (CSS custom, `st.components.html`, componentes custom) → ¿destraban
    la personalización sin migrar? Si sí, la migración podría no hacer falta.
  - **Playwright** para el front nuevo (markup controlado, donde sí es estable) — no para Streamlit.
- [ ] **Experimento barato de personalización:** probar los escape hatches de Streamlit en la pantalla
  que más duele, para decidir *con evidencia* si migrar siquiera hace falta.
- [ ] Con el benchmark resuelto, **registrar la arquitectura elegida como ADR nuevo** (hoy NO está
  decidida; el ADR 0010 solo fija que se difiere y con qué restricciones).

---

## Drill-down por curva (era v0.10.0)
> _Estado: diferido — post-v1.0. Spec en [PRODUCT_BRIEF.md § 10](PRODUCT_BRIEF.md)_

Convierte la tabla de tiempo perdido en coaching accionable. El piloto pica en una curva y ve exactamente qué corregir, calculado desde los datos sin LLM. Se difiere porque la 1.0 prioriza estabilizar y validar el pipeline que ya existe, no añadir features.

### Cambios previstos
- [ ] Tabla de curvas clickeable en UI Paso 2 — click en una fila abre panel de detalle
- [ ] Panel de detalle por curva: Δ frenada (metros), Δ intensidad de freno, progresividad, V-Min target, Δ gas, Δ G-lat, marcha/RPM
- [ ] Síntesis en lenguaje natural: "Frenas 40 m antes con 15% menos intensidad → llegas 8 km/h más lento al ápex → pierdes 0.6 s" — aritmética pura sobre `corners_compare.csv`
- [ ] Función `corner_coaching(row, trace)` en `core/` que produce el dict de coaching
- [ ] Los datos ya existen en `trace` y `rows` de `compare()` — no requiere nueva telemetría

### QA antes de publicar
- [ ] Click en la curva con mayor pérdida → panel de detalle visible con todos los campos
- [ ] Curva sin canal gear → panel omite el campo de marcha sin crashear
- [ ] Curva sin glat → panel omite G-lat sin crashear
- [ ] Síntesis en lenguaje natural coherente con los números del panel
- [ ] Curva donde el piloto es más rápido → mensaje positivo ("ganas X s aquí")

---

## v0.6.0 — Histórico entre sesiones
> _Estado: diferido — post-v1.0_

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
> _Estado: diferido — post-v1.0 (v1.0 cubre solo AMS2)_

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

## v0.8.0 — Coaching de voz via CrewChief Pace Notes
> _Estado: diferido — post-v1.0 (investigado y validado, spec completa disponible)_

**Hallazgo clave (2026-06-14):** CrewChief tiene un sistema nativo llamado **Pace Notes** que reproduce archivos WAV en metros exactos de la pista. SimGhostInputs ya tiene esos metros en `corners.json`. La integración es generar los archivos correctos — sin modificar CrewChief, sin construir un sistema de voz propio.

Ver especificación completa: [`docs/decisions/0002-crewchief-pacenotes.md`](docs/decisions/0002-crewchief-pacenotes.md)

### Cómo funciona
1. `fantasma compare` genera el análisis: qué curvas, cuánto tiempo, qué problema específico
2. `fantasma pacenotess` lee ese análisis y genera:
   - Frases en español con edge-tts → MP3 → WAV (24kHz, 32-bit float)
   - `metadata.json` con el metro exacto de cada curva (del `corners.json` existente)
3. Los archivos se escriben en `Documents\CrewChiefV4\pace_notes\ams2\[pista]\`
4. El piloto activa las pace notes con un botón antes de salir del pit — CrewChief habla en el momento exacto

### Dos capas de audio (ver spec completa en `docs/decisions/0002-crewchief-pacenotes.md`)

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

# 🔧 Transversal

---

## Gaps técnicos identificados

Cosas que están en el código pero no tienen cobertura de QA formal ni están documentadas:

| Gap | Descripción | Prioridad |
| :-- | :-- | :-- |
| Test de degradación por canales ausentes | No hay prueba sistemática de qué pasa cuando faltan glat, glong, gear, abs, tcs en distintas combinaciones (parcialmente cubierto ya por la suite de tests) | Media |
| Comportamiento con vueltas muy cortas | ¿Qué pasa si el piloto sale de pista y la vuelta tiene solo 500 m? | Media |
| ~~CSV con separador de punto y coma~~ ✅ | Resuelto: `importers/_util.py` detecta el separador (`;`) y parsea coma decimal europea. Pendiente validar con un export europeo real de i2 (cubierto con fixtures sintéticos) | — |
| Circuitos con vuelta que cruza la línea de meta más de una vez | Circuitos en 8 o con chicane en meta podrían romper la detección de vueltas | Media |
| ~~Overlay con FPS distintos al de la grabación~~ 🔍 | Investigado (2026-06-17): **no reproduce desync**. Los frames se generan en `t = n/fps`, así que la duración real del `overlay.webm` = duración de la vuelta sea cual sea el fps; ffmpeg compone por PTS (duplica/descarta frames por timestamp, no desincroniza). El único efecto real de un fps bajo es un HUD más "a saltos" (suavidad visual), no desfase. La guía ya recomienda `--fps 60` para igualar la grabación. Pendiente solo: si en el QA visual aparece un desync real, capturar repro. | Baja |
| `--format prores` cuelga ffmpeg en vueltas largas | En Nordschleife (~394s) el encode ProRes arranca, escribe ~4 GB de frames y luego ffmpeg se congela sin actividad CPU. El moov atom nunca se escribe y el archivo queda corrupto. Reproducido en QA 2026-06-14. Default cambiado a `webm` como mitigación; causa raíz pendiente de investigar. **Diagnóstico de código (2026-06-21, sin reproducir el cuelgue):** (1) `_run_ffmpeg` en `viz/overlay.py` manda `stderr=subprocess.DEVNULL`, así que cuando el encode falla solo queda un `CalledProcessError` con código pelón — el motivo real de ffmpeg se descarta. Es la misma trampa que ya se corrigió en `compose.py` (v0.6.5, captura el stderr a temporal y reporta las últimas 15 líneas), pero la lección no se aplicó aquí; por eso "investigar la causa" hoy es imposible desde el log. (2) Asimetría: la rama `webm` pasa `-row-mt 1 -threads N`; la rama `prores_ks` no pasa threading. **Pendiente:** instrumentar `_run_ffmpeg` (capturar stderr) y reproducir el encode real de una vuelta larga en AMS2 para ver si es error (saldría en stderr) o cuelgue verdadero (I/O / muxer / tamaño de archivo — ojo al límite de 4 GB de FAT32/exFAT si la salida va a un disco externo). | Alta |
| `fantasma compose` sin ffmpeg instalado | El error actual puede no ser claro para el usuario — mejorar mensaje | Baja |
| Versión mínima de Python no declarada | ~~`pyproject.toml` debería declarar `requires-python`~~ ✅ ya declara `requires-python = ">=3.10"` | — |
| `setup.ps1` mezcla propósito dev/usuario | Ofrece instalar **GitHub CLI «para subir el repositorio»** — eso es de contribuidor, no del piloto que instala para analizar. Candidato a moverlo detrás de un flag `-Dev` o quitarlo del flujo de usuario. Detectado en la revisión 2026-06-21 (v0.7.1). | Baja |
| Aviso si el piloto va más rápido que la referencia | Es fácil invertir `--reference`/`--driver` por error (pasó en QA visual 2026-06-21: el GAP sale verde/negativo cuando deberían estar al revés). Un aviso al renderizar — "¿seguro? la vuelta del piloto es más rápida que la de referencia" — lo atajaría. Idea para luego. | Baja |
| Colores ABS/TC de la referencia parecidos a los del piloto | Deuda de la regla 3 del **ADR 0006**: hoy el tono codifica «qué» (ABS=ámbar, TCS=violeta) y solo el brillo codifica «quién», lo que confunde piloto vs referencia. Dirección elegida: opción B (tonos distintos), diferida. | Baja |
| Auto-sync no detecta un video EQUIVOCADO que sí tiene motor | Ya cubierto: un video **sin** señal de motor se rechaza por `z < 3.0σ` (líneas 48/107, hecho). Lo que falta: un video de **otra carrera/sesión con motor** puede superar el umbral y, con el multi-vuelta del **ADR 0008**, ofrecer candidatos espurios para elegir — el audio no distingue "vuelta equivocada del video correcto" de "vuelta de un video equivocado". Mejora propuesta: avisar «calidad baja en todos los candidatos, ¿seguro que el video corresponde?» cuando todos los z rondan el mínimo. Se relaciona con el QA pendiente «video que NO corresponde» (línea 78). Detectado 2026-06-21 (v0.8.0). | Baja |

---

## Deuda técnica conocida

| Item | Descripción |
| :-- | :-- |
| `motec_csv.py` codificación | Lee con `utf-8-sig` — CSV generados por i2 en Windows pueden tener encoding distinto en setups no-inglés |
| Tests automáticos (en progreso) | Suite implementada: 48 tests (Tier 1 `core/` + Tier 2 importadores + Tier 3 `compose`/`sync` + smoke de UI) con pytest y fixtures sintéticas, y **CI en GitHub Actions** (Windows, Python 3.10–3.12). Cumple el requisito de v1.0 de "tests unitarios de `core/`". Pendiente: ampliar cobertura conforme crezca el código. Estrategia y estado en [`docs/decisions/0003-testing.md`](docs/decisions/0003-testing.md) |
| ~~Docs en `docs/` referenciadas pero no escritas~~ ✅ | Resuelto: `docs/guia-usuario.md` (131 líneas), `docs/hud-reference.md` (138) y `docs/formato-datos.md` (88) ya existen con contenido. Pendiente solo mantenerlas al día con los cambios de UI/HUD |
| Branch protection en `master` (para colaboradores) | Hoy el CI **avisa** (verde/rojo) pero no **bloquea el merge** sin branch protection — single-author no lo necesita. Al sumar al primer colaborador: activar en GitHub «requiere PR + checks `lint` y `pytest` en verde», para que el CI sea barrera **obligatoria** para todos. Ya documentado como expectativa en `CONTRIBUTING.md` §6 y el flujo en `docs/flujo-de-trabajo.md`. |

---

_Última revisión: 2026-06-26 — **ADR 0010** (UI = Streamlit en v1.0; front de escritorio custom diferido a v2.0) + bloque **v2.0** de evaluación de migración del front y tarea de benchmark de herramientas. Antes: 2026-06-22 — release **v0.9.0** (campo GASTO + carga de deslizamiento ADR 0009; glosario; matriz de docs CONTRIBUTING §8; regla de pruebas). Antes: **v0.8.0** (auto-sync multivuelta ADR 0008; `setup.ps1` ASCII + auto-instala Python; `fantasma wear` + ADRs 0004–0008). Antes (2026-06-21): suite de tests + CI + fix separador `;` en release; diagnóstico de código del gap `prores` (stderr descartado en `_run_ffmpeg`, asimetría de threading) asentado sin tocar código. (2026-06-17): drill-down (era v0.10.0) diferido a post-1.0; la 1.0 se reenfoca a estabilizar/testear/documentar/validar el pipeline offline existente en AMS2; reordenadas las versiones; v0.9.0 marcada completa; deudas resueltas (docs, requires-python)._
