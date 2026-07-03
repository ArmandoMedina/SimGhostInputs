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

**Rama:** `codex/sgi-v2-merge` — lista para mergear. No tocar `master` sin autorización del PO.

**Suite:** 193 tests verdes (2026-07-02). CI en verde. `verificar.ps1` sin bloqueos.

**Todo el QA pre-merge completado.** Detalles en [CHANGELOG](CHANGELOG.md) §[Unreleased].

## Siguiente acción (requiere autorización del PO)

```powershell
gh auth switch --user ArmandoMedina   # verificar con: gh auth status
git checkout master
git merge codex/sgi-v2-merge --no-ff
# luego: skill release-helper → tag v2.0.0 + push + GitHub release
```

## Acción pendiente del PO (no puede hacerlo la IA)

Marcar `audit`, `docs-graph`, `lint` y `pytest` como *required checks* en el ruleset
de `master` en GitHub — sin eso el job `audit` (ADR 0019) es cosmético.

## Backlog

Ver [ROADMAP](ROADMAP.md) §"Post-v2.0" y §"Transversal".
