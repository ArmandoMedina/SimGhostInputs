# Entorno Windows / PowerShell 5.1 — el recetario de trampas pagadas

> Jidoka corre hoy sobre Windows + PowerShell 5.1 (multiplataforma en Sprint 3). Estas trampas se pagaron en el linaje **más de una vez** — sesión tras sesión — antes de que alguien las escribiera. Por eso existen dos reglas, no una:
>
> 1. **Las lecciones de entorno viven versionadas en el repo** (este archivo), no en la configuración global del operador.
> 2. **Cada `SKILL.md` lleva la versión de 5 líneas embebida**, apuntando aquí. La razón es estructural: *los subagentes no leen la configuración global del operador* — el prompt del subagente es el único canal garantizado. Sin la copia embebida, cada subagente re-descubre estas trampas y las paga de nuevo.

## Commits en español (acentos) — la receta

Los here-strings inline se parten y PS 5.1 corrompe los acentos. La receta que funciona:

1. Escribe el mensaje de commit a un archivo **UTF-8 sin BOM**.
2. `git commit -F <archivo>`.
3. En el cuerpo del mensaje: **sin `->` ni ` / `** (los guards del sandbox los interceptan).

## Scripts de barrera: ASCII puro

Los scripts que corren como gate (hooks, verificador) van en **ASCII puro** — un acento sin BOM se corrompe en 5.1 y el gate truena por encoding, no por la regla. La prosa con acentos vive en los `.md`; el código de barrera, sin ellos.

## `Out-File` mete BOM

`Out-File -Encoding utf8` en PS 5.1 escribe UTF-8 **con BOM** — rompe archivos que otros procesos leen (JSON, mensajes de commit). Para UTF-8 sin BOM: `[IO.File]::WriteAllText($ruta, $texto)`.

## Lo que NO existe en PowerShell 5.1

| Quieres | En 5.1 |
|---|---|
| `&&` / `\|\|` | `A; if ($?) { B }` |
| ternario `? :`, `??`, `?.` | `if/else`, `$null -eq` explícito |
| `ConvertFrom-Json -AsHashtable` | no existe: devuelve `PSCustomObject` |
| redirigir stderr de un exe con `2>&1` | envenena `$?` — no redirijas |

## Los skills no son `subagent_type`

Lección operativa del linaje (las sesiones reales fallaron intentándolo directo): un skill-asiento **no se invoca como tipo de subagente**. Se spawnea un subagente general **con el `SKILL.md` en el prompt**. Los skills del Sprint 2 nacen con este patrón — y con su sección "Entorno" de 5 líneas.
