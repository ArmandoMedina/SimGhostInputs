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
  bien**; **≠ 0 = hubo problema**. El hook local sale **0 siempre** (solo avisa). Las barreras
  del CI salen ≠ 0 si fallan (y entonces **bloquean**).
- **CI / Integración Continua / GitHub Actions / "pipeline" / "workflow"**: una **máquina en la
  nube de GitHub** que corre comprobaciones **solas en cada push y PR**. Si una falla, el push
  queda **en rojo**. Es **la barrera que nadie puede saltar** desde su computadora. Vive en
  `.github/workflows/tests.yml`.
- **Verificador (`tools/verificar.ps1`)**: nuestro script de PowerShell que corre **las cuatro
  barreras locales de un jalón** (lint, formato, tests, doc-gate) en modo aviso.
- **Modo aviso vs bloquea**: *avisar* = imprime el hallazgo y deja seguir; *bloquear* = detiene
  la operación. Regla del repo: **lo local avisa; el CI bloquea.**

### 2.4 Los artefactos del repo (qué es cada cosa)

- **Código** (`fantasma/`): el motor (núcleo `core/`, importadores, visualización `viz/`, UI
  Streamlit). Es lo que el linter y los tests vigilan.
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
| **Doc-gate** | Avisa si tocaste `fantasma/` sin actualizar `CHANGELOG.md`, con checklist (¿ADR? ¿ROADMAP?) | dentro de `tools/verificar.ps1` |
| **Hook `pre-push`** | Corre el verificador **solo**, justo antes de `git push` (avisa, no bloquea) | `.githooks/pre-push` |
| **CI (pipeline)** | Barrera dura en la nube: lint + formato + tests en cada push/PR | `.github/workflows/tests.yml` |
| **Decisiones (ADR)** | El porqué de todo, con su camino descartado | `docs/decisions/` + su `README.md` |
| **Benchmark del linter** | Por qué ruff y no las alternativas (licencias verificadas) | `docs/benchmark-linter.md` |
| **Revisión IA (consultiva)** | Lee el diff y **aconseja** correcciones; nunca bloquea | skill `/code-review` (Claude Code) |

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
  equivocado) → **regístrala como ADR** (skill `adr-helper`), actualiza el índice y el CHANGELOG.
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
4. **Doc-gate**: ¿tocaste `fantasma/` sin anotar el `CHANGELOG`? Imprime un checklist
   (¿fue decisión? → ADR · ¿cambió el plan? → ROADMAP). *Solo el CHANGELOG se auto-detecta;
   ADR y ROADMAP dependen de juicio, por eso checklist y no validación: forzarlos generaría
   entradas vacías.*

> Es **aviso, no barrera**: el push continúa aunque haya avisos. La barrera dura viene en el Paso 3.

### Paso 3 — Push (el CI **bloquea**)

Al hacer `git push`, GitHub corre el **CI** (`.github/workflows/tests.yml`). Si algo falla, el
push queda **en rojo**. Es el respaldo **que nadie puede saltar** desde su máquina. Dos jobs:

1. **`lint`** (Ubuntu): `ruff check` (basura) **y** `ruff format --check` (formato canónico).
2. **`pytest`** (Windows, Python 3.10 / 3.11 / 3.12): toda la suite de tests, en la plataforma
   objetivo del proyecto y en las tres versiones soportadas.

### Las tres barreras, juntas

```
  EXPLORAS         CONSOLIDAS              PUSH (git push)         PUSH (en la nube)
  (rama sucia)  →  cambio + test + ADR  →  hook pre-push       →  CI en GitHub Actions
   nada corre      (+ /code-review IA)     verificar.ps1          tests.yml
                   juicio, aconseja        (AVISA, sale 0)        (BLOQUEA, sale ≠0 si falla)
```

Mismas comprobaciones, autoridad creciente. **Avisa temprano, bloquea al final.**

### La frontera de versión (de vez en cuando)

