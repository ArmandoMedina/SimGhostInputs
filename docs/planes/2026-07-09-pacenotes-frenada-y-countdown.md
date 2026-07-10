---
tipo: plan-de-trabajo
estado: en_curso
---

# Plan — Pace notes: frenada tardía, contador mutilado y sonidos indistinguibles

> **Para qué es esta plantilla (ADR 0019, enmienda 2026-07-03):** una tarea larga con IA muere a media ejecución (tokens, contexto compactado, subagente caído) — y lo no escrito se pierde (pasó aquí: "me quedé sin tokens" a media migración NiceGUI). El plan te da un guion para no perder el hilo. Al retomar: **verifica contra el código real**, no contra el resumen de la sesión anterior (los resúmenes de compactación pueden mentir — caso `storage.user` vs `storage.client`).
>
> **El plan es EFÍMERO y NO se versiona** (decisión del PO, 2026-07-03; ADR 0019 §Enmienda). Vive en la **sesión / el task-tracker** mientras la tarea corre — **no** se commitea, ni siquiera a `docs/planes/`. Al morir la tarea, lo durable se reparte:
>
> - dejó una **decisión** (elegiste un camino sobre otro) → va a un **ADR**;
> - dejó **estado en vuelo** al morir la sesión (rama, último paso, qué NO tocar) → va al **HANDOFF**;
> - resultado liberable → **CHANGELOG**.
>
> Cuando la tarea cierra, el plan simplemente se descarta: su valor ya migró a ADR/HANDOFF/CHANGELOG.
>
> **Nota de esta instancia:** el propio plan (ver `Plan` más abajo) instruye persistirlo en el repo
> antes de empezar, por su tamaño y por el riesgo de corte de contexto en una tarea de 7 fases. Se
> commitea como excepción puntual; al cerrar la tarea, su contenido se reparte a ADR/HANDOFF/CHANGELOG
> como marca esta plantilla, y la instancia se puede borrar.

## Objetivo

Cerrar los 13 hallazgos que el PO levantó sobre un video de pace notes en Nordschleife, reducidos a
**cuatro defectos** de código (no 13 bugs sueltos) y **tres preguntas de producto**, de forma que:
para las curvas reales de la vuelta de referencia (`C:\Users\jose_\Downloads\Pruebas finales`),
(a) el hito de frenada de las curvas en los metros 3589 y 20064 caiga donde empieza la frenada real,
(b) las curvas que hoy suenan con 2 sonidos recuperen el tercero cuando corresponda, (c) ningún tick
se descarte del `plan.json` sin razón registrada, y (d) el catálogo de sonidos deje de ser una única
onda seno y el PO elija variante tras oírlas. Verificable con `pytest` en verde, `tools/verificar.ps1`
limpio, y el pipeline extremo a extremo (`detect` → `compare` → `pacenotes`) corrido sobre material real
con evidencia en `qa_runs/2026-07-09-pacenotes-frenada/`.

## Contexto

El PO revisó un video de estudio con pace notes sobre Nordschleife y levantó 13 hallazgos.
Tras leer el motor y hacer forense sobre un `plan.json` real (55 curvas), los 13 se reducen a
**cuatro defectos** y **tres preguntas de producto** — no son 13 bugs sueltos.

El norte, dicho por el PO: *todos los sonidos salen de la vuelta de REFERENCIA*, para que el
piloto haga imaginería mental con el video y, al llegar a pista con CrewChief, los sonidos le
sean familiares y adopte los puntos de frenada correctos. El cue de frenada es el que **evita
que se pase y se mate**, y su función es *llevar el pedal al máximo freno aprovechando la
transferencia de peso*. Ese es el criterio que manda sobre cualquier heurística.

### Evidencia ya recogida (no repetir)

De `C:\Users\jose_\Downloads\Pruebas finales\_pack_v2\plan.json` (pack **viejo**: sus `lead_m`
de 171–242 m solo salen con el `countdown_gap_s` de 1.75 s previo al ADR 0028 — sirve para
estructura, no para los metros exactos):

