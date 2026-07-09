# Roadmap — SimGhostInputs

> Estado vivo del proyecto: dónde va y qué falta. El **porqué** de cada decisión vive en
> [`docs/decisions/`](docs/decisions/README.md); el historial de cambios enviados, en
> [`CHANGELOG.md`](CHANGELOG.md); el relevo en-vuelo, en [`HANDOFF.md`](HANDOFF.md).

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md) · 🧩 [Decisiones (ADR)](docs/decisions/README.md)

---

## Estado actual

**v2.3.1** (2026-07-09) — estable. 392 tests. Patch: repara el build del instalador Windows, que fallaba desde el [ADR 0022](docs/decisions/0022-ci-release-installer.md) sin que nadie lo notara porque `release.yml` solo corría al publicar un release (`v2.3.0` es el primer release que lo ejercitó, y falló 3 veces). `pyinstaller` pasa a vivir en el extra `pack`; nacen el workflow `installer-smoke` (ensaya el empaquetado en cada PR que lo toca) y el `workflow_dispatch` de rescate en `release.yml`. **Primer release con instalador adjunto desde v2.2.0.**

**v2.3.0** (2026-07-09) — estable. 381 tests. Cues configurables completo (catálogo, prioridad, perfiles, coast, subtítulos adaptativos, cue `gear`; ADR 0024-0028) + cierre de 8 ítems de deuda técnica Media del ROADMAP (normalización por Hz, anti-saturación de voz, job de render en `state`, lockfile, pin de ruff, hooks endurecidos, cobertura E2E; ver [CHANGELOG](CHANGELOG.md)).

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
- [x] **El job de render del Paso 3 vive en variable local, no en `state`** (`ng_step3.py`) — resuelto: el `RenderJob` ahora vive en `state.active_overlay_job` (`AppState`, `ng_state.py`), respaldado por `app.storage.tab` en vez de `app.storage.user` (el job trae un `threading.Event`, no serializable a JSON, y `app.storage.user` se respalda a disco en cada escritura); `app.storage.tab` sobrevive también a un refresh de página (F5) dentro de la misma pestaña, a diferencia de `app.storage.client`. Al reentrar al Paso 3 con un render activo, `render()` reengancha el polling sobre el job existente en vez de arrancar uno nuevo sobre el mismo `outdir`. `_cancel_on_nav` sigue cancelando solo el timer de polling (el render debe seguir en background mientras navegas). Pre-existente; destapado por el Reviewer en `feat/pacenotes-ui`.
- [ ] **El job de composición del Paso 4 tiene el mismo bug que tenía el Paso 3** (`ng_step4.py`, `job_holder` local en `_start_compose`) — mismo patrón que el ya corregido en el Paso 3 (ver entrada anterior): navegar fuera durante una composición activa y volver puede arrancar una segunda composición concurrente sobre el mismo archivo de salida. No corregido en este PR (fuera de alcance declarado); aplicar el mismo fix (`state.active_overlay_job` → un `state.active_compose_job` análogo). Destapado por el Reviewer al revisar el fix del Paso 3. _Prioridad: Media._
- [ ] **`state.active_overlay_job` (Paso 3) no protege contra dos pestañas/ventanas del mismo flujo** — `app.storage.tab` es por pestaña, no por sesión: abrir el mismo flujo en una segunda pestaña no ve el render que ya corre en la primera y puede arrancar un segundo render concurrente sobre el mismo `outdir` por defecto. Cerrar esta brecha requeriría un lock cruzado por conexión (p. ej. un registro por `outdir` en `ng_helpers.py`, o un lock de archivo), fuera de alcance del fix de "job en `state`" (que solo cubre navegación SPA dentro de una misma pestaña). Documentado como limitación conocida en `docs/guia-usuario.md`. Destapado por el Reviewer al revisar el fix del Paso 3. _Prioridad: Baja._
- [x] **Cobertura de `viz/charts.py` y `viz/report.py`** — resuelto (2026-07-06): `tests/viz/test_report.py` (render_markdown rama por rama + write_outputs + integración con el pipeline real) y `tests/viz/test_charts.py` (smoke de render_charts generando PNGs + degradación sin matplotlib). Antes 0%, output primario del flujo de análisis; deterministas y sin ffmpeg (auditoría 2026-07-03, `qa_runs/2026-07-03-auditoria-integral/fase1-suite.md`).
- [x] **Pinear la versión de ruff en pyproject** — resuelto (2026-07-09): `dev = ["ruff==0.15.20", ...]` reemplaza el rango abierto `>=0.15,<1` que ya había divergido del local una vez (I001 solo en CI, PR #15). CI y local corren ahora la misma versión exacta; subir de versión es editar el pin a mano (ver `docs/benchmark-linter.md`).
- [ ] **Endurecer los hooks de sesión** — ciegos ante commits durante la sesión, markers seteables sin hacer el trabajo, evidencia de Mariana sin validar relevancia (auditoría, `fase3-hooks.md`). _Prioridad: Media._
  - [x] **ALTO-04 resuelto**: `$ErrorActionPreference = 'SilentlyContinue'` global quitado de `review-stop.ps1`, `mariana-stop.ps1` y `escribano-stop.ps1`; las llamadas reales a `git status`/`git diff` ahora se revisan por `$LASTEXITCODE` y, si git falla de verdad (no "sin cambios"), el hook **avisa** (`additionalContext`, sin `decision: block`) en vez de pasar en silencio. El resto de hallazgos de `fase3-hooks.md` (CRITICO-01/02, ALTO-01/02/03, MEDIO-01/02) **se deja explícitamente fuera** — ya evaluados y aceptados por disciplina de proceso, no por código, en el [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md) (enmienda 2026-07-03).
- [x] **Ningún test unitario cubre lectura de `app.storage.user` en hilos `run.io_bound`** — resuelto: `tests/ui/visual/test_e2e_step5_mux_storage_context.py` ejerce la ruta real de `_do_mux` (clics de Playwright contra un server NiceGUI real de `tests/ui/visual/conftest.py`, sin el mock plano `_StateWithRowsNoDrv`), subiendo dos CSVs sintéticos mínimos para poblar `state.drv_lap`/`state.drv_name` sin telemetría real. Verificado reintroduciendo a mano el bug de #30 (leer `state.drv_name` dentro del hilo): el test falla con el `RuntimeError` real de `app.storage.user`; con el fix, pasa.
- [x] **Lockfile de dependencias** — resuelto (2026-07-09): `requirements-lock.txt` en la raíz, generado con `pip-compile` (extras `full`, `test`, `dev`) desde `pyproject.toml`; regenerable a mano en el proceso de release, documentado en `CONTRIBUTING.md` §3 ([ADR 0029](docs/decisions/0029-lockfile-pip-compile.md)). Antes: builds no reproducibles, drift de supply chain (auditoría, `fase1-seguridad.md`).
- [ ] **PO: revisar las capturas del QA visual de v2.0** (`qa_runs/mariana-20260703-0740/`) — checkpoint de Mariana que vuelve al PO; la cadena H-01 del Paso 2 se cerró con esa evidencia. _Prioridad: Media._
- [ ] **PO: re-exportar el ORECA 07 INT desde MoTeC i2** — el archivo del material de pruebas carece del canal Distance y el pipeline lo rechaza (correcto); es el único de 17 no procesable (Charbel, `fase1-charbel.md`). _Prioridad: Baja._
- [ ] **Cues de cambio de marcha de la REFERENCIA (candidata de producto)** — el PO definió el norte (2026-07-06): la banda sonora completa es una "cinta de estudio" donde TODOS los sonidos marcan a la referencia (coaching + upshifts del rápido a 1500 Hz), agregados unos a otros; la vuelta del piloto solo mapea al video. Prototipo validable en `qa_runs/charbel-20260706-cinta-estudio/` (`_DEMO_COMPLETO.mp4`, 174 sonidos). Si al PO le funciona el demo, llevar "upshifts de la referencia" al motor (`pacenotes.py`) y a la UI como tipo de cue opcional. **Regla de producto: nunca generar cues desde la vuelta del piloto.** _Prioridad: Alta (pendiente del oído del PO)._
- [ ] **Lógica "fault-matched" de cues** — hoy varias reglas disparan por `pierdes ≥ 0.25 s` en vez del fallo puntual (una curva con apex bueno puede recibir "sube el apex"). Prototipada en demo la noche del 2026-07-05 (16 vs 20 cues); necesita definición de producto con el PO antes de portarla al motor ([ADR 0024](docs/decisions/0024-sincronia-pace-notes.md), fuera de alcance). _Prioridad: Media._
- [x] **Las notas de VOZ no pasan por el plan anti-saturación** — resuelto: `build_voice_pack` reutiliza `_resolve_min_gap` (el mismo gap global que `plan_tone_events`, extraído a función de módulo) y deriva su anticipo de la velocidad de llegada a la frenada (`_voice_lead_m`, por tiempo, no metros fijos) — ver [ADR 0024](docs/decisions/0024-sincronia-pace-notes.md), enmienda "notas de voz". Sigue pendiente que el modo "both" aplique el gap CRUZADO entre tonos y voces (hoy cada pack resuelve su propio gap por separado); anotado como deuda nueva abajo.
- [ ] **`_STEPS` y los labels del breadcrumb divergen** (`ng_helpers.py`) — dos listas de nombres de pasos ("Comparar/Componer" vs "Análisis/Video"); consolidar en una sola fuente. _Prioridad: Baja._
- [ ] **Limiter/ducking en la mezcla de pace notes** — `normalize=0` suma sin atenuar y puede clipear en picos motor+tono coincidentes; hoy aceptable por lo breve del tono. Si aparece distorsión audible: bajar `volume` del cue o añadir `alimiter` (nota en `_audio_mix_filter`). _Prioridad: Baja._
- [x] **`throttle_on_window`/`full_throttle` cuentan en muestras fijas, no normalizadas por tasa de muestreo** (`fantasma/core/corners.py`) — resuelto: la ventana ahora se define en segundos (`throttle_on_window_s=0.3`) y se convierte a muestras vía el `dt` real de la vuelta; `full_throttle` reusa el mismo parámetro en vez de su propio hardcode de `15`. A 50 Hz el resultado es idéntico al comportamiento histórico (verificado con datos reales, `qa_runs/charbel-20260709-corners-window-sample-rate/`). Ver [ADR 0027](docs/decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md).
- [ ] **El coast no se emite si hay frenada sin `brake_release`** (`fantasma/core/corners.py`) — trail-braking hasta el borde del segmento deja el tramo de inercia sin nombrar. Ver ADR 0027. _Prioridad: Baja._
- [x] **`detect_gear_shifts` reimplementa el patrón de "ventana sostenida"** (`fantasma/core/corners.py`) en vez de reusar el que ya usan `throttle_on`/`full_throttle` en el mismo archivo — **evaluado y cerrado (2026-07-09), no se extrae**: resuelve un problema distinto (transición discreta entre marchas con debounce de confirmación, no un umbral continuo sostenido); forzar un helper único arriesgaría tocar código de producción reciente sin beneficio real. Ver enmienda 2026-07-09 en [ADR 0028](docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md).
- [ ] **`_gear_label` (`fantasma/viz/pacenotes.py`) duplica la lógica N/R/número de marcha** que ya existe en `fantasma/viz/overlay.py` (`t_gear_val`) — la limpieza correcta es extraer un helper compartido, no se hizo para no ampliar el diff del release ([ADR 0028](docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)). _Prioridad: Baja._
- [ ] **Un cue mudo (`gear`) y uno sonoro pueden solaparse VISUALMENTE en el subtítulo quemado** — al separar la cabida de audio en dos pools (enmienda ADR 0028, 2026-07-08), un `gear` y un cue de audio a <50 m ya no se excluyen entre sí (antes uno de los dos se descartaba). La ventana adaptativa de `build_cue_ass` (`CUE_SUB_MIN_S=1.2s`) puede terminar mostrando dos etiquetas encimadas un instante, incluida la combinación freno+cambio-de-marcha simultáneos (antes `brake` protegido siempre desplazaba al no-protegido). Sin test de `build_cue_ass` que cubra el caso (`/code-review` de alto esfuerzo, 2026-07-08). No bloquea: es un tema de legibilidad visual, no de datos incorrectos — criterio del PO al ver la cinta. _Prioridad: Media (pendiente del ojo del PO)._
- [x] **Detección de cambio de marcha (cue `gear`)** — implementado **solo-subtítulo, audio pendiente**: `detect_gear_shifts` (`fantasma/core/corners.py`) wireado end-to-end (CLI + UI), subtítulo `"cambio a Nª"` en magenta. Sin sonido a propósito (`sound=False`): evita meter una frecuencia nueva sin QA de oído. Ver [ADR 0028](docs/decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md) (enmienda al ADR 0027). Sigue pendiente el audio como follow-up de menor riesgo.
  - **Regla de diseño del PO (2026-07-08): el cambio de marcha tiene DOS modos según el contexto.**
    - **Modo estudio (cinta/video):** el upshift sale de la **referencia**, igual que el resto de la cinta — el objetivo es copiar al piloto rápido y memorizar (coherente con la regla de arriba, "todo de la referencia").
    - **Modo en vivo / ingame (asistente en tiempo real, producto futuro distinto):** el upshift **NO** sale de la referencia, se **calcula por las RPM reales del motor del piloto** en ese instante. Razón: si el piloto sale mal de una curva y cambia donde cambió la referencia, va con las revoluciones equivocadas y empeora. En vivo manda el motor del piloto, no la vuelta ideal. Es la **única excepción** a "nunca generar cues desde la vuelta del piloto" (esa regla es para la cinta de estudio; el asistente en vivo es otro producto).
- [x] **Verificar contra un `Agent` real el campo `tool_input.isolation` que consume `agent-concurrency-gate.ps1`** — resuelto (2026-07-09): se lanzó un `Agent` real con `isolation: "worktree"` (QA de PR #38) y `~/.claude/.agent-heavy-window.txt` registró una entrada nueva de inmediato. El campo coincide, el hook no está en fail-open silencioso.
- [ ] **El tope de 3 agentes "pesados" es un número sugerido, no medido** — no hay evidencia de cuánto margen real deja frente a la cuota de la cuenta; puede seguir siendo insuficiente combinado con el trabajo del hilo principal. Ajustar con datos si se repite el corte. Ver enmienda ADR 0019, 2026-07-09. _Prioridad: Baja._
- [ ] **El hook de concurrencia cubre ráfaga en paralelo, no cupo acumulado en ventana de tiempo** — si el "session limit" de la cuenta es un total por ventana (no un límite de simultaneidad), lanzar 3 agentes pesados en secuencia dentro de los mismos ~20 min puede agotarlo igual sin que el tope de concurrencia dispare nunca. Falta confirmar la naturaleza real del límite con el proveedor. Ver enmienda ADR 0019, 2026-07-09. _Prioridad: Media._
- [ ] **Modo "both" no aplica gap cruzado entre tonos y voces** (`fantasma/viz/pacenotes.py::build_pack`) — al arreglar el gap de `build_voice_pack` (ver arriba, ADR 0024 enmienda "notas de voz"), cada pack (`build_tone_pack`/`build_voice_pack`) sigue resolviendo su propio `min_gap_m` por separado; en modo `"both"` un tono y una narración de curvas distintas todavía pueden caer muy cerca uno de otro en el tiempo. Requiere fusionar ambas listas de candidatos ANTES del gap (o un segundo pase de `_resolve_min_gap` sobre la unión) — no se hizo en este fix para no ampliar su alcance (el bug reportado era la ausencia total de gap DENTRO de las voces, no el cruce con tonos). _Prioridad: Baja._
