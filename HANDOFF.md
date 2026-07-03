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

**v2.0.0 LIBERADA (2026-07-03).** Tag y release publicados con el instalador
`SimGhostInputs-v2.0.0-Setup.exe` (104.7 MB) como asset; bundle onedir 373 MB;
smoke del exe PASA (HTTP 200 en 127.0.0.1:8765). PR #15 mergeado por squash
(el ruleset solo permite squash). Suite: 202 tests verdes en local y en los
7 required checks.

## Siguiente accion

Ninguna en vuelo. Pendientes chicos del PO:

- Mirar las capturas de QA visual (`qa_runs/mariana-20260703-0740/`) — checkpoint de Mariana.
- Re-exportar el ORECA 07 INT desde MoTeC i2 (sin canal Distance; hallazgo de Charbel).
- Decidir si se pinea la version de ruff en pyproject (el CI corre el ultimo de `>=0.15,<1` y ya divergio del local una vez).

## Backlog

Ver [ROADMAP](ROADMAP.md) §"Post-v2.0" y §"Transversal". Destacados de la auditoría:
cobertura de `charts.py`/`report.py`, endurecer hooks de sesión (ventanas de bypass,
fase3-hooks), lockfile de dependencias, y la feature candidata a v2.1: monitoreo
remoto del render desde otro dispositivo (requiere diseño de seguridad; hoy la UI
escucha solo en 127.0.0.1 a propósito).
