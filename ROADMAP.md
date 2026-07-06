# Roadmap — SimGhostInputs

> Estado vivo del proyecto: dónde va y qué falta. El **porqué** de cada decisión vive en
> [`docs/decisions/`](docs/decisions/README.md); el historial de cambios enviados, en
> [`CHANGELOG.md`](CHANGELOG.md); el relevo en-vuelo, en [`HANDOFF.md`](HANDOFF.md).

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md) · 🧩 [Decisiones (ADR)](docs/decisions/README.md)

---

## Estado actual

**v2.2.0** (2026-07-05) — estable. 234 tests. Flujo "Solo Pace Notes" (entrada directa Importar→Análisis→Pace Notes saltando overlay/compose, [ADR 0021](docs/decisions/0021-flujo-solo-pacenotes.md)) + guía del Paso 5 (tooltips, panel② siempre visible, fix del estado disabled del botón «Aplicar sonido»).

**v2.1.1** (2026-07-05) — estable. 226 tests. Patch: corrige el badge de versión del footer (mostraba «v2.0»).

**v2.1.0** (2026-07-05) — Pace Notes en la UI, pipeline autónomo overlay→compose, mux standalone y remediación de UI/UX (2 rondas de QA visual).

**v2.0.0** (2026-07-03) — anterior. 212 tests. Auditoría integral, remediación crítica y retiro de Streamlit.

**v1.0.0** (2026-06-30) — anterior. 142 tests.

---

## Post-v2.0 — pendiente de iniciar

### QA Pace Notes en sesión real en pista

Requiere AMS2 en pista — no bloqueó el merge.

- [ ] `--mode both` en sesión real: voz 200m antes + tono en el metro exacto, sin solaparse
- [ ] WAV validado con ffprobe
- [ ] Tonos suenan en los metros correctos auditivamente (Nordschleife o similar)

### ~~Pipeline desatendido: overlay → compose en secuencia + notificación~~ — entregado en `feat/pacenotes-ui`

- [x] Checkbox «Al terminar, componer automáticamente» en el Paso 3 (flujo compose); encadena overlay→compose sin intervención.
- [x] Notificación de escritorio al terminar (Web Notifications API con degradación a `ui.notify`).

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

### Monitoreo remoto del render (candidata v2.1)

Arrancar el overlay en la PC y seguir el progreso desde otro dispositivo (celular en la misma LAN). Hoy es imposible a propósito: la UI escucha solo en `127.0.0.1` (fix de seguridad de la auditoría 2026-07-03) y el estado vive en `app.storage.user` (por navegador). Requiere diseño: opt-in explícito (`--lan`), token de acceso, y estado del job compartido (`app.storage.general` o página de estado) — no reabrir el hueco de escritura arbitraria que se cerró.

---

### fantasma-live (repo separado)

Coaching adaptativo en tiempo real. Solo si Pace Notes no cubre el caso de uso.

- [ ] Listener UDP para AMS2 (60 Hz)
- [ ] Comparador en vivo — delta continuo vs referencia
- [ ] Motor de voz adaptativo (edge-tts, latencia <200ms)

---

### Acelerar el render del overlay (candidata v3.0 — gated por benchmark)

El loop de generación de frames del HUD es el único punto claramente CPU-bound (la UI anuncia "5 a 30 min" por overlay; ya se usa multiprocessing en todos los cores). Idea: bajar **solo ese loop** a un hot-path compilado (Rust vía PyO3 / C) o a GPU/shaders (moderngl), dejando Python como orquestador de todo lo demás (telemetría, ffmpeg, UI). **No se arranca sin datos** que lo justifiquen.

- [ ] **Perfilar un render real y separar el tiempo del loop de frames vs. el resto** (I/O, encode ffmpeg, sync) — benchmark reproducible con números, sobre una vuelta larga (p. ej. Nordschleife ~394s). _Este es el gate: sin evidencia de que el dibujado de frames domina el tiempo, no se avanza._
- [ ] **Si el loop domina:** evaluar hot-path compilado (PyO3/C) o GPU (moderngl) **solo para el dibujado de frames**, manteniendo la misma salida y el resto en Python.
- [ ] **Decidir con números:** proceder solo si el beneficio proyectado es significativo (p. ej. ≥N× en render) frente al costo de mantener una extensión nativa o una dependencia de GPU. _Prioridad: a definir tras el benchmark._

