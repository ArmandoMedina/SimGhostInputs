# Roadmap — SimGhostInputs

> Estado vivo del proyecto: dónde va y qué falta. El **porqué** de cada decisión vive en
> [`docs/decisions/`](docs/decisions/README.md); el historial de cambios enviados, en
> [`CHANGELOG.md`](CHANGELOG.md); el relevo en-vuelo, en [`HANDOFF.md`](HANDOFF.md).

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md) · 🧩 [Decisiones (ADR)](docs/decisions/README.md)

---

## Estado actual

**v1.0.0** (2026-06-30) — estable. Pipeline AMS2 completo (análisis + overlay + compose + pace notes). 142 tests.

**v2.0 en rama `codex/sgi-v2-merge`** — código completo. UI NiceGUI, CrewChief Pace Notes, empaquetado Windows, 191 tests (incluye e2e wizard con datos reales). QA completado (2026-07-01): bundle 370.9 MB, native=True ✅, Pace Notes CLI 5/5 ✅, VirusTotal 4/63 FPs ✅. Listo para merge a master.

---

## Antes de mergear v2.0 a master

Estos 4 ítems requieren hardware real — no hay código pendiente:

- [x] **Bundle size real** — **370.9 MB** en `dist/SimGhostInputs/` (Windows 11, Python 3.11, stack completo: nicegui 3.14 + pywebview + scipy + numpy + PIL + matplotlib + pandas). Medido 2026-07-01 en laptop de desarrollo con `nicegui-pack --onedir`.
- [x] **`native=True` en VM limpia** — Confirmado en laptop Windows 11 24H2: la app abre ventana de escritorio nativa (pywebview 6.2.1) sin errores. Nota: para tests futuros que abran ventanas, lanzar con `Start-Process -PassThru` en background y matar tras el timeout.
- [x] **VirusTotal** — 4/63 falsos positivos (Bkav, APEX, Gridinsoft, Yandex). Todos los motores principales (Windows Defender, Kaspersky, Norton, Avast, ESET, etc.) limpios. Yandex etiqueta explícitamente "PyInstaller". Aceptable para publicar. Medido 2026-07-01.
- [x] **QA de Pace Notes CLI** — 5/5 ítems verificados (2026-07-01): tones sin deps, metros correctos, escala distinguible, voice con edge-tts, --top 3. QA en sesión real en pista queda como deseable post-v2.0:
  - [x] `--mode tones`: genera `metadata.json` + WAV de tonos sin instalar edge-tts
  - [x] Tonos suenan en los metros correctos (Nordschleife)
  - [x] Escala de frecuencias distinguible: agudo ≠ medio ≠ grave
  - [x] `--mode voice`: frases coherentes con el problema detectado por curva
  - [x] `--top 3`: solo las 3 curvas con más pérdida generan audio
  - [ ] `--mode both` en sesión real en pista (deseable, no bloqueante)
  - [ ] WAV validado con ffprobe (deseable, no bloqueante)

---

## Post-v2.0 — pendiente de iniciar

### Pipeline desatendido: overlay → compose en secuencia + notificación

**Dolor real (2026-06-30):** el usuario lanza el overlay, se va a hacer otra cosa y al volver tiene que
esperar a que compose termine — dos esperas en lugar de una.

**Qué se quiere:**
- Un modo "encadenar": al terminar el overlay, lanzar compose automáticamente con los parámetros ya configurados.
- Notificación al terminar (push al móvil, o al menos un sonido/pop-up de escritorio).

**Por qué se difiere:** requiere arquitectura de tareas en background y un canal de notificación.
**Gatillo:** cuando el usuario reporte que esperar las dos etapas es fricción frecuente.

---

### Previsualización del HUD en Paso 4

**Dolor real (2026-06-30):** el usuario lanzó el compose sin cambiar el tamaño del HUD y el overlay
cubrió la mitad del video. Los sliders de escala y posición se configuran a ciegas.

**Qué se quiere:** frame de referencia dinámico (primer fotograma del video o placeholder) que se actualiza
al mover los sliders — tamaño y posición del HUD previsualizados antes de renderizar.

**Por qué se difiere:** trabajo de UX más que de motor. No bloqueó v1.0 ni v2.0.
**Gatillo:** cuando se repita el problema de HUD mal dimensionado, o en el siguiente pass de UX del Paso 4.

---

### Histórico entre sesiones

Comparar el rendimiento en una misma curva a lo largo de varias tandas (¿progreso, techo, retroceso?).

- [ ] Modelo `SessionHistory` + `fantasma history add/show --corner`
- [ ] Gráfica de tendencia por curva (X = fechas, Y = tiempo perdido); paso opcional en UI
- [ ] Almacenamiento local (SQLite o directorio de JSONs — sin servidor, sin cloud)

