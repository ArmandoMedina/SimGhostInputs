# Roadmap — SimGhostInputs

> Estado vivo del proyecto: dónde va, qué falta para la **v1.0** y qué queda **diferido** para después. El **porqué** de cada decisión vive en [`docs/decisions/`](docs/decisions/README.md); el historial de cambios, en [`CHANGELOG.md`](CHANGELOG.md); qué documentos tocar al hacer un cambio, en [`CONTRIBUTING.md` §8](CONTRIBUTING.md#8-mantenimiento-de-documentación).
>
> **Para retomar en frío:** el relevo en-vuelo (dónde voy, qué falta ahora) vive en [`HANDOFF.md`](HANDOFF.md). Este ROADMAP guarda el camino a v1.0; lo efímero está en el HANDOFF.

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md) · 🧩 [Decisiones (ADR)](docs/decisions/README.md)

---

## Estado actual — v1.0.0

Último release: **v1.0.0** (2026-06-30) — **Pipeline AMS2 completo, documentado y probado.** `setup.ps1` validado en instalación limpia de Windows 11 (Hyper-V VM). Drill-down por curva en UI Paso 2. 142 tests en verde.

La v1.0 está declarada estable. El camino a continuación es la **v2.0**: nuevos importadores, coaching de voz (CrewChief Pace Notes), histórico entre sesiones, y evaluación del front de escritorio. Ver «Diferido post-v1.0» abajo.

> **▶️ Para la próxima sesión:** ver [`HANDOFF.md`](HANDOFF.md). La v1.0 está cortada — continuar con el roadmap post-v1.0.

---

## Camino a la v1.0

El criterio para llamarla v1.0 es que el pipeline offline esté **completo, documentado y probado**. Alcance declarado: **AMS2 únicamente**. Importadores adicionales (iRacing, rF2, ACC) y features avanzadas (drill-down, histórico, pace notes) van después.

### Requisitos para la v1.0

- [x] v0.9.0 completada y en producción
- [x] Suite de tests de `core/` + CI en GitHub Actions ([ADR 0003](docs/decisions/0003-testing.md))
- [x] Docs completas y al día: guía de usuario, referencia de HUD (con leyenda visual y campo GASTO), formato de datos, cómo contribuir, **glosario**
- [x] **Los gaps `Alta` no bloquean la 1.0** (decidido 2026-06-21): el único vivo es `--format prores`, ya mitigado con el default `webm`; se difiere a post-1.0
- [x] **API interna (`core/`) estabilizada** — `__all__` declarado, prefijos `_` consistentes, `CANONICAL` muerta eliminada (v0.15.0)
- [x] 👤 **Probado en AMS2 en ≥3 circuitos distintos** — **4 circuitos ✓** (Barcelona NC, Interlagos, Nordschleife 2025, Nürburgring GP) y **clases más allá de GT3** (Hypercar, Fórmula F3, Prototipo/LMP2). QA de cierre 2026-06-30 sobre telemetría real: el pipeline de análisis procesa todas las clases sin errores de lógica. Único hallazgo (corregido): un export del ORECA 07 sin canal de distancia, que ahora degrada con gracia y se avisa temprano ([ADR 0017](docs/decisions/0017-distancia-canal-requerido.md))
- [x] 👤 **`setup.ps1` probado en instalación limpia de Windows 11** — ✅ validado en VM Hyper-V (2026-06-30). Happy path completo sin errores. La detección de dependencias y el encoding ASCII se corrigieron en v0.7.1 / v0.7.2.
  - **Fase 0 — SSH a la PC potente: ✅ montado (2026-06-28).** Host `SERVER` (LAN), acceso por llave dedicada sin password desde la laptop de trabajo (alias `pcpotente` en `~/.ssh/config`).
  - **Fase 1 — VM limpia de Windows para `setup.ps1` (Hyper-V): ✅ ejecutada y validada (2026-06-30).**
  - **Fase 2 — mover el QA pesado a ese hardware:** diferido post-v1.0.
- [x] **Cortar release del `[Unreleased]`** acumulado — hecho en v0.10.0

### Notas vivas (no bloquean, a refinar)

