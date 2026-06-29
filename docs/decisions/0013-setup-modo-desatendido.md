# ADR 0013 — Modo desatendido (`-Yes`) en `setup.ps1` para pruebas reproducibles

- **Estado:** Aceptada
- **Fecha:** 2026-06-28

## Contexto

El objetivo de fondo del entorno de pruebas es usar la PC potente (host SERVER) y una **VM
Windows limpia repetible** (`sgi-win11-clean`, con snapshot) para probar `setup.ps1` desde cero
de forma **automática y reproducible**, sin que un humano tenga que estar sentado dando clics.

Probando `setup.ps1` en esa VM virgen aparecieron dos obstáculos para correrlo desatendido:

1. **Cada confirmación es un `Read-Host`** (instalar Python, matplotlib, ffmpeg, gh, VLC,
   Kdenlive). En una sesión no-interactiva (PowerShell Direct, SSH, CI) `Read-Host` falla con
   "NonInteractive mode" o se cuelga esperando una tecla que nunca llega.
2. **Tras instalar Python, el script relanza una terminal nueva** (`Start-Process powershell …`)
   para heredar el PATH actualizado. Una ventana nueva es **inservible en headless/CI**: no se
   observa, y la sesión que la lanzó termina sin saber el resultado.

Sin resolver esto, el `setup.ps1` no se puede validar de forma automática en la VM ni en el CI —
justo lo que el entorno de pruebas pretende habilitar. (Los bugs F2 —stub de Python de la Store—
y F3 —`--source winget`— ya se corrigieron en el commit `4a08f8b`; este ADR es sobre la
ergonomía desatendida, no sobre esos bugs.)

## Decisión

Añadir un switch **`-Yes`** (modo desatendido) a `setup.ps1`:

1. Todas las confirmaciones pasan por un helper `Confirm-Action`; con `-Yes` responde "sí"
   automáticamente y no llama a `Read-Host`.
2. En modo `-Yes` **no se relanza una terminal nueva** tras instalar Python: se resuelve la ruta
   donde winget deja Python (`%LOCALAPPDATA%\Programs\Python\Python312`, `%ProgramFiles%\Python312`)
   y se añade al PATH de la misma sesión. Si aun así no aparece, se **falla claro** con código ≠0
   (anti-bucle), en vez de abrir una ventana invisible.

Combo recomendado para CI / VM: **`setup.ps1 -Yes -SkipSystem`** (evita instalar las apps
grandes de escritorio VLC y Kdenlive, que no aportan a una prueba del instalador).

## Razones

- **Es la condición para el objetivo del entorno de pruebas:** sin un modo desatendido, "probar
  `setup.ps1` en limpio de forma repetible" exige un humano dando clics — lo contrario de
  automatizar en la PC potente.
- **El relaunch de terminal es un patrón de máquina interactiva**, no de servidor. Resolver la
  ruta de Python en la misma sesión es determinista y observable; la ventana nueva no.
- **Bajo riesgo:** `-Yes` es opt-in; el flujo interactivo por defecto no cambia para el usuario
  que corre el script a mano.

## El camino que NO se toma (y por qué tienta)

- **Dejar `setup.ps1` solo-interactivo** y "ya lo probará un humano". Tienta porque es cero
  trabajo, pero choca de frente con el objetivo: no se puede meter en CI ni correr desatendido en
  la VM, y cada validación vuelve a depender de que alguien se siente a teclear "s".
- **Alimentar respuestas por stdin a los `Read-Host`** (p. ej. `"s`ns`n…" | setup.ps1`). Tienta
  porque no toca el script, pero es **frágil**: `Read-Host` en modo no-interactivo no lee de
  stdin de forma confiable, el orden de respuestas se rompe en cuanto cambian los prompts, y no
  resuelve el relaunch de terminal (el problema #2).
- **Quitar el relaunch siempre** (no solo en `-Yes`). No se hace para no cambiarle el
  comportamiento al usuario interactivo, donde reabrir la terminal sí resuelve el PATH sin que
  tenga que cerrar y volver a abrir a mano.

## Consecuencias

- **Se gana:** `setup.ps1` se puede correr y validar **desatendido** en la VM limpia y en CI; el
  entorno de pruebas reproducible queda habilitado de punta a punta.
- **Se pierde / costo:** una rama de código más (`-Yes`) y la suposición de las rutas de
  instalación de winget para Python (si winget cambia la ruta por defecto, hay que actualizar la
  lista de candidatos).
- **Pendiente de validar:** correr `setup.ps1 -Yes -SkipSystem` end-to-end en la VM desde el
  checkpoint `baseline-win11-clean` y confirmar que termina sin intervención. (`setup.ps1` no
  está cubierto por `pytest`: es dependiente del entorno —winget, PATH—, así que su prueba es la
  corrida en la VM, no un test unitario; ver [ADR 0003](0003-testing.md).)
