# Flujo de trabajo — guía completa (explicada desde cero)

> **Para qué es este documento.** Explica **todo** el sistema que mantiene a SimGhostInputs
> consistente y evita que un cambio (tuyo o de la IA) suba "basura" a GitHub o se salte un
> paso: desde el cambio de código hasta el *push*, pasando por el linter, los tests, el hook
> y el CI. **No asume que sabes git ni programar.** Cada concepto técnico está explicado en
> simple. Si solo quieres el resumen, salta a la [sección 11](#11-resumen-en-una-frase).
>
> Este repo es **Python, un solo autor, AGPL-3.0**. La disciplina escala con el riesgo del
> repo: aquí no hay gobernanza de equipo, pero sí **barreras deterministas que avisan** para
> que nada se cuele. El *porqué* de cada decisión vive en [`docs/decisions/`](decisions/README.md);
> qué documentos tocar al cambiar algo, en [`CONTRIBUTING.md` §8](../CONTRIBUTING.md#8-mantenimiento-de-documentación).

---

## 1. El problema que resuelve (por qué existe todo esto)

Tres dolores reales del vibe-coding (la IA escribe código que el autor no lee línea por línea):

1. **La IA arranca sin memoria en cada chat.** Reconstruye de lo que le das; puede bifurcar
   distinto a como ya se había decidido. → Por eso las decisiones se asientan en **ADRs**.
2. **Es fácil subir "basura" sin darse cuenta:** un import que quedó sin usar, una variable
   muerta, un nombre indefinido, formato inconsistente, o un cambio de comportamiento **sin
   su test**. → Por eso hay un **linter**, un **formatter** y la **suite de tests**.
3. **Es fácil saltarse la documentación:** cambiar código y olvidar el CHANGELOG, el ROADMAP
   o un ADR. → Por eso hay un **doc-gate** que lo recuerda.

**La idea que lo resuelve, en una frase:** sacar los chequeos mecánicos de manos no confiables
(ponerlos en herramientas que corren solas) y **atrapar lo que se cuela** con verificadores
que corren en varios momentos, con autoridad creciente.

---

## 2. Glosario — cada concepto, en simple

### 2.1 Git y GitHub (guardar el historial)

- **Git**: un programa que guarda el **historial** de tus archivos. Como un "guardado infinito":
  cada punto importante queda con nombre, fecha y autor, y siempre puedes volver atrás.
- **Repositorio (repo)**: la carpeta del proyecto **con todo su historial**. El nuestro vive
  en `C:\Repositorio personal\SimGhostInputs`.
- **Commit**: una **foto guardada** de tus cambios en un momento, con un **mensaje** que dice
  qué cambiaste. Es un punto al que siempre puedes regresar. (Se pronuncia "cómit".)
- **Rama (branch)**: una **línea de trabajo**. La principal aquí se llama **`master`**. Puedes
  abrir otra rama para experimentar sin tocar `master`, y luego unir los cambios.
- **Árbol de trabajo (working tree)**: tus archivos **tal como están ahorita** en la carpeta,
  antes de "fotografiarlos".
- **Stage / staging (preparar)**: una "sala de espera" donde **eliges qué cambios entran** en
  la próxima foto. El comando `git add` mete cosas a esa sala.
- **GitHub**: una **copia de tu repo en la nube** (`github.com/ArmandoMedina/SimGhostInputs`).
  Sirve para respaldar y para que la comunidad lo use (es público, AGPL).
- **Remote / `origin`**: el **apodo** de esa copia en la nube. `origin` = "el GitHub de este repo".
- **Push**: **subir** tus commits locales a GitHub. **Pull**: bajar los de otros. **Clone**:
  copiar el repo de GitHub a una máquina nueva.
- **`.gitignore`**: lista de archivos que git debe **ignorar** (no guardar), p. ej. `.pytest_cache`.
- **Aviso "LF will be replaced by CRLF"**: LF y CRLF son dos maneras de marcar "fin de línea"
  (Linux vs Windows). Es **solo un aviso inofensivo**; el commit procede igual. No arregles nada.

### 2.2 Las herramientas que corren solas

- **Linter**: lee tu código **sin ejecutarlo** (análisis estático) y **marca** problemas:
  imports/variables sin usar, nombres indefinidos, código muerto. Es la "basura" del punto 2.
  El nuestro es **ruff** (regla `F` = pyflakes).
- **Formatter**: reescribe espacios, comillas y largo de línea a un **estilo canónico**. No
  cambia la lógica. El nuestro también es **ruff** (`ruff format`).
- **ruff**: un linter **+** formatter para Python, muy rápido, MIT. Reemplaza a flake8 + black
  + isort en una sola herramienta. Por qué se eligió y no otras: [`docs/benchmark-linter.md`](benchmark-linter.md).
- **pytest**: el programa que corre la **suite de tests**. Dice **pasa / falla**.
- **Test (prueba automática)**: un chequeo que **corre solo** y verifica que una función da el
  resultado esperado. Los nuestros usan datos sintéticos deterministas (`make_lap`), nunca
  telemetría real. Enfoque y qué se automatiza vs qué es manual: [`docs/decisions/0003-testing.md`](decisions/0003-testing.md).
- **Determinista**: misma entrada → misma salida, siempre. Solo lo determinista se puede
  automatizar como barrera; lo visual/subjetivo es juicio humano (ver [sección 4](#las-tres-dimensiones-y-dónde-acaba-la-máquina)).

### 2.3 Git hook, CI y exit code (cuándo corre cada barrera)

- **Git hook**: un script que git ejecuta **automáticamente** en cierto momento. El nuestro es
  `pre-push`: corre **justo antes de un `git push`** y dispara el verificador local. **Avisa**, no
  bloquea (el `push` continúa).
- **`.githooks` y `core.hooksPath`**: por defecto git busca los hooks en una carpeta oculta
  (`.git/hooks`) que **no se versiona**. Le dijimos que los busque en `.githooks` (que **sí**
  viaja en el repo). Se enciende una vez por clon: `git config core.hooksPath .githooks`.
- **Exit code (código de salida)**: un número que un programa devuelve al terminar. **0 = todo
  bien**; **≠ 0 = hubo problema**. El verificador local sale **0 cuando solo hay avisos**
  (lint/formato/tests/CHANGELOG), pero sale **≠ 0 y BLOQUEA el push si detecta doc-drift de la
  §8** (código sin su doc dueño; ver abajo). Las barreras del CI salen ≠ 0 si fallan (bloquean en la nube).
- **Hook de sesión (Claude Code `Stop`)**: distinto del git hook. Es un script que Claude Code
  corre **cuando la IA termina de responder**; puede **frenar el cierre e instruir a la IA** que
  corra un paso (el Reviewer o el Escribano) antes de dar por terminado. Vive en `.claude/hooks/`
  y se registra en `.claude/settings.json`. Es lo que hace que el auto-cableado **no dependa de
  que alguien se acuerde** de invocar el rol.
- **CI / Integración Continua / GitHub Actions / "pipeline" / "workflow"**: una **máquina en la
  nube de GitHub** que corre comprobaciones **solas**. Si una falla, el push queda **en rojo**.
  Es **la barrera que nadie puede saltar** desde su computadora. Los workflows viven en
  `.github/workflows/`: `tests.yml` (gate de calidad en push/PR), `release.yml` (genera y adjunta
  el instalador Windows al publicar un release, [ADR 0022](decisions/0022-ci-release-installer.md))
  e `installer.yml` (ensaya ese mismo empaquetado en los PR que lo tocan, sin publicar nada).
- **Verificador (`tools/verificar.ps1`)**: nuestro script de PowerShell que corre **las cuatro
  barreras locales de un jalón** (lint, formato, tests, doc-gate) en modo aviso.
- **Modo aviso vs bloquea**: *avisar* = imprime el hallazgo y deja seguir; *bloquear* = detiene
  la operación. Regla del repo: **lint/formato/tests avisan local y el CI los bloquea; el
  doc-drift de la §8 (código sin su doc dueño) BLOQUEA ya en local** — excepción deliberada,
  porque la desincronización doc↔código es el dolor #1 de este repo y no queremos que se suba.

### 2.4 Los artefactos del repo (qué es cada cosa)

- **Código** (`fantasma/`): el motor (núcleo `core/`, importadores, visualización `viz/`, UI
  NiceGUI). Es lo que el linter y los tests vigilan.
- **Tests** (`tests/`): las pruebas automáticas que espejan al paquete.
- **ADR** (`docs/decisions/NNNN-*.md`): un **registro de decisión**. Guarda **qué se decidió,
  por qué, y el camino que NO se tomó**, para que la próxima sesión (o IA) no repita el error.
  Una decisión = un archivo. (Aquí solo usamos ADR; no separamos "MADR de método" como otros
  repos — para un repo personal sería sobre-gobernanza.)
- **`CHANGELOG.md`**: la bitácora de cambios por versión (formato Keep a Changelog).
- **`ROADMAP.md`**: el estado vivo (en qué versión va, qué sigue, gaps, deuda).
- **`docs/glosario.md`**: la definición canónica del vocabulario del proyecto.
- **Fuente de verdad (SSOT)**: el documento que **manda** sobre un hecho; los demás enlazan, no
  duplican. El mapa de quién es dueño de qué está en [`CONTRIBUTING.md` §8](../CONTRIBUTING.md#8-mantenimiento-de-documentación).

---

## 3. Las piezas que construimos (y qué hace cada una)

| Pieza | Qué hace | Dónde vive |
|---|---|---|
| **Linter + formatter** | Marca basura (imports/vars sin usar, nombres indefinidos) y fija el formato canónico | `ruff`, config en `pyproject.toml` (`[tool.ruff]`) |
| **Suite de tests** | Verifica la lógica determinista del motor con datos sintéticos | `tests/` (pytest); enfoque en `docs/decisions/0003-testing.md` |
| **Verificador local** | Corre lint + formato + tests + doc-gate de un jalón, en modo aviso | `tools/verificar.ps1` |
| **Doc-gate (CHANGELOG)** | Avisa si tocaste `fantasma/` sin anotar el `CHANGELOG.md` (checklist ¿ADR? ¿ROADMAP?) | dentro de `tools/verificar.ps1` |
| **Doc-gate (blast-radius §8)** | **BLOQUEA** los `doc_bloquea` faltantes por área; **AVISA** los `doc_avisa` y `product_avisa` faltantes. Reglas en `tools/blast-radius.json` (fuente única — agrega un área ahí y listo) | `tools/verificar.ps1` + `tools/blast-radius.json` |
| **Auditor del grafo de docs** | Audita `product/`+`engineering/`: **BLOQUEA** frontmatter incompleto, wikilinks rotos, capacidades `vigente` sin criterios; **avisa** sin-test-citado y huérfanos. Modulado por estado. Dueño: Armando | `tools/auditar.ps1` ([ADR 0016](decisions/0016-gate-grafo-documentacion.md)) |
| **Hook `pre-push`** | Corre el verificador **solo**, justo antes de `git push` (avisa lint/formato/tests; **bloquea** doc-drift §8) | `.githooks/pre-push` |
| **CI (push/PR)** | Barrera dura en la nube: lint + formato + tests en cada push/PR | `.github/workflows/tests.yml` |
| **CI (release)** | Genera y adjunta el instalador Windows (`Setup.exe` + zip portable) como assets permanentes del release de GitHub. `workflow_dispatch` re-dispara el build contra un tag existente | `.github/workflows/release.yml` ([ADR 0022](decisions/0022-ci-release-installer.md)) |
| **CI (installer-smoke)** | Ensaya el empaquetado (`nicegui-pack` + Inno Setup) en cada PR que toca el camino del instalador, y deja el `Setup.exe` como artefacto del run | `.github/workflows/installer.yml` |
| **Import-smoke NiceGUI** | Verifica que `ng_app` importa y arranca sin excepción — sustituyó al smoke visual Playwright al migrar la UI a NiceGUI (hallazgo de auditoría `fase3-ci`). Dueño: Mariana | `tests/ui/visual/` ([ADR 0012](decisions/0012-playwright-smoke-visual-ui.md)) |
| **Decisiones (ADR)** | El porqué de todo, con su camino descartado | `docs/decisions/` + su `README.md` |
| **Benchmark del linter** | Por qué ruff y no las alternativas (licencias verificadas) | `docs/benchmark-linter.md` |
| **Reviewer** | Lee el diff y **aconseja** (bugs, calidad); su contenido no bloquea. **Auto-disparado** por hook de sesión cuando hay código sin revisar | `/code-review` + `.claude/hooks/review-stop.ps1` |
| **Escribano** | Sincroniza los docs dueños (§8) tras un cambio de código. **Auto-disparado** por hook de sesión al detectar doc-drift | `.claude/skills/escribano/` + `.claude/hooks/andon-stop.ps1` |
| **Mariana** | Checkpoint de QA visual: al tocar `viz/` (HUD) o `ui/` (NiceGUI) frena el cierre y manda revisar la UI a ojo. Vuelve al PO; **no juzga sola** lo visual. **Auto-disparado** por hook de sesión | `.claude/hooks/gemba-stop.ps1` ([ADR 0011](decisions/0011-cablear-mariana-no-charbel.md)) |
| **Hooks de sesión (Claude Code)** | Frenan el cierre de la IA y disparan Reviewer/Escribano/Mariana **sin que nadie los invoque** | `.claude/hooks/` + `.claude/settings.json` |
| **Router de roles (§8 extendida)** | Mapea cada área a su doc dueño **y** su rol validador (Charbel, Mariana, Reviewer…) | `CONTRIBUTING.md` §8 |

---

## 4. El flujo completo, paso a paso

### Paso 0 — ¿Estás explorando o consolidando? (lo marca git)

- **Explorando** = todavía pruebas; el código puede cambiar o tirarse. Trabajas suelto; **nada
  de la maquinaria corre**. (Idealmente en una rama aparte para no ensuciar `master`.)
- **Consolidar** = "esto se queda". El acto de **commitear** ES consolidar. No hay que declarar
  la fase: **la marca dónde estás en git.**

> Política de este repo (personal): **commit libre** mientras las docs queden completas; el
> **push y el release esperan tu OK**. Por eso la barrera fuerte se concentra en el push.

### Paso 1 — El cambio incluye su test y su decisión (juicio, antes de commitear)

Cuando decides que el cambio se queda:

- **Si cambiaste lógica determinista** (`core/`, `importers/`, helpers puros de `viz/`), **el
  cambio incluye su test** — no es "para después". Es lo que permite confiar en código que no
  se lee línea por línea. Regla completa: [`CONTRIBUTING.md` §3](../CONTRIBUTING.md#3-entorno-de-desarrollo) y [ADR 0003](decisions/0003-testing.md).
- **Si fue una decisión** (elegiste un camino sobre otro y una sesión futura podría tomar el
  equivocado) → **regístrala como ADR** (lo redacta **Armando** con tu decisión como PO), actualiza
  el índice y el CHANGELOG.
- **Si quieres una segunda opinión**, corre la **revisión IA** (`/code-review`): lee el diff y
  **aconseja**. Es juicio, no determinismo → **aconseja, no bloquea** (ver más abajo).

### Paso 2 — Verificar local (el hook **avisa**)

Antes de subir, corre las cuatro barreras locales. Dos formas:

- **A mano:** `./tools/verificar.ps1` — cuando quieras auditar el estado.
- **Automático:** al hacer `git push`, el hook `pre-push` (en `.githooks/`) corre el verificador
  **solo**. Imprime los avisos y **deja seguir el push** (sale 0). Si ves algo que no te gusta,
  cancelas con Ctrl-C, arreglas, y vuelves a empujar.

El verificador corre, en orden:

1. **Lint** (`ruff check`): ¿hay imports/variables sin usar, nombres indefinidos? (regla `F`+`I`).
2. **Formato** (`ruff format --check`): ¿el código está en el formato canónico?
3. **Tests** (`pytest`): ¿la lógica del motor sigue verde?
4. **Doc-gate**, dos partes:
   - **CHANGELOG** (avisa) — ¿tocaste `fantasma/` sin anotar el `CHANGELOG`? Checklist
     (¿fue decisión? → ADR · ¿cambió el plan? → ROADMAP); ADR y ROADMAP dependen de juicio, por
     eso checklist y no validación (forzarlos generaría entradas vacías).
   - **Blast-radius §8** (**BLOQUEA**, sale ≠ 0) — tocaste un área sin su `doc_bloquea` dueño.
     Las 8 áreas y sus reglas viven en `tools/blast-radius.json` (fuente única). Salir a propósito:
     `git push --no-verify`.
   - **Grafo de producto** (**AVISA**) — tocaste `fantasma/` sin actualizar nada en `product/`.
     Preguntarse: ¿cambió algún criterio funcional? Si sí → actualizar la capacidad o módulo del
     área antes de cerrar el PR.

> **Mixto:** los avisos (lint/formato/tests/CHANGELOG) dejan seguir; el **doc-drift de la §8
> bloquea ya aquí** (push detenido hasta sincronizar el doc dueño). La barrera dura de
> lint/formato/tests sigue en el Paso 3 (CI).

### Paso 3 — Push (el CI **bloquea**)

Al hacer `git push`, GitHub corre el **CI** (`.github/workflows/tests.yml`). Si algo falla, el
push queda **en rojo**. Es el respaldo **que nadie puede saltar** desde su máquina. Cinco jobs:

1. **`lint`** (Ubuntu): `ruff check` (basura) **y** `ruff format --check` (formato canónico).
2. **`docs-graph`** (Ubuntu, pwsh): `tools/auditar.ps1 -Bloquea` — integridad del grafo de
   `product/`+`engineering/` (frontmatter, wikilinks, criterios). No necesita Python; solo lee los
   `.md`. Ver [ADR 0016](decisions/0016-gate-grafo-documentacion.md).
3. **`audit`** (Ubuntu, pwsh, solo PRs): `tools/auditar-radius.ps1` — el **blast-radius §8 sobre
   el rango del PR** (ADR 0019, homologado del starter v0.5.0). Cierra la ventana de "PR con docs
   desfasadas" que el hook de sesión (solo working tree) y `verificar.ps1` (push local, saltable
   con `--no-verify`) no cubren.
4. **`pytest`** (Windows, Python 3.10 / 3.11 / 3.12): toda la suite de tests, en la plataforma
   objetivo del proyecto y en las tres versiones soportadas.
5. **`visual-smoke`** (Ubuntu, Python 3.12): import-smoke de NiceGUI — verifica que `ng_app` importa y arranca sin excepción; sustituyó al smoke Playwright al migrar la UI a NiceGUI ([ADR 0012](decisions/0012-playwright-smoke-visual-ui.md)).

> **Regla anti-bypass (ADR 0019):** un job de CI solo es **muro** si está marcado *required
> check* en el ruleset de master; un rojo no-requerido deja pasar el merge igual. Todo aviso
> local se asume bypaseable por diseño — lo que importa se re-verifica aquí como requerido.

### Las tres barreras, juntas

```
  EXPLORAS         CONSOLIDAS              PUSH (git push)         PUSH (en la nube)
  (rama sucia)  →  cambio + test + ADR  →  hook pre-push       →  CI en GitHub Actions
   nada corre      (+ /code-review IA)     verificar.ps1          tests.yml
                   juicio, aconseja        (AVISA, sale 0)        (BLOQUEA, sale ≠0 si falla)
```

Mismas comprobaciones, autoridad creciente. **Avisa temprano, bloquea al final.**

### La capa en sesión — los roles disparan solos (sin que te acuerdes)

Las barreras de arriba (git hook + CI) corren en `git push`. Antes de eso, **dentro de la sesión de
Claude Code**, hay una capa que evita que el trabajo *llegue* sin revisar o con docs desfasados — sin
depender de que invoques nada. La mueven los **hooks de sesión** (`Stop`) en `.claude/`:

- **review-stop** → si hay código **sin revisar** en un área con `revisa: true` de la ley (`fantasma/`), frena el cierre y dispara
  `/code-review`. *Data-driven* (lee la ley, ya no hardcodea rutas — convergencia ADR 0034). Marca el diff revisado (`.claude/.review-marker`) para no re-revisar lo mismo.
- **andon-stop** → si tocaste código y su **doc dueño quedó desfasado** (§8), frena el cierre y
  dispara el **Escribano**, que lo actualiza. Cuando ya está sincronizado, deja cerrar. Lee las reglas
  de `tools/blast-radius.json` (fuente única ejecutable): por cada área (`core/`, `viz/`, `ui/`,
  `importers/`, `cli`, `barreras`, `orquestacion`, `setup`) sabe qué `doc_bloquea` debe estar presente. **Scope real del hook:**
  cubre los docs técnicos (`doc_bloquea`); los de `product/capacidades/` son AVISA, no bloquean el
  cierre — los sincroniza el Escribano si detecta que un criterio funcional cambió.
  El `doc_avisa` por área también evoluciona con el manifiesto: p. ej. `viz` avisa además sobre
  `docs/cues.md` desde que ese catálogo existe (si el cambio toca el catálogo/prioridad/countdown
  de cues en `pacenotes.py`).
  **Nota sobre las dos ventanas:** este hook evalúa `git status --porcelain` (cambios sin commitear).
  Si committeas código sin sus docs, el working tree queda limpio y el hook ya no dispara; el drift
  lo atrapa `verificar.ps1` al hacer push. Para que nada se pierda: commitea código y docs juntos.
- **gemba-stop** → si tocaste áreas visuales (`rol: revisor-visual` en el manifiesto; persona **Mariana**: `viz/`, `ui/`),
  exige **evidencia verificable en `qa_runs/`** posterior al cambio (screenshots, logs de la corrida)
  antes de dejar cerrar — un veredicto de QA sin artefacto **no vale** (ADR 0019, homologado del
  starter v0.5.0; el "probé clic por clic" sin rastro ya falló aquí). Sigue siendo checkpoint que
  vuelve al PO: **no detecta solo** si algo se ve mal (límite semántico), obliga a mirar y a dejar
  rastro. El marcador `.claude/.gemba-marker` queda como respaldo para el caso raro de aprobar
  sin artefacto. Ver [ADR 0011](decisions/0011-cablear-mariana-no-charbel.md).
  **Endurecido (actualización núcleo Jidoka 1.4.0):** la evidencia de `qa_runs/` ya no basta con
  estar **fresca**; debe estar **rastreada por git** (`git add -f`). Antes, un archivo fresco pero
  sin versionar satisfacía el gate y luego no viajaba en el commit — un Goodhart clásico (la métrica
  "hay artefacto" se cumplía sin que el artefacto quedara). Ahora un artefacto fresco pero **no
  rastreado bloquea**. La prueba de vida del hook (`tools/probar-hooks.ps1`) cubre ambos casos
  (bloquea evidencia fresca-pero-no-rastreada; deja cerrar con `git add -f`). El cambio baja del
  núcleo Jidoka (su ADR 0013); en SGI extiende la regla de evidencia ya asentada en
  [ADR 0019](decisions/0019-adopcion-homologacion-starter-v0.5.0.md).
- **no-memorias** (hook `PreToolUse`, no `Stop`) → **deniega escribir** en la carpeta de memoria de
  Claude (`~/.claude/projects/<slug>/memory/`): el disparo anti-memoria de Jidoka manda todo al repo,
  nunca a una memoria privada del LLM. **Leer/recall de la memoria sí se permite** — solo bloquea la
  escritura. **Actualización 1.4.0:** el matcher pasó de `Write|Edit` a `Write|Edit|Bash` — antes un
  `Set-Content`/`Out-File` o una redirección `>` por Bash rodeaban el gate; ahora también los atrapa
  (busca un cmdlet de escritura + la ruta de memoria, o una redirección cuyo destino sea la memoria).
  Con cuidado deliberado de **no** bloquear en falso las redirecciones de stderr (`2>&1`,
  `2>/dev/null`), que no son escrituras a memoria. Límite confesado: aliases (`sc`/`ni`) y rutas
  ofuscadas evaden el matcher heurístico; no hay cobertura server-side (frontera en `andon/README.md`).

**Si git falla de verdad, el hook avisa, no calla.** Los tres hooks de sesión revisan sus llamadas
reales a `git status`/`git diff` (no solo interpretan "sin salida" como "sin cambios"): si git falla
de verdad (no instalado, repo corrupto, permisos — no el caso normal de "nada que revisar"), el hook
deja un `additionalContext` de aviso y sigue **sin bloquear** (corrección de auditoría, `fase3-hooks.md`
ALTO-04; el resto de hallazgos de esa auditoría —hooks ciegos ante código ya commiteado, markers
seteables a mano, evidencia de Mariana sin validar relevancia— se mitigan por disciplina de proceso,
no por código: ver [ADR 0019](decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).

Ambos son **auto-terminantes**: bloquean solo mientras falte el paso. Es poka-yoke: *el sistema no te
deja olvidar; y si algo se cuela, el bloqueo del push (doc-gate §8) + git (todo reversible) te dejan corregir.*

> **Actualización del núcleo Jidoka (1.4.0) — mecánica del lazo, además de los hooks de arriba.**
> Junto al endurecimiento de `gemba-stop` y `no-memorias`, esta bajada de núcleo trajo:
> - **`tools/probar-disparos.ps1`** (nuevo): prueba de vida del **registro de disparos** cableados
>   (`kit/.jidoka/disparos`). Verifica que cada disparo declare su estado y que cada punto marcado
>   *Cableado* nombre el slug real de su barrera; omite los disparos cuyo target no está sembrado en
>   este clon (p. ej. los que apuntan a piezas que SGI no adoptó).
> - **`tools/estado-motor.ps1 -Detallado`**: reporta la divergencia **pieza por pieza y por hash**
>   contra la versión de Jidoka del sello (`al día` / `DIVERGE` / `AUSENTE`), no solo la versión global.
> - **Hasheo del sello EOL-agnóstico:** el sello del lazo (`tools/jidoka-motor.json`) normaliza a LF
>   antes de hashear, así que el drift CRLF↔LF ya no produce **falsos DIVERGE**. Las piezas genéricas
>   quedan pristinas contra el núcleo; las **code-first** de SGI (`verificar.ps1`, `auditar.ps1`,
>   `.githooks/pre-push`, `escribano/SKILL.md`) se preservan intencionalmente como DIVERGE.

**Los roles.** Cada cambio enciende a quien valida, según el **router de la §8 extendida**
(`CONTRIBUTING.md`): **Reviewer** (todo código) y **Escribano** (docs) van siempre; los especialistas
por área — **Charbel** (telemetría: `core/`/`importers/`, casi todo tests) y **Mariana** (UX del HUD:
`viz/`, casi todo juicio, checkpoint que vuelve a ti). El **PO** (tú) y **Armando** (arquitecto: ADRs y estructura de docs) viven en
la ideación, no en un hook.

> **Estado honesto:** hoy disparan solos **Reviewer**, **Escribano** y **Mariana** (cableada en [ADR 0011](decisions/0011-cablear-mariana-no-charbel.md)
> cuando un bug visual lo pidió). **Charbel** sigue **declarado** en el router §8 **sin hook a propósito**: su asiento son
> los tests deterministas (`pytest`), no la IA — cablearlo sería sobre-orquestar (mismo ADR 0011).

### El casting — asientos, no skills

El trabajo se reparte en **asientos** (roles) con **nombres** propios, para poder hablar de ellos
("pásalo a Charbel") y para que cada sesión los ocupe igual. Hay **un solo humano: tú (el PO).**
Le hablas a **Mau**; Mau ocupa o delega los demás asientos.

| Asiento | Función | Vive como | ¿Hook? |
|---|---|---|---|
| **Mau** | **orquestador** / cara al PO: decide, rutea, teje | **la sesión principal** de Claude Code | — |
| **Ahiram** | **desarrollador**: escribe `fantasma/` y sus tests | `.claude/skills/ahiram/`; puede correr en sesión o como subagente | no (deliberado) |
| **Armando** | **arquitecto-doc**: jerarquía `product/`+`engineering/`, wikilinks, frontmatter, **ADRs** | `.claude/skills/armando/` | no (deliberado) |
| **Charbel** | **validador** de telemetría (`core/`, importers) | `.claude/skills/charbel/` | no (sus tests son el asiento) |
| **Mariana** | **revisor-visual** del HUD/UI (`viz/`, `ui/`) | `.claude/skills/mariana/` | sí (gemba-stop) |
| **Escribano** | **sincroniza** docs↔código (§8) | `.claude/skills/escribano/` | sí (andon-stop) |
| **Reviewer** | revisa el diff (bugs, calidad) — función, no persona | `/code-review` | sí (review-stop) |
| **Oscar** | **infra y ops del entorno** (rol `devops`): VMs, SSH, Windows Sandbox, mounts, despliegues, la "PC potente" para QA limpio | agente de plataforma global (no vive en el repo) | no |

> **La maquinaria es neutral; el nombre es la persona** (convergencia ADR 0034). La ley (`blast-radius.json`) y los hooks usan el **token de rol genérico** (`rol: revisor-visual`, `validador`, `arquitecto-doc`, `devops`); las carpetas de skills (`mariana/`, `charbel/`…) son el **casting** — la etiqueta de persona. La autoridad la da la ley, no el nombre. Por eso SGI corre *la misma metodología* que Jidoka y tracker-financiero, con su propio casting. Cero metodologías paralelas.

> **Asiento ≠ skill.** Una **skill** es un comportamiento especializado, disparable, con límites
> escritos (lo que SÍ y lo que NO hace) — un archivo en `.claude/skills/`. Un **asiento** es el
> rol que alguien ocupa, y puede ocuparse **en la sesión** (Mau lo hace directo) o **como subagente**
> (Mau lo spawnea). Por eso **Mau no es skill**: Mau *es* la sesión; no tiene sentido "invocar a Mau".
> Ahiram/Armando/Charbel/Mariana/Escribano sí están escritos como skills porque son comportamientos
> acotados que conviene disparar igual cada vez. **Oscar** es agente de plataforma global (ops de
> entorno), no un asiento del repo — no tiene skill aquí porque su dominio es la máquina, no el código.

> **Antipatrón a evitar: "Mau desarrollando".** El recurso escaso de Mau es **su contexto**, no su
> capacidad. Si Mau se pone a escribir `fantasma/` en el hilo principal, envenena el contexto que
> necesita para orquestar (Context Rot) y borra la frontera de asientos. El desarrollo es de
> **Ahiram** — en sesión si es una edición chica y acotada, o delegado si es voluminoso. Mau decide
> y teje; **no es el que pica código**, igual que no es el que lee el bulto.

> **Convención 🎭 — anunciar la sustitución de asiento.** Cuando Mau hace **en sesión** un trabajo
> que pertenece a un asiento definido (en vez de delegarlo), lo **anuncia** con una línea:
> `🎭 Asiento: <rol> (en sesión) — <por qué>`. **No es pedir permiso** — Mau ya decidió; es para que
> el PO distinga una **elección deliberada** (p. ej. "🎭 Asiento: Armando (en sesión) — edición de
> una sola nota, no amerita subagente") de un **olvido**. Si un asiento debió actuar y no se anuncia,
> es una omisión a corregir, no un atajo válido.

### Orquestación: quién dispara a quién, y con qué modelo

**Tú no llamas a los subagentes.** Hablas con el **agente principal** — la sesión de Claude Code que
abres en el repo (`claude` en la terminal, dentro de SimGhostInputs). Ese agente es el **orquestador**:
tú describes la tarea y **él decide** si la hace en sesión o si **detona un subagente** (su herramienta
Task), y con qué modelo. Para que sea **consistente** entre sesiones, esta política vive **aquí** (no en
tu cabeza ni en un chat).

**¿En sesión o subagente?**
- **En sesión** (el principal lo hace directo): tarea chica, que necesita el contexto de lo que vienen
  platicando, o una edición acotada de un archivo.
- **Subagente** (ventana propia, fría; devuelve solo la conclusión condensada): cuando la tarea
  (1) leería muchos archivos o haría una búsqueda grande — **aislar el ruido** para no inflar el hilo
  principal (esto es lo que pelea el **Context Rot**); (2) es autocontenida (entrada chica → salida
  chica); o (3) querés correr **varias en paralelo**.

> **Regla dura — la lectura voluminosa SIEMPRE va a un subagente.** El recurso escaso del orquestador
> es **su propio contexto**, no su capacidad. Leer en el hilo principal transcripts, logs largos, dumps
> de búsqueda o archivos gordos **lo envenena aunque solo te quedes con la conclusión** — el volumen ya
> entró y desplaza lo que importa (Context Rot). Si vas a *buscar-y-condensar* (¿qué se decidió en tal
> chat?, ¿dónde está X en estos 200 KB?), **delegá a un subagente** (`Explore`/`general-purpose`, modelo
> `haiku`/`sonnet`) que se trague el volumen y te devuelva **solo el hallazgo**. El orquestador decide y
> teje; **no es el que lee el bulto.** Duda razonable: si el material a leer no cabe holgado en contexto
> o no lo vas a citar entero, no lo leas tú — delegá.
>
> **Lo mismo aplica a la ejecución mecánica: `git` (commit y push), builds, dumps.** No es solo lectura:
> el orquestador **delega la mecánica** y se queda con la decisión y la condensación. Si el commit fue
> por subagente, el push va por el mismo camino — partirlo (commit delegado, push en sesión) es
> incongruente.

**Calcular el esfuerzo y elegir el modelo** (model-routing, "no uses Ferrari para ir por tortillas").
El subagente acepta `model`: `haiku` · `sonnet` · `opus`:
- **haiku** — mecánico, reglas claras, sin razonamiento profundo: aplicar la §8 (Escribano), formatear,
  mover ítems, buscar y condensar (Explorador), ruteo simple.
- **sonnet** — juicio acotado que sí requiere razonar: Reviewer de bugs, juzgar una anomalía de
  telemetría (Charbel), entender un diff.
- **opus** — decisión profunda con trade-offs: Armando (arquitecto), redactar un ADR, un refactor con criterio.

**Regla de calibración (sin complacencia): iguala el modelo a la COMPLEJIDAD, no al precio.** Un modelo
barato en tarea compleja **falla y pagas doble** (re-correr). Si dudas entre dos, **sube uno**: un sonnet
de más cuesta menos que un haiku que se equivoca. Heurística rápida: ¿la tarea es *ejecución de reglas* o
tiene *juicio*? Solo reglas → haiku · juicio acotado → sonnet · decisión con consecuencias → opus.

### Cómo se opera (playbook)

El modelo de operación tiene **un solo actor humano: tú.**

```
PO (tú, humano)  ──hablas──►  Sesión principal de Claude Code (ORQUESTADOR)  ──spawnea──►  subagentes
```

- **Tú solo haces la primera flecha: hablas.** No spawneás nada a mano. Abres `claude` dentro del
  repo, arrancas con `/arranca` (o *"lee `docs/flujo-de-trabajo.md` + `CONTRIBUTING §8` a detalle"*), y
  describes la tarea en lenguaje normal.
- **El orquestador hace el resto**, guiado por la política de arriba: decide si lo hace en sesión o
  delega, con qué modelo, y dispara los subagentes. Tú **no** tocas la herramienta de subagentes —
  eres el humano; el orquestador es quien orquesta.

**Lección del primer caso real (extender Mariana a `ui/`):** el orquestador **decidió hacerlo en
sesión, sin subagente**, porque era una edición acotada de reglas (la política: chico y mecánico → en
sesión). Eso es la calibración funcionando: **no todo merece un subagente.** Sobre-orquestar es el
error caro; se delega solo cuando la tarea es pesada, aislable o paralela.

**Lección del segundo caso real (cablear Mariana, ADR 0011):** el orquestador acertó en hacer el ADR y
la implementación en sesión (acotado, dependía del hilo), pero **falló al leer dos transcripts de
~250 KB directo en su contexto** para reconstruir qué se había decidido — el caso de libro de la *regla
dura* de arriba. Debió delegar esa búsqueda-y-condensa a un subagente y quedarse solo con el hallazgo.
Corregido aquí para que la próxima sesión delegue la lectura voluminosa **por defecto**, no como opción.

**Lección del tercer caso real (subir los tests de degradación):** el orquestador delegó el commit a un
subagente pero luego corrió `git push` **en sesión** — incongruente. La delegación no es solo de lectura;
cubre la **ejecución mecánica de git**. Corregido en la *regla dura* de arriba: si el commit va por
agente, el push también.

**Lección del cuarto caso real (cerrar deuda técnica, 2026-07-09):** el orquestador lanzó **5 subagentes
worktree pesados** (skill Ahiram, cada uno explora+codea+testea+abre PR) en paralelo, más su propio
trabajo en el hilo principal — agotó la cuota de sesión de la cuenta de golpe; los 5 fallaron a mitad de
tarea (nada se perdió: cada worktree conserva su diff en disco). **Regla dura, ahora mecánica, no de
juicio:** un hook global (`~/.claude/hooks/agent-concurrency-gate.ps1`, fuera del repo — ver
[`docs/recursos-del-proyecto.md`](recursos-del-proyecto.md)) topa a **3 los agentes con `isolation:
"worktree"` corriendo en los últimos 20 minutos**; el 4º se deniega solo, sin que el orquestador tenga
que "acordarse" de contar. Detalle completo en [ADR 0019, enmienda 2026-07-09](decisions/0019-adopcion-homologacion-starter-v0.5.0.md).

### La frontera de versión (de vez en cuando)

Muchos commits se acumulan; al cerrar un hito, la skill **`release-helper`** corta una **versión**
(un tag SemVer `vX.Y.Z` + release en GitHub + CHANGELOG). Es otro ritmo, no cada cambio.

Al publicar el release, el workflow **`release.yml`** genera y adjunta automáticamente el instalador
Windows (`SimGhostInputs-vX.Y.Z-Setup.exe`) y un zip portable como **assets permanentes** del
release de GitHub, sin intervención manual. Ver [ADR 0022](decisions/0022-ci-release-installer.md).

**Caso real (2026-07-09):** entre el tag `v2.2.0` y el `v2.3.0` pasaron 12 commits (una feature
completa más 8 ítems de deuda técnica) sin que nadie cortara un release — nada disparó
`release.yml` en ese tiempo. Al fin cortar `v2.3.0`, el job **falló**: `pip install ... nicegui-pack`
trataba `nicegui-pack` como paquete de PyPI, pero es un script que **ya viene incluido** al instalar
`nicegui` (el extra `ui-ng`), no una distribución aparte — el bug estaba ahí desde el ADR 0022 y
nadie lo vio porque el workflow nunca había corrido de verdad. Lección: un workflow que solo se
dispara al cortar release puede quedar roto en silencio si pasa mucho tiempo sin cortar uno.

Arreglado eso, el mismo release falló **otra vez**, ahora en el build: `nicegui-pack` invoca
`pyinstaller` como subproceso, pero `pyinstaller` no estaba declarado en ningún lado (`nicegui` no
lo trae como dependencia ni expone un extra `[pack]` propio); en local nunca se notó porque las
máquinas de desarrollo lo tenían instalado a mano. Vive ahora en el extra `pack` de `pyproject.toml`.

De ese doble fallo salieron **dos barreras nuevas**, ambas contra la misma causa raíz (un pipeline
que nadie ejercita hasta el día que importa):

- **`installer-smoke`** (`.github/workflows/installer.yml`): ensaya el empaquetado completo
  (`nicegui-pack` + Inno Setup) en cada PR que toque `main_gui.py`, `pyproject.toml`,
  `tools/build_installer.py`, `tools/installer.iss` o cualquiera de los dos workflows. Deja el
  `Setup.exe` como artefacto descargable del run, para probar la instalación **antes** de cortar el tag.
- **`workflow_dispatch`** en `release.yml`: en el evento `release`, GitHub lee el workflow desde el
  commit del **tag**, no desde `master` — así que un bug en el propio workflow obligaba a borrar y
  recrear tag y release en cada intento. Un `workflow_dispatch` se lee siempre desde la rama por
  defecto: se re-dispara el build contra un release ya existente pasándole el tag como input, sin
  tocar el tag. Es la vía de rescate cuando un release queda publicado sin sus assets.

### Las tres dimensiones, y dónde acaba la máquina

El repo cuida la consistencia con **barreras deterministas**, cada una con su herramienta. Importa
ver **qué cubre cada una y qué NO**, porque no todo se puede atar por máquina.

| Dimensión | Pregunta que responde | Herramienta | Severidad |
|---|---|---|---|
| **Basura de código** | ¿imports/vars sin usar, nombres indefinidos? | `ruff check` (`F`+`I`) | avisa local · **bloquea en CI** |
| **Formato** | ¿el código está en el estilo canónico? | `ruff format --check` | avisa local · **bloquea en CI** |
| **Comportamiento del motor** | ¿la lógica determinista sigue dando los números correctos? | `pytest` | avisa local · **bloquea en CI** |
| **Import-smoke UI (NiceGUI)** | ¿`ng_app` importa y arranca sin excepción? | import-smoke NiceGUI (`tests/ui/visual/`) | **bloquea en CI** |
| **Documentación (CHANGELOG)** | ¿el cambio quedó anotado? | doc-gate CHANGELOG + checklist | **avisa** (ADR/ROADMAP son juicio) |
| **Doc-drift §8 (doc dueño)** | ¿tocaste un área sin su `doc_bloquea`? (`blast-radius.json`) | doc-gate blast-radius | **BLOQUEA local** · el Escribano lo arregla |
| **Doc-aviso §8 (product/eng)** | ¿tocaste un área sin actualizar `doc_avisa` o `product_avisa`? | doc-gate blast-radius | **AVISA** · Escribano sincroniza si cambió un criterio funcional |
| **Grafo de docs (product/engineering)** | ¿frontmatter, wikilinks y criterios de las notas están íntegros? | `tools/auditar.ps1` | **avisa local · bloquea en CI** (job `docs-graph`) |

> **Dónde acaba la máquina — el límite semántico.** Ningún chequeo determinista garantiza que el
> **HUD se vea bien**, que el overlay esté **visualmente correcto**, o que la sincronía de video
> "se sienta" bien. Eso siempre será **juicio humano**: el **QA manual con telemetría y video
> reales** (ADR 0003: *automatiza lo determinista; prueba a mano lo visual, lo subjetivo y lo que
> depende del entorno —GPU/ffmpeg/video—*). El QA manual no desaparece: **se aligera**, dejando de
> gastar tiempo en verificar matemáticas (lo hace la máquina) para concentrarse en lo que solo un
> humano juzga.
>
> Dos defensas, fuera de las barreras:
> 1. **DRY / fuente única** ([`CONTRIBUTING.md` §8](../CONTRIBUTING.md#8-mantenimiento-de-documentación)):
>    cada hecho vive en **un** documento; los demás enlazan. Lo que no se duplica no puede divergir.
> 2. **Revisión IA consultiva** (`/code-review`): la IA mira el diff y **aconseja**. Su
>    no-determinismo **no debe ser portero** — por eso aconseja, no bloquea. **Determinismo bloquea;
>    juicio aconseja.**

---

## 5. Por qué este flujo y no el de otro repo (adaptación)

El **objetivo** es el mismo en todos los repos: *sacar lo mecánico de manos no confiables y atrapar
lo que se cuela, avisando temprano y bloqueando al final*. Lo que **cambia entre repos** son los
**artefactos** que se vigilan, y por tanto las herramientas:

- Un repo de **documentación / mockups** (un vault de Obsidian) verifica que el mockup HTML y su
  resumen no diverjan (hash), que el grafo de enlaces no se rompa, y que las pantallas se comporten
  (Playwright E2E).
- Este repo es **código Python**, así que verifica lo propio del código: **linter** (basura),
  **formatter** (estilo) y **tests** (comportamiento del motor).

Mismo objetivo, checks distintos. No se copia la maquinaria de otro repo; se copia **la idea** y se
adapta a lo que este repo produce. La disciplina escala con el riesgo: aquí, single-author y
personal, las barreras **avisan localmente** y el **CI bloquea**, sin gobernanza de equipo.

---

## 6. Cómo usarlo (comandos para copiar)

```powershell
# Correr las cuatro barreras locales a mano (auditoría)
./tools/verificar.ps1

# Solo el linter (marcar basura) y arreglar lo seguro
ruff check .
ruff check . --fix

# Solo el formato: ver qué cambiaría / aplicarlo
ruff format --check .
ruff format .

# Solo los tests
pytest

# Encender el hook pre-push (una sola vez por clon)
git config core.hooksPath .githooks

# Subir saltándose el hook a propósito (raro)
git push --no-verify
```

---

## 7. Local vs nube (qué activa cada quién)

| Pieza | ¿Local o nube? | Cómo se activa |
|---|---|---|
| `ruff`, `pytest` | **Local** (instalados) | `pip install -e ".[full,test,dev]"` (el extra real de la UI es `ui-ng`, no `ui`; `full` ya lo incluye) |
| Hook `pre-push` | **Local** | `git config core.hooksPath .githooks` (una vez por clon) |
| `tools/verificar.ps1` | **Local** | se corre a mano o lo dispara el hook |
| **CI / pipeline** | **Nube** | automático en cada push/PR; no se activa ni se salta |
| Tests, ADRs, docs | viajan en el repo | — |

> **La regla de oro:** lo local **avisa rápido pero es opcional** (fácil de olvidar encender el
> hook); el **CI es la barrera automática**. Aunque olvides el hook, **el CI te atrapa al push.**
>
> **Para que el CI *bloquee* (no solo avise) en colaboración:** hoy reporta verde/rojo pero no
> impide mergear. Con **branch protection** en GitHub (requiere PR + checks `lint`/`pytest` en
> verde) pasa a **detener a cualquiera** que no cumpla las reglas. Es el paso pendiente para
> cuando el repo tenga colaboradores (apuntado en el ROADMAP); single-author no lo necesita.

---

## 8. Dependencias (qué necesitas instalado)

| Dependencia | Para qué |
|---|---|
| **Git** | versionar (commits, push, ramas) y disparar el hook |
| **Python ≥ 3.10** | correr el motor, ruff y pytest |
| **ruff** | linter + formatter — `pip install -e ".[dev]"` |
| **pytest** (+ extras) | suite de tests — `pip install -e ".[full,test,dev]"` (instalación completa de dev; el extra de UI es `ui-ng`) |
| **playwright + Pillow** | smoke visual del Paso 0 — `pip install -e ".[dev]"` + `playwright install chromium` (solo para los tests visuales; skipean si no está) |
| **Windows PowerShell 5.1** | correr `tools/verificar.ps1` |
| **ffmpeg** (sistema) | solo para el QA manual de overlay/compose; los tests NO lo invocan |

---

## 9. Mapa: dónde vive cada cosa

```
C:\Repositorio personal\SimGhostInputs\   <- raíz del repo
├─ .githooks/pre-push                      <- el git hook (avisa lint/formato/tests; BLOQUEA doc-drift §8)
├─ .github/workflows/tests.yml             <- CI push/PR (barrera en la nube: lint + formato + tests)
├─ .github/workflows/release.yml           <- CI release (genera y adjunta el instalador al release de GitHub; ADR 0022)
├─ .github/workflows/installer.yml         <- CI ensayo del empaquetado en PR (installer-smoke), sin publicar nada
├─ .claude/                                <- roles y auto-cableado en sesión (viaja con el repo)
│  ├─ settings.json                        <- registra los hooks de sesión (Stop)
│  ├─ hooks/                               <- review-stop, andon-stop, gemba-stop (frenan el cierre, disparan el rol)
│  └─ skills/                              <- los asientos-skill: escribano, armando (arquitecto), charbel, mariana
├─ .gitignore                              <- qué NO se versiona
├─ pyproject.toml                          <- versión, deps, extras y config de ruff
├─ CHANGELOG.md                            <- bitácora de cambios
├─ ROADMAP.md                              <- estado vivo, camino a v1.0, gaps, deuda
├─ CONTRIBUTING.md                         <- entorno dev, convención de commits, matriz de docs (§8)
├─ tools/
│  ├─ verificar.ps1                        <- el verificador local (lint + formato + tests + doc-gate + auditor)
│  └─ auditar.ps1                          <- auditor del grafo de docs (product/ + engineering/); lo corre el CI
├─ fantasma/                               <- el código (core, importers, viz, ui, cli)
├─ tests/                                  <- la suite de pytest (espejo del paquete)
└─ docs/
   ├─ flujo-de-trabajo.md                  <- esta guía
   ├─ benchmark-linter.md                  <- por qué ruff
   ├─ glosario.md                          <- vocabulario canónico
   └─ decisions/                           <- los ADR (el porqué de cada decisión) + índice
```

---

## 10. Decisiones relacionadas (el porqué)

- [ADR 0003 — Estrategia de pruebas automatizadas](decisions/0003-testing.md): qué se automatiza
  vs qué se prueba a mano, la regla operativa de pruebas, y el límite de la máquina.
- [ADR 0010 — Framework de UI](decisions/0010-framework-ui-streamlit.md): por qué Streamlit hoy y
  qué se difiere a v2.0; incluye la directiva de **tests a prueba de migración**.
- [`docs/benchmark-linter.md`](benchmark-linter.md): por qué ruff y no flake8/pylint/black; cómo
  se configuró (`F`+`I`, sin el ruido de E701/E741) y el baseline de formato.
- [ADR 0014 — Gate de UX/UI](decisions/0014-gate-ux-ui.md) y [`docs/ux-patterns.md`](ux-patterns.md):
  el equivalente de las barreras para la **interfaz** — lo medible (layout, contraste, estructura)
  bloquea como los tests; lo subjetivo es checkpoint de Mariana que vuelve al PO. Casos de uso que
  alimentan la evaluación en [`docs/casos-de-uso.md`](casos-de-uso.md).

---

## 11. Resumen en una frase

> **Exploras** (suelto, nada corre) → el **cambio incluye su test** (y un ADR si fue decisión) →
> **en sesión**, los hooks disparan solos al **Reviewer** (`/code-review`) y al **Escribano**
> (sincroniza los docs §8) → al hacer **push**, `verificar.ps1` **avisa** lint/formato/tests y
> **BLOQUEA si hay doc-drift §8** → el **CI bloquea** lint/formato/tests en la nube → y cada tanto
> **`release-helper`** corta una versión.

Linter + formatter + tests = deterministas (avisan local, **bloquean en CI**). El **doc-drift §8**
(código sin su doc dueño) es determinista y **bloquea ya en local**. El **contenido** del Reviewer y
del Escribano es juicio (aconseja / propone, reversible), pero **su disparo está automatizado** (hooks
de sesión). **Determinismo bloquea; el juicio se auto-dispara, pero nunca es portero de lo irreversible.**
