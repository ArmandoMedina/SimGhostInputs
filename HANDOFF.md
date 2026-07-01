# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## Pendiente inmediato

### Integración v2.0 — UI NiceGUI + CrewChief Pace Notes

Las ramas `feature/pacenotes` y `worktree-agent-a6afee076164bda53` se integran en
`codex/sgi-v2-merge` antes de llevar v2.0 a `master`.

Incluye:

- UI NiceGUI v2.0 + packaging/installer (`tools/build_installer.py`, `tools/installer.iss`).
- CrewChief Pace Notes (`fantasma pacenotes`) con flags de compare y `trackName` en metadata.

## Pendiente después de los merges

1. **Bundle size (spike inconcluso):** Oscar se quedó sin tokens — el spike de nicegui-pack en PC
   potente NO se completó. Cuando la PC potente vuelva a estar disponible, correr:
   ```
   python tools/build_installer.py
   ```
   y reportar el tamaño real del directorio `dist/SimGhostInputs/` en MB.

2. **Drill-down en NiceGUI:** `codex/Drill-down` queda como referencia de qué construir.
   Una vez que PR #13 esté en master, portar el drill-down de Streamlit a NiceGUI como
   feature branch separado.

3. **QA de pacenotes en carrera real:** tras mergear PR #14, validar en sesión real que
   los tonos suenan en los metros correctos (checklist del ROADMAP).

## Para retomar en frío

Ver [ROADMAP.md](ROADMAP.md) → «Front de escritorio custom (v2.0)» y «CrewChief Pace Notes».

**Nota de rama:** `codex/Drill-down` NO es la rama de v2.0 — es referencia histórica del
drill-down en Streamlit. La v2.0 avanza por feature branches hacia master (igual que siempre).
