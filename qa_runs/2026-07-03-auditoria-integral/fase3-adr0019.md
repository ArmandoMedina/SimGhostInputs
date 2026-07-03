# Fase 3 — Auditoría de METODOLOGÍA de trabajo con IA (ADR 0019 y flujo)

**Fecha:** 2026-07-03 · **Auditor:** Reviewer de método (subagente) · **Alcance:** ¿la práctica reciente
cumple lo que el método escrito exige, y tiene grietas el método mismo?
**Fuentes:** `docs/decisions/0019-*.md`, `docs/flujo-de-trabajo.md`, `HANDOFF.md`, `docs/decisions/README.md`,
`git log` 2026-06-12→07-03, `qa_runs/`, `templates/plan-de-trabajo.md`, `.gitignore`.

---

## Veredicto

**El método está bien escrito y la disciplina de commits/HANDOFF es real, pero su gate estrella —"evidencia
de QA verificable" (ADR 0019)— es teatro fuera de la máquina local: ningún artefacto llega al repo, y el
muro de CI que debía respaldarlo sigue sin ser *required*.** El método funciona mientras haya UNA sesión
disciplinada; no cubre concurrencia ni durabilidad de evidencia.

## Conteo por severidad

| Severidad | # | IDs |
|---|---|---|
| **Alta** | 3 | H1, H2, H3 |
| **Media** | 5 | M1, M2, M3, M4, M5 |
| **Baja** | 2 | L1, L2 |

## Los 3 hallazgos más graves (una línea c/u)

1. **H1 — Evidencia de QA nunca llega a git:** solo `qa_runs/README.md` está trackeado (`.gitignore: qa_runs/*`), 0 artefactos commiteados pese a que ADR 0019 y el propio README exigen `git add -f` de lo citado; el README ya se autoconfiesa ("varios artefactos que se pierden por no vivir en el repo") → el "visual PASS" pre-merge v2.0 es inauditable desde la historia.
2. **H2 — El muro que respalda todo el gate sigue apagado:** `audit`, `docs-graph`, `lint`, `pytest` no son *required checks* en el ruleset de master (HANDOFF §"Acción pendiente del PO"); por la propia regla anti-bypass de ADR 0019 el job `audit` es "cosmético" y el punto 2 del ADR queda inerte.
3. **H3 — El método no contempla sesiones concurrentes:** hoy dos sesiones de IA operaron el mismo working tree/HANDOFF a la vez (`73f5ac1` commiteado 06:22 mientras la sesión de auditoría orquestaba, `qa_runs/2026-07-03-auditoria-integral/` creado 06:46) y el flujo asume sesiones seriales — HANDOFF como archivo único compartido y hooks que leen un `git status` que la otra sesión muta.

---

## Hallazgos detallados

