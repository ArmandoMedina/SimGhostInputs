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

**En vuelo: rama `fix/version-fuente-unica`** (sobre `master` en v2.2.0). Cierra la **#2**: unifica la
fuente de verdad de la versión (el badge del footer quedaba en «v2.1» tras cada release por ser un
literal manual). Ahora: **`__version__` literal en `fantasma/__init__.py` = SSOT**; `pyproject.toml`
lo deriva con `dynamic = {attr = "fantasma.__version__"}`; el badge (`ng_app.py`) y
`build_installer.py._get_version()` lo leen de ahí. Se descartó `importlib.metadata` (stale en editable,
no fiable en el exe congelado). Decisión: [ADR 0023](docs/decisions/0023-fuente-unica-de-version.md).
**Consecuencia de proceso: bumpear la versión = editar `fantasma/__init__.py`, no `pyproject.toml`.**
Validado: `attr`/`meta`/`_get_version` todos 2.2.0; badge → «v2.2»; 229 tests verde, ruff limpio.
Docs §8: ADR 0023 + índice, CHANGELOG, `docs/guia-usuario.md` (doc dueño de `ui`).

**Contexto previo (ya mergeado hoy):** flujo "Solo Pace Notes" (#21 + release #22, v2.2.0 con
Setup.exe + zip portable adjuntos) y automatización release→installer en CI (#23, [ADR 0022](docs/decisions/0022-ci-release-installer.md)).

## Siguiente acción

**Cerrar la rama** (autorizado): verificar → commit → PR → merge a `master`. No amerita release nuevo.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
