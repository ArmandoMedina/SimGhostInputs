---
tipo: plan-de-trabajo
estado: en_curso
---

# Plan — Anunciar cada frenada real dentro de una curva (doble frenada)

> **Para qué es esta plantilla (ADR 0019, enmienda 2026-07-03):** una tarea larga con IA muere a
> media ejecución (tokens, contexto compactado, subagente caído) — y lo no escrito se pierde. El plan
> te da un guion para no perder el hilo. Al retomar: **verifica contra el código real**, no contra el
> resumen de la sesión anterior (los resúmenes de compactación pueden mentir).
>
> **Nota de esta instancia:** el template dice que el plan es efímero y NO se versiona; se commitea
> como **excepción puntual** por indicación de `/arranca` (regla 4) y por el riesgo de corte de
> contexto en una tarea de varios asientos. Al cerrar, su contenido se reparte a ADR/HANDOFF/CHANGELOG
> y la instancia se puede borrar. (Contradicción template↔`/arranca` anotada para que el PO la zanje.)

## Contexto

El PO detectó, escuchando la vuelta real de Nordschleife, que cuando frena → suelta a fondo → vuelve
a frenar dentro de una misma curva, **la segunda frenada no suena**. Confirmado por Charbel contra el
dato crudo (`qa_runs/charbel-20260710-frenos-encadenadas/`):

- **Metro 1119 (C05):** dos frenadas reales — 100% (m1042) · suelta y acelera al 78% · vuelve a
  frenar 90% (m1117). El detector **sí ve** dos fases pero solo emite el aviso de pico más alto
  (m1042); la segunda queda muda.
- **Metro 803 (C03):** 100% (m726–772) · suelta el pedal a **0** por ~0.4 s pisando gas ~26%
  (m780–800) · vuelve a frenar 100% (m806–833). El detector **funde** las dos en una (gap 0.44 s <
  `PHASE_GAP_S`=0.5 s y velocidad aún baja) → una sola fase, un solo aviso.

**Norte (PO):** el cue de frenada evita que el piloto se pase y se mate; **cada frenada real que mete
el coche a la curva debe sonar**, sin pitar en modulaciones de trail-braking (el pedal nunca se suelta
del todo).

**Restricción dura — ADR 0031:** decidió "pico máximo" usando *este mismo C05* como ejemplo, y exige
simetría ref↔piloto en `select_brake_phase` (`d_brake_m==0` en la misma vuelta). El diseño **enmienda**
0031 (ADR 0033): el aviso principal sigue en m1042; **añade** la segunda frenada. No revierte nada.

## Objetivo

En modo estudio (vuelta de referencia), C03 (≈m726 y ≈m806) y C05 (≈m1042 y ≈m1117) emiten **dos**
avisos de frenada con su countdown; las 53 curvas de frenada simple quedan **byte-idénticas**;
`compare`/coaching y `d_brake_m` **no cambian**. Verificable: `pytest` verde + regeneración de
`corners.json` real + QA de oído de Mariana.

## Decisión de diseño (mínimo blast-radius)

Separar las dos preguntas que hoy resuelve un solo algoritmo:

| Pregunta | Mecanismo | ¿Cambia? |
| :-- | :-- | :-- |
| ¿Cuál es EL punto de frenada comparable? (métrica simétrica) | `select_brake_phase` → `chosen` → `brake_start` escalar | **NO** — 0031 y `compare` intactos |
| ¿Qué frenadas deben SONAR? (todas las reales) | **`detect_brakings` (nueva)** → **`brake_starts` (lista, nueva)** | Solo la consume `pacenotes.py` |

Por qué no "partir 803 dentro de `select_brake_phase`": sus dos fases quedan a 100% empatadas y el
desempate "gana la tardía" (0031) movería el **primario** de m726 a m806 (80 m tarde) — el fallo que
mata al piloto. El camino elegido no toca esa regla.

