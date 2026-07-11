# ADR 0034 — Convergencia al núcleo neutral de Jidoka (una sola metodología)

- **Estado:** Aceptada (2026-07-10)

## Contexto

Este repo (SGI) y su hermano tracker-financiero corrían una **versión paralela** del método respecto a [Jidoka](https://github.com/ArmandoMedina/jidoka), la destilación pública que se homologó *de* estos labs. Mantener tres metodologías divergentes es deuda: un arreglo se hace tres veces. Un diagnóstico de delta (dos agentes, evidencia contra el artefacto) mostró que **en el motor Jidoka ya es la versión más nueva** (falla-cerrado, hooks *data-driven*, campo `reason`), así que converger hacia Jidoka es un **upgrade**, no una regresión. SGI adopta el **núcleo neutral** de Jidoka, conservando lo suyo. La convergencia toca solo la **maquinaria de método**, no `fantasma/` ni la app publicada.

## Decisión

SGI adopta la **maquinaria neutral** de Jidoka y **conserva su instancia, su casting y su producto**:

1. **Comandos:** `/planea`, `/gemba`, `/cierra`, `/que-sigue`, `/desatendido` (antes solo `/arranca`, que se conserva con sus 6 reglas duras).
2. **Motor:** `verificar.ps1` gana **falla-cerrado** (exit 2) y `-Base/-Manifiesto/-Repo`; **se conservan** sus barreras de stack Python (ruff lint/format, pytest, cobertura, CHANGELOG-gate) y el auditor del grafo. `auditar.ps1` gana `-Repo`. Self-tests `probar-hooks`/`probar-auditor`.
3. **Hooks neutrales:** `escribano-stop → andon-stop`, `mariana-stop → gemba-stop` (filtra `rol: revisor-visual`), `review-stop` *data-driven* (lee `revisa: true`, ya no hardcodea `fantasma/`).
4. **Casting desacoplado:** la ley usa **tokens de rol genéricos** (`validador`/`revisor-visual`/`arquitecto-doc`/`devops`); las carpetas de skills **conservan sus nombres** (`ahiram`, `charbel`, `mariana`, `armando`, `escribano`) como **personas**. El área `setup` estrena el asiento **`devops`** (plataforma). La autoridad la da la ley, no el nombre.

## Consecuencias

- La maquinaria que juzga (ley, hooks, motor) es ahora **idéntica** entre SGI, tracker-financiero y Jidoka. Solo difieren las **áreas de la ley** (instancia: `fantasma/`, Python) y los **nombres de los skills** (personas). Un arreglo se hace una vez. **Los tres repos corren una sola metodología.**
- **Cero regresión:** pytest sigue verde (453 passed); el producto y su instalador `.exe` no se tocaron.
- Follow-up: converger el CI de SGI a la ley-en-base + summary de Jidoka.

## Lo que NO se toma

- Sobrescribir SGI con la versión simple de Jidoka: sería regresión (se perderían las barreras de stack y el casting). Por eso Jidoka primero se volvió el superset.
- Renombrar los skills a genéricos: el casting vive en el repo; la convergencia es de **maquinaria**, no de nombres.