### H1 (Alta) — La "evidencia verificable" de QA no es verificable desde el repo
ADR 0019 §Decisión.3 y `qa_runs/README.md` mandan: *"la evidencia citada se commitea con `git add -f
qa_runs/<corrida>/<archivo>`"*. Realidad:
- `git ls-files qa_runs/` → **1 archivo**: `qa_runs/README.md`. Cero artefactos.
- `.gitignore:11-12`: `qa_runs/*` + `!qa_runs/README.md`.
- Hay artefactos locales reales y frescos (`qa_runs/playwright_e2e/step0_done.png` 2026-07-03 06:47, `mariana-*`, `pacenotes-*`), pero **viven solo en la laptop**. El README lo admite: *"que ya van varios artefactos que se pierden por no vivir en el repo"*.
- El hook `mariana-stop` verifica el **working tree**, no el commit → un artefacto satisface el gate y luego se borra/pierde. La exigencia es local y efímera; para el merge de v2.0 (lo que un revisor ve) **no existe evidencia de QA**.
**Impacto:** el aprendizaje que originó el gate ("UI rota con tests verdes") no está blindado; se reconstruyó la misma condición (evidencia que nadie más puede auditar).

### H2 (Alta) — Required checks pendientes → el gate de CI es cosmético
`HANDOFF.md:36-39` y ADR 0019 §Consecuencias lo dicen explícito: sin marcar los 4 jobs como *required* en
el ruleset, *"el job `audit` (ADR 0019) es cosmético"* y *"un rojo no-requerido deja pasar el merge igual"*.
Acción de PO abierta desde 2026-07-01 (commit `1bb6903`), 2+ días sin cerrarse, justo cuando el HANDOFF
propone mergear v2.0 a master. El pilar #2 del ADR 0019 no bloquea nada hoy.

### H3 (Alta) — Sin modelo de concurrencia entre sesiones
Evidencia de la corrida paralela de hoy: `73f5ac1` (perf viz) commiteado **06:22:14** por una sesión;
`qa_runs/2026-07-03-auditoria-integral/fase0/fase1` escritos **06:48-06:49** por la sesión de auditoría.
El método (flujo §"HANDOFF", ADR 0019 §Decisión.4 "ciclo del HANDOFF") trata el HANDOFF como **archivo único
que se llena al cerrar / se limpia al abrir** — un contrato de *lost-update* si dos sesiones lo escriben.
Además `escribano-stop`/`mariana-stop` evalúan `git status --porcelain`: si otra sesión está a medio commit,
el hook lee un árbol inconsistente. **El método debería pronunciarse:** worktree por sesión, o "una sola
sesión es dueña del HANDOFF/rama a la vez", o un lock. Hoy no dice nada → grieta real.

### M1 (Media) — Veredictos de QA sin citar el directorio de la corrida
El README exige: *"El veredicto… va a HANDOFF.md o al CHANGELOG.md, **citando el directorio de la corrida**"*.
`grep "qa_runs/<dir>"` sobre `HANDOFF.md` y `CHANGELOG.md` → **0 citas**. Los veredictos existen
("`24ce576` QA pre-merge completo, 7/7 tests E2E y visual PASS"; HANDOFF: "Todo el QA pre-merge completado")
pero **ninguno enlaza la corrida que lo respalda**. Es el patrón "afirmé que probé" que el ADR 0019 quería matar.

### M2 (Media) — Contradicción template↔práctica sobre el plan de trabajo (decisión a asentar)
`templates/plan-de-trabajo.md:8` dice a la vez *"El plan **vive en el repo** antes de ejecutar; cada paso
commiteable se commitea"* **y** *"este plan **se borra** (es efímero…)"*. La práctica de hoy ejecutó
literalmente el churn: `0679592` (2026-07-03) **añade** el plan al repo → `9006528` (mismo día) lo **retira**.
El PO ahora define que el plan es efímero y **NO se versiona** — que choca con "vive en el repo… se commitea".
**Es una decisión sin asentar:** conviene un ADR (o enmienda al 0019) que fije si el plan se versiona,
vive fuera del repo, o va a un dir ignorado. Mientras, el template manda dos cosas opuestas.

### M3 (Media) — Model-routing y delegación dependen 100% de la disciplina de sesión
El flujo §"Orquestación" define **operativamente** cuándo delegar (lectura voluminosa / autocontenida /
paralela) y qué modelo (haiku/sonnet/opus, "sube uno si dudas"). Pero **nada lo verifica**: no hay hook, log
ni artefacto que registre qué modelo se usó o si se delegó. El propio enunciado lo reconoce ("no verificable
en git"). Y el método ya documenta **dos violaciones auto-detectadas** (§"Cómo se opera": leer 2 transcripts
de ~250KB en el hilo principal; correr `push` en sesión tras delegar el commit) — atrapadas por honestidad
retrospectiva, no por barrera. Estructuralmente: bien definido, cero enforcement.

### M4 (Media) — Cambio en área de Mariana sin artefacto visual
`73f5ac1` (2026-07-03) modifica `fantasma/viz/overlay.py` (+149) — área que el router §8 asigna a **Mariana**
y que `mariana-stop` debería frenar exigiendo `qa_runs/` posterior. No hay dir de QA de overlay del 07-03
(el más reciente es `overlay-smoke-60fps-5s` del 06-30). Atenuante: es un cambio **perf**, salida pretende ser
pixel-idéntica, y trae **+85 líneas de test** (`tests/viz/test_overlay.py`) → cubierto por Charbel/pytest.
Pero por la letra del método (viz/ ⇒ evidencia visual verificable) quedó sin artefacto, y lo commiteó la
**sesión paralela** — precisamente donde el hook de la otra sesión no aplica (ver H3).

### M5 (Media) — Docs/CHANGELOG rezagados respecto al código (viola "viajan juntos")
El flujo insiste "commitea código y docs juntos" porque `escribano-stop` solo ve el working tree. Contraejemplos
en la rama v2.0: `fc16976` (feat ui-ng, 807 líneas, **0 docs / 0 tests / 0 CHANGELOG**), `26eaa05`
(fix ui, **sin CHANGELOG ni docs**) — el CHANGELOG se batchea después en commits `docs(changelog)` sueltos
(`14e7bc6`, `1aea730`, `31e4997`). Contrasta con el buen patrón: `73f5ac1`, `b14a3b3`, `6ee831f` sí empacan
código+tests+CHANGELOG+docs juntos. Convive lo correcto con el rezago; el rezago abre justo la ventana que el
método admite como su punto ciego.

### L1 (Baja) — Commit basura en la historia
`c44b3a7` (2026-06-30): *"Me quedé sin tokens en codex cambia este commit jaja"* — no-Conventional, WIP, quedó
en la línea de master. (Los ~30 commits `ui:`/`ux:` no-convencionales son todos del 2026-06-13/14, **anteriores**
a la adopción del método —flujo/roles llegan el 06-27— así que no cuentan como incumplimiento del método vigente,
pero conviene saber que la convención Conventional Commits solo se sostiene desde ~06-27.)

### L2 (Baja) — Convenciones honor-system sin verificador
El anuncio `🎭 Asiento: <rol> (en sesión)` (flujo §"Convención 🎭") y el fallback `.claude/.mariana-marker`
("respaldo para el caso raro de aprobar sin artefacto") son puertas de honor: declaradas, nada las verifica.
El marcador es explícitamente un back-door al gate de evidencia de H1.

---

## Balance de lo que SÍ cumple (justo, no solo el palo)
- **Ciclo del HANDOFF: funciona.** Tamaño oscila 15→59→64→**73**→37→43 líneas; se hincha y luego se **poda**
  (`9bc834e` "limpia HANDOFF al minimo", `7b7e1fc`). No hay estado stale acumulándose; el HANDOFF actual
  (201 tests, rama lista) es coherente con la historia. La disciplina "se limpia al abrir" es real.
- **Conventional Commits: sólido desde 06-27** (feat/fix/docs/chore/test/refactor/perf con scope).
- **Bundling code+test+CHANGELOG:** ejemplar en los commits recientes clave (`73f5ac1`, `b14a3b3`).
- **ADRs vivos y enlazados:** índice al día (0001–0019), ADR 0019 registra el porqué con camino descartado.

## Qué es teatro (declarado, nada lo verifica)
1. **Evidencia de QA durable** (H1) — el gate vive en el working tree local; nada asegura que sobreviva al commit.
2. **Muro de CI** (H2) — jobs no-*required* = verde/rojo decorativo; el método mismo lo llama "cosmético".
3. **Model-routing / delegación** (M3) — política operativa sin un solo verificador.
4. **Citas de evidencia en veredictos** (M1) — exigidas por el README, cero en la práctica.
5. **Anuncio 🎭 y `.mariana-marker`** (L2) — honor-system y back-door al propio gate.

## Recomendaciones (para el PO, sin ejecutar)
- **H2 primero (1 clic):** marcar los 4 jobs *required* — desbloquea el valor real de ADR 0019 antes del merge v2.0.
- **H1:** decidir el mecanismo de durabilidad — o `git add -f` obligatorio de lo citado (y que `mariana-stop`
  verifique commit, no working tree), o mover la evidencia a un store externo enlazado. Hoy se pierde.
- **M2:** asentar en ADR si el plan de trabajo se versiona o no; corregir `templates/plan-de-trabajo.md` para que
  no mande dos cosas opuestas.
- **H3:** añadir al método una regla de concurrencia (worktree por sesión / dueño único del HANDOFF / lock).
- **M1:** que todo veredicto de QA en HANDOFF/CHANGELOG cite `qa_runs/<dir>`.
