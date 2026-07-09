# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).
>
> **Ciclo de vida (ADR 0019): se llena al cerrar, se lee y se LIMPIA al abrir.** Al arrancar
> sesión (`/arranca` lo instruye): lee esto y borra lo ya atendido — un HANDOFF que acumula
> historia deja de leerse. La historia va al CHANGELOG; el porqué, a los ADRs.

## Estado actual

**2026-07-09 — rama `fix/pacenotes-frenada-y-countdown`, en vuelo.** El ciclo de deuda técnica
"Media" (PR #45, squash `dd65f9b`) quedó cerrado y fundido; nada de aquello bloquea. Lo que sigue
es trabajo nuevo, abierto por 13 hallazgos del PO sobre un video de estudio con pace notes en
Nordschleife.

El plan persistido vive en `docs/planes/2026-07-09-pacenotes-frenada-y-countdown.md`. Los 13
hallazgos se redujeron a **4 defectos** y **3 preguntas de producto**, con forense sobre la vuelta
real (no sobre teoría).

**Norte del producto, dicho por el PO:** todos los sonidos se generan de la vuelta de
**REFERENCIA**, para que el piloto haga imaginería mental con el video y, al llegar a pista con
CrewChief, los sonidos le sean familiares y adopte los puntos de frenada correctos. El cue de
frenada es **el que evita que se pase y se mate**; su función es llevar el pedal al máximo freno
aprovechando la transferencia de peso. Ese criterio manda sobre cualquier heurística.

### Commits de la rama (ninguno pusheado)

| Hash | Qué |
| :-- | :-- |
| `cb2fdf8` | plan persistido |
| `faf6d2d` | ADR 0030 — modos estudio vs. en vivo |
| `0ebe1a8` | `brake_start` por fases + ventana ampliada (`brake_lo` = ápex previo) |
| `fdee18f` | trazabilidad de ticks de countdown descartados |
| `534fdae` | **arreglo revisión 1**: restaura el piso `brake_strong` a nivel de FASE, cruce ascendente en `turn_in`, reancla `brake_release` a la última fase cronológica |
| `b853790` | **arreglo revisión 1**: `against` reporta el evento real que estorbó, no el índice del padre |
| `6908d7d` | **arreglo revisión 1**: `brake_start` en la fase de pico máximo (no la última); `turn_in` desde `brake_start` |
| `38b2d5f` | ADR 0031 — propiedad de la frenada y contrato de `segment_m` (recomienda Opción A: derivar, no publicar) |
| `e2f1724` | ADR 0030 — evidencia externa de CrewChief en vez de cita circular |
| `2feacc2` | helper compartido `select_brake_phase`; cierra la asimetría ref/piloto de `compare.py` |
| `759413f` | perfil de sonido configurable (seno, timbre, ritmo, chirp) — sólo en `pacenotes.py` |
| `b4068ca` | cablea `--sound-profile` a CLI y UI + endurece la síntesis (7 arreglos); seno **byte-idéntico** a `759413f` (24 WAV, sha256) |
| `7c520ae` | **quita `brake_window_m`**; `compare` reconstruye la ventana desde el ápex publicado (ADR 0031, Opción A); invariante `compare(REF,REF)→d_brake_m==0` verde en las 75 curvas con frenada |
| `5eb5efc` | escribano: `formato-datos.md`, `COR-01`, `CMP-02` al día con la frenada derivada |
| `2519513` | escribano: `--sound-profile` en la guía; corrige clamp del countdown `[60,350]`→`[30,250]` |
| `5670ff3` | Armando: 3 deudas medidas al ROADMAP (steering en %, `brake_strong=50`, `turn_in`) |

Suite tras `b4068ca`: **413 passed, 11 skipped**. `ruff` limpio. Evidencias en `qa_runs/2026-07-09-*`.

### La revisión adversarial (hecha, con hallazgos atendidos)

`/code-review high` sobre `faf6d2d..HEAD`: 5 ángulos buscadores → 8 candidatos deduplicados → 1
escéptico independiente por candidato. **Ninguno refutado: 6 CONFIRMED, 2 PLAUSIBLE.**

Lección que no debe perderse: `0ebe1a8` arregló los cuatro metros que el PO pidió, **y de paso
rompió tres cosas que nadie pidió tocar**. Al ensanchar la ventana de frenada hasta el ápex previo,
esa ventana se filtró a `turn_in`, a `brake_release` y a `compare.py`. Además retiró en silencio el
piso de intensidad del 50 % (`brake_strong` quedó como parámetro muerto), con lo que un roce del
20 % podía anclar el cue de máxima prioridad 132 m antes. Los tres se arreglaron en `534fdae`.

**Arreglado (`534fdae` + `b853790`):** piso de intensidad a nivel de fase; `turn_in` por cruce
ascendente del umbral (mata el volante residual de la curva anterior); `brake_release` anclado a la
última fase cronológica y buscado sobre `data` acotado por `hi`; `against` con el evento real.

**Cerrado desde entonces:** la asimetría de `compare.py` (helper `select_brake_phase`, `2feacc2`) y
el contrato de `segment_m` (ADR 0031 + `7c520ae` quita `brake_window_m`). El código de la rama está
**completo**; lo que queda son dos decisiones del PO y el cierre (revisión → marker → rebase).

## Siguiente acción

**Lo que falta NO es código: son dos decisiones del PO y el cierre de la rama.**

1. **Fase 3 — cabida del countdown, la decide el PO con números.** Medido sobre la vuelta real: con
   la regla "solo cede lo que puede ceder", **35** curvas recuperan el 3-2-freno (hoy 24) y se
   pierden **cero** frenadas protegidas. Posición argumentada de Mau: de acuerdo con "el contador
   solo si hay espacio libre", **en desacuerdo** con que un cue no protegido (prioridad 75) cuente
   como espacio ocupado frente a un tick de frenada (prioridad 100). **No se implementa hasta que el
   PO elija.**

2. **Fase 4 — el PO elige el sonido de oído.** Cuatro videos en
   `OneDrive/SimGhostInputs-QA/2026-07-09-sonidos/`: `e2e_seno_actual.mp4` + `e2e_A_timbre.mp4` /
   `e2e_B_ritmo.mp4` / `e2e_C_chirp.mp4`. **Vuelta completa, pipeline real, sin re-encode** (MD5 del
   stream de vídeo idéntico en los cuatro; sólo cambia el audio). Sincronía **verificada** en
   721/1042/3543/20065 (±0.15 s, medido sobre el audio del propio vídeo). Recomendación de Mariana:
   partir de **A** y robar de **B** el freno más largo; **no C** (su freno se sale de 1000 Hz).
   Evidencia en `qa_runs/mariana-20260709-audio-abc/`. Ahora sí valida la sincronía (a diferencia
   del banco viejo de clips de 25 s, que se archivó).

3. **Revisión adversarial del código nuevo (`b4068ca` + `7c520ae`) — CERRADA, 4 hallazgos
   arreglados.** 3 ángulos + escépticos que reprodujeron ejecutando. Los cuatro CONFIRMED y ya
   arreglados: (a) `KeyError` en `compare()` con `corners.json` a mano — `4a0bb50`; (b) hueco de
   validación `--brake-freq 11000 --sound-profile timbre` — `4a0bb50`; (c) `--tone-duration 0`
   crashea las paletas — `4a0bb50`; (d) **auto-consistencia de la ventana de frenada**, el defecto
   profundo: `extract_milestones` calculaba su ventana con el ápex de EVENTO pero publicaba el V-Min,
   así que `compare` no podía reproducir la referencia (auto-consistencia del ADR 0031). Arreglado en
   `0eb08d7` **detrás de compuerta dura**: `brake_start` byte-idéntico en las 36 curvas con frenada
   (los 4 metros del PO incluidos), invariante 0/36 intacto, y el caso sintético del escéptico pasó
   de 20 m a 0. Dato corregido: la vuelta tiene **55 curvas, 36 con frenada** (los "75"/"108" de
   escépticos aislados venían de copias con config distinta).

4. **Cierre de la rama (mecánico):** escribir `.claude/.review-marker` con el hash del diff FINAL
   (la revisión está hecha y los 4 hallazgos atendidos — el marker es legítimo). El rebase sobre
   `origin/master` (`43f9ba8`) se hace **sólo al abrir el PR**; conflicto esperado en `CHANGELOG.md`
   resuelto **por unión**; `[Unreleased]` vacío en master (v2.3.1 ya salió).

   **OJO — la rama NO está lista para PR:** faltan las dos decisiones del PO (puntos 1 y 2), y cada
   una **añade código** que reabrirá la revisión: la regla de cabida elegida se implementa en
   `pacenotes.py`, y el perfil de sonido elegido cambia el default.

6. **Diferido a propósito:** `docs/cues.md` (el mapa de un vistazo del sistema de cues) y la Fase 5
   (frontera estudio/vivo en un ADR + guía). Los ADR 0030/0031 ya cubren lo esencial; el mapa
   consolidado espera a que los arreglos asienten.

**Sobre `.claude/.review-marker`:** la revisión adversarial está HECHA y los 4 hallazgos atendidos,
así que escribirlo ahora es legítimo (no es callar la alarma: es certificar un diff realmente
revisado). Se escribe con el hash del diff actual; cuando las decisiones del PO añadan código, ese
código reabre la revisión y el marker se rehace. `corners.py` es el motor de detección: el marker
nunca se escribe sin la revisión hecha, que es justo lo que el ADR 0019 protege.

## Backlog

Deuda anotada durante esta rama (no bloquea, ya en [ROADMAP](ROADMAP.md)):

- **`fileNames: []` revienta CrewChief (probable, severidad alta).** Auditoría externa del código de
  CrewChief: `getRandomRecordingName()` hace `recordingNames[Utilities.random.Next(recordingNames.Count)]`;
  con `Count == 0`, `Next(0)` devuelve 0 → `ArgumentOutOfRangeException`. Nuestros cues mudos
  (`gear`) emiten `fileNames: []`. El auditor **no pudo trazar** que la llamada no filtre antes, así
  que **no está verificado al 100 %**. Solo se manifiesta en pista. Arreglo propuesto: WAV silencioso
  en vez de lista vacía.
- **ADR 0030 cita circularmente al propio repo.** Sustituir por la evidencia externa ya recogida:
  `DriverTrainingService.cs::checkDistanceAndPlayIfNeeded` dispara **solo por distancia**
  (`previousDistanceRoundTrack < entry.distanceRoundTrack && currentDistanceRoundTrack > entry.distanceRoundTrack`);
  `MetaDataEntry` tiene 4 campos; CrewChief **no** trae beep de cambio por RPM propio. La tesis del
  ADR queda **CONFIRMADA**.
- **`steering` en % vs. grados.** `Steering Pos` de MoTeC (%) y `STEERANGLE` (grados) caen en el
  mismo canal (`importers/motec_csv.py:23,34`) y `turn_in_deg=8` los trata como grados. Según el
  archivo, "8°" puede significar "8 % de recorrido".
- **Doc-drift del ADR 0002:** el índice (`docs/decisions/README.md:14`) lo da como "Propuesta
  (diferida post-v1.0)" y el propio ADR como "Aceptada · implementada (v2.0)".
- **Eficiencia (menor):** `brake_pre` recorre la vuelta entera por cada una de las ~55 curvas; el
  módulo ya tiene el patrón de bisección sobre `dist` ordenado (`core/normalize.py:66-79`).
- Modo `"both"` sin gap cruzado tono↔voz; los 3 ítems del hook de concurrencia (enmienda 2026-07-09
  del [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).

**Limpieza de ramas pendiente (heredada):** 8 ramas locales del ciclo Media siguen existiendo porque
están checked-out en worktrees de otras sesiones. Están 100 % absorbidas en `dd65f9b` — sin riesgo.
Se borran cuando esas sesiones cierren sus worktrees.
