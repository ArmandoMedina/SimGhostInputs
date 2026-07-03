# Fase 0 — Reviewer del commit 73f5ac1 (render paralelo de overlay)

> Auditoría integral pre-v2.0.0 · 2026-07-03 · Reviewer (subagente sonnet).
> Código escrito por otra IA en sesión paralela; revisado post-commit.

## Veredicto: APROBADO CON OBSERVACIONES

## Hallazgos

1. **MAYOR — `test_render_parallel_collect_round_robin` no discrimina el código viejo**
   (`tests/viz/test_overlay.py`, test nuevo, líneas ~49–130). El test pasa también con la
   implementación secuencial original (verificado por simulación: las dos aserciones son
   trivialmente satisfechas porque el código viejo también alcanza `n_frames` al final).
   Para blindar la optimización debería asertar el orden de recolección, p. ej.
   `collected_done[0] == 10` (los frames del worker rápido se cuentan en la primera pasada,
   sin esperar al worker 0). Hoy es smoke test, no detector de regresión.

2. **MENOR — código muerto: `_count_events` sin callers** (`fantasma/viz/overlay.py:96-100`).
   Era el mecanismo anterior de conteo de flancos ABS/TC; sus entradas se eliminaron del
   tuple `base`. Queda definida sin un solo callsite. Ruff no la marca.

3. **MENOR — `progress()` redundante en la misma iteración** (`overlay.py:595-601`).
   Cuando un worker termina y quedan pendientes, se llama dos veces con el mismo `done`
   en el mismo intervalo de 0.5 s. Inocuo, pero redundante.

## Correctitud del slicing — sin bugs encontrados

Revisados y correctos: indexación global de arrays por distancia (`np.interp`, masks,
`_slip_window`), `_flag_recent_grid(..., cur_d - d_offset, HOLD_M)` con guard `max(0,...)`,
`_load_at` sobre cumsum no re-inicializado, guards ±1 de `t_arr`/`searchsorted`, padding
`d_lo = int(d_min) - W_BEFORE - HOLD_M` (conservador, inofensivo), `trace`/`corners_by_seg`
sin slicear (acceso global correcto), fallback serial usa `chunk_args_map` con offset
correcto (no regresa al `base` original), tempfiles Windows sin doble apertura, salida
determinista (rangos de frames no solapados).

## Resultados reales

| Comando | Resultado |
|---|---|
| `pytest tests/viz/ -q` | 47 passed (1.15s) |
| `pytest --ignore=tests/ui -q` | 149 passed (3.40s), exit 0 |
| `ruff check` (overlay + test) | All checks passed |
| `ruff format --check` | 2 files already formatted |

## Riesgos residuales (solo QA real los vería)

1. Vueltas sub-328 m: clamps correctos en teoría, pero sin test para ese caso.
2. Worker que muere escribiendo el frame: el fallback serial sobreescribe el PNG parcial —
   correcto en teoría, no testado con PNG corrupto.
3. Telemetría con gaps (GPS): `searchsorted` puede dar `i_s == i_e` y el slice del chunk
   quedar corto para sus últimos frames. Solo detectable con MoTeC real con gaps.
