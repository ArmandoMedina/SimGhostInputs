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

**2026-07-09 — rama `fix/pacenotes-frenada-y-countdown`, sesión CERRADA (sin push, `ahead` de
`origin/master`).** El código de la rama está **completo, revisado y QA'd**; lo que queda es de
OÍDO del PO y el paso a PR. Esta sesión cerró los tres frentes técnicos que quedaban abiertos —
el crash de CrewChief (#9), la atribución de curva del HUD (ADR 0031) y la cabida del countdown
(D2, ADR 0032) — y reconcilió la documentación con el fuente REAL de CrewChief V4.

El plan persistido vive en `docs/planes/2026-07-09-pacenotes-frenada-y-countdown.md`. Los 13
hallazgos del PO (video de estudio, Nordschleife) se redujeron a 4 defectos + 3 preguntas de
producto; todos atendidos salvo el perfil de sonido, que es juicio del PO (ver decisiones abajo).

**Norte del producto, dicho por el PO:** todos los sonidos se generan de la vuelta de
**REFERENCIA**, para que el piloto haga imaginería mental con el video y, al llegar a pista con
CrewChief, los sonidos le sean familiares y adopte los puntos de frenada correctos. El cue de
frenada es **el que evita que se pase y se mate**; su función es llevar el pedal al máximo freno
aprovechando la transferencia de peso. Ese criterio manda sobre cualquier heurística.

### Commits de la rama (ninguno pusheado)

Bloque previo (documentado en handoffs anteriores, ya asentado): `cb2fdf8` plan · `faf6d2d`/`e2f1724`
ADR 0030 · `0ebe1a8`/`534fdae`/`b853790`/`6908d7d` `brake_start` por fases + arreglos revisión 1 ·
`fdee18f` trazabilidad de ticks · `38b2d5f` ADR 0031 · `2feacc2` helper `select_brake_phase` ·
`759413f`/`b4068ca` perfil de sonido + `--sound-profile` · `7c520ae` quita `brake_window_m` ·
`5eb5efc`/`2519513` escribano · `5670ff3` 3 deudas al ROADMAP · `4a0bb50`/`0eb08d7` 3 crashes de
entrada + auto-consistencia de la ventana de frenada · `82895bd` estado ADR 0002 en el índice ·
`b39881e` mapa de cues.

Commits de ESTA sesión (encima del bloque previo):

| Hash | Qué |
| :-- | :-- |
| `6d8cdf1` | fix(viz): overlay/charts derivan la ventana de curva del hito `brake_start` (ADR 0031, Opción A); "última coincidencia gana" para la curva dueña de la frenada |
| `4062428` | fix(overlay): blinda el orden de `corners_by_seg` (`sorted`) para el desempate — hallazgo H1 de la revisión adversarial del HUD |
| `0213730` | docs: ADR 0002 + `formato-datos` reconciliados con el fuente REAL de CrewChief V4 (`DriverTrainingService.cs`, commit `84fe63b`) |
| `a37c097` | docs: sincroniza atribución de curva del HUD (`hud-reference.md`/`ux-patterns.md`) y cierra el "SIN verificar" del ADR 0030 |
| `f8a85b8` | fix(pacenotes): **#9** — los cues mudos embarcan `silent.wav` en vez de listas vacías (Opción A) |
| `9af94e6` | fix(pacenotes): hardening #9 — `_write_silent_wav` escribe siempre |
| `a8728b7` | docs: **ADR 0032** — regla de cabida del countdown (enmienda 0025/0026/0028) |
| `3d14d41` | fix(pacenotes): **D2** — cabida del countdown "solo cede lo que puede ceder" |
| `9ef9e0e` + `f5360d7` | docs: `cues.md` reconciliado (sección pendiente-PO + mecánica del countdown) |

`pytest` verde toda la sesión, `ruff` limpio, doc-gate (`auditar.ps1`) con grafo íntegro en cada
commit de docs. Evidencias de QA en `qa_runs/`. Los markers de review/mariana los escribe el
orquestador al cerrar (todo `fantasma/` quedó revisado + QA'd).

### Lo que se logró esta sesión (revisado + QA'd, con evidencia)

1. **CrewChief #9 — crash confirmado en el fuente REAL.** Un entry de `metadata.json` con
   `recordingNames`/`fileNames` VACÍAS revienta el hilo principal de CrewChief V4
   (`getRandomRecordingName` indexa una lista vacía, sin `catch`). Nuestro pack embarcaba justo eso
   para el cue mudo `gear`. FIX Opción A: `silent.wav`. Review limpio + QA Mariana **PASA**
   (`qa_runs/mariana-20260709-172727/`: pack real 225 entries, 0 vacías, 128/128 sonoros
   byte-idénticos). Opción C (separar metadata del pack vs. subtítulo, no embarcar cues mudos/RPM)
   **DIFERIDA** a ROADMAP / Fase 5.
2. **HUD — atribución de curva (ADR 0031).** overlay/charts ya no tratan `segment_m` como
   contención; la etiqueta de curva se ancla a `brake_start`. Review adversarial (1 hallazgo H1 de
   orden, blindado en `4062428`) + QA Mariana **PASA** A/B real
   (`qa_runs/mariana-20260709-170717/`: C54 pasa de `C53/292` a `C54/102`).
3. **Countdown D2 — cabida (Fase 3, ADR 0032).** Regla "solo cede lo que puede ceder": un cue no
   protegido cede su hueco al tic del countdown; **invariante: un tic NUNCA desplaza una frenada
   protegida**. Charbel midió **24→35** curvas con 3-2-freno, **0 frenadas perdidas**. Review
   adversarial LIMPIO (S1 de seguridad refutada empíricamente) + QA A/B auditiva Mariana **PASA**
   (`qa_runs/mariana-20260709-countdown/`: 35==35 frenadas, mismo metro/energía).

## Decisiones del PO

Ambas son juicio de OÍDO, reservadas al PO. El PO delegó todo lo demás esta sesión y avisó que no
podría revisar.

- **[PENDIENTE] Perfil de sonido por defecto — ÚNICO pendiente-PO real abierto.** Los 4 videos siguen
  en OneDrive (`SimGhostInputs-QA/2026-07-09-sonidos/`). Default actual = **seno**. Recomendación de
  Mariana: partir de **A** (timbre) y robar de **B** el freno más largo.
- **[DECIDIDA-REVISABLE] Regla del countdown.** Implementada y verificada; A/B de audio entregado a
  OneDrive (`SimGhostInputs-QA/2026-07-09-countdown/`: extractos E2E C12/C20/C33 antes/después +
  LEEME + garantía de seguridad). El PO la valida/veta de oído; si no le gusta el "precio" (silenciar
  ~8 avisos de "ya a fondo" de salida), se revierte/ajusta.

## Siguiente acción (para quien abra)

1. **La rama NO está en PR.** Al llevarla a PR: **rebase sobre `origin/master`** + **unión de
   `CHANGELOG.md`** (no se tocó en la sesión; se une en PR). Verificar que sigue **ahead-only**.
2. **Esperan las dos acciones de OÍDO del PO:** el perfil de sonido por defecto y el veto/acepta de
   la regla del countdown.
3. **En pista (no automatable):** confirmar que CrewChief ya no crashea con el pack — sesión AMS2 del
   PO, Capa B.

## Backlog

Deuda anotada esta rama, NO curada (no bloquea; ya en [ROADMAP](ROADMAP.md), tareas #16–#18):

- **`turn_in`:** dos defectos reales que hoy no muerden.
- **`steering` en POR-CIENTO tratado como grados (`turn_in_deg`).** `Steering Pos` de MoTeC (%) y
  `STEERANGLE` (grados) caen en el mismo canal (`importers/motec_csv.py:23,34`).
- **`brake_strong=50` demasiado alto** para frenadas flojas del piloto → banderas falsas.
- **Menor (omisión, no contradicción):** la enumeración de razones de descarte en `cues.md` §
  "Prioridades" (~línea 78) no lista `cedio_al_countdown`; la razón sí está documentada en la sección
  del countdown.
- Modo `"both"` sin gap cruzado tono↔voz; los 3 ítems del hook de concurrencia (enmienda 2026-07-09
  del [ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).
- **Eficiencia (menor):** `brake_pre` recorre la vuelta entera por cada una de las ~55 curvas; el
  módulo ya tiene el patrón de bisección sobre `dist` ordenado (`core/normalize.py:66-79`).

**Limpieza de ramas pendiente (heredada):** 8 ramas locales del ciclo Media siguen existiendo porque
están checked-out en worktrees de otras sesiones. Están 100 % absorbidas en `dd65f9b` — sin riesgo.
Se borran cuando esas sesiones cierren sus worktrees.
