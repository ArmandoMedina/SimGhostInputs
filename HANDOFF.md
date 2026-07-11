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

> **`v2.4.0` liberada (2026-07-10) con instalador Windows adjunto.** `master` limpia y al día;
> detalle en [CHANGELOG](CHANGELOG.md) y [ROADMAP](ROADMAP.md). Lo que queda es de **OÍDO del PO**.

**2026-07-11 — SGI se enchufa al lazo de sincronización labs↔Jidoka (primer consumidor). [ADR 0036]**

> *La lección sube, la máquina baja.* Sobre la convergencia manual de ADR 0034/0035, ahora hay máquina.
> Rama de trabajo: `lazo-sincronizacion-jidoka` (sin push, sin merge). Solo se **añadieron** archivos —
> el motor de SGI (`verificar.ps1`/`auditar.ps1`/hooks) **no se tocó**; pytest sigue verde.

- **Sello sembrado** (`tools/jidoka-motor.json`): registra que el motor de SGI corresponde a Jidoka
  **0.10.1-beta** + el SHA256 de cada pieza mecánica. Es la línea base honesta para futuros `-Actualizar`.
  NO sella instancia/estética (ley, `product/`, skills-persona, comandos).
- **Canal de subida disponible:** `tools/reportar-leccion.ps1` (abre el issue prellenado en Jidoka) +
  guía `docs/guias/reportar-leccion-a-jidoka.md`. Estado consultable con
  `tools/estado-motor.ps1 -Jidoka <ruta-de-Jidoka>` (aviso, no muro).
- **El motor NO se auto-actualiza:** la divergencia de dominio (ruff/pytest, `engineering/`, pre-push
  bash) y estética (casting de personas, comandos sin namespace) **se preserva**; la mecánica común se
  converge cuando exista la costura, en rama y revisando el diff.
- **Lecciones draft pendientes de presentar** en `qa_runs/lazo-sync-20260711/` (redactadas, NO subidas):
  (1) excepción de QA visual "con nombre" para el mandato sintético-only; (2) `probar-gate.ps1` como
  ítem de **bajada** (necesita `-Cambiados` en `verificar.ps1`, que Jidoka ya tiene); (3) dos cosechadas
  del ADR 0019 (durabilidad de evidencia con `git add -f`; tope de agentes worktree por hook). También
  ahí: `divergencias.md` (comparación pieza por pieza) y `estado-motor.txt`.
- **[Decisión humana]** `estado-motor.ps1` reporta **atrás**: el checkout local de Jidoka ya está en
  **0.11.0-beta** (rama en-vuelo, sin publicar). Cuando 0.11.0-beta se libere, evaluar la bajada. Detalle
  en `qa_runs/lazo-sync-20260711/divergencias.md`.

**2026-07-10 — v2.4.0 publicada. La DOBLE FRENADA (ADR 0033) quedó cerrada, mergeada y versionada.**

- **Doble frenada (ADR 0033) en master.** El PO detectó, de oído, que cuando frena → suelta a fondo →
  vuelve a frenar dentro de una misma curva, la **segunda frenada no sonaba** (metros reales 803/C03 y
  1119/C05). Ahora **cada frenada real de una curva suena, no solo la primera**: `core/corners.py` gana
  `detect_brakings` y expone el campo nuevo `milestones.brake_starts` (lista cronológica de toda frenada
  fuerte real; criterio = **gas sostenido** `throttle≥15%` por ≥0.15 s); `pacenotes.py` emite un cue
  `brake` **protegido** por cada una. **`select_brake_phase`, el escalar `brake_start` y `compare` NO se
  tocaron** (simetría ADR 0031 intacta; el ADR 0033 **enmienda** el 0031, no lo revierte). C21 (m7084/m7167)
  es legítima y suena doble por diseño. Entró por **PR #52 (squash, `aa63e41`)**, CI verde, suite 453 passed.
- **v2.4.0 cortada y publicada.** **PR #53 (squash, `098c755`)**, tag `v2.4.0`, release público de GitHub
  con instalador adjunto — `SimGhostInputs-v2.4.0-Setup.exe` (84.8 MB) y
  `SimGhostInputs-v2.4.0-portable.zip` (124 MB). `release.yml` corrió en **4m15s, todos los pasos verdes**.
  Minor por la superficie nueva (`milestones.brake_starts` + cue por frenada), no solo fixes.
- **Video E2E de la vuelta completa corregida** en OneDrive
  `SimGhostInputs-QA/2026-07-10-doble-frenada/e2e_doble_frenada_subs.mp4` (995 MB, 394 s, perfil mezcla):
  C03/C05/C21 suenan y se **rotulan doble**. Evidencia en
  `qa_runs/mariana-20260710-doble-frenada-e2e-completo/`.

Ramas de esta sesión ya borradas: `fix/pacenotes-frenada-y-countdown`, `backup/pre-rebase-doble-frenada`,
`chore/release-v2.4.0`.

