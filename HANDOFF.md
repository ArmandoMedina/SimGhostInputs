# HANDOFF — relevo para la siguiente sesión

> **Documento vivo de continuidad:** léelo completo antes de tocar nada. El estado en-vuelo vive
> **aquí y en el repo**, nunca en la memoria de la IA. Si avanzas, **actualiza este archivo**.
> Reparto por caducidad: el [ADR](docs/decisions/) guarda *lo permanente* (por qué), el
> [CHANGELOG](CHANGELOG.md) *lo enviado* (qué cambió), el [ROADMAP](ROADMAP.md) *el camino*,
> y este HANDOFF *lo efímero* (dónde voy, qué falta ahora).
>
> **Ciclo de vida (ADR 0019): se llena al cerrar, se lee y se LIMPIA al abrir.** Al arrancar
> sesión (`/arranca` lo instruye): lee esto y borra lo ya atendido — un HANDOFF que acumula
> historia deja de leerse. La historia va al CHANGELOG; el porqué, a los ADRs.

## Estado actual

**2026-07-09 — `v2.3.1` publicada CON instalador adjunto. El pipeline de release, reparado.**
Ver [release v2.3.1](https://github.com/ArmandoMedina/SimGhostInputs/releases/tag/v2.3.1)
(`SimGhostInputs-v2.3.1-Setup.exe` 80 MB + zip portable 118 MB). Es el primer release con assets
desde `v2.2.0`. El ciclo de deuda técnica "Media" (PRs #37–#44, squash `dd65f9b`) quedó cerrado y
liberado; su historia vive en el [CHANGELOG](CHANGELOG.md).

**Qué pasó:** al cortar `v2.3.0`, `release.yml` falló **3 veces seguidas**, cada una destapando un
bug distinto. Causa raíz única: ese workflow solo corre al publicar un release, así que llevaba
desde el [ADR 0022](docs/decisions/0022-ci-release-installer.md) sin ejercitarse ni una vez. Y como
en el evento `release` GitHub lee el workflow **desde el commit del tag**, no desde `master`, cada
arreglo obligaba a borrar y recrear tag y release: un release quemado por bug.

**Qué entró ([PR #49](https://github.com/ArmandoMedina/SimGhostInputs/pull/49) + release
[PR #50](https://github.com/ArmandoMedina/SimGhostInputs/pull/50)):**
- `pyproject.toml`: extra **`pack = ["pyinstaller>=6,<7"]`**. `nicegui-pack` invoca `pyinstaller` como
  subproceso, pero `nicegui` 3.14 **no** lo declara ni expone un extra `[pack]` propio (sus extras
  son `altair, anywidget, highcharts, matplotlib, native, plotly, redis`) — la sugerencia
  `pip install nicegui[pack]` que imprimía `build_installer.py` tampoco habría funcionado. En local
  no se notaba porque las máquinas de desarrollo tenían PyInstaller instalado a mano.
- `tools/build_installer.py`: verifica `pyinstaller` en el PATH por adelantado; `_compile_inno()`
  sale con código 1 en vez de en silencio cuando falta `ISCC.exe`.
- **`.github/workflows/installer.yml`** (`installer-smoke`, nuevo): ensaya el empaquetado completo
  (`nicegui-pack` + Inno Setup) en cada PR que toque `main_gui.py`, `pyproject.toml`,
  `tools/build_installer.py`, `tools/installer.iss` o cualquiera de los dos workflows, y publica el
  `Setup.exe` como artefacto del run (14 días). El pipeline ya no puede pudrirse en silencio.
- **`workflow_dispatch`** en `release.yml`: vía de rescate. Se lee siempre desde la rama por defecto,
  así que re-dispara el build contra un release ya publicado sin tocar el tag. Ojo con su límite: el
  código se compila **desde el tag**, así que solo rescata bugs que estén *en el workflow*. Si el bug
  está en el código del tag (como pasó con `v2.3.0` y el extra `pack`), hay que cortar un patch.

**Por qué `v2.3.1` y no mover el tag `v2.3.0`:** el commit de `v2.3.0` no tiene el extra `pack`, así
que ese código **no puede** producir un instalador; colgarle un binario compilado de `master` sería
mentir sobre su contenido. [`v2.3.0`](https://github.com/ArmandoMedina/SimGhostInputs/releases/tag/v2.3.0)
queda publicado **sin assets**, con una nota que apunta a `v2.3.1`. Decisión del usuario, explícita.

**Verificación:** bundle compilado en Windows local (363.3 MB) antes de tocar CI; `installer-smoke`
verde en #49 generando el `Setup.exe` con Inno Setup (80.8 MB); `release.yml` verde en `v2.3.1`
(4m34s) adjuntando ambos assets; **392 tests** en verde; CI 7/7 en #49 y #50; `auditar-radius.ps1`
y `auditar.ps1 -Bloquea` limpios.

## Siguiente acción

**Nadie ha instalado el `Setup.exe` todavía.** Sabemos que *compila*, no que la app *arranque* bien
empaquetada (PyInstaller `--onedir` + `pywebview` es terreno donde los fallos aparecen en runtime,
no en build). Bájalo del release o del artefacto del run e instálalo. Si falla ahí, el
`installer-smoke` es el sitio donde añadir un smoke de arranque.

**En vuelo, otra sesión:** la rama `fix/pacenotes-frenada-y-countdown` está siendo trabajada por otro
agente (frenada tardía, contador mutilado y sonidos indistinguibles). **No la toques ni borres.**

**Limpieza pendiente:** quedan en el remoto 6 ramas de PRs ya mergeados
(`fix/release-pyinstaller`, `release/v2.3.1`, `release/v2.3.0`,
`fix/release-nicegui-pack-not-a-pypi-package`, `docs/cierre-deuda-media-handoff`,
`homologacion-starter-v0.5.0`). Las locales ya se borraron. El borrado en remoto lo bloqueó el
clasificador de permisos por ser destructivo y no estar nombrado en la tarea.

**Ramas locales con commits propios, sin PR, sin dueño claro:** `pr29` (4 commits), `pr-30` (2) y
`qa/dependency-lockfile-review` (2). No están en master. Antes de borrarlas hay que mirar qué traen.

**Deuda nueva anotada en `ROADMAP.md`** (no bloquea): modo `"both"` sin gap cruzado tono↔voz (#42),
y los 3 ítems del hook de concurrencia (campo `tool_input.isolation`, el "3" sin medir, concurrencia
vs. cupo acumulado — enmienda 2026-07-09 del
[ADR 0019](docs/decisions/0019-adopcion-homologacion-starter-v0.5.0.md)).

## Backlog

Deuda y pulido viven en [ROADMAP](ROADMAP.md), no bloquean.
