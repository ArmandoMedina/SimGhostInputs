# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).

## Estado actual

**Rama de trabajo:** `codex/sgi-v2-merge` (no tocar `master` hasta cerrar los pendientes de QA abajo).

**Suite:** 185 tests verdes. `verificar.ps1` y `auditar.ps1` pasan sin bloqueos.

La integración v2.0 está **completa en código**:
- UI NiceGUI v2.0 (5 pasos, AppState, breadcrumb, F-01 neutral, ffmpeg guards, encoder info, C10 hint)
- CrewChief Pace Notes (`fantasma pacenotes`, modos tones/voice/both, plan anti-saturación)
- UX post-auditoría: aviso piloto invertido, C19 ffmpeg aviso en step0, slider reactivo, sidebar done-state
- Empaquetado: `tools/build_installer.py` + `tools/installer.iss`
- CI: job `build-installer` en `release.yml`
- Docs sincronizadas: CHANGELOG, ROADMAP, casos-de-uso, ux-patterns, UI-01/02/03, PAC-01/02

## Pendiente antes de mergear a master

Estos 4 ítems son QA **que requiere hardware** — no se pueden hacer desde la laptop en desarrollo:

1. **Bundle size real** — correr `python tools/build_installer.py` en la PC potente y reportar el
   tamaño del directorio `dist/SimGhostInputs/` en MB. El spike quedó sin tokens antes del merge.
   ```
   # desde la PC potente (SSH o presencial):
   cd /ruta/SimGhostInputs
   python tools/build_installer.py
   du -sh dist/SimGhostInputs/
   ```

2. **`native=True` en VM limpia Windows 11 24H2** — la VM de Hyper-V `sgi-win11-clean` ya existe.
   Arrancar el instalador `.exe` y verificar que la ventana nativa abre sin errores.

3. **VirusTotal** — subir el `.exe` a virustotal.com y revisar falsos positivos de antivirus
   antes de publicar el release.

4. **QA de pacenotes en sesión real** — checklist completo en ROADMAP §"Coaching de voz":
   tonos en metros correctos, escala distinguible, voz coherente, `--top N`, etc.

## Para retomar en frío

- Lee este HANDOFF.
- Corre `verificar.ps1` para confirmar verde.
- Si los 4 ítems de QA están listos: `git checkout master; git merge codex/sgi-v2-merge --no-ff`
  y cortar el release v2.0.0 con `gh release create v2.0.0`.
- Si no: continúa en `codex/sgi-v2-merge` con lo que esté disponible.

## Deuda técnica registrada (no bloquea merge)

Ver ROADMAP §"Gaps técnicos" y §"Deuda técnica". Los más relevantes:
- Encodings distintos a `utf-8-sig` en `motec_csv.py` (CSV de Windows no-inglés)
- Distinguir DESLIZ de GASTO visualmente en el HUD
- Invertir colores del HUD cuando el piloto va más rápido que la referencia (aviso existe en compare(), falta en renderer)
- `--format prores` congela en vueltas largas (ffmpeg stderr descartado)
