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

**En vuelo: rama `feat/pacenotes-ui`** (~18 commits sobre `master`). Código completo, **verde
(226 tests, `verificar.ps1` OK)**, revisado (Reviewer), docs §8 sincronizadas (Escribano), y con
**aceptación visual del PO** (2ª ronda Mariana/Opus). Trae, sobre lo ya descrito en el CHANGELOG:

- **Features** A1 (Paso 5 Pace Notes), A2 (sonido en video: preview al componer + mux standalone
  `-c:v copy`), B (pipeline autónomo overlay→compose + notificación).
- **Remediación de QA visual** (2 rondas Mariana/Opus): uploader, indicadores, acentos, jerarquía
  de botones (I3 vía CSS `!important`, sin `.props("flat")`), y **rediseño de layout centrado con
  ancho máximo + 2 columnas en Pasos 4 y 5**.
- **Fixes de correctness** destapados al verificar de verdad (varios estaban en falso-verde):
  contraste del botón "Seleccionado"; **el Paso 3 ya no bloquea el panel con la detección de
  curvas** (se detecta al final del render, con "Analizando el trazado…" y botón deshabilitado
  hasta tener las curvas); guard de doble-clic en "Aplicar sonido" del Paso 5.

## Siguiente acción

1. **Push de la rama** — autorizado por el PO en sesión (2026-07-05). Si ya está pusheada al leer
   esto, abrir PR hacia `master` cuando el PO lo pida.
2. Nada más pendiente de esta tanda: la aceptación visual está dada y la evidencia citada vive en
   `qa_runs/mariana-20260705-r2/` (commiteada).

**Deuda/pulido abierto (en ROADMAP, no bloquea):**
- Labels truncados en los inputs del Paso 4 (cosmético, prioridad baja) — decisión del PO de
  pushear ya y dejarlo al backlog.
- El job de render del Paso 3 vive en variable local, no en `state`: navegar fuera durante un
  render no lo cancela (riesgo de render concurrente al mismo outdir). Pre-existente, prioridad
  media. Fix propuesto: `state.active_overlay_job` + cancelar en `_cancel_on_nav`.

## Backlog

Ver [ROADMAP](ROADMAP.md) §"Post-v2.0", §"Transversal" y la candidata **v3.0** (acelerar el render
del overlay, *gated por benchmark*).