- 55 curvas; **solo 35 tienen cue de frenada**. 20 curvas no emiten ninguno.
- Del 3-2-freno completo: **11 curvas**. Con el patrón roto de 2 sonidos (1 tick + freno):
  **13 curvas**. Con frenada pero sin ningún tick: 11.
- `skipped_global` tiene **6 entradas, ninguna es un tick**.

### Los cuatro defectos

**D1 — Los ticks se descartan en silencio.** `fantasma/viz/pacenotes.py:417-420` hace `continue`
sin registrar nada. `plan.json` se documenta como "la auditoría de qué suena y qué no" y **miente
por omisión**. Es el defecto que hay que arreglar primero: sin él, todo lo demás se diagnostica a
ciegas.

**D2 — Un cue menor mata el aviso de la frenada.** La prueba de cabida del countdown
(`pacenotes.py:419`) es **puramente por distancia y no mira prioridad ni protección**. En la
ventana [3450-3700] el `full_throttle` de C11 (prioridad 75) vive en 3470 y el tick de C12 caería
en 3452: 18 m → tick eliminado. Idéntico en C54 (tick en 20016 vs `full_throttle` en 20023). Un
cue informativo de salida borra el aviso de la frenada siguiente, que es prioridad 100 y protegida.
→ Explica los hallazgos 2, 3, 5 y 10.

**D3 — `brake_start` puede señalar la segunda pisada, no el inicio de la frenada.**
`fantasma/core/corners.py:143-146`: `blk = strong[-1]` toma el **último** bloque con pico ≥50 %.
Si la referencia frena fuerte, suelta >0.3 s y vuelve a pisar, el hito salta a la segunda pisada.
El comentario dice que es para ignorar blips de trail-braking previos, pero el filtro también
descarta una primera frenada fuerte legítima. Es la hipótesis principal de los hallazgos 8 y 13
(cue ~50-60 m tarde). **Hipótesis, no hecho: la fase 0 la confirma o la tira.**

**D4 — Los sonidos son la misma onda.** `DEFAULT_FREQS` + `generate_tone` (`pacenotes.py:186`):
todos son seno puro de 0.12 s; solo cambia la frecuencia. Con motor de fondo, el tono solo no
separa. → Hallazgo 7.

### Lo que NO es un bug

- **Hallazgo 3 ("sale doble")**: no es doble. Son dos cues distintos — `contador de frenada` (tick)
  y `punto de frenada` (el "ya"). Lo que falta es **el segundo tick**, víctima de D2. La lectura
  correcta, según ADR 0025, es *tick — tick — FRENO*.
- **Hallazgos 9 y 11 ("con 2 sonidos la frenada suena tarde")**: probablemente **percepción, no
  desincronía**. Un patrón de 2 sonidos se oye como "3-2…" y el oído espera un tercero; el piloto
  frena tarde porque *cuenta de más*. Cuando D2 se arregle, la mayoría de esas 13 curvas
  recuperarán su tercer sonido. Si aun así quedan curvas de 2 sonidos, hay que decidir qué hacer
  (ver Fase 3). **Si la fase 0 muestra desincronía real, esta lectura se cae y se trata como bug.**
- **Sincronía distancia→tiempo**: las distancias salen de la referencia y el instante se calcula
  sobre la vuelta del piloto (`pacenotes.py:656` y `:1220`). Es **deliberado** y correcto: el cue
  suena cuando el piloto pisa el metro donde la referencia frenaba. No hay `adelay` ni `itsoffset`
  en el mux (`viz/compose.py`), no hay offset oculto.

### Respuestas directas a las preguntas del PO

- **Hallazgo 6 — turn-in**: primera muestra **después del inicio de frenada** con volante > 8°
  hacia el lado del ápex, y antes del ápex (`core/corners.py:157-165`). Como cue, solo se emite si
  en esa curva **pierdes ≥ 0.25 s** (`pacenotes.py:867`).
