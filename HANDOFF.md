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

**Rama de trabajo:** `codex/sgi-v2-merge` (no tocar `master` hasta cerrar los pendientes de QA abajo).

**Suite:** 185 tests verdes. `verificar.ps1` y `auditar.ps1` pasan sin bloqueos.

**Homologación starter v0.5.0 adoptada** (ADR 0019, mergeada aquí desde `homologacion-starter-v0.5.0`): job `audit` en CI, Mariana exige evidencia en `qa_runs/`, hook no-memorias, `/arranca` reforzado, `docs/recursos-del-proyecto.md`, recetario PS 5.1. **Pendiente del PO:** marcar `audit`, `docs-graph`, `lint` y `pytest` como *required checks* en el ruleset de master — sin eso el job nuevo es cosmético.

La integración v2.0 está **completa en código**:
- UI NiceGUI v2.0 (5 pasos, AppState, breadcrumb, F-01 neutral, ffmpeg guards, encoder info, C10 hint)
- CrewChief Pace Notes (`fantasma pacenotes`, modos tones/voice/both, plan anti-saturación)
- UX post-auditoría: aviso piloto invertido, C19 ffmpeg aviso en step0, slider reactivo, sidebar done-state
- Empaquetado: `tools/build_installer.py` + `tools/installer.iss`
- CI: job `build-installer` en `release.yml`
- Docs sincronizadas: CHANGELOG, ROADMAP, casos-de-uso, ux-patterns, UI-01/02/03, PAC-01/02

## Pendiente antes de mergear a master

De los 4 ítems de QA, 3 completados en laptop de desarrollo (2026-07-01):

| # | Ítem | Estado | Detalle |
|---|------|--------|---------|
| 1 | **Bundle size real** | ✅ **370.9 MB** | `python tools/build_installer.py` en Windows 11 24H2, Python 3.11. `dist/SimGhostInputs/` completo con nicegui 3.14 + pywebview + scipy + numpy + PIL + matplotlib + pandas. |
| 2 | **`native=True` en Windows** | ✅ **Confirmado** | App abre ventana nativa (pywebview 6.2.1) en laptop de desarrollo. Sin errores. Nota: `fantasma-ng` entry point requiere `pip install -e ".[ui-ng]"` para registrarse en PATH. |
| 3 | **Pace Notes CLI** | ✅ **5/5 PASS** | --mode tones sin edge-tts, WAV 24kHz mono 16-bit, error claro en --mode voice sin edge-tts, --top 3 selección correcta, campos metadata.json correctos para CrewChief. |
| 4 | **VirusTotal** | ⏳ **Pendiente** | El .exe está en `dist/SimGhostInputs/SimGhostInputs.exe`. Solo falta subirlo manualmente a virustotal.com. |

**Nota sobre #4:** el directorio `dist/` se generó en el build de 2026-07-01 con nicegui-pack + PyInstaller 6.21.0. El .exe no se commitea; si no existe en tu máquina, corre `python tools/build_installer.py` para regenerarlo antes de subir.

**QA de pacenotes en sesión real** (separado del VirusTotal) — requiere AMS2 en pista:
- Tonos suenan en los metros correctos (Nordschleife o similar)
- Escala de frecuencias distinguible auditivamente (agudo ≠ medio ≠ grave)
- `--mode voice` con edge-tts: frases coherentes con el problema detectado
- `--mode both`: voz 200m antes + tono en el metro exacto, sin solaparse

## Para retomar en frío

1. Lee este HANDOFF.
2. Corre `verificar.ps1` para confirmar verde.
3. Sube `dist/SimGhostInputs/SimGhostInputs.exe` a virustotal.com (si no lo hiciste antes).
4. Cuando VirusTotal sea OK: `git checkout master; git merge codex/sgi-v2-merge --no-ff` y cortar el release con `gh release create v2.0.0`.
5. El QA de pace notes en sesión real (AMS2) puede hacerse post-merge si hay prisa — no bloquea la funcionalidad core.

## Deuda técnica registrada (no bloquea merge)

Ver ROADMAP §"Gaps técnicos" y §"Deuda técnica". Los más relevantes:
- Encodings distintos a `utf-8-sig` en `motec_csv.py` (CSV de Windows no-inglés)
- Distinguir DESLIZ de GASTO visualmente en el HUD
- Invertir colores del HUD cuando el piloto va más rápido que la referencia (aviso existe en compare(), falta en renderer)
- `--format prores` congela en vueltas largas (ffmpeg stderr descartado)
