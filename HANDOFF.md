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
| 4 | **VirusTotal** | ✅ **OK** | Subido y verificado (2026-07-02). |

**QA adicional completado (2026-07-02, laptop de desarrollo):**
- **E2E wizard 5/5 PASS** — `tests/ui/test_e2e_wizard.py` con CSV reales de `Paterial para test` (GO BMW M4 GT3 Nordschleife + jocmaster Race 2026-06-21). Todos los pasos del wizard ejercitados con clics reales.
- **Playwright smoke visual 2/2 PASS** — layout del Paso 0 contra baseline. (Warning menor: `Image.getdata` deprecada en Pillow 14; no bloquea, deuda técnica.)
- **Playwright E2E clic-a-clic 3/3 PASS** — `tests/ui/visual/test_e2e_playwright_wizard.py` con CSVs reales de Nordschleife. Paso 0 (selector de flujo), Paso 1 (upload 31 MB y 59 MB con confirmacion visual), Paso 3 (render overlay completo sin timeout). Screenshots en `qa_runs/playwright_e2e/` (local, gitignoreado). Commit: `6ee831f`. QA visual aprobado por PO (marker Mariana seteado 2026-07-02).
- **Migración ui.upload Paso 1** — `ng_step1.py` y `ng_step4.py` migrados a API NiceGUI 3.x (e.file.name, await e.file.read()). Deuda técnica: `_save_upload` no cierra file handle si write() falla, temp files con delete=False nunca se limpian.

**QA de pacenotes en sesión real** (post-merge, no bloquea) — requiere AMS2 en pista:
- Tonos suenan en los metros correctos (Nordschleife o similar)
- Escala de frecuencias distinguible auditivamente (agudo ≠ medio ≠ grave)
- `--mode voice` con edge-tts: frases coherentes con el problema detectado
- `--mode both`: voz 200m antes + tono en el metro exacto, sin solaparse

## Para retomar en frío

**TODO el QA pre-merge está completo.** Siguiente paso:
1. `gh auth switch --user ArmandoMedina` (verificar cuenta correcta con `gh auth status`).
2. `git checkout master; git merge codex/sgi-v2-merge --no-ff`
3. Cortar release con skill `release-helper` para v2.0.0.
4. El QA de pace notes en sesión real (AMS2) puede hacerse post-merge — no bloquea.

## Deuda técnica registrada (no bloquea merge)

Ver ROADMAP §"Gaps técnicos" y §"Deuda técnica". Los más relevantes:
- Encodings distintos a `utf-8-sig` en `motec_csv.py` (CSV de Windows no-inglés)
- Distinguir DESLIZ de GASTO visualmente en el HUD
- Invertir colores del HUD cuando el piloto va más rápido que la referencia (aviso existe en compare(), falta en renderer)
- `--format prores` congela en vueltas largas (ffmpeg stderr descartado)