- **Hallazgo 12 — coast**: tramo entre soltar freno (o el `lift`) y el gas sostenido, con freno
  < 10 % y acelerador < 5 % (`core/corners.py:187-202`). **Nunca lo oyes** porque viene
  `enabled: False` y `solo_sin_frenada: True` (`pacenotes.py:921-937`).

### Desacuerdo explícito sobre el contador

El PO propone: *"el contador es solo si hay espacio libre"*. **Estoy de acuerdo con el principio y
en desacuerdo con lo que hoy cuenta como espacio ocupado.**

Hoy "ocupado" significa *cualquier cue a menos de 50 m* — incluido un `full_throttle` informativo
de la curva anterior. Eso invierte la jerarquía: el cue que existe para que no te mates cede ante
el que te dice que ya estás a fondo. Propongo mantener la regla oportunista, pero que "espacio
ocupado" signifique **solo lo que no puede ceder**: frenadas y ticks de *otras* curvas. Un cue no
protegido (`turn_in`, `throttle_on`, `full_throttle`, `brake_release`) **cede su hueco** al tick.

No lo doy por decidido: la Fase 3 **mide** sobre la vuelta real cuántas curvas recuperan el
3-2-freno con cada regla, y el PO elige con el número delante.

## Pasos (cada uno commiteable y verde)

- [ ] **Fase 0 — Banco de diagnóstico sobre la vuelta real** *(no toca el motor)*. Asiento:
  **Charbel**. Salida: `qa_runs/2026-07-09-pacenotes-frenada/`. Script que carga la referencia y el
  piloto reales de `C:\Users\jose_\Downloads\Pruebas finales`, corre `detect_corners` +
  `extract_milestones` + `plan_tone_events` con el código de hoy, y vuelca:
  - **Por curva**: bloques de freno (metro de inicio, fin, pico, hueco con el bloque anterior),
    cuál eligió `strong[-1]`, el ápex, y la velocidad de llegada.
  - **Por evento**: los cues seleccionados y los descartados **con razón**, instrumentando a mano
    el `continue` silencioso de los ticks.
  - **Tabla focalizada** en los metros que citó el PO: 721, 803, 1050, 3589, 20064.
  - **Cambios de marcha** alrededor de 803 y 20129: dirección real (subida/bajada) vs etiqueta.

  Esto responde, con evidencia y no con teoría:
  - ¿Por qué 20 de 55 curvas no tienen cue de frenada? (hallazgos 1 y 5) — ¿frenada real
    inexistente o hito perdido?
  - ¿`brake_start` salta a la segunda pisada en 3589 y 20064? (hallazgos 8 y 13) — confirma o tira
    D3.
  - ¿Los 2 sonidos suenan donde deben, o hay desincronía real? (hallazgos 9 y 11).
  - ¿Los cues de marcha del hallazgo 4 están bien etiquetados y bien ubicados?

  **Puerta:** sin este artefacto no se toca `core/`. Las constantes de la Fase 2 se calibran con
  estos datos, no se inventan. Verificación: artefacto presente en
  `qa_runs/2026-07-09-pacenotes-frenada/` con las cuatro respuestas arriba.

- [ ] **Fase 1 — Los descartes dejan rastro** *(pequeña, desbloquea todo)*.
  `fantasma/viz/pacenotes.py:397-432`: los dos `continue` del countdown pasan a registrar en
  `skipped` con razón (`antes_de_la_meta`, `tic_sin_espacio`) y a salir en `plan["skipped_global"]`.
  Verificación: test que afirma que un tick descartado aparece en el plan con su razón.