- **Desgaste acumulado en dos vistas** (enmienda [ADR 0004](docs/decisions/0004-desgaste-acumulable.md)/0005; unidad en [ADR 0009](docs/decisions/0009-unidad-desgaste-acumulado.md)):
  - **(1) HUD del overlay** — acumulado *de la vuelta* (campo **GASTO**): **✅ implementado en v0.9.0**.
  - **(2) Gráficas (Producto 1)** — acumulado de *stint* entre vueltas: **⏳ pendiente** (hoy solo en `fantasma wear`, CLI).
- **Umbrales de desgaste a recalibrar:** en el QA real las gomas no llegaron al amarillo porque **el tanque se acaba antes** (vida total de goma vs. degradación dentro del stint). Recopilar más datos antes de rediseñar. Detalle en [ADR 0004 §Consecuencias](docs/decisions/0004-desgaste-acumulable.md).

---

## ⏸️ Diferido — post-v1.0

> Fuera del alcance de la 1.0 (solo AMS2, pipeline offline). Se retoman después de declararla estable. El detalle fino de cada uno vive en su documento dueño (ADR o PRODUCT_BRIEF); aquí el qué, el porqué se difiere y el alcance previsto.

### Pipeline desatendido: overlay → compose en secuencia + notificación

**Dolor real (2026-06-30):** el usuario lanza el overlay, se va a hacer otra cosa y al volver tiene que esperar a que compose termine — dos esperas en lugar de una. No hay forma de delegar ambas operaciones juntas y recibir aviso al terminar.

**Qué se quiere:**
- Un modo "encadenar": al terminar el overlay, lanzar compose automáticamente con los parámetros ya configurados.
- Notificación al terminar (push al móvil, o al menos un sonido/pop-up de escritorio) para no tener que estar mirando la pantalla.

**Por qué se difiere:** requiere arquitectura de tareas en background (hilo o proceso separado que sobreviva la interacción de Streamlit) y un canal de notificación. Es una mejora de experiencia, no un bug ni un requisito de v1.0.

**Gatillo para retomar:** cuando el usuario reporte que esperar las dos etapas es fricción frecuente, o al evaluar el front custom (v2.0) donde esto es más natural.

### Front de escritorio custom (v2.0)
> Decisión en [ADR 0018](docs/decisions/0018-framework-ui-nicegui.md) (enmienda a [ADR 0010](docs/decisions/0010-framework-ui-streamlit.md)).

**Decisión tomada (2026-06-30):** la UI de v2.0 migra a **NiceGUI** (MIT), empaquetada con `nicegui-pack` + Inno Setup. El instalador final es `SimGhostInputs-vX.Y-Setup.exe` — doble-click, sin Python, sin terminal. El benchmark completo está en [`docs/benchmark-ui-framework.md`](docs/benchmark-ui-framework.md).

**Antes de iniciar la migración — spike obligatorio:**
- [ ] `nicegui-pack --onedir` en venv limpio: medir bundle size real con el stack completo (numpy + scipy + PIL + matplotlib)
- [ ] Probar `native=True` en VM limpia Windows 11 24H2 (ya tenemos Hyper-V del spike de v1.0)
- [ ] Prototipo de preview HUD reactiva: slider → PIL → `image.set_source()` → medir latencia percibida
- [ ] Subir el `.exe` a VirusTotal: detectar false positives de antivirus antes de publicar

**Migración (post-spike):**
- [ ] Skeleton NiceGUI: `ng_app.py` + sidebar con navegación de 5 pasos + gestión de estado
- [ ] Portar pasos 0–4 a NiceGUI (mantener `app.py` Streamlit en paralelo hasta completar)
- [ ] Preview reactiva del HUD en Paso 4 (el feature que justificó la migración)
- [ ] Empaquetado: `nicegui-pack --onedir` + script `.iss` de Inno Setup
- [ ] CI: job `build-installer` en `release.yml` → artefacto en GitHub Release
- [ ] Mockups con Claude Design antes de implementar cada paso

### Coaching de voz — CrewChief Pace Notes
> Investigado y validado; spec completa en [ADR 0002](docs/decisions/0002-crewchief-pacenotes.md).

