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

**En vuelo: rama `feat/pacenotes-ui`** (7 commits sobre `master`, NO pusheada). Código completo y
verde (suite pytest exit 0), docs §8 sincronizados (`auditar.ps1` verde). Trae:

- **A1** — Paso 5 "Pace Notes" en la UI (genera el pack para CrewChief: tonos/voz/ambos) + helper
  `crewchief_pacenotes_dir`; arreglado el botón stub del Paso 2 (iba al Overlay) y el bug `Venue`.
- **A2** — `compose_video` acepta `pace_notes_dir/volume/lap` (mezcla en el video, expuesto en Paso 4);
  helper `mux_pace_notes_into_video` (`-c:v copy`, sin recomponer) + panel "Aplicar sonido a video
  existente" en Paso 5. Cubre 3 estados: nada / solo overlay / video ya terminado.
- **B** — pipeline autónomo: checkbox opt-in en Paso 3, encadena overlay→compose, notificación de
  escritorio al terminar. Estado `auto_compose`/`pending_autocompose`.
- **C** — loading states (carga CSV + "Calculando vuelta rápida…"), botones deshabilitados por
  contexto, consistencia de tokens de color, fix del selector de idioma.
- **Fix del Reviewer** — corregido BUG1 crítico (auto-compose era no-op: `poll` sync llamaba
  `navigate(4)` async sin await) + 4 hallazgos menores. Test AST que blinda BUG1.

## Siguiente acción

1. **QA visual (fase D, tarea pendiente):** correr la UI de verdad (`fantasma-ng`) con material real
   (`docs/recursos-del-proyecto.md`) + el video `C:\Users\amedina\Downloads\0207\frames\2_composed.mp4`,
   capturas por pantalla/estado, análisis con Mariana/Opus (cuestionar UI/UX, no solo "¿se ve bien?").
   Evidencia OBLIGATORIA en `qa_runs/` (ADR 0019). **Difería a infra estable** (decisión del PO;
   los subagentes cayeron 4 veces por conexión/límite de sesión durante esta sesión).
2. **Push** — pendiente de OK del PO. Antes: `verificar.ps1` verde (doc-gate §8 ya cubierto) y la
   evidencia de Mariana. El push es la única acción hacia afuera; la autoriza el PO.

**Hallazgos de UX abiertos** (a juzgar en la fase D, ya anotados en el tracker):
- Selector de idioma del Paso 5: al re-mostrarse reinicia valor si se cambió antes de togglear modo
  (parcialmente mitigado en C con `_lang_state`; validar).
- Panel de mux del Paso 5 depende de `state.drv_lap`; evaluar mini-uploader de CSV si el usuario
  entra sin vuelta cargada.
- Guard del Paso 5 redirige al Paso 2 vs mostrar UI griseada con banner — decisión de producto.

**Posibles ADR (señalados por el Escribano, PO decide si asentar):** `-c:v copy` vs recomponer en el
mux; Web Notifications + degradación vs push a móvil.

## Backlog

Ver [ROADMAP](ROADMAP.md) §"Post-v2.0" y §"Transversal".