- [ ] **Fase 2 — `brake_start` = inicio de la fase que lleva al máximo freno**. Asiento:
  **Ahiram** + validación de **Charbel**. Archivo: `fantasma/core/corners.py:131-152`. Regla
  propuesta, **a calibrar con la Fase 0**: agrupar los bloques de freno en **fases** (fusionando
  los separados por menos de un umbral, mientras el coche siga desacelerando); elegir la fase que
  contiene el **pico de freno máximo** antes del ápex; anclar `brake_start` en la **primera
  muestra** de esa fase. Cumple el criterio del PO: marca dónde empezar a cargar el pedal hacia el
  máximo, no dónde ya vas a mitad de la frenada. Efecto colateral esperado y deseado: al mover
  `brake_start`, el `lead_m` y los ticks se recolocan. Verificación: tests en
  `tests/core/test_corners.py` — caso de doble pisada (freno fuerte → suelta → freno fuerte) con
  `make_lap`; caso de blip de trail-braking previo que **no** debe adelantar el hito; no-regresión
  de la frenada simple.

- [ ] **Fase 3 — Cabida del countdown, decidida con números**. `fantasma/viz/pacenotes.py:397-432`.
  Implementar la regla "solo cede lo que puede ceder" y **medir** sobre la vuelta real: cuántas
  curvas quedan con 3 sonidos, 2 y 1, bajo (a) la regla de hoy, (b) la regla propuesta. Se le
  presenta la tabla al PO. Queda abierto, sujeto a esa tabla y al banco de sonidos: **qué hacer
  cuando solo cabe un tick** — suprimirlo (todo-o-nada, el ritmo nunca miente) o darle un timbre
  propio de "aviso único". Verificación: tabla comparativa (a) vs (b) presentada al PO + tests en
  `tests/viz/test_pacenotes.py` (cabida del countdown, descartes con razón).

- [ ] **Fase 4 — Banco de sonidos y videos comparativos**. Asiento: **Mariana**. El PO pidió
  **oírlos antes de decidir**. Generar, sobre el mismo tramo real, tres variantes del catálogo y
  **un video corto por variante**:
  1. **Timbre por familia** — frenada con armónicos (corta el ruido de motor), ticks como clics de
     seno, gas triangular.
  2. **Ritmo y duración** — frenada del doble de largo, gas como doble-blip, turn-in como pulso
     breve.
  3. **Chirp** — el gas barre hacia arriba, el freno hacia abajo.

  Evidencia en `qa_runs/`. El PO elige; recién entonces se toca `DEFAULT_FREQS`/`generate_tone`.
  Verificación: tres videos comparativos en `qa_runs/2026-07-09-pacenotes-frenada/` y veredicto del
  PO registrado.

