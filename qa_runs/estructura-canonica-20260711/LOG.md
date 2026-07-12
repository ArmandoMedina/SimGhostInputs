# QA — Estructura canónica (ADR 0023): comandos namespaced únicos + skills persona

- **Fecha:** 2026-07-11
- **Rama:** `jidoka/estructura-canonica`
- **Versión:** SGI `2.8.0` · motor Jidoka `1.7.1`
- **Método reproducible:** desde `C:\Repositorios\SimGhostInputs`, correr los comandos de la tabla.

## Qué se hizo

1. **Comandos** — se borraron los 12 (6 planos + 6 namespaced genéricos), se re-derivaron los 6 desde Jidoka `.claude/commands/jidoka/*` y se re-personalizaron con el sabor de SGI (persona Mau, rutas reales, reglas propias, refs internas `/jidoka:*`). Resultado: 6 comandos, solo `/jidoka:*`.
2. **Skills** — se borraron las carpetas neutrales duplicadas `arquitecto-doc`/`revisor-visual`/`validador` (sin referencia operativa); se conservan las 4 personas + `escribano`.
3. **Sello** — `excluir` = las 3 carpetas neutrales + back-outs (`tools/probar-gate.ps1`, `.github/workflows/andon.yml`).
4. **Lazo** — `-Actualizar` (bajó a Jidoka 1.7.1) + `-Sellar` limpio.

## Resultados

| # | Caso | Check | Resultado |
|---|---|---|---|
| 1 | `python -m pytest` | suite del producto | **453 passed, 11 skipped** |
| 2 | `ruff check .` | lint | All checks passed |
| 3 | `ruff format --check .` | formato | 81 files already formatted |
| 4 | `.\tools\probar-hooks.ps1` | vida de los hooks | **17/17** sanos |
| 5 | `.\tools\probar-auditor.ps1` | vida del auditor del grafo | **5/5** sanos |
| 6 | `.\tools\probar-disparos.ps1` | registro de disparos | **4/4** (registro sano) |
| 7 | `.\tools\auditar.ps1` | grafo de docs | Grafo íntegro |
| 8 | `.\tools\estado-motor.ps1` | versión del motor | Jidoka **1.7.1** |

## `-Actualizar` (extracto: exclusiones respetadas + comandos preservados)

```
[EXCLUIDA] tools/probar-gate.ps1 (el hijo la excluyo del motor)
[EXCLUIDA] .claude/skills/arquitecto-doc/SKILL.md (el hijo la excluyo del motor)
[EXCLUIDA] .claude/skills/revisor-visual/SKILL.md (el hijo la excluyo del motor)
[EXCLUIDA] .claude/skills/validador/SKILL.md (el hijo la excluyo del motor)
[EXCLUIDA] .github/workflows/andon.yml (el hijo la excluyo del motor)
[DIVERGE] .claude/commands/jidoka/arranca.md    (preservado)
[DIVERGE] .claude/commands/jidoka/cierra.md     (preservado)
[DIVERGE] .claude/commands/jidoka/desatendido.md (preservado)
[DIVERGE] .claude/commands/jidoka/planea.md     (preservado)
== Motor: 59 al dia | 2 actualizado(s) | 1 nuevo(s) | 8 divergen | 5 excluida(s) ==
```

Nota: `gemba.md` y `que-sigue.md` NO aparecen en DIVERGE — quedaron byte-idénticos al canónico de Jidoka (no requerían personalización de rutas ni persona). Los `.jidoka-nuevo` de las piezas DIVERGE se borraron. `-Sellar`: 62 pristinas | 8 preservadas | `excluir` intacto.

## Veredicto

Todo verde. Los 6 comandos namespaced presentes y válidos; cada ruta citada existe en SGI. Sabor persona de SGI conservado; neutrales duplicados retirados y excluidos del lazo.