---

## 🔧 Transversal

### Gaps técnicos

- [~] **Reproducir el encode `--format prores` de una vuelta larga** para diagnosticar por qué cuelga. En Nordschleife (~394s) arranca, escribe ~4 GB de frames y se congela; el stderr ya se captura desde v2.0.0. Mitigado con el default `webm`. _Prioridad: Alta (solo afecta a quien pida prores explícito)._
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
- [x] **Recolección secuencial de workers en `_render_parallel`** — resuelto: collect round-robin en `codex/sgi-v2-merge` (2026-07-03).
- [x] **Pickle overhead en render paralelo** — resuelto: slice por rango de distancia por chunk, ~1 MB en Nordschleife (antes ~4-5 MB) en `codex/sgi-v2-merge` (2026-07-03).
- [x] **`_save_upload` no limpia archivos temporales** (`ng_helpers.py`) — resuelto: cleanup en `finally` tras cargar las vueltas + registro `atexit` como red de seguridad, en `codex/sgi-v2-merge` (2026-07-03, remediación de auditoría).
- [ ] **Inconsistencia de tokens CSS entre pasos** — ng_step2 usa `.style("color:var(--muted)")` mientras ng_step3/4 usan `text-gray-400` Tailwind tras la migración de contraste. Uniformizar ng_step2 al mismo patrón. _Prioridad: Baja._
- [x] **La versión del footer estaba hardcodeada** (`ng_app.py`, `version-badge`) — resuelto en #24 ([ADR 0023](docs/decisions/0023-fuente-unica-de-version.md)): SSOT = literal `__version__` en `fantasma/__init__.py`, `pyproject` lo deriva con `dynamic`, badge y `build_installer` lo leen. **Consecuencia:** bumpear = editar `fantasma/__init__.py`; la skill global `release-helper` (paso 2, dice pyproject) queda pendiente de actualizar cuando el PO lo autorice.
- [ ] **Subida concurrente de CSV puede perder el segundo archivo** (`ng_step1.py`) — subir referencia y piloto casi simultáneos hace que el segundo `on_upload` se pierda mientras el primero (MoTeC grande) procesa; secuencial funciona. Un usuario real sube secuencialmente, borde raro. Detectado en el e2e del recorrido pacenotes (`qa_runs/mariana-20260705-pacenotes/recorrido-e2e.md`). _Prioridad: Baja._
- [ ] **Labels truncados en los inputs del Paso 4** (`ng_step4.py`) — en la columna izquierda del rediseño 2 columnas, los inputs quedan estrechos junto al botón «Explorar…» y cortan su label flotante («Tu video de grabaci…», «Overlay del HUD (ge…», «Carpeta donde guardar el v…»). Ensanchar el input o bajar el botón debajo. Cosmético, destapado en la 2ª ronda de Mariana (`qa_runs/mariana-20260705-r2/11_step4_compose_default.png`). _Prioridad: Baja._
- [ ] **El job de render del Paso 3 vive en variable local, no en `state`** (`ng_step3.py`) — al navegar fuera durante un render activo se cancela el timer de polling pero el job sigue en background; volver al Paso 3 crea un `job_holder` nuevo y puede arrancar un segundo render concurrente sobre el mismo `outdir` (riesgo de corromper el webm). Fix: guardar el handle en `state.active_overlay_job` y cancelarlo en `_cancel_on_nav`. Pre-existente; destapado por el Reviewer en `feat/pacenotes-ui`. _Prioridad: Media._
- [x] **Cobertura de `viz/charts.py` y `viz/report.py`** — resuelto (2026-07-06): `tests/viz/test_report.py` (render_markdown rama por rama + write_outputs + integración con el pipeline real) y `tests/viz/test_charts.py` (smoke de render_charts generando PNGs + degradación sin matplotlib). Antes 0%, output primario del flujo de análisis; deterministas y sin ffmpeg (auditoría 2026-07-03, `qa_runs/2026-07-03-auditoria-integral/fase1-suite.md`).
- [ ] **Pinear la versión de ruff en pyproject** — el CI instala el último de `>=0.15,<1` y ya divergió del local una vez (I001 solo en CI, PR #15). _Prioridad: Media._
- [ ] **Endurecer los hooks de sesión** — ciegos ante commits durante la sesión, markers seteables sin hacer el trabajo, evidencia de Mariana sin validar relevancia (auditoría, `fase3-hooks.md`). _Prioridad: Media._
- [ ] **Lockfile de dependencias** (uv.lock o pip-compile) — builds no reproducibles, drift de supply chain (auditoría, `fase1-seguridad.md`). _Prioridad: Media._
- [ ] **PO: revisar las capturas del QA visual de v2.0** (`qa_runs/mariana-20260703-0740/`) — checkpoint de Mariana que vuelve al PO; la cadena H-01 del Paso 2 se cerró con esa evidencia. _Prioridad: Media._
- [ ] **PO: re-exportar el ORECA 07 INT desde MoTeC i2** — el archivo del material de pruebas carece del canal Distance y el pipeline lo rechaza (correcto); es el único de 17 no procesable (Charbel, `fase1-charbel.md`). _Prioridad: Baja._
- [ ] **Cues de cambio de marcha de la REFERENCIA (candidata de producto)** — el PO definió el norte (2026-07-06): la banda sonora completa es una "cinta de estudio" donde TODOS los sonidos marcan a la referencia (coaching + upshifts del rápido a 1500 Hz), agregados unos a otros; la vuelta del piloto solo mapea al video. Prototipo validable en `qa_runs/charbel-20260706-cinta-estudio/` (`_DEMO_COMPLETO.mp4`, 174 sonidos). Si al PO le funciona el demo, llevar "upshifts de la referencia" al motor (`pacenotes.py`) y a la UI como tipo de cue opcional. **Regla de producto: nunca generar cues desde la vuelta del piloto.** _Prioridad: Alta (pendiente del oído del PO)._
- [ ] **Lógica "fault-matched" de cues** — hoy varias reglas disparan por `pierdes ≥ 0.25 s` en vez del fallo puntual (una curva con apex bueno puede recibir "sube el apex"). Prototipada en demo la noche del 2026-07-05 (16 vs 20 cues); necesita definición de producto con el PO antes de portarla al motor ([ADR 0024](docs/decisions/0024-sincronia-pace-notes.md), fuera de alcance). _Prioridad: Media._
- [ ] **Las notas de VOZ no pasan por el plan anti-saturación** — `build_voice_pack` no usa `plan_tone_events`: anticipo fijo de 200 m (mismo defecto que los 120 m del countdown, corregido solo para tonos en el ADR 0024), sin gap global entre curvas (frases de ~7.5 s se enciman, demo `_DEMO_VOZ_referencia`), y en modo "both" tonos y voces se mezclan sin gap entre sí. El refactor correcto es extraer el plan (descarte + gap + anticipo por tiempo) para que ambos packs lo consuman (Reviewer sobre ADR 0024). _Prioridad: Media._
- [ ] **`_STEPS` y los labels del breadcrumb divergen** (`ng_helpers.py`) — dos listas de nombres de pasos ("Comparar/Componer" vs "Análisis/Video"); consolidar en una sola fuente. _Prioridad: Baja._
- [ ] **Limiter/ducking en la mezcla de pace notes** — `normalize=0` suma sin atenuar y puede clipear en picos motor+tono coincidentes; hoy aceptable por lo breve del tono. Si aparece distorsión audible: bajar `volume` del cue o añadir `alimiter` (nota en `_audio_mix_filter`). _Prioridad: Baja._
