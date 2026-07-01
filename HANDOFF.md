# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino a v1.0*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## Pendiente inmediato

### PR #13 — UI NiceGUI v2.0 (`worktree-agent-a6afee076164bda53`)

CI corriendo. Último fix empujado: `eaefd42` — registra `nicegui.testing` en `tests/ui/conftest.py`
(el `pytest_plugins` en el archivo de test no registra fixtures globalmente).
Revisar si los 6 checks pasan en verde → si sí, mergear a master.

### PR #14 — CrewChief Pace Notes (`feature/pacenotes`)

Abierto: https://github.com/ArmandoMedina/SimGhostInputs/pull/14
CI corriendo. 155 tests en verde localmente.
Pendiente: revisar CI → mergear a master → QA manual en carrera real.

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