---

### Nuevos importadores

Eliminar la dependencia de MoTeC i2 como intermediario.

- [ ] Importador `.ld` nativo (MoTeC) y `.ibt` (iRacing)
- [ ] Ampliar `GUESS` (SimHub, ACC CSV) y `MOTEC_MAP` (variantes ACC/iRacing/rF2)
- [ ] Docs de compatibilidad por sim (qué canales exporta cada uno, qué queda como `None`)

---

### Lista de vueltas procesadas en la sesión (UI)

Tabla acumulada de vuelta + salida + calidad de sync para quien procesa varias seguidas. Conveniencia, no corrección.

---

### fantasma-live (repo separado)

Coaching adaptativo en tiempo real. Solo si Pace Notes no cubre el caso de uso.

- [ ] Listener UDP para AMS2 (60 Hz)
- [ ] Comparador en vivo — delta continuo vs referencia
- [ ] Motor de voz adaptativo (edge-tts, latencia <200ms)

---

## 🔧 Transversal

### Gaps técnicos

- [ ] **Instrumentar `_run_ffmpeg` (capturar stderr) y reproducir el encode `--format prores` de una vuelta larga** para diagnosticar por qué cuelga. En Nordschleife (~394s) arranca, escribe ~4 GB de frames y se congela; hoy `stderr=DEVNULL` descarta el motivo real. Mitigado con el default `webm`. _Prioridad: Alta (solo afecta a quien pida prores explícito)._
- [ ] **Definir y probar el comportamiento con vueltas muy cortas** (salida de pista, vuelta de 500 m). _Prioridad: Media._
- [ ] **Probar circuitos cuya vuelta cruza meta más de una vez** (trazado en 8 o chicane en meta) — podrían romper la detección de vueltas. _Prioridad: Media._
- [~] **Avisar al renderizar si el piloto va más rápido que la referencia** — `compare()` ya emite aviso en `summary["avisos"]`; la UI lo muestra en el Paso 2. Pendiente: invertir colores del HUD en el overlay cuando se detecta inversión. _Prioridad: Baja._
- [~] **Avisar cuando todos los candidatos de auto-sync tienen calidad baja** — zona gris del ADR 0008 cubre el caso de confianza moderada; pendiente el caso de varios candidatos todos débiles pero sobre 3σ. _Prioridad: Baja._
- [ ] **Distinguir DESLIZ de GASTO visualmente en el HUD** — ambos en la misma franja; se confunde el instantáneo (DESLIZ) con el acumulado (GASTO). _Prioridad: Baja._
- [ ] **Diferenciar colores ABS/TC de referencia vs piloto** (opción B del ADR 0006). _Prioridad: Baja._

### Deuda técnica

- [ ] **Manejar encodings distintos a `utf-8-sig` en `motec_csv.py`** — CSV de i2 en Windows con setups no-inglés pueden traer otro encoding. Pendiente de caso real de fallo.
- [ ] **Desgaste en gráficas (Producto 1)** — acumulado de stint entre vueltas en la vista de análisis (hoy solo en `fantasma wear` CLI). Pendiente de datos para recalibrar umbrales.
- [ ] **Ampliar cobertura de tests** conforme crezca el código. Estrategia en [ADR 0003](docs/decisions/0003-testing.md).
- [ ] **Activar branch protection en `master`** al sumar al primer colaborador. Ya documentado en `CONTRIBUTING.md` §6.
- [ ] **Recolección secuencial de workers en `_render_parallel`** (`overlay.py` ~500) — el loop espera al worker 0 antes de mirar al 1; si el chunk 0 es el más lento, los demás esperan con sus PKLs ya listos. Reemplazar con `concurrent.futures.as_completed` o polling concurrente. _Prioridad: Baja._
- [ ] **Pickle overhead en render paralelo** — cada subprocess de overlay recibe copia completa de todos los arrays numpy (ds, ref_ch, drv_ch, slips...) serializada a disco; con Nordschleife puede ser 10-50 MB por worker x N workers. Considerar shared memory (`multiprocessing.shared_memory`) o pasar solo el slice. _Prioridad: Baja._
- [ ] **`_save_upload` no limpia archivos temporales** (`ng_helpers.py`) — usa `NamedTemporaryFile(delete=False)` sin cleanup; los CSVs subidos se acumulan en el directorio temp del OS hasta que el OS los elimine. Agregar cleanup en `do_load()` o al cerrar la sesión. _Prioridad: Baja._
- [ ] **Inconsistencia de tokens CSS entre pasos** — ng_step2 usa `.style("color:var(--muted)")` mientras ng_step3/4 usan `text-gray-400` Tailwind tras la migración de contraste. Uniformizar ng_step2 al mismo patrón. _Prioridad: Baja._