**Hallazgo clave:** CrewChief tiene un sistema nativo (**Pace Notes**) que reproduce WAV en metros exactos de la pista. SimGhostInputs ya tiene esos metros en `corners.json` — la integración es solo generar los archivos, sin modificar CrewChief ni construir un motor de voz propio.

**Cómo funciona:**
- `fantasma compare` genera el análisis (qué curvas, cuánto tiempo, qué problema).
- `fantasma pacenotes` lee ese análisis y genera las frases (edge-tts → MP3 → WAV 24kHz) + `metadata.json` con el metro exacto de cada curva (del `corners.json`).
- Los archivos se escriben en `Documents\CrewChiefV4\pace_notes\ams2\[pista]\`.
- El piloto activa las pace notes antes de salir del pit; CrewChief habla en el metro exacto.

**Dos capas de audio:**
- **Tonos posicionales** (núcleo, sin dependencias): un tono por hito del `corners.json` — frenada 880 Hz, ápex 440 Hz, gas 220 Hz. El piloto aprende la escala como reflejo; reacción ~100ms vs ~300ms visual.
- **Voz contextual** (opcional, edge-tts): frases 200m antes del punto de frenada, basadas en los flags de `compare`. La voz enseña, el tono actúa.
- **Modos:** `--mode tones` (default) · `--mode voice` · `--mode both`.

**Cambios previstos:**
- [ ] Módulo `fantasma/viz/pacenotes.py` (`generate_tone`, `generate_voice`, `build_pack`).
- [ ] Comando `fantasma pacenotes --corners --compare --mode {tones|voice|both} --top --output-dir`.
- [ ] Frases de voz basadas en los flags de `compare` (`late_brake`, `early_gas`, `d_vmin`).
- [ ] Dependencia opcional `edge-tts` → `pip install 'fantasma-inputs[voice]'`.
- [ ] Resolver el nombre de pista AMS2 (campo `Venue` del CSV o preguntar al usuario).

**QA antes de publicar:**
- [ ] `--mode tones`: genera `metadata.json` + WAV de tonos sin instalar edge-tts.
- [ ] Tonos suenan en los metros correctos en una sesión real en Nordschleife.
- [ ] Escala de frecuencias distinguible: agudo ≠ medio ≠ grave.
- [ ] `--mode voice`: frases coherentes con el problema detectado por curva.
- [ ] `--mode both`: voz 200m antes + tono en el metro exacto, sin solaparse.
- [ ] `--top 3`: solo las 3 curvas con más pérdida generan audio.
- [ ] `--volume 0.3`: tonos audibles pero no intrusivos junto al audio del sim.
- [ ] Sin `edge-tts` con `--mode voice`: error claro con instrucción de instalación.
- [ ] Nombre de pista incorrecto: CrewChief no carga el pack — documentar cómo dar con el nombre correcto.
- [ ] WAV en formato aceptado por CrewChief: 24kHz, mono (verificar con ffprobe).

### Drill-down por curva
> Spec en [PRODUCT_BRIEF.md §10](PRODUCT_BRIEF.md).

Convierte la tabla de tiempo perdido en coaching accionable: el piloto pica una curva y ve qué corregir (Δ frenada, Δ intensidad, V-Min target, Δ gas/G-lat), con síntesis en lenguaje natural — aritmética pura sobre `corners_compare.csv`, sin LLM. Los datos ya existen en el `trace` de `compare()`.

**Cambios previstos:**
- [x] Tabla de curvas seleccionable en UI Paso 2 → panel de detalle por curva.
- [x] Función `corner_coaching(row, trace)` en `core/` que produce el dict de coaching.
- [x] Síntesis en lenguaje natural ("frenas 40m antes con 15% menos intensidad → 0.6s perdidos").

**QA antes de publicar:**
- [x] Click/selección en la curva con mayor pérdida → panel de detalle con todos los campos disponibles.
- [x] Curva sin canal gear → panel omite la marcha sin crashear.
- [x] Curva sin glat → panel omite G-lat sin crashear.
- [x] Síntesis en lenguaje natural coherente con los números del panel.
- [x] Curva donde el piloto es más rápido → mensaje positivo ("ganas X s aquí").

### Histórico entre sesiones
Comparar el rendimiento en una misma curva a lo largo de varias tandas (¿progreso, techo, retroceso?).

**Cambios previstos:**
- [ ] Modelo `SessionHistory` + `fantasma history add/show --corner`.
- [ ] Gráfica de tendencia por curva (X = fechas, Y = tiempo perdido); paso opcional en UI.
- [ ] Almacenamiento local por decidir: SQLite o directorio de JSONs (sin servidor, sin cloud).

**QA antes de publicar:**
- [ ] Registrar 3 sesiones distintas y verificar que el histórico acumula bien.
- [ ] `fantasma history show` sin sesiones previas → mensaje claro, sin crash.
- [ ] Importar sesión antigua (CSV ya procesado) al histórico.
- [ ] Gráfica de tendencia con una sola sesión → no crashea, mensaje informativo.
- [ ] Migración: si el esquema de almacenamiento cambia entre versiones, migrar datos existentes.

### Nuevos importadores
Elimina la dependencia de MoTeC i2 como intermediario. (v1.0 cubre solo AMS2.)

**Cambios previstos:**
- [ ] Importador `.ld` nativo (MoTeC) y `.ibt` (iRacing).
- [ ] Ampliar `GUESS` (SimHub, ACC CSV) y `MOTEC_MAP` (variantes ACC/iRacing/rF2).
- [ ] Docs de compatibilidad por sim (qué canales exporta cada uno, qué queda como None).

**QA antes de publicar:**
- [ ] Importar `.ld` de AMS2 directamente → mismo resultado que vía CSV exportado.
- [ ] Importar `.ibt` de iRacing → detección de vueltas y canales básicos funcionan.
- [ ] CSV de SimHub para AMS2 → auto-detectado sin `--map`.
- [ ] CSV de ACC vía sim-to-motec → degradación graceful en ABS/TCS.
- [ ] Tabla de compatibilidad en README actualizada con estado real probado.

### fantasma-live (repo separado)
Coaching **adaptativo en tiempo real** — reacciona a lo que pasa en esa vuelta (trompo, contacto, pista cambiante), no al histórico. Solo si Pace Notes no cubre el caso de uso.

**Fases tentativas:**
- [ ] Listener UDP para AMS2 — captura telemetría en vivo a 60 Hz.
- [ ] Comparador en vivo — delta continuo por curva vs referencia.
- [ ] Motor de voz adaptativo — TTS con edge-tts, latencia <200ms.
- [ ] Modos de coaching — Aprendizaje · Qualy · Carrera.

### Previsualización del HUD en el formulario de Componer (Paso 4)

**Dolor real (2026-06-30):** el usuario lanzó el compose sin cambiar el tamaño del HUD y el overlay cubrió la mitad del video. Los parámetros (escala, posición) se configuran a ciegas: no hay referencia visual de cuánto ocupa el HUD antes de renderizar.

**Qué se quiere:**
- En el formulario de Paso 4, junto a los sliders de escala y posición del HUD, mostrar un frame de referencia dinámico (imagen estática o GIF corto) que simule el tamaño y posición resultantes sobre un fondo de video placeholder.
- Al mover el slider la previsualización se actualiza en tiempo real (o con debounce).
- El frame de referencia puede ser el primer fotograma del video del piloto si está disponible, o un placeholder con las dimensiones correctas.

**Por qué se difiere:** requiere diseñar el componente de preview (generar un frame compuesto en Python/PIL + `st.image` reactivo a los sliders), que es trabajo de UX más que de motor. No bloquea v1.0.

**Gatillo para retomar:** cuando se repita el problema de HUD mal dimensionado, o al hacer el pass de usabilidad de Paso 4.

### Lista de vueltas procesadas en la sesión (UI)
Tabla acumulada de vuelta + salida + calidad de sync para quien procesa varias seguidas. Conveniencia, no corrección.

---

## 🔧 Transversal

### Gaps técnicos

_Contexto: cosas en el código sin cobertura de QA formal ni documentación. Ninguno bloquea la 1.0. Los pendientes puntuales:_

- [ ] **Instrumentar `_run_ffmpeg` (capturar stderr) y reproducir el encode `--format prores` de una vuelta larga** para diagnosticar por qué cuelga. _Contexto:_ en Nordschleife (~394s) arranca, escribe ~4 GB de frames y se congela; hoy `stderr=DEVNULL` descarta el motivo real (misma trampa ya corregida en `compose.py` v0.6.5) y la rama `prores_ks` no pasa threading. Mitigado con el default `webm`; ojo al límite de 4 GB de FAT32/exFAT. _Prioridad: **Alta** (no bloquea: solo afecta a quien pida prores explícito)._
- [ ] **Distinguir DESLIZ de GASTO en el HUD** (separación visual, etiqueta legible, o que GASTO «se llene»). _Contexto:_ ambos en la misma franja, GASTO con etiqueta chica/tenue (fontsize 9); se confunde el instantáneo (DESLIZ, se reinicia por curva) con el acumulado (GASTO). Detectado en QA 2026-06-26. _Prioridad: Baja._
- [ ] **Confirmar con un video de 60 fps real que el overlay no desincroniza** (ver «próxima sesión»); si aparece desync, capturar repro. _Contexto:_ el código no debería desincronizar (frames en `t = n/fps`); investigado 2026-06-17, sin repro. La guía ya recomienda `--fps 60`. _Prioridad: Baja._
- [ ] **Definir y probar el comportamiento con vueltas muy cortas** (p. ej. salida de pista, vuelta de 500 m). _Prioridad: Media._
- [ ] **Probar circuitos cuya vuelta cruza meta más de una vez** (en 8 o con chicane en meta) — podrían romper la detección de vueltas. _Prioridad: Media._
- [x] **Agregar test sistemático de degradación por canales ausentes** (combinaciones de glat/glong/gear/abs/tcs) — hecho: `tests/core/test_degradacion_canales.py` cubre las 32 combinaciones.
- [~] **Avisar cuando todos los candidatos de auto-sync tienen calidad baja** ("¿seguro que el video corresponde?"). _Cubierto parcialmente_ por la zona gris de la [enmienda 2026-06-28 al ADR 0008](docs/decisions/0008-sync-multivuelta-candidatos.md): si el candidato aceptado tiene confianza moderada (`3σ ≤ z < 6.5σ`) se acepta pero se avisa. _Pendiente:_ el caso de varios candidatos todos débiles pero sobre 3σ, a medir con más datos. _Prioridad: Baja._
- [ ] **Avisar al renderizar si el piloto va más rápido que la referencia** (atajar el `--reference`/`--driver` invertido, que pinta el GAP verde cuando debería ser rojo). _Prioridad: Baja._
- [ ] **Diferenciar colores ABS/TC de referencia vs piloto** (tonos distintos, opción B del [ADR 0006](docs/decisions/0006-grosor-uniforme-lineas-hud.md)). _Contexto:_ hoy el tono codifica «qué» y solo el brillo «quién», lo que confunde. _Prioridad: Baja._
- [ ] **Mejorar el mensaje de error de `fantasma compose` cuando falta ffmpeg.** _Prioridad: Baja._
- [ ] **Separar el propósito dev del de usuario en `setup.ps1`** (mover la instalación de GitHub CLI detrás de un flag `-Dev` o quitarla del flujo de usuario). _Prioridad: Baja._

### Deuda técnica

_Contexto: lo conocido a saldar cuando toque. Los pendientes puntuales:_

- [ ] **Ampliar la cobertura de tests** conforme crezca el código. _Contexto:_ la suite (121 tests, Tier 1–4 + smoke de UI) y el CI ya cumplen el requisito de v1.0. Estrategia en [ADR 0003](docs/decisions/0003-testing.md).
- [ ] **Manejar encodings distintos a `utf-8-sig` en `motec_csv.py`** (CSV de i2 en Windows con setups no-inglés pueden traer otro encoding).
- [ ] **Activar branch protection en `master` al sumar al primer colaborador** (requiere PR + checks `lint` y `pytest` en verde). _Contexto:_ hoy el CI avisa pero no bloquea el merge (single-author no lo necesita). Ya documentado en `CONTRIBUTING.md` §6 y `docs/flujo-de-trabajo.md`.
