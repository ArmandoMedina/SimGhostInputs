# Actualización al núcleo Jidoka 1.4.0 — evidencia (2026-07-11)

Rama: `jidoka/bajar-1.4` (desde `master` @ v2.6.0 / Jidoka 0.13.0-beta).
Se descartó el intento previo `jidoka/actualizar-1.3`.

## Procedimiento
Fix ADR 0021: el hasheo del lazo es EOL-agnóstico (normaliza a LF). El sello viejo
(Sprint B) tenía hashes CRLF → un `-Actualizar` normal marcaría las genéricas-atrasadas
como DIVERGE falso. Se resolvió pieza por pieza y se re-selló limpio.

## Clasificación de las 12 piezas DIVERGE

### Preservadas (code-first / instancia de SGI — se borró su sidecar, quedó la de SGI)
- `tools/verificar.ps1`
- `tools/auditar.ps1`
- `.githooks/pre-push`
- `.claude/skills/escribano/SKILL.md`

### Adoptadas (genéricas-atrasadas = mejoras 1.4 — se tomó la versión 1.4.0)
- `tools/estado-motor.ps1`
- `.claude/settings.json`
- `.claude/hooks/no-memorias-pretooluse.ps1`  (ahora cubre Bash, no solo Write/Edit)
- `.claude/commands/jidoka/arranca.md`
- `andon/README.md`
- `kit/.jidoka/disparos/README.md`
- `.claude/hooks/gemba-stop.ps1`  (endurecido: exige evidencia rastreada por git — cierra Goodhart, ADR 0013)
- `tools/probar-hooks.ps1`  (test que acompaña; sube de 10 a 17 casos)

> **Corrección de clasificación:** `gemba-stop.ps1` y `probar-hooks.ps1` son GENÉRICOS
> (hooks/tests agnósticos al lenguaje), no code-first. SGI solo tenía versiones viejas.
> Se adoptaron las 1.4.0.

## Piezas NUEVAS
- **KEEP** `tools/probar-disparos.ps1` (nueva herramienta 1.4).
- **BACK-OUT** `tools/probar-gate.ps1` (incompatible con el `verificar.ps1` code-first de SGI).
- **BACK-OUT** `.github/workflows/andon.yml` (duplica `tests.yml` de SGI).

No quedó ningún `.jidoka-nuevo` tras la resolución.

## Sello (`-Sellar`)
- Versión: **1.4.0**. 68 pristinas registradas | 4 divergen (preservadas) | 2 ausentes.
- Las 4 code-first (`verificar.ps1`, `auditar.ps1`, `.githooks/pre-push`, `escribano/SKILL.md`) NO están en `sembrado_hashes` → `-Actualizar` las verá DIVERGE y las preservará.
- `probar-disparos.ps1`, `gemba-stop.ps1` y `probar-hooks.ps1` quedaron registradas pristinas.

## Verde (todos exit 0 — ver .txt adjuntos)
- `pytest`: 453 passed, 11 skipped.
- `ruff check .`: All checks passed. `ruff format --check .`: 81 files already formatted.
- `probar-hooks.ps1`: **17/17** (no-memorias cubre Bash; gemba-stop exige evidencia rastreada por git).
- `probar-auditor.ps1`: 5/5. `auditar.ps1`: grafo íntegro.
- `probar-disparos.ps1`: 4/4 (omite correctamente `probar-gate.ps1`, no sembrado).
- `estado-motor.ps1 -Detallado`: reporta Jidoka **1.4.0**, 4 code-first DIVERGE, 2 back-outs AUSENTES, 68 al día.

## Versión
- `fantasma/__init__.py __version__`: 2.6.0 → **2.7.0**.
- CHANGELOG: `## [2.7.0] - 2026-07-11`.
