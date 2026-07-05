# ADR 0023 — Fuente unica de verdad de la version: literal en `fantasma/__init__.py`

- **Estado:** Aceptada
- **Fecha:** 2026-07-05
- **Autor:** Armando Medina
- **Relacionada con:** [ADR 0022](0022-ci-release-installer.md) (CI que lee la version para el instalador), [v2.1.1](../../CHANGELOG.md) (donde se bumpeó el badge a mano por tercera vez)

## Contexto

La versión del proyecto vivía en tres lugares distintos sin ningún mecanismo que los
mantuviera sincronizados:

1. **`pyproject.toml`** — literal estático (`version = "2.2.0"`). Es la fuente que
   setuptools usa para publicar y que `importlib.metadata` expone en runtime.
2. **`fantasma/__init__.py`** — `__version__` leído desde `importlib.metadata.version(
   "fantasma-inputs")`. En un editable install (`pip install -e .`) este valor queda
   **congelado al momento de la instalación**: si se bumpeó después sin reinstalar,
   `__version__` devuelve la versión antigua (se comprobó devolviendo `2.1.1` mientras
   `pyproject.toml` ya marcaba `2.2.0`). En el ejecutable empaquetado con PyInstaller el
   comportamiento de `importlib.metadata` también es poco fiable.
3. **Badge del footer de la UI** (`fantasma/ui/ng_app.py`) — literal manual (`"v2.1"`,
   etc.). Al ser independiente del código, se olvida en cada release: quedó en `v2.0`
   tras el release 2.1.0, fue corregido a mano en 2.1.1, y volvió a quedar en `v2.1`
   tras el release 2.2.0.

El ADR 0022 introdujo adicionalmente `tools/build_installer.py` como cuarto consumidor,
que leía la versión vía `importlib.metadata` — con el mismo problema de stale en editable.

El resultado: tres contextos (dev editable, build CI, exe congelado) con comportamientos
distintos y un proceso de release que requiere acordarse de actualizar un literal que
ninguna herramienta valida.

## Decisión

La **fuente unica de verdad de la version es un literal `__version__` en
`fantasma/__init__.py`**. Todos los demas consumidores derivan de ahi:

- **`pyproject.toml`** usa `dynamic = ["version"]` con
  `[tool.setuptools.dynamic] version = {attr = "fantasma.__version__"}`. Setuptools lee
  el atributo por AST en tiempo de build, sin importar el paquete; es compatible con
  editable installs y con el entorno de CI.
- **El badge del footer** (`ng_app.py`) importa `fantasma.__version__` en lugar de usar
  un literal.
- **`tools/build_installer.py`** importa `fantasma.__version__` para pasársela a ISCC
  en lugar de usar `importlib.metadata`.

Para bumpear la version **solo se edita `fantasma/__init__.py`**. `pyproject.toml` ya no
contiene la version como campo estatico.

## Razones

- **Un literal en codigo es la unica fuente fiable en los tres contextos.** En dev
  editable el modulo se importa directamente desde el disco (no hay metadata compilada
  que quedarse stale). En build, setuptools extrae el atributo por AST (no ejecuta el
  modulo). En el exe congelado de PyInstaller el string esta en el bytecode compilado.
  `importlib.metadata` falla en al menos dos de los tres contextos.

- **El badge olvidado es evidencia empirica, no teoria.** Falló en 2.1.0, en 2.1.1 y en
  2.2.0 — tres releases consecutivos. Un proceso que requiere memoria humana y falla con
  esa frecuencia debe eliminarse, no reforzarse con documentacion.

- **setuptools soporta `attr:` desde hace años** y es el patron recomendado para
  proyectos que quieren mantener `__version__` en el codigo. No es una solucion ad-hoc.

## El camino que NO se toma (y por que tienta)

- **`pyproject.toml` como SSOT y que todos lean `importlib.metadata`** — Tienta porque
  es el patron mas documentado ("la version vive en `pyproject`"). Se descarta: en
  editable install la metadata queda stale hasta reinstalar; en PyInstaller la metadata
  puede no estar disponible o resolver una version antigua. Es exactamente el problema
  que se quiere eliminar.

- **Bumpear el badge manualmente en cada release (status quo)** — Se descarta: ya fallo
  en tres releases consecutivos. El proceso que depende de memoria humana en una tarea
  mecanica es un proceso roto.

- **Leer `pyproject.toml` en runtime** — Tienta como alternativa a `importlib.metadata`
  porque siempre refleja la version exacta en disco. Se descarta: `pyproject.toml` no
  se empaqueta en el exe congelado de PyInstaller; en el instalador distribuido no
  existe ese archivo.

- **Mantener los tres literales sincronizados con un script de bump** — Tienta porque
  no requiere cambiar la estructura del proyecto. Se descarta: añade una herramienta de
  mantenimiento propia que puede desincronizarse o no ejecutarse. La solucion correcta
  elimina la redundancia, no la automatiza.

## Consecuencias

- **Se gana:** un solo punto de edicion para bumpear (`fantasma/__init__.py`). El badge
  del footer y el instalador reflejan siempre la version correcta sin intervencion
  manual. Desaparece la fuente de los tres bugs de badge consecutivos. `importlib.metadata`
  queda como deuda anotada (ROADMAP), no como fuente de verdad.

- **Impacto en el proceso de release:** la skill `release-helper` bumpeaba hasta ahora
  `pyproject.toml`. Con este cambio el bump va a `fantasma/__init__.py`. Cualquier
  sesion futura (o una IA con el mismo contexto) que intente bumpear `pyproject.toml`
  directamente estara tocando el lugar equivocado — `pyproject.toml` ya no contiene la
  version como campo estatico.

- **Costo:** quien revise `pyproject.toml` buscando la version no la encontrara ahi;
  el `dynamic` redirige a `fantasma/__init__.py`. Se acepta: es el comportamiento
  estandar de setuptools con `attr:` y queda registrado en este ADR.

- **Pendiente de validar:** que el CI (`release.yml`, ADR 0022) lee la version
  correctamente tras el cambio — `build_installer.py` importa `fantasma.__version__`
  en lugar de llamar a `importlib.metadata`, lo que requiere que el paquete sea
  importable en el entorno de CI (ya lo es, via `pip install -e .[ui-ng]`).
