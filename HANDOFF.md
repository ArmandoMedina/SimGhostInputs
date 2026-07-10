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

> Rama rebasada sobre `origin/master` (`v2.3.1` ya liberada; detalle en [CHANGELOG](CHANGELOG.md) y [ROADMAP](ROADMAP.md)) — el "ahead-only de `origin/master`" de abajo ya lo asume.

**2026-07-10 — rama `fix/pacenotes-frenada-y-countdown`. Cerrada la tarea DOBLE FRENADA (ADR 0033).**
El PO detectó, de oído, que cuando frena → suelta a fondo → vuelve a frenar dentro de una misma curva,
la **segunda frenada no sonaba** (metros reales 803/C03 y 1119/C05). Diseño de mínimo blast-radius:
`core/corners.py` gana una función nueva `detect_brakings` y expone un campo nuevo
`milestones.brake_starts` (lista de todas las frenadas fuertes reales, criterio = **gas sostenido**
`throttle≥15%` por ≥0.15 s en el hueco); `pacenotes.py` emite un cue `brake` protegido por cada una.
**`select_brake_phase`, el escalar `brake_start` y `compare` NO se tocaron** — byte-idénticos en las
55 curvas, `d_brake_m`=0 (simetría ADR 0031 intacta). El ADR 0033 **enmienda** el 0031 (no lo revierte:
el aviso principal sigue en la fase de pico máximo; se AÑADE la segunda frenada). Suite **453 passed**,
`ruff` limpio, grafo íntegro.

- **Revisión adversarial** encontró y se arreglaron: gas sostenido (antes bastaba 1 muestra → frágil) y
  un test que tapaba el countdown ausente. El countdown de la 2ª frenada es **oportunista** (ADR 0032):
  cede con razón `tic_sin_espacio` si choca con la 1ª; el **cue** de la 2ª siempre suena (protegido).
- **Validación de Charbel** (`qa_runs/charbel-20260710-doble-frenada-validacion/`): C03 y C05 emiten 2 en
  los metros correctos. Destapó una TERCERA curva, **C21** (m7084/m7167). El PO confirmó que **C21 es
  legítima — NO subir `THROTTLE_REAPPLY` para matarla: es gemela del 803** (mismo patrón, gas modesto +
  velocidad plana). Fue trampa del PO para ver si se detectaba el acoplamiento; suenan las dos o ninguna.
- **QA de audio Mariana** (`qa_runs/mariana-20260710-doble-frenada/` + OneDrive `2026-07-10-doble-frenada/`):
  6 extractos A/B (C03/C05/C21 antes/después). Verificado que el 2º tono es NUEVO (silencio en el "antes",
  RMS 0.0), no un desplazamiento. **Pendiente: la escucha final del PO** (sin preguntas abiertas ya).

Commits de hoy: `ebd31ac` plan · `1cfecf9` ADR 0033 · `feaf660` reconcilia countdown · `bb41f5b` core
`detect_brakings` · `6f1f7a5` pacenotes · `ec061c3` endurecido+tests · `b4237ee` docs.

**Deuda que BLOQUEARÁ el push (doc-drift §8 preexistente, ajeno a hoy):** `fantasma/ui/ng_step5.py`
(commit `2ad7499`, mezcla) sin `docs/guia-usuario.md`; `tools/blast-radius.json` (commit `b39881e`) sin
`docs/flujo-de-trabajo.md`. Cerrarlas (o `--no-verify` consciente) antes del PR.

---

**2026-07-09 — sesión previa (sin push, `ahead` de `origin/master`).** El código de la rama está
**completo, revisado y QA'd**; lo que queda es de
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

- **[PENDIENTE] Perfil de sonido "mezcla" como default.** El PO YA lo aprobó de oído (2026-07-10: "el
  tema de los sonidos ya me gustó"), pero pidió cerrar frenos primero. Falta: (a) decidir si se cambia
  `DEFAULT_SOUND_PROFILE` de `"seno"` a `"mezcla"` (cambio de comportamiento audible → commit + revisión),
  y (b) su único reparo de oído pendiente — el contraste `throttle_on` vs `full_throttle` (la pareja que
  se puede confundir; ajuste de diseño de Ahiram si lo pide). Ver `qa_runs/mariana-20260709-mezcla-e2e/`.
  *(Superada la vieja recomendación "partir de A y robar de B": el PO rechazó A/B/C y salió "mezcla".)*
- **[PENDIENTE] Escucha final del PO de la doble frenada** (A/B en OneDrive `2026-07-10-doble-frenada/`).
  Sin preguntas abiertas; C21 ya confirmada. Es solo el visto bueno de oído.
- **[DECIDIDA-REVISABLE] Regla del countdown.** Implementada y verificada; A/B de audio entregado a
  OneDrive (`SimGhostInputs-QA/2026-07-09-countdown/`: extractos E2E C12/C20/C33 antes/después +
  LEEME + garantía de seguridad). El PO la valida/veta de oído; si no le gusta el "precio" (silenciar
  ~8 avisos de "ya a fondo" de salida), se revierte/ajusta.

## Siguiente acción (para quien abra)

1. **La rama ya está rebasada sobre `origin/master` (v2.3.1)** y el `CHANGELOG.md` unido
   (entradas de la rama en `[Unreleased]`, `[2.3.1]` byte-idéntico a lo liberado). Falta el
   **push + abrir PR** (force-push tras rebase; `backup/pre-rebase-doble-frenada` guarda el pre-rebase).
2. **Esperan las dos acciones de OÍDO del PO:** el perfil de sonido por defecto y el veto/acepta de
   la regla del countdown.
3. **En pista (no automatable):** confirmar que CrewChief ya no crashea con el pack — sesión AMS2 del
   PO, Capa B.

## Backlog

Deuda de esta rama, ahora MEDIDA sobre la vuelta real (`qa_runs/charbel-20260709-deudas/`; ya en
[ROADMAP](ROADMAP.md)): de las tres, **dos quedan cerradas por medición** y **una queda accionable
pero diferida** (el fix de unidad del volante, bloqueado por falta de una vuelta en grados):

- **`turn_in`:** MEDIDO (`qa_runs/charbel-20260709-deudas/`): no muerde en el par real. Veredicto:
  dos defectos latentes inertes — ceguera de unidad de `turn_in_deg` (dormida con datos en %) y
  `turn_in` unos metros antes de `segment_m[0]` (C14 y C15, −5 y −6 m, por diseño según ADR 0031);
  tercer modo (volante residual) refutado, 0 casos. Sin acción propia.
- **`steering` en POR-CIENTO tratado como grados (`turn_in_deg`).** MEDIDO
  (`qa_runs/charbel-20260709-deudas/`): no muerde en el par real (REF y piloto ambos `Steering Pos`
  %, absmax ~36; 0 de 55 curvas mal ubicadas). Veredicto: landmine LATENTE de código en
  `importers/motec_csv.py:23,34` (mezcla `Steering Pos` % y `STEERANGLE` grados en el mismo canal).
  **Único residuo accionable, DIFERIDO por falta de material:** canonizar la unidad del volante en el
  importer (o `turn_in` relativo al pico); requiere una vuelta real con `STEERANGLE` para QA.
- **`brake_strong=50`.** MEDIDO (`qa_runs/charbel-20260709-deudas/`): no muerde en el par real.
  Veredicto: mantener en 50 — el barrido {50,45,40,35} mueve 0 `brake_start` (curvas de freno
  monofásicas); de 15 banderas `frenada`, 13 legítimas y 2 marginales (C08 y C10) que no se quitan
  bajando el piso. Sin acción de código.
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
