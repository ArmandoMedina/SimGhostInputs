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

**Rama:** `codex/sgi-v2-merge` — lista para mergear tras completar R3.

**Suite:** 212 tests verdes (2026-07-03). CI en verde.

**Auditoría integral pre-v2.0.0 completada.** Informe en `qa_runs/2026-07-03-auditoria-integral/informe.md`.

- Remediación R1 aplicada: doble-append importers, exit codes CLI, ffmpeg stderr overlay, asyncio pacenotes, ffmpeg hud_preview, temp leak UI, event loop Paso 3, timers Paso 3/4, host 127.0.0.1.
- Decisiones asentadas: ADR 0020 (blast-radius viz), enmienda ADR 0018 (spikes sin acreditar + retiro Streamlit autorizado), enmienda ADR 0019 (plan efímero, sesión única escritora, evidencia commiteada).
- `audit` configurado como required check en el ruleset de `master` (ADR 0019).

## Siguiente acción

**R3 — retiro de código Streamlit** (autorizado por enmienda ADR 0018, antes del tag v2.0.0):

```
# Ahiram ejecuta el retiro según decision-retiro-streamlit.md:
# qa_runs/2026-07-03-auditoria-integral/decision-retiro-streamlit.md
```

Tras R3 y OK del PO:

```powershell
gh auth switch --user ArmandoMedina   # verificar con: gh auth status
git checkout master
git merge codex/sgi-v2-merge --no-ff
# luego: skill release-helper -> tag v2.0.0 + push + GitHub release
```

## Backlog

Ver [ROADMAP](ROADMAP.md) §"Post-v2.0" y §"Transversal".