**Criterio de separación (803):** dos bloques de freno se **funden** salvo que en el hueco haya gas
real (`throttle ≥ THROTTLE_REAPPLY`, candidato **15 %**). El trail-braking nunca entra (el pedal no
baja de `BRAKE_ON`=10 → un solo bloque). Coasting (throttle≈0) funde; 803 (26 %) y C05 (78 %) parten.

**Forma JSON:** se conserva `milestones.brake_start` (escalar, primario = `chosen`) y se **añade**
`milestones.brake_starts` (lista cronológica de toda frenada fuerte, forma `{d,t,v,gear,brake_pct}`),
presente solo con ≥2 fuertes. `compare` **no se toca** (usa solo `chosen`).

## Pasos (cada uno commiteable y verde)

- [x] **0.** Persistir este plan y commitear.
- [ ] **1.** ADR 0033 (Armando) — enmienda a 0031: frenadas múltiples, criterio gas-en-hueco, campo
  `brake_starts`, y que `compare`/escalar NO cambian. Fila en `docs/decisions/README.md`.
- [ ] **2.** `core/corners.py` + tests (Ahiram) — `THROTTLE_REAPPLY=15`, `detect_brakings` (hermana de
  `select_brake_phase:123`, reusa bloques `:151-158`), emisión `ms["brake_starts"]` en
  `extract_milestones:283-289` cuando haya ≥2 fuertes. Extender `_lap_brake_blocks` (test) con
  `throttle_blocks`; tests: 803, lift-to-rotate, trail-braking; regresión L244/L310/L322/L337.
- [ ] **3.** `viz/pacenotes.py` + tests (Ahiram) — iterar `brake_starts` en `_corner_candidates:1347-1367`
  (fallback `[brake_start]`), un `_event("brake",...,protected=True, lead_m=...)` por frenada, countdown
  por frenada (`:857-861` ya lo soporta). `brake_release` sigue singular. Tests de doble cue.
- [ ] **4.** Docs (Escribano) — `formato-datos.md` (SSOT, añade `brake_starts`), `cues.md`, `CHANGELOG`;
  corregir el veredicto del 803 en `qa_runs/charbel-20260710-frenos-encadenadas/LEEME.md` (era "no-bug").
- [ ] **5.** Validación Charbel — regenerar `corners.json` real; asertar 803 y 1119 = 2 frenadas, set de
  curvas con `brake_starts` pequeño/explicable, `d_brake_m` idéntico. Evidencia en `qa_runs/`.
- [ ] **6.** QA audio Mariana — regenerar E2E (perfil actual), confirmar de oído 803/1119 suenan doble y
  el countdown no satura. Evidencia en `qa_runs/` (hook lo exige).

## Decisiones tomadas en el camino

- (a resolver) Doble countdown por curva: default = sí (fiel al norte); Mariana/PO lo juzgan de oído.
- (a resolver) `THROTTLE_REAPPLY=15`: Charbel afina si sale split espurio en las 55.

## Para retomar en frío

- **Rama:** `fix/pacenotes-frenada-y-countdown`. **Diseño validado** por agente Plan (opus) el 2026-07-10.
- **Estado:** pasos 0–6 HECHOS + revisión adversarial atendida. Código, docs y QA commiteados; validado
  por Charbel (C03/C05/C21 emiten 2, escalar/`d_brake_m` idénticos) y QA A/B de Mariana entregada.
  **Solo falta la escucha final del PO.** El estado al día vive en `HANDOFF.md` (2026-07-10). C21 quedó
  confirmada por el PO (NO subir `THROTTLE_REAPPLY`).
- **Qué NO tocar:** `select_brake_phase` (corners.py:123-177), el escalar `brake_start`
  (corners.py:283-289 → `chosen`), y `compare._corner_metrics`. Romperlos viola ADR 0031 (simetría) y
  mueve el aviso principal. El plan de detalle vive en el plan-mode del orquestador.
- **Evidencia base:** `qa_runs/charbel-20260710-frenos-encadenadas/` (traza cruda de C03/C05).