- [ ] **Fase 5 — La frontera estudio / en-vivo, por fin escrita donde manda**. Asiento: **Armando**.
  Esto no es deuda menor: es **la causa de que el PO tenga que re-explicar lo mismo cada sesión**, y
  él mismo señaló que la complejidad lo está rebasando.

  **Lo que se descubrió al buscarlo:**
  - La regla **sí está escrita**, literal, en `ROADMAP.md:140-143` (estudio = referencia; en vivo =
    RPM reales del piloto; "es la única excepción a *nunca generar cues desde la vuelta del
    piloto*"). No falta el texto: **falta que esté donde alguien lo lea al decidir.** Vive en un
    ítem de backlog marcado `[x]`, no en un ADR, ni en `docs/guia-usuario.md`, ni en `product/`.
  - **El hallazgo nuevo, que nadie había conectado:** un pace note de CrewChief **se dispara por
    `distanceRoundTrack`** — por el metro de pista. El formato **no admite** un disparo por RPM.
    Por tanto un cue de cambio de marcha por revoluciones **no cabe, por construcción, en un pack
    de CrewChief**: exige el listener en vivo (`fantasma-live`, UDP), que el **ADR 0002 dejó
    diferido y fuera de este repo** (`0002-crewchief-pacenotes.md:151-157`). Esa implicación no
    está escrita en ningún lado y es justo la que se pierde entre sesión y sesión.

  **Entregables:**
  1. **ADR nuevo — "Modos estudio vs. en vivo: qué ancla cada cue".** Fija: los cues de posición
     (frenada, turn-in, gas) se anclan a la **distancia de la referencia** y viajan en el pack de
     CrewChief; los cues de **estado del motor** (cambio de marcha) se anclan a las **RPM del
     piloto** y **no pueden viajar en ese pack** — pertenecen a `fantasma-live`. Consecuencia
     operativa: en modo estudio el `gear` es legítimo como **subtítulo** del video, y **nunca** debe
     ganar un WAV en el exportable.
  2. **`docs/cues.md` — el mapa de un vistazo.** Hoy el sistema de cues está repartido entre cinco
     ADRs (0024-0028) + `formato-datos.md` + `guia-usuario.md`, y **ningún documento lo cuenta
     entero**. Un solo documento: catálogo, prioridades, qué es protegido, cómo funciona el
     countdown, y la frontera estudio/vivo. Los ADRs siguen siendo el *porqué*; este es el *qué*.

  Verificación: ADR nuevo mergeado + `docs/cues.md` existente y referenciado desde
  `CONTRIBUTING.md` §8 y `tools/blast-radius.json`.

- [ ] **Fase 6 — Deuda anotada, no resuelta aquí** (registrar, no cerrar en esta rama):
  - **`fileNames: []` nunca se verificó contra CrewChief.** El código emite entradas de cue mudo
    con listas vacías (`pacenotes.py:1061-1082`) y `docs/formato-datos.md:113` lo declara, pero el
    spec original (ADR 0002, §metadata.json) **siempre trae un WAV**. Nadie comprobó que el parser
    de CrewChief acepte una entrada sin audio. Riesgo real de pack roto en pista. → QA con
    CrewChief.
  - **`steering` en % vs grados**: `Steering Pos` de MoTeC (%) y `STEERANGLE` (grados) caen en el
    mismo canal (`importers/motec_csv.py:23,34`) y el umbral de turn-in los trata como grados.
    Según el archivo, "8°" puede significar "8 % de recorrido". → ROADMAP.
  - **Doc-drift del ADR 0002**: el índice (`docs/decisions/README.md:14`) lo da como "Propuesta
    (diferida post-v1.0)" y el propio ADR como "Aceptada · implementada (v2.0)". → Escribano.

- [ ] **Documentación (§8 del CONTRIBUTING)**:
  - **ADR nuevo (A)** — semántica de `brake_start` y regla de cabida del countdown. Enmienda
    declarada a los ADR 0025/0026/0028.
  - **ADR nuevo (B)** — modos estudio vs. en vivo (Fase 5).
  - `docs/cues.md` (nuevo) + su entrada en la tabla SSOT de `CONTRIBUTING.md` §8 y en
    `tools/blast-radius.json`.
  - `docs/formato-datos.md` — algoritmo de detección de frenada (es su SSOT).
  - `product/capacidades/PAC-02 - Plan anti-saturacion de senales.md` — criterios Gherkin nuevos.
    (De paso: hoy dice clamp `[60,350]`; el código usa `[30,250]`. Drift a corregir.)
  - `CHANGELOG.md` y `ROADMAP.md` (el ítem de `gear` deja de ser la única ancla de la regla).

- [ ] **Verificación final**:
  1. **Determinista:** `pytest` completo en verde (hoy: 381 passed, 11 skipped). Tests nuevos en
     `tests/core/test_corners.py` (fases de frenada) y `tests/viz/test_pacenotes.py` (cabida del
     countdown, descartes con razón).
  2. **Barreras:** `tools/verificar.ps1` limpio (lint, formato, tests, doc-gate, grafo de docs).
  3. **Extremo a extremo con material real** — la prueba que importa: `fantasma detect` sobre la
     referencia real → `compare` → `pacenotes` → `plan.json`. Verificar en el plan que (a) el hito
     de frenada de las curvas de 3589 y 20064 cae donde empieza la frenada real, (b) las curvas que
     hoy tienen 2 sonidos recuperan el tercero, (c) ningún tick se descarta sin razón registrada.
  4. **QA visual/auditiva (Mariana):** videos comparativos de las 3 variantes de sonido y del tramo
     corregido, con artefactos en `qa_runs/2026-07-09-pacenotes-frenada/`. Sin artefacto no hay
     veredicto — lo verifica el hook.

## Decisiones tomadas en el camino

- **Rama nueva `fix/pacenotes-frenada-y-countdown`, desde `origin/master` sincronizado** — no desde
  la `master` local, que hoy está `ahead 1, behind 3` respecto a `origin/master` (el commit local
  `aab9dda` ya entró como `53976b4` vía PR #46; son el mismo contenido con distinto SHA). Esta
  instancia del plan se persiste en el repo (`docs/planes/`, usando la plantilla
  `templates/plan-de-trabajo.md`) y se commitea antes de empezar, como excepción declarada por el
  tamaño de la tarea (7 fases) y el riesgo de corte de contexto — ver nota al pie de esta plantilla.
- Los hallazgos 3, 9 y 11 del PO **no se tratan como bugs de código**: son percepción/nomenclatura
  (ver "Lo que NO es un bug" arriba), condicionado a que la Fase 0 no muestre desincronía real.
- Regla de "espacio ocupado" del countdown: se propone que solo lo **no protegido** (`turn_in`,
  `throttle_on`, `full_throttle`, `brake_release`) ceda su hueco al tick; frenadas y ticks de otras
  curvas no ceden. **No decidido** — la Fase 3 mide y el PO elige con el número delante.
- La frontera estudio/en-vivo (Fase 5) se resuelve con dos entregables nuevos (ADR + `docs/cues.md`)
  en vez de seguir dependiendo de un ítem de `ROADMAP.md` marcado `[x]` que nadie relee al decidir.

## Para retomar en frío

- **Rama:** `fix/pacenotes-frenada-y-countdown`, creada desde `origin/master` (commit
  `75fed70` — "fix(ci): declarar pyinstaller y ensayar el empaquetado antes del release (#49)").
- **Último paso completado:** ninguno de los pasos de ejecución todavía; esta instancia solo
  transcribe y persiste el plan. La Fase 0 (banco de diagnóstico) es el siguiente paso real y
  **es la puerta**: sin su artefacto en `qa_runs/2026-07-09-pacenotes-frenada/` no se toca
  `fantasma/core/` ni `fantasma/viz/pacenotes.py`.
- **Qué comando corre el estado actual:** `pytest` (hoy: 381 passed, 11 skipped) confirma que el
  motor no se tocó aún. `git log --oneline -5` confirma la base (`75fed70`).
- **Qué NO tocar:** `fantasma/core/corners.py` y `fantasma/viz/pacenotes.py` hasta tener el
  artefacto de la Fase 0. No commitear cambios al motor sin el diagnóstico previo — las Fases 2 y 3
  se calibran con esos datos, no se inventan.
- **Rutas clave citadas en el diagnóstico:** `fantasma/viz/pacenotes.py:417-420` (D1, ticks
  descartados en silencio), `pacenotes.py:419` (D2, prueba de cabida sin prioridad),
  `fantasma/core/corners.py:143-146` (D3, `strong[-1]`), `pacenotes.py:186` (D4,
  `DEFAULT_FREQS`/`generate_tone`).
- **Datos de referencia:** `plan.json` viejo en
  `C:\Users\jose_\Downloads\Pruebas finales\_pack_v2\plan.json` (55 curvas, 35 con cue de frenada,
  11 con 3 sonidos, 13 con 2, 6 entradas en `skipped_global`, ninguna tick). Vuelta real de
  referencia y piloto en `C:\Users\jose_\Downloads\Pruebas finales`.
