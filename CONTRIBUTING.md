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

### Blast radius — al hacer este cambio, revisa estos documentos

> `CHANGELOG.md` se actualiza **siempre** que el cambio sea liberable; se omite abajo por brevedad.

| Cambio | Documentos a actualizar |
| :-- | :-- |
| Flag/comando CLI nuevo, o cambio de comportamiento de uno | `README` (uso rápido) · `guia-usuario` · `formato-datos` si cambian las salidas |
| Cambio visual del HUD/overlay (color, panel, franja de datos) | `hud-reference` · `README` (tabla de colores) · **ADR nuevo** + `docs/decisions/README.md` |
| Cambio en `core/` (detección de curvas, comparación, `wear`, normalización) | `formato-datos` (algoritmo + JSON + CSV) · `tests/` si cambian números/signos · ADR si es una decisión |
| Dependencia o extra nuevo | `pyproject.toml` · `README` (tabla de deps + instalación) · §3 de este doc · `setup.ps1` |
| Importador o formato de entrada nuevo | `README` (tabla de sims) · `guia-usuario` · `formato-datos` (canales) · §7 (bienvenidas) |
| Cambio de alcance o de un principio de diseño | `PRODUCT_BRIEF` · `ROADMAP` · §4 de este doc si aplica |
| Release / bump de versión | `pyproject.toml` · `CHANGELOG` (`[Unreleased]` → versión con fecha) · `ROADMAP` (estado actual + footer) · `README` (badge) · tag git anotado |
| Decisión de arquitectura/diseño | **ADR nuevo** en `docs/decisions/` · su `README.md` (índice) · el documento que la decisión afecta |

### Regla de consistencia de vocabulario

El mismo concepto debe llamarse **igual** en todos los documentos. Si renombras algo (un color, un campo de salida, una fase), búscalo en el resto de la documentación antes de cerrar el cambio. Vocabularios que deben coincidir entre docs:

- Nombres de colores del HUD → `README` ↔ `docs/hud-reference.md`
- Nombres de versiones/fases → `ROADMAP` ↔ `PRODUCT_BRIEF`
- Nombres de campos de salida → `docs/formato-datos.md` ↔ el código que los emite
