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

**En vuelo: rama `feat/ci-release-installer`** (sobre `master` en v2.2.0). Automatiza que **cortar un
release genere y adjunte el instalador Windows** — antes no lo hacía (el job `build-installer` de
`tests.yml` nunca corría: el workflow solo se dispara en push/PR a master, no en tags; y el instalador
de v2.0.0 se armó a mano). Trae:

- **CI**: nuevo `.github/workflows/release.yml` (trigger `release: published` → `windows-latest` →
  `choco install innosetup` → `build_installer.py --inno` → sube `Setup.exe` + zip portable como
  assets con `gh release upload`, permiso `contents: write`). Job muerto `build-installer` eliminado de
  `tests.yml`. Decisión: [ADR 0022](docs/decisions/0022-ci-release-installer.md).
- **Tooling**: `installer.iss` con versión parametrizable (`/DMyAppVersion`, antes hardcodeada "2.0.0")
  + icono habilitado; `build_installer.py` lee la versión de **pyproject** (SSOT; la metadata del
  editable install quedaba stale) y detecta ISCC (incluida la ruta per-user).
- **Validado local end-to-end**: se compiló `SimGhostInputs-v2.2.0-Setup.exe` (104.7 MB) con Inno
  Setup y se **adjuntó al release v2.2.0** (+ zip portable) — el CI aplica desde el **próximo** release.
- **Docs**: ADR 0022 + índice, CHANGELOG `[Unreleased]`, `docs/flujo-de-trabajo.md` (doc dueño de
  `barreras`) sincronizado (Escribano).

## Siguiente acción

**Cerrar la rama** (autorizado por el PO): verificar → commit → PR → merge a `master`. No amerita
release nuevo (la automatización aplica al siguiente). Considerar encadenar la **#2** (fuente única de
versión para el badge del footer) que quedó pendiente.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
