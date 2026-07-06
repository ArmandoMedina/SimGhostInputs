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

**Plan autorizado (efímero, vive en la sesión — esto es el resumen durable):**
- **PR 1** `fix(viz)`: `normalize=0` en amix (cues −6 dB bajo el motor) — este PR.
- **PR 2** `feat(viz)` motor: descartar cues d≤0, gap global entre curvas, anticipación por
  tiempo (`countdown_s=3.5`, clamp [60, 350] m, usa `v` del milestone), `top=0` = todas las
  curvas, brake a 1000 Hz, sidecar de sync (`<video>.sync.json`, mux bloquea si laptime
  difiere > 0.1 s) + ADR 0024 + tests + e2e con datos reales (`_DEMO_FIXED.mp4` para el oído
  del PO).
- **PR 3** `feat(ui)`: leyenda de tonos, checkbox "todas las curvas", caption del botón
  "Aplicar sonido", aviso de sidecar mismatch, breadcrumbs por flujo (`render_breadcrumb`
  con `_FLOWS[flow]["steps"]`); guia-usuario + ux-patterns + Mariana con screenshots.
- **Fuera de alcance** (ROADMAP): lógica fault-matched, solape de voz, limiter/ducking.

Contexto previo: `master` en **v2.2.0** con tres tandas mergeadas hoy:
1. **Flujo "Solo Pace Notes"** (#21) + release **v2.2.0** (#22, con `Setup.exe` + zip portable adjuntos).
2. **Automatización release→installer en CI** (#23, [ADR 0022](docs/decisions/0022-ci-release-installer.md)): al publicar un release se compila y adjunta el instalador solo (aplica desde el próximo release).
3. **Fuente única de versión** (#24, [ADR 0023](docs/decisions/0023-fuente-unica-de-version.md)): SSOT = literal `__version__` en `fantasma/__init__.py`; `pyproject` lo deriva con `dynamic`; el badge del footer y `build_installer.py` lo leen. **Bumpear la versión = editar `fantasma/__init__.py`.**

> **Pendiente fuera del repo:** la skill global `release-helper` (paso 2) aún dice "bump `pyproject.toml`";
> con la #24 el bump va a `fantasma/__init__.py`. Actualizarla cuando el PO lo autorice.
>
> Cambio local sin commitear (esta limpieza del HANDOFF): `master` exige PR — lo recoge el próximo PR.

## Siguiente acción

PR 2 del plan (motor de cues + sidecar + ADR 0024) y luego PR 3 (UI Paso 5 + breadcrumbs).
Si esta sesión murió a medias: verificar contra el código real qué PR quedó mergeado
(`git log`) y retomar el siguiente paso del plan resumido arriba.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
