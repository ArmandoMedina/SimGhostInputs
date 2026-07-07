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

**Sesión de "cues configurables" (2026-07-07).** En curso el rediseño que el PO pidió tras revisar la
cinta: los cues pasan de set hardcodeado a **catálogo configurable con prioridad**, con perfiles JSON
compartibles (packs de comunidad). Reencuadra el ADR 0026 (el ápex **no se borra, se apaga por
defecto**). Todo en la rama **`feat/cues-configurables`** (parte de #29), que **absorbe a #29 y #32**
— se fundirá como un solo release coherente; #32 se cierra absorbido. El PO autorizó commit/push/PR en
automático; el **merge lo dispara él** (avisar y preguntar). Regla de método vigente: **todo entregable
que el PO evalúa sale de la UI real, E2E clic-por-clic con Playwright**, nunca por script externo.

**Plan persistido:** `~/.claude/plans/tender-hugging-whale.md` — tiene el detalle de cada workstream.

**Hecho y revisado (commits en `feat/cues-configurables`, todo pusheado a origin):**
- **WS-1** `5bc17f9`+`3215095` — motor: `throttle_on` sostenido (15 muestras, patrón de `full_throttle`)
  + modela el **coast** (`coast_start`/`coast_end`); arregla el bug **317/393** (el roce fugaz ya no
  cuenta como "inicio de acelerador", ancla en el gas real). Reviewer + fix del borde de ventana.
  Doc dueño: `docs/formato-datos.md`.
- **WS-2** `1d62758`+`229c93e` — **catálogo filtrable + prioridad configurable**: `DEFAULT_CONFIG`
  (default = comportamiento de hoy, sin regresión), `cue_config` threadeado por
  `build_pack→build_tone_pack→plan_tone_events→_corner_candidates`, la cabida usa la prioridad de la
  config, **frenada protegida sigue universal**. Ápex (off por defecto), coast (off, flag "solo curvas
  sin frenada"), slot de `gear`. Countdown wireado (enable + prioridad de tics, `a321011` intacto).
  2 pasadas de Reviewer, LIMPIO. `_cue_cfg` resuelve config completa (rellena faltantes + `None`→default).
- **WS-3** `d742513` — formato de perfil JSON compartible (`fantasma/viz/cue_profiles.py`):
  load/save/validate/degradar con gracia, `profiles_dir()` (`~/.simghostinputs/cue-profiles`),
  `list_profiles`; 3 ejemplos en `docs/cue-profiles-ejemplo/`.
- **WS-4** `f947a9d`+`6a61ce5`+`39cefb6`+`292b35d` — UI del Paso 5 (casillas + `ui.number` de prioridad
  por cue + cargar/importar/guardar perfil, persistencia en `AppState.cue_config`). Robustez ante JSON
  malformado (3 bugs del Reviewer arreglados con tests falla-sin/pasa-con: `list_profiles` no crashea,
  `cues` mal formado → `ValueError`, `priority` no-numérico manejado; confirma sobrescritura). Affordance
  del sub-checkbox de coast (CSS en `ng_app.py`). E2E parametrizado (`SIMGHOST_TEST_MATERIAL`).
  Reviewer + Mariana (evidencia en `qa_runs/mariana-20260707/`). Suite: **308 passed, 10 skipped**.

**Decisión del countdown (opción 3 acotada):** se puede apagar + prioridad como metadata, pero **sigue
oportunista** (no pelea por espacio en la cabida) — hacerlo pelear contradiría el diseño validado de
oído. Si el PO de verdad quiere que el 3-2-1 desplace otros cues, es un cambio aparte y más riesgoso.

**Material de pruebas en esta PC:** `C:\Users\jose_\Downloads\Pruebas finales` (los CSV existen; el E2E
ya lee `SIMGHOST_TEST_MATERIAL`, con fallback a la ruta histórica).

## Siguiente acción

Retomar en `feat/cues-configurables`. En orden:
1. **WS-5** — traer los subtítulos de #32 (`build_cue_ass`, `compose` `burn_cue_subs`) sobre el motor
   final; adaptar al catálogo/coast; arreglar la ventana fija de 1.5 s (hasta el siguiente cue o mínimo
   sensato). Nota: el countdown final es el de #29 (tics), no el WAV de #32.
2. **WS-6** — ADR nuevo (reencuadra 0026: catálogo configurable con prioridad; coast; formato de perfil
   compartible; enmienda 0027) + Escribano (CHANGELOG, ux-patterns, hud-reference, product/, ROADMAP con
   las deudas de abajo, y codificar en `docs/decisions/0003-testing.md` la regla del E2E-Playwright).
3. **Cinta desde el E2E real** del Paso 5 (con un perfil de cues), `SIMGHOST_TEST_MATERIAL=C:\Users\jose_\Downloads\Pruebas finales`, para que el PO la oiga/vea (fin del 317/393).
4. Abrir el **PR paraguas** (sin fundir; el merge lo dispara el PO). Antes: barrido de Reviewer
   consolidado que incluya la robustez de WS-3/WS-4 (`292b35d` aún sin pasada dedicada).

**Deuda anotada (Reviewer WS-1, a ROADMAP en WS-6):** (a) `throttle_on_window`/`full_throttle` en
muestras fijas, no normalizado por tasa de muestreo (mal a ≠50 Hz); (b) coast no se emite si hay frenada
sin `brake_release` (trail-braking al borde del segmento).

**Decisiones de juicio del PO pendientes (no bugs — QA de Mariana):** asimetría leyenda-cerrada /
cues-abierta; rango de prioridad 0-999 sin pista visual; columnas desbalanceadas con cues abierto;
¿el select de perfiles necesita salvaguarda anti-cambio-accidental?; modo-claro fuera de alcance (la app
fuerza dark global, `ng_app.py:17`).

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
