# ADR 0022 — CI que genera y adjunta el instalador Windows en cada release

- **Estado:** Aceptada
- **Fecha:** 2026-07-05
- **Autor:** Armando Medina
- **Relacionada con:** [ADR 0018](0018-framework-ui-nicegui.md) (empaquetado Inno Setup)

## Contexto

El ritual de release (`release-helper`: CHANGELOG + tag anotado + GitHub release) no producía
ningún distribuible. El workflow `build-installer` definido en `tests.yml` tenía un `if` que
comprobaba `refs/tags/v*`, pero el workflow solo se dispara en `push`/`pull_request` a `master`;
los tags nunca lo activaban. Aunque hubiera corrido, el job solo subía un artifact de CI (caducidad
7 días) y no adjuntaba nada al release de GitHub. Además, `build_installer.py` requiere `--inno`
para generar el `Setup.exe`, bandera que el job no pasaba. Por si fuera poco, `installer.iss`
tenía la versión `MyAppVersion "2.0.0"` hardcodeada, de modo que cada instalador habría declarado
la versión equivocada.

El instalador de v2.0.0 se armó a mano. El problema salió a la luz al pedir "regenera el
ejecutable" tras el release v2.2.0: no existía ningún mecanismo automático que lo hubiera
producido.

## Decisión

1. **Nuevo workflow `.github/workflows/release.yml`** disparado por `on: release: types: [published]`
   que, en `windows-latest`:
   - instala dependencias Python y Choco (Inno Setup: `choco install innosetup`),
   - ejecuta `python tools/build_installer.py --inno`,
   - sube `SimGhostInputs-vX.Y.Z-Setup.exe` y un zip portable del bundle como assets del release
     con `gh release upload --clobber` (permiso `contents: write`).

2. **Eliminación del job muerto `build-installer` de `tests.yml`**: estaba mal cableado y nunca
   corría; quitarlo reduce el ruido del CI y evita confundir a quien lea el workflow.

3. **Versión parametrizada del instalador**: `build_installer.py` lee la versión del paquete
   (`importlib.metadata.version("fantasma")`) y la pasa a ISCC con `/DMyAppVersion=<ver>`.
   `installer.iss` usa `{#MyAppVersion}` en vez del literal hardcodeado. Además se habilita el
   icono (`docs/icon.ico`, que ya existía en el repo pero no estaba referenciado).

## Razones

- **El evento `release: published` es el más preciso.** Ocurre exactamente cuando `release-helper`
  publica, trae el contexto del release para adjuntar assets con `gh release upload`, y mantiene
  `tests.yml` enfocado en el gate de calidad (required checks) sin enredo con el empaquetado.

- **El distribuible debe ser un asset permanente.** Un artifact de CI caduca en 7 días; un asset
  del release vive mientras el release viva. Los usuarios descargan desde GitHub Releases, no desde
  la pestaña de Actions.

- **La versión hardcodeada es una fuente de error probada.** Con `importlib.metadata` hay una sola
  fuente de verdad: `pyproject.toml`. El instalador siempre declarará la versión correcta sin
  intervención manual.

- **El icono ya existe.** `docs/icon.ico` estaba en el repo desde v2.0 pero `installer.iss` no lo
  referenciaba; habilitarlo es un cambio trivial que mejora la presentación del instalador.

## El camino que NO se toma (y por qué tienta)

- **`push: tags: [v*]`** — Tienta porque es el patrón clásico "CI en cada tag" y es más sencillo
  de entender a primera vista. Se descarta: no trae el contexto del release de GitHub (no hay
  release object al que adjuntar assets sin buscarlo con `gh api`), y mezcla el empaquetado con el
  flujo de tests. El evento `release: published` es más limpio y semánticamente correcto.

- **Mantener `build-installer` en `tests.yml` y arreglarlo** — Tienta porque es un cambio menor
  (añadir `on: push: tags:` o mover el if). Se descarta: seguiría mezclando el gate de calidad con
  la producción del distribuible, y el artifact de 7 días no resuelve el problema de distribución.
  Un workflow dedicado separa responsabilidades.

- **Build manual local en cada release (status quo)** — Se descarta: se olvida, no es reproducible
  (depende del entorno local de quien corte el release) y ya falló en la práctica con v2.2.0.

- **Adjuntar solo el artifact de CI** — Se descarta: los artifacts caducan; los releases de GitHub
  son el canal de distribución para los usuarios finales y deben tener assets permanentes.

## Consecuencias

- **Se gana:** cada `release-helper` produce automáticamente un `Setup.exe` con la versión
  correcta adjunto al release de GitHub. La versión del instalador siempre coincide con
  `pyproject.toml`. El icono aparece en el instalador. El job muerto desaparece del CI.

- **Se pierde / costo:** un workflow adicional que mantener; el build en `windows-latest` añade
  tiempo de CI (estimado 5-10 min) al momento de publicar.

- **Nota de activación:** GitHub ejecuta el workflow del evento `release` desde la rama por defecto
  (`master`). El workflow de v2.2.0 se armó localmente; el nuevo mecanismo entra en vigor a partir
  del siguiente release que se publique con `release-helper` después de mergear esta rama.
