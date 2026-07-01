# Contribuir a SimGhostInputs

> Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

Gracias por considerar contribuir. Este documento explica cómo reportar bugs, proponer mejoras y enviar código.

> Convenciones base de método: [project-starter](https://github.com/ArmandoMedina/project-starter).

Al contribuir aceptas que tu código se publique bajo **AGPL-3.0-or-later**.

---

## Índice

1. [Reportar un bug](#1-reportar-un-bug)
2. [Proponer una mejora o feature](#2-proponer-una-mejora-o-feature)
3. [Entorno de desarrollo](#3-entorno-de-desarrollo)
4. [Principios de diseño](#4-principios-de-diseño)
5. [Convenciones de commits](#5-convenciones-de-commits)
6. [Proceso de Pull Request](#6-proceso-de-pull-request)
7. [Qué contribuciones son bienvenidas](#7-qué-contribuciones-son-bienvenidas)
8. [Mantenimiento de documentación](#8-mantenimiento-de-documentación)

---

## 1. Reportar un bug

Abre un **Issue** en GitHub con:

- **Versión** — `fantasma --version` o el valor en `pyproject.toml`
- **Sistema operativo y versión de Python**
- **Pasos exactos para reproducirlo** — cuanto más específico, más rápido se resuelve
- **Qué esperabas que pasara vs qué pasó**
- **Traza de error completa** (el bloque que empieza con `Traceback`)
- **Tipo de archivo de telemetría** — MoTeC i2 CSV, XLSX, CSV genérico, ¿de qué sim?

Si el bug involucra un archivo de telemetría, no lo subas completo. Con las primeras 30–50 filas del CSV (sin datos personales) suele ser suficiente. Nunca subas telemetría que no sea tuya.

---

## 2. Proponer una mejora o feature

Abre un **Issue** antes de escribir código. Describe:

- **El problema que resuelve** — no la solución todavía, el problema
- **Quién se beneficia** — ¿solo tu caso de uso o es común en la comunidad?
- **Alternativas que consideraste**

Esto evita que inviertas tiempo en algo que ya está en el roadmap, que duplica otra cosa, o que no encaja con la dirección del proyecto.

---

## 3. Entorno de desarrollo

**Requisitos:** Python ≥ 3.10, git, ffmpeg en el PATH.

```powershell
# Clona y entra al directorio
git clone https://github.com/ArmandoMedina/SimGhostInputs.git
cd SimGhostInputs

# Instala en modo editable con todas las dependencias opcionales
pip install -e ".[full]"

# Verifica que el CLI funciona
fantasma --help
```

Para la UI:

```powershell
fantasma ui
```

**Smoke test sin datos privados:** usa cualquier export de MoTeC i2 propio y corre
`fantasma laps`, `detect` y `compare`. Puedes comparar una vuelta contra otra del mismo outing.

**Estructura del proyecto:**

```
fantasma/
  core/         modelo de datos (lap.py), normalización, detección de curvas, comparación
  importers/    lectura de archivos (MoTeC CSV/XLSX, CSV genérico)
  viz/          gráficas, overlay HUD, composición de video, sincronía
  ui/           interfaz Streamlit — app.py (router), step0-4.py (pasos), _helpers.py (compartido)
  cli.py        punto de entrada de comandos
```

La suite de tests está arrancada (pytest). Instálala y córrela con:

```powershell
pip install -e ".[test]"
pytest
```

Los tests usan datos sintéticos deterministas (`make_lap` en `tests/conftest.py`) —
nunca telemetría real. El enfoque, la estructura y la directiva de qué se automatiza
vs qué se prueba a mano están en [`docs/decisions/0003-testing.md`](docs/decisions/0003-testing.md).
Ampliar la cobertura (resto de `viz/`, importadores) es especialmente bienvenido.

**Pruebas — cuándo, cómo y qué hacer si falla o falta:**

- **Cuándo:** corre `pytest` **antes de cerrar cualquier cambio que toque comportamiento**. Verde es condición para commitear/pushear.
- **El test es parte del cambio:** si añades o cambias lógica determinista (`core/`, `importers/`, helpers puros de `viz/`), **el cambio incluye su test** — no es opcional ni "para después".
- **Cómo / qué se automatiza vs qué es manual:** ver [`docs/decisions/0003-testing.md`](docs/decisions/0003-testing.md).
- **Si el escenario no existe:** créalo (blinda el comportamiento nuevo o el bug, para que no reaparezca).
- **Si un test está mal o desactualizado:** corrígelo — pero **primero entiende por qué falla**. Un rojo suele ser el test atrapando una regresión real, no un estorbo; ajustarlo para que pase sin diagnosticar es apagar la alarma de humo.

**Puesta a punto del clon (hazla una vez):**

Las barreras locales **viven en el repo pero no se encienden solas** (git, por seguridad, no
ejecuta hooks de un clon sin que tú lo autorices). Actívalas al clonar:

```powershell
# 1. Instala las herramientas de desarrollo (linter + tests)
pip install -e ".[dev,test,ui,sync]"

# 2. Enciende el hook que corre las validaciones antes de cada push
git config core.hooksPath .githooks
```

A partir de ahí, cada `git push` dispara `tools/verificar.ps1` (lint + formato + tests +
doc-gate) en **modo aviso**: te avisa antes de subir, pero **no bloquea** (puedes cancelar y
arreglar, o seguir bajo tu responsabilidad). La barrera que **sí bloquea** es el CI en GitHub
(corre solo en cada push/PR; nadie la puede saltar desde su máquina). El sistema completo —qué
corre cuándo y qué avisa vs qué bloquea— está explicado desde cero en
[`docs/flujo-de-trabajo.md`](docs/flujo-de-trabajo.md). **Saltarse esto solo es posible a
propósito** (`git push --no-verify`), nunca por desconocimiento.

---

## 4. Principios de diseño

1. **Motor sin datos.** El repo nunca incluye telemetrías, referencias ni setups. Los tests usan datos sintéticos o aportados por quien los corre.
2. **Comparación por distancia.** El metro de pista es el índice maestro, no el tiempo.
3. **Sin dependencias en el núcleo.** `fantasma/core` e `importers` son librería estándar pura. Las dependencias viven en extras opcionales (`[overlay]`, `[ui]`, `[sync]`…) y deben degradar con gracia si faltan.
4. **Determinista.** Mismo archivo de entrada → misma salida, siempre.

---

## 5. Convenciones de commits

Usamos **Conventional Commits**:

```
<tipo>(<scope opcional>): descripción en minúsculas
```

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Cambio estructural sin cambiar comportamiento |
| `docs` | Solo documentación |
| `chore` | Mantenimiento (versión, deps, CI) |
| `test` | Añadir o corregir tests |

Ejemplos:

```
feat(importers): soporte para CSV de SimHub con detección automática de columnas
fix(overlay): corregir render paralelo en Linux con multiprocessing fork
docs: añadir guía de exportación para iRacing
```

---

## 6. Proceso de Pull Request

1. **Abre un issue primero** si el cambio es significativo
2. **Haz fork** del repo y trabaja en una rama descriptiva (`feat/acc-importer`, `fix/overlay-cancel`)
3. **Un PR por tema** — si tienes dos cambios independientes, dos PRs
4. **Describe qué problema resuelve el PR**, no solo qué archivos tocaste
5. Si tocas el detector o el comparador, incluye un antes/después con datos reales (basta el `report.md`)
6. **Prueba manualmente** con telemetría real antes de enviar
7. **El CI debe quedar en verde para mergear.** En tu PR corren solos el `lint` (`ruff check` + `ruff format --check`) y los `tests` (`pytest` en Python 3.10–3.12). Un PR en rojo no se mezcla — la barrera es automática, no depende de que alguien se acuerde de revisar.

---

## 7. Qué contribuciones son bienvenidas

**Alta prioridad:**

- **Importadores nuevos** — MoTeC `.ld` directo (formato binario, sin copiar código sin licencia compatible), iRacing `.ibt`, logs de SimHub, Assetto Corsa, rFactor 2
- **Track packs** — JSONs de nombres de curvas por circuito/trazado (ver `docs/formato-datos.md`). Van en un repo de datos comunitario, no en el motor
- **Tests unitarios** para `core/` — normalización, detección de curvas, comparación
- **Robustez del detector** — el emparejamiento de frenadas da artefactos cuando piloto y referencia difieren >100 m; ideas bienvenidas

**También bienvenido:**

- Empaquetado como `.exe` con PyInstaller para usuarios sin Python
- Traducciones de la UI o documentación (inglés primero)
- Guías de exportación para sims no documentados aún
- Mejoras de rendimiento con benchmarks que las demuestren

**Fuera de scope (discutir en issue antes de abrir PR):**

- Cambios de estilo sin impacto funcional
- Dependencias nuevas sin justificación clara
- Refactors grandes sin issue previo

---

## 8. Mantenimiento de documentación

La documentación está repartida en varias piezas con responsabilidades distintas, y **un solo cambio de código suele tocar más de un documento**. Dejar docs desincronizados es la causa #1 de deriva en este repo. Esta sección es el mapa para evitarlo: úsala como checklist al cerrar cualquier cambio.

### Quién es la fuente de verdad (SSOT) de qué

Cada hecho vive en **un** documento. Los demás enlazan, no duplican.

| Documento | Es dueño de |
| :-- | :-- |
| `pyproject.toml` | Versión, dependencias y extras (`fantasma/__init__.py` lee la versión de aquí — no se duplica) |
| `CHANGELOG.md` | Historial de cambios por versión (Keep a Changelog) |
| `ROADMAP.md` | Estado vivo, camino a v1.0, gaps técnicos y deuda |
| `README.md` | Vitrina: qué hace, instalación, uso rápido, tabla de colores del HUD, tabla de sims, badge de estado |
| `PRODUCT_BRIEF.md` | El norte: alcance (dentro/fuera), nicho, principios de diseño, landscape |
| `docs/guia-usuario.md` | Flujo de usuario de punta a punta (CLI + UI) |
| `docs/hud-reference.md` | Anatomía y código de colores del HUD |
| `docs/formato-datos.md` | Modelo canónico de datos, esquema `corners` JSON, salidas CSV, algoritmo de detección |
| `CONTRIBUTING.md` | Estructura del proyecto, entorno dev, convenciones y este mapa |
| `docs/decisions/` + su `README.md` | El porqué de cada decisión (un ADR por decisión) + índice |
| `docs/glosario.md` | Definición canónica de los términos del proyecto (vocabulario) |
| `docs/flujo-de-trabajo.md` | El sistema de barreras y el flujo explorar→commit→push (linter, formato, tests, hook, CI, doc-gate) explicado desde cero |
| `docs/benchmark-linter.md` | Por qué `ruff` y no las alternativas; cómo se configuró |
| `docs/benchmark-ui-framework.md` | Por qué NiceGUI y no las alternativas; cómo se empaqueta como instalador doble-click |
| `tools/build_installer.py` | Cómo generar el bundle one-dir con nicegui-pack y medir su tamaño |
| `tools/installer.iss` | Script Inno Setup para el instalador Windows doble-click de v2.0 |
| `product/` (+ su `README.md`) | El **QUÉ**: jerarquía funcional (ecosistema→solución→dominio→módulo→capacidad), criterios de aceptación y backlog. Las notas **enlazan** a su dueño SSOT (p. ej. una capacidad de `core/` cede el esquema a `formato-datos`), no duplican |
| `engineering/` (+ su `README.md`) | El **CÓMO**: panorama de arquitectura, especificaciones técnicas, modelos de datos y estrategia de pruebas. Igual: enlaza a los dueños canónicos (`formato-datos`, `hud-reference`, ADRs) |
| `templates/` (+ su `README.md`) | Los moldes canónicos de cada tipo de nota de `product/`+`engineering/` |

### Blast radius — al hacer este cambio, revisa estos documentos

> `CHANGELOG.md` se actualiza **siempre** que el cambio sea liberable; se omite abajo por brevedad.

> **Espejo ejecutable de esta tabla: `tools/blast-radius.json`.** Cada entrada de la tabla tiene su par en ese manifiesto, que consumen `verificar.ps1` (gate de push) y `escribano-stop.ps1` (hook de sesión). Para agregar un área: edita el JSON — nada más. Esta prosa es la explicación; el JSON es la ley que el gate ejecuta.

| Cambio | Documentos a actualizar | Rol especialista que valida |
| :-- | :-- | :-- |
| Flag/comando CLI nuevo, o cambio de comportamiento de uno | `README` (uso rápido) · `guia-usuario` · `formato-datos` si cambian las salidas | _solo Reviewer_ |
| Cambio visual del HUD/overlay (color, panel, franja de datos) | `hud-reference` · `README` (tabla de colores) · `ux-patterns.md` · **ADR nuevo** + `docs/decisions/README.md` | **Mariana** (UX) |
| Cambio de UX/layout en la UI Streamlit (`fantasma/ui/`) | `guia-usuario` (BLOQUEA) · `ux-patterns.md` (AVISA) · `product/capacidades/UI-*` si cambia un criterio funcional (AVISA) | **Mariana** (UX) |
| Cambio en `core/` (detección de curvas, comparación, `wear`, normalización) | `formato-datos` (algoritmo + JSON + CSV, BLOQUEA) · `tests/` si cambian números/signos · `product/capacidades/CMP-*/COR-*/NRM-*/WER-*` si cambia un criterio (AVISA) · ADR si es una decisión | **Charbel** (telemetría) |
| Dependencia o extra nuevo | `pyproject.toml` · `README` (tabla de deps + instalación) · §3 de este doc · `setup.ps1` | _solo Reviewer_ |
| Importador o formato de entrada nuevo o modificado (`fantasma/importers/`) | `README` (tabla de sims, AVISA) · `guia-usuario` (AVISA) · `formato-datos` (canales, AVISA) · §7 (bienvenidas) · `product/capacidades/IMP-*` si cambia un criterio (AVISA) | **Charbel** (telemetría) |
| Cambio de alcance o de un principio de diseño | `PRODUCT_BRIEF` · `ROADMAP` · §4 de este doc si aplica | **PO** + Armando |
| Release / bump de versión | `pyproject.toml` · `CHANGELOG` (`[Unreleased]` → versión con fecha) · `ROADMAP` (estado actual + footer) · `README` (badge) · tag git anotado | **PO** (corta la versión) |
| Decisión de arquitectura/diseño | **ADR nuevo** en `docs/decisions/` · su `README.md` (índice) · el documento que la decisión afecta | **Armando** (arquitecto, + PO) |
| Término o concepto nuevo (o renombrado) | `docs/glosario.md` (definición canónica) · busca el término en los demás docs para dejarlo consistente | _solo Reviewer_ (consistencia) |
| Cambio en las barreras o la gobernanza (linter, formato, hook, CI, tests, doc-gate) | `docs/flujo-de-trabajo.md` · `docs/benchmark-linter.md` si cambia la herramienta · `.github/workflows/tests.yml` si cambia el CI | **PO / Armando** |
| Capacidad/dominio/módulo nuevo, o cambio del motor que afecta una capacidad | la nota de `product/` correspondiente (`estado`, criterios de aceptación, wikilinks) · `engineering/` si cambia un algoritmo o modelo | **Armando** (lo verifica `auditar.ps1`) |

> **La integridad de `product/`+`engineering/` se gatea determinísticamente.** Igual que `pytest` hace cumplir el código, [`tools/auditar.ps1`](docs/decisions/0016-gate-grafo-documentacion.md) audita el grafo de docs: **BLOQUEA** frontmatter ausente/incompleto, wikilinks rotos y capacidades `vigente` sin criterios Gherkin; **avisa** lo que es juicio (capacidad vigente sin test citado, notas huérfanas). Lo corre `verificar.ps1` (local) y el CI (job `docs-graph`, infranqueable). Modulado por estado: `en_definicion` solo exige frontmatter + enlaces. No hay archivos de auto-firma: el gate lee el artefacto, no confía en que un agente declare "ya validé" ([ADR 0016](docs/decisions/0016-gate-grafo-documentacion.md)).

### Roles que validan

La columna de arriba enruta *quién juzga* un cambio, igual que la de en medio enruta *qué docs* tocar. Dos roles son **base** y por eso no se repiten por fila:

- **Reviewer** — revisa **todo** cambio de código (bugs, calidad). Aplica siempre que toques `fantasma/`.
- **Escribano** — cierra los **docs dueños** de la fila. Es el paso final de todo cambio.

Los especialistas se encienden solo cuando aplica su área:

- **Charbel** (telemetría) — correctitud de datos. **Casi todo determinista** (tests, rangos físicos, ¿parsea el archivo?, ¿están los canales?); la IA solo juzga lo ambiguo (¿archivo malo o anomalía real?). **No** pongas la IA a "validar la telemetría" en bloque — ese asiento es de los tests.
- **Mariana** (UX del HUD y UI) — aceptación visual. **Casi todo juicio**: "¿el HUD se ve bien?" y "¿el layout de la UI tiene sentido?" son **checkpoints que vuelven al PO**, no un auto-pase.
- **Armando** (arquitecto) — decisiones técnicas (ADR) y la **estructura** de `product/`+`engineering/`. Se co-produce con el PO; se dispara por necesidad, no "todos los ADR arriba".
- **PO** (tú, el humano) — alcance, prioridad, release. Inicia la tarea y es el único que aprieta lo irreversible.

> Estos nombres son **asientos** del casting; quién los ocupa y cómo (en sesión o como subagente), en [`docs/flujo-de-trabajo.md` §4 — El casting](docs/flujo-de-trabajo.md#el-casting--asientos-no-skills).

> **Estado de cableado (sé honesto al leer esto: no todo está automatizado).** Hoy disparan solos por hook el **Reviewer**, el **Escribano** y **Mariana** (ver `.claude/hooks/`; Mariana se cableó en [ADR 0011](docs/decisions/0011-cablear-mariana-no-charbel.md) cuando un bug visual lo pidió). **Charbel** sigue **declarado aquí** —esta tabla es su router— pero **sin hook a propósito**: su validación de telemetría ya vive en los tests, y cablearlo sería sobre-orquestar (ADR 0011). **PO** y **Armando** (arquitecto) viven en la capa de ideación (tú + el chat), no en un hook.

### Regla de consistencia de vocabulario

El mismo concepto debe llamarse **igual** en todos los documentos. Si renombras algo (un color, un campo de salida, una fase), búscalo en el resto de la documentación antes de cerrar el cambio. Vocabularios que deben coincidir entre docs:

- Nombres de colores del HUD → `README` ↔ `docs/hud-reference.md`
- Nombres de versiones/fases → `ROADMAP` ↔ `PRODUCT_BRIEF`
- Nombres de campos de salida → `docs/formato-datos.md` ↔ el código que los emite
