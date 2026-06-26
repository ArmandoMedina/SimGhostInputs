# Benchmark — Linter/formatter para SimGhostInputs

> Decisión de adopción (2026-06-26). Por qué se eligió **ruff** y no las alternativas,
> con licencias y actividad verificadas en vivo (no de memoria). Contexto: proyecto
> Python, AGPL-3.0, un solo autor, vibe-coding. Objetivo: una **barrera determinista**
> del pipeline pre-push en modo aviso que atrape "basura" antes de subir a GitHub.

## Qué hace un linter vs un formatter (no son lo mismo)

- **Linter** — lee el código **sin ejecutarlo** (análisis estático) y marca imports y
  variables sin usar, nombres indefinidos, código muerto, *smells*. Es la "basura" real
  que se quiere atajar.
- **Formatter** — reescribe espacios, comillas y largo de línea a un estilo canónico.
  No cambia la lógica. Atrapa el `trailing whitespace` y compañía.

Ambos son **deterministas** (misma entrada → misma salida); por eso califican como
barrera del pipeline.

## ¿Es seguro? (tres capas)

1. **Cadena de suministro.** Son dependencias **solo de desarrollo** (no se instalan al
   usuario final). El riesgo es el de cualquier paquete pip; ruff (Astral) y black (PSF)
   están entre los tools Python más usados del mundo (pandas, scipy, fastapi) → riesgo bajo.
2. **Auto-fix que rompa código — el riesgo real.** ruff separa **fixes seguros**
   (preservan comportamiento, `--fix`) de **inseguros** (requieren `--unsafe-fixes`
   explícito); black verifica que el resultado sea **AST-equivalente**. Red de seguridad
   no negociable: correr en git, revisar el diff, y que **pytest pase**. Nunca auto-arreglar a ciegas.
3. **Licencia.** Importa porque este repo es AGPL: usar un tool MIT/Apache no ata nada.

## Opciones (verificado 2026-06-26)

| Opción | Qué es | Auto-fix | Veredicto corto |
| :-- | :-- | :-- | :-- |
| **ruff** | Linter **+** formatter (Rust). Reemplaza flake8 + black + isort + pydocstyle + pyupgrade | Sí (seguro/inseguro separados) | **Elegido.** Un solo tool, una sola config. |
| black | Solo formatter | Sí (AST-equivalente) | Maduro, pero **no lintea**. |
| flake8 | Solo linter (wrapper de pyflakes + pycodestyle + mccabe) | No (solo reporta) | Necesitaría black aparte. |
| pylint | Linter profundo (motor de inferencia) | No | Lento + licencia GPLv2. Overkill aquí. |
| (nada) | — | — | Deja pasar toda la basura que se quiere atajar. |

## Licencias y actividad (verificadas en vivo)

| Opción | Licencia | Estrellas | Último release | Mantenedor |
| :-- | :-- | :-- | :-- | :-- |
| **ruff** | **MIT** ✅ | 48.2k | v0.15.20 (2026-06-25) | Astral (empresa; también hace `uv`) |
| black | MIT ✅ | 41.6k | v26.5.1 (2026-05) | PSF / comunidad |
| flake8 | MIT ✅ | 3.8k | activo | A. Sottile, I. Cordasco |
| pylint | **GPLv2** ⚠️ | 5.7k | v4.0.6 (2026-06) | pylint-dev / comunidad |

## El contrapunto a ruff (cuestionado a propósito)

Su único pero real: **es de un solo vendor** (Astral, con capital de riesgo), mientras que
black/flake8 son comunidad/PSF. Si Astral cambiara de rumbo, habría que migrar.
**Mitigantes:** es MIT (te quedas con la versión actual para siempre) y su adopción es tan
amplia que un fork sobreviviría. Para un repo personal el riesgo es despreciable.

## Veredicto

**ruff.** No por moda: para este caso (un autor, vibe-coding, se quiere *una* barrera con
mínima fricción) **consolida flake8 + black + isort en un solo tool**, MIT, mantenido al
día, y lo usan los proyectos Python más grandes. El combo black + flake8 + isort serían
**tres configs** para lo mismo. pylint pierde por GPLv2 + lento + sin auto-fix. "Nada"
derrota el propósito.

## Cómo se aplicó (decisiones de configuración)

- **Conjunto de reglas corto y de alta señal:** `select = ["F", "I"]` en `pyproject.toml`.
  - **F** (pyflakes) = la basura real (imports/variables sin usar, nombres indefinidos).
  - **I** (isort) = orden de imports, auto-arreglable y sin drama.
  - **No** se activan `E701`/`E741` (pycodestyle): sobre código que ya funciona serían
    **ruido** (one-liners y nombres de una letra intencionales). El formateo de espacios
    lo hace `ruff format`, no esas reglas. Ampliar a `B` (bugbear) o `UP` (pyupgrade)
    cuando aporte, no por default.
- **Fixes seguros aplicados** al adoptar: 1 import sin usar + orden de imports en 17
  archivos. **74 tests verdes** después → comportamiento preservado.
- **Formato (`ruff format`): baseline aplicado.** Reformateó 34 de 38 archivos en un
  commit dedicado (cambio mecánico y AST-equivalente; **74 tests verdes** después como
  red). Con el baseline en su lugar, el CI ya gatea `ruff format --check` además de
  `ruff check`.

## Dónde vive esto

- Config: `pyproject.toml` (`[tool.ruff]`, `[tool.ruff.lint]`, extra `[dev]`).
- CI: job `lint` en `.github/workflows/tests.yml` (corre `ruff check` y `ruff format --check`).
- Local (modo aviso): `tools/verificar.ps1` (lint + formato + tests + doc-gate).
