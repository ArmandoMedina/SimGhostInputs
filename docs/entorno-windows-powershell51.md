---
tipo: guia
estado: vigente
---

# Entorno Windows + PowerShell 5.1 — el recetario de lecciones pagadas

> **Por qué vive en el repo y no en un CLAUDE.md global (ADR 0019, homologado del starter v0.5.0):** los subagentes de una sesión **no leen** la configuración global del operador — cada subagente re-descubría estas trampas y las pagaba de nuevo, sesión tras sesión (todas las lecciones de abajo se pagaron en ESTE repo). Aquí las lee cualquiera (humano, orquestador o subagente al que el orquestador se lo pase en el prompt). Los `SKILL.md` de `.claude/skills/` llevan la versión de 5 líneas y apuntan aquí.

## Mensajes de commit (la trampa #1)

- **Nunca** pases mensajes multilínea inline (here-strings a `git commit -m` se parten y git los lee como pathspecs). **Receta:** escribe el mensaje a un archivo **UTF-8 SIN BOM** y usa `git commit -F <archivo>`:

  ```powershell
  [System.IO.File]::WriteAllText($p, $msg, (New-Object System.Text.UTF8Encoding($false)))
  git commit -F $p
  ```

- En el **cuerpo** del mensaje evita `->` y ` / ` (slash entre espacios): guards de sandbox los leen como operaciones de ruta y bloquean el comando entero. Usa "a", "y", "-".
- No borres el archivo de mensaje en el **mismo comando** del commit (mismo motivo); bórralo aparte o déjalo fuera del repo.

## Encoding (la trampa #2)

- `Out-File`/`Set-Content -Encoding utf8` en PS 5.1 meten **BOM**; un BOM rompe detección de "primera línea" en otras herramientas. Para archivos que otra herramienta va a leer: `WriteAllText` con `UTF8Encoding($false)` (arriba).
- Scripts `.ps1` con **acentos** se corrompen si no llevan BOM (PS 5.1 los lee como ANSI). Por eso los scripts de barrera del método van en **ASCII puro** — no los "arregles" agregando acentos.
- Archivos `.md` del repo: UTF-8 **sin** BOM.

## Lo que NO existe / no funciona en PS 5.1

| Costumbre | En PS 5.1 usa |
|---|---|
| `&&` / `\|\|` | `A; if ($?) { B }` |
| ternario, `??`, `?.` | `if/else`, comparación explícita con `$null` |
| `head` / `tail` | `Select-Object -First N` / `-Last N`, `Get-Content -TotalCount/-Tail` |
| heredoc bash `<<'EOF'` | here-string `@'...'@` (cierre en columna 0) |
| `2>&1` en exes nativos | no redirijas: envuelve stderr en ErrorRecord y marca `$?` falso con exit 0 |

## Git y sandbox

- Rutas con espacios (p. ej. `C:\Repositorio personal\...`) siempre entre comillas; para exes con path con espacios usa el call operator `& "C:\ruta con espacios\app.exe"`.
- `git add`/`commit` avisando `LF will be replaced by CRLF` es **solo aviso** (autocrlf): el commit procede, no "arregles" nada.
- Evita reemplazos regex **a cadena vacía** de texto tipo comentario/ruta (`[regex]::Replace(x, patron, '')`): guards de sandbox los bloquean. Reemplaza el bloque viejo por el nuevo en un solo paso.

## Relacionado con

- [flujo-de-trabajo](flujo-de-trabajo.md) (por qué los scripts van en ASCII y los hooks salen 0)
- [recursos-del-proyecto](recursos-del-proyecto.md)
