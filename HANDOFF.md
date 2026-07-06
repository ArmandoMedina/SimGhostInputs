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

**En vuelo: el "pedo de los sonidos" (pace notes) — diagnosticado; plan de 3 PRs autorizado
por el PO (5-jul).** El desync que reportó el PO quedó diagnosticado con datos — evidencia y
veredicto en `qa_runs/charbel-20260705-desync/notas.md`: la hipótesis de descalibración de
distancia ref(2025) vs piloto(2020) es FALSA (0.1 % de diferencia; cues a ±1 s del paso
real). El desync percibido viene de: (a) cues clampados a t=0, (b) sin gap mínimo entre
curvas → sopa de tonos indistinguibles, (c) anticipación fija 120 m en vez de por tiempo,
(d) brake y countdown ambos a 880 Hz y sin leyenda en la UI, (e) sin sidecar video↔vuelta
en el panel ② del Paso 5.

**Plan autorizado (efímero, vive en la sesión — esto es el resumen durable) y su avance (6-jul):**
- **PR 1** `fix(viz)` `normalize=0`: **MERGEADO** (#25, CI 7/7 verde).
- **PR 2** `feat(viz)` motor (rama `feat/pacenotes-sync`, commits `f559230`+`2f5513c`):
  descartar cues d≤0 **con fallback a tono de frenada plano**, gap global entre curvas
  (plan.json reconciliado: selected == WAVs reales), anticipación por tiempo
  (`countdown_s=3.5` = `DEFAULT_COUNTDOWN_S`, clamp [60, 350] m), `top=0` = todas las curvas
  (también en CLI), brake a 1000 Hz, sidecar `<video>.sync.json` (valida laptime ± 0.1 s +
  identidad del CSV vía `sync_sidecar_mismatch`, fuente única; borra sidecars huérfanos;
  rechaza formatos futuros) + ADR 0024 + tests + e2e real (`_DEMO_FIXED.mp4`: 101 cues,
  anticipo mediano 3.60 s, evidencia `qa_runs/charbel-20260705-pr2-e2e/`). Reviewer corrido
  (7 ángulos) y hallazgos atendidos. **Falta: push + PR + merge.**
- **PR 3** `feat(ui)` (rama `feat/pacenotes-ui-paso5`, encimada en la del PR 2): leyenda de
  tonos derivada del motor, checkbox "todas las curvas", caption "Falta: …", aviso ✓/⚠ de
  sidecar, breadcrumbs por flujo (respetan `flow_chosen`), y DOS bugs sistémicos destapados
  por el Reviewer/captura: `navigate()` sin await (el botón "Generar Pace Notes" del Paso 2
  NO navegaba — el "no llego a pace notes" del PO) y `e.value` inexistente en handlers
  `update:model-value` (volumen/offset/selects rotos de origen) — todos corregidos, reglas
  en `ux-patterns.md`. **Falta: evidencia de Mariana (captura Playwright), commit final,
  push + PR + merge.**
- **Fuera de alcance** (ROADMAP): lógica fault-matched, plan de voz (anticipo 200 m fijo +
  sin gap), limiter/ducking, `_STEPS` vs labels del breadcrumb.

Contexto previo: `master` en **v2.2.0** con tres tandas mergeadas hoy:
1. **Flujo "Solo Pace Notes"** (#21) + release **v2.2.0** (#22, con `Setup.exe` + zip portable adjuntos).
2. **Automatización release→installer en CI** (#23, [ADR 0022](docs/decisions/0022-ci-release-installer.md)): al publicar un release se compila y adjunta el instalador solo (aplica desde el próximo release).
3. **Fuente única de versión** (#24, [ADR 0023](docs/decisions/0023-fuente-unica-de-version.md)): SSOT = literal `__version__` en `fantasma/__init__.py`; `pyproject` lo deriva con `dynamic`; el badge del footer y `build_installer.py` lo leen. **Bumpear la versión = editar `fantasma/__init__.py`.**

> **Pendiente fuera del repo:** la skill global `release-helper` (paso 2) aún dice "bump `pyproject.toml`";
> con la #24 el bump va a `fantasma/__init__.py`. Actualizarla cuando el PO lo autorice.
>
> Cambio local sin commitear (esta limpieza del HANDOFF): `master` exige PR — lo recoge el próximo PR.

## Siguiente acción

1. Captura de Mariana del Paso 5 (`qa_runs/mariana-20260705-paso5/capture.py` — correrla
   SIN pytest de UI en paralelo: ambos usan el puerto 8765).
2. Push + PR + merge de `feat/pacenotes-sync` (PR 2) y luego `feat/pacenotes-ui-paso5`
   (PR 3, rebasar sobre master tras mergear el 2).
3. El PO escucha `C:\Users\amedina\Downloads\0207\_DEMO_FIXED.mp4` (countdown 3.5 s,
   frenada 1000 Hz, sin sopa) — su oído es el tilde final del ADR 0024.
Si esta sesión murió a medias: verificar contra el código real qué quedó mergeado
(`git log`, `gh pr list`) y retomar aquí.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