Muchos commits se acumulan; al cerrar un hito, la skill **`release-helper`** corta una **versión**
(un tag SemVer `vX.Y.Z` + release en GitHub + CHANGELOG). Es otro ritmo, no cada cambio.

### Las tres dimensiones, y dónde acaba la máquina

El repo cuida la consistencia con **barreras deterministas**, cada una con su herramienta. Importa
ver **qué cubre cada una y qué NO**, porque no todo se puede atar por máquina.

| Dimensión | Pregunta que responde | Herramienta | Severidad |
|---|---|---|---|
| **Basura de código** | ¿imports/vars sin usar, nombres indefinidos? | `ruff check` (`F`+`I`) | avisa local · **bloquea en CI** |
| **Formato** | ¿el código está en el estilo canónico? | `ruff format --check` | avisa local · **bloquea en CI** |
| **Comportamiento del motor** | ¿la lógica determinista sigue dando los números correctos? | `pytest` | avisa local · **bloquea en CI** |
| **Documentación** | ¿el cambio quedó anotado donde debe? | doc-gate (CHANGELOG) + checklist | **avisa** (ADR/ROADMAP son juicio) |

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

- Un repo de **documentación / mockups** (como LivoTransfer) verifica que el mockup HTML y su
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
| `ruff`, `pytest` | **Local** (instalados) | `pip install -e ".[dev,test,ui,sync]"` |
| Hook `pre-push` | **Local** | `git config core.hooksPath .githooks` (una vez por clon) |
| `tools/verificar.ps1` | **Local** | se corre a mano o lo dispara el hook |
| **CI / pipeline** | **Nube** | automático en cada push/PR; no se activa ni se salta |
| Tests, ADRs, docs | viajan en el repo | — |

> **La regla de oro:** lo local **avisa rápido pero es opcional** (fácil de olvidar encender el
> hook); el **CI es la barrera automática**. Aunque olvides el hook, **el CI te atrapa al push.**

---

## 8. Dependencias (qué necesitas instalado)

| Dependencia | Para qué |
|---|---|
| **Git** | versionar (commits, push, ramas) y disparar el hook |
| **Python ≥ 3.10** | correr el motor, ruff y pytest |
| **ruff** | linter + formatter — `pip install -e ".[dev]"` |
| **pytest** (+ extras) | suite de tests — `pip install -e ".[test,ui,sync]"` |
| **Windows PowerShell 5.1** | correr `tools/verificar.ps1` |
| **ffmpeg** (sistema) | solo para el QA manual de overlay/compose; los tests NO lo invocan |

---

## 9. Mapa: dónde vive cada cosa

```
C:\Repositorio personal\SimGhostInputs\   <- raíz del repo
├─ .githooks/pre-push                      <- el hook (avisa al hacer push)
├─ .github/workflows/tests.yml             <- el CI (barrera en la nube: lint + pytest)
├─ .gitignore                              <- qué NO se versiona
├─ pyproject.toml                          <- versión, deps, extras y config de ruff
├─ CHANGELOG.md                            <- bitácora de cambios
├─ ROADMAP.md                              <- estado vivo, camino a v1.0, gaps, deuda
├─ CONTRIBUTING.md                         <- entorno dev, convención de commits, matriz de docs (§8)
├─ tools/
│  └─ verificar.ps1                        <- el verificador local (lint + formato + tests + doc-gate)
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

---

## 11. Resumen en una frase

> **Exploras** (suelto, nada corre) → el **cambio incluye su test** (y un ADR si fue decisión;
> `/code-review` te aconseja) → al hacer **push**, el **hook avisa** con `verificar.ps1` (lint +
> formato + tests + doc-gate) → y el **CI bloquea** si lint, formato o tests fallan → y cada tanto
> **`release-helper`** corta una versión.

Linter + formatter + tests = barreras deterministas (avisan local, **bloquean en CI**). Doc-gate y
`/code-review` = juicio (**avisan/aconsejan**, no bloquean). **Determinismo bloquea; juicio aconseja.**