**Norte del producto (recordatorio del PO):** todos los sonidos se generan de la vuelta de
**REFERENCIA**, para que el piloto haga imaginería mental con el video y, al llegar a pista con CrewChief,
los sonidos le sean familiares y adopte los puntos de frenada correctos. El cue de frenada es **el que
evita que se pase y se mate**. Ese criterio manda sobre cualquier heurística.

## Decisiones del PO (de OÍDO, pendientes)

Son juicio de OÍDO, reservadas al PO — **no son de código**.

- **[PENDIENTE] Escucha final del PO de la doble frenada.** Tiene el video E2E de la vuelta completa en
  OneDrive (`2026-07-10-doble-frenada/e2e_doble_frenada_subs.mp4`). Sin preguntas abiertas; C03/C05/C21 ya
  confirmadas y rotuladas doble. Es solo el visto bueno de oído sobre lo ya liberado.
- **[PENDIENTE] Perfil `mezcla` como default + contraste throttle_on/full_throttle.** El PO ya lo aprobó
  de oído (2026-07-10: "el tema de los sonidos ya me gustó"), pero pidió cerrar frenos primero. Falta:
  (a) decidir si se cambia `DEFAULT_SOUND_PROFILE` de `"seno"` a `"mezcla"` (cambio de comportamiento
  audible → commit + revisión), y (b) su único reparo de oído pendiente — el contraste `throttle_on` vs
  `full_throttle` (la pareja que se puede confundir; ajuste de diseño de Ahiram si lo pide). Ver
  `qa_runs/mariana-20260709-mezcla-e2e/`.
- **[DECIDIDA-REVISABLE] Regla del countdown.** Implementada y verificada; A/B de audio entregado a
  OneDrive (`SimGhostInputs-QA/2026-07-09-countdown/`). El PO la valida/veta de oído; si no le gusta el
  "precio" (silenciar ~8 avisos de "ya a fondo" de salida), se revierte/ajusta.

## Siguiente acción (para quien abra)

1. **Recoger las decisiones de OÍDO del PO** (sección de arriba): visto bueno de la doble frenada ya
   liberada, y `mezcla` por defecto + contraste `throttle_on`/`full_throttle`. **Nada de código está
   bloqueado** — solo esperan el oído del PO.
2. **[Diferido, en ROADMAP] Migrar el QA E2E al pipeline nativo — QA desde el producto, no desde scripts
   «por fuera».** Meta: QA E2E 100% desde la UI / el pipeline de `fantasma`, cero scripts ad-hoc. Concreto:
   **exponer `burn_cue_subs` en la UI** (Paso 4 / compose) y **retirar** `subs_burn.py` / `run_fantasma.py`
   / `verificar_sync.py` de `qa_runs/`. La base nativa **ya existe** (`fantasma/viz/compose.py` acepta
   `burn_cue_subs=True` y quema `cue_subs.ass` en el mismo pase). El QA actual funciona; se migra después,
   no ahora. Detalle en [ROADMAP](ROADMAP.md).
3. **En pista (no automatable):** confirmar que CrewChief ya no crashea con el pack (#9) — sesión AMS2 del
   PO, Capa B.

## Backlog

Deuda **preexistente vigente** (no tocada esta sesión, sigue abierta):

- **`turn_in` / unidad del volante.** MEDIDO (`qa_runs/charbel-20260709-deudas/`): no muerde en el par
  real. Único residuo accionable, **DIFERIDO por falta de material:** canonizar la unidad del volante en
  el importer (`importers/motec_csv.py:23,34` mezcla `Steering Pos` % y `STEERANGLE` grados en el mismo
  canal) o hacer `turn_in` relativo al pico; requiere una vuelta real con `STEERANGLE` para QA.
- **Menor (omisión, no contradicción):** la enumeración de razones de descarte en `cues.md` §
  "Prioridades" (~línea 78) no lista `cedio_al_countdown` (ni los `antes_de_la_meta` / `tic_sin_espacio`
  del ADR 0032); las razones sí están documentadas en la sección del countdown.
- Modo `"both"` sin gap cruzado tono↔voz; los 3 ítems del hook de concurrencia (enmienda 2026-07-09 del
  [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).
- **Eficiencia (menor):** `brake_pre` recorre la vuelta entera por cada una de las ~55 curvas; el módulo
  ya tiene el patrón de bisección sobre `dist` ordenado (`core/normalize.py:66-79`).
- **QA Pace Notes en sesión real en pista (AMS2):** los 3 ítems de `--mode both` en pista real (voz+tono
  sin solaparse, WAV con ffprobe, tonos en los metros correctos de oído). Requiere AMS2 — no bloquea
  merge. Detalle en [ROADMAP](ROADMAP.md).

**Limpieza de ramas pendiente (heredada):** 8 ramas locales del ciclo Media siguen existiendo porque
están checked-out en worktrees de otras sesiones. Están 100 % absorbidas en `dd65f9b` — sin riesgo.
Se borran cuando esas sesiones cierren sus worktrees.
