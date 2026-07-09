# ADR 0029 — Lockfile de dependencias con `pip-compile`

- **Estado:** Aceptada
- **Fecha:** 2026-07-09

## Contexto

Auditoría integral (`qa_runs/2026-07-03-auditoria-integral/fase1-seguridad.md`, Superficie 6
"Dependencias con CVEs conocidos"): el repo no tiene lockfile. `pyproject.toml` declara todos
los extras como rangos (`ruff>=0.15,<1`, etc.), nunca versiones exactas. Resultado: **NO
AUDITABLE** — sin `poetry.lock`, `requirements.txt` fijado ni `uv.lock` no es posible verificar
versiones instaladas contra bases de CVE, y dos instalaciones del mismo commit pueden traer
dependencias transitivas distintas (build no reproducible). Recomendación de la auditoría:
generar un lockfile como parte del proceso de release. Anotado en `ROADMAP.md` como deuda
técnica Media.

El repo hoy instala con `pip install -e ".[full]"` (`CONTRIBUTING.md` §3) y no usa `uv` en
ningún punto — ni CI, ni scripts, ni documentación de instalación.

## Decisión

Adoptar **`pip-compile`** (del paquete `pip-tools`) para generar `requirements-lock.txt` a
partir de los extras de `pyproject.toml`, regenerable a mano en el proceso de release. Se suma
`pip-tools` al extra `dev` de `pyproject.toml`.

## Razones

- **Se queda en el ecosistema `pip` que el repo ya usa.** El flujo de instalación del
  contribuidor no cambia (`pip install -e ".[full]"` sigue siendo el comando); el lockfile es un
  artefacto adicional para auditoría/reproducibilidad, no un reemplazo del flujo de desarrollo.
- **No introduce una herramienta nueva sin necesidad probada.** `uv` es más rápido y generaliza
  mejor, pero es un cambio de tooling con superficie propia (instalación, versión, comportamiento
  distinto de resolución) para un repo single-author donde el problema real es "no hay ningún
  lockfile", no "pip es lento". Adoptar la opción de menor fricción resuelve el hallazgo de la
  auditoría sin sumar una dependencia de infraestructura nueva.
- **`pip-compile` es el estándar de facto para este problema en el ecosistema `pip`** (mantenido
  por el mismo proyecto `pip` — `jazzband/pip-tools`), ampliamente usado, sin licencia que choque
  con AGPL-3.0.

## El camino que NO se toma (y por qué tienta)

- **Adoptar `uv` como gestor de dependencias/lockfile.** Tienta porque es la herramienta más
  moderna y ya se menciona en `docs/benchmark-linter.md` como la empresa detrás de `ruff` — fácil
  asumir que "ya estamos en su órbita". Pero adoptarlo aquí significa migrar el flujo de
  instalación completo (`uv sync` en vez de `pip install -e`), tocar CI y `CONTRIBUTING.md` §3
  más allá de lo que pide el hallazgo de auditoría. Se descarta por ahora — no hay evidencia de
  que `pip-compile` sea insuficiente.
- **`pip freeze > requirements-lock.txt` manual.** Es el camino más simple y tentador (cero
  dependencias nuevas), pero congela exactamente lo instalado en la máquina que lo corre sin
  resolver desde `pyproject.toml` — no distingue dependencias directas de transitivas ni permite
  regenerar de forma determinista con extras específicos. `pip-compile` resuelve desde el
  `pyproject.toml` real, que es la fuente de verdad de dependencias del repo.

## Consecuencias

- Se gana: `requirements-lock.txt` auditable contra CVEs, builds reproducibles al fijar exacto.
- Se pierde / cuesta: el lockfile requiere regeneración manual (`pip-compile`) cuando cambian los
  extras de `pyproject.toml` — no hay automatización de CI que lo valide todavía; queda como paso
  del proceso de release, documentado en `CONTRIBUTING.md` §3.
- Pendiente: la generación mecánica del lockfile inicial y la nota de proceso van en un PR
  separado (deuda técnica, ROADMAP), no en este ADR.
