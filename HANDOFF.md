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

**En vuelo: rama `feat/flujo-solo-pacenotes`** (sobre `master` en `v2.1.1`). Añade un **flujo de
entrada "Solo Pace Notes"** (4ª tarjeta en el Paso 0) que rutea Importar(1)→Análisis(2)→Pace
Notes(5) saltándose overlay/compose — resuelve la fricción reportada por el PO (un video con overlay
ya hecho que solo quiere pace notes era arrastrado a generar overlay). Trae:

- **Código** (`fantasma/ui/`): entrada `pacenotes` en `_FLOWS` (`ng_helpers.py`); 4ª tarjeta
  (`ng_step0.py`); grid del Paso 0 a 4 columnas (`ng_app.py`); guard del Paso 5 reestructurado para
  que el **panel② ("aplicar sonido a video existente") sea visible siempre** (antes lo ocultaba el
  guard); tooltips en ambos paneles + caption puente ①→②; fix del estado visual disabled del botón
  "Aplicar sonido" (selector CSS `.disabled` de Quasar).
- **Tests**: `tests/ui/test_ng_flows.py` (nuevo, ruteo), + extensiones a `test_ng_step0.py` y
  `test_ng_step5.py`. Suite **verde (227)**; visuales **7/7** (baseline `step0.png` regenerado a 4 tarjetas).
- **Decisión**: [ADR 0021](docs/decisions/0021-flujo-solo-pacenotes.md) (por qué 4º flujo, alternativas
  descartadas: CSV único / mini-import / paso huérfano). Restricción de producto: las pace notes exigen
  **2 vueltas** (priorizan por tiempo perdido, `compare()`) — no se generan de una sola vuelta ni del video.
- **Docs §8** sincronizadas (Escribano): `guia-usuario.md`, `ux-patterns.md`, `casos-de-uso.md` (C36),
  `product/capacidades/UI-01` y `UI-04`. **CHANGELOG** con entrada `[Unreleased]`.
- **QA visual** (Mariana): **aprobado**; evidencia en `qa_runs/mariana-20260705-pacenotes/`.

## Siguiente acción

1. **Publicación autorizada por el PO** (commit/push/PR/versión): push de `feat/flujo-solo-pacenotes`,
   PR + merge a `master`, y cortar **v2.2.0** con `release-helper` (recordar
   `gh auth switch --user ArmandoMedina`, devolver a `Armandomedina9705` al terminar).
2. **Recorrido e2e 0→1→2→5 VERIFICADO** en sesión con CSVs reales (Nordschleife BMW vs Audi):
   evidencia en `qa_runs/mariana-20260705-pacenotes/recorrido-e2e.md` + capturas `e2e_*`. El botón
   "Ir al Paso 5" y el flujo completo funcionan; panel② con "Aplicar sonido" atenuado correcto.

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean:
- **Paso 1 — subida concurrente:** subir los dos CSV casi simultáneos puede perder el segundo
  `on_upload` mientras el primero (MoTeC grande) procesa. Secuencial funciona. Borde raro,
  prioridad baja (detectado en el e2e del recorrido pacenotes).
- Labels truncados en los inputs del Paso 4 (`ng_step4.py`) — cosmético, prioridad baja.
- Job de render del Paso 3 en variable local, no en `state` (`ng_step3.py`) — riesgo de render
  concurrente al mismo `outdir`; fix propuesto `state.active_overlay_job`. Prioridad media.
- Candidata **v3.0**: acelerar el render del overlay (*gated por benchmark*).
