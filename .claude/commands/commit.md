Ejecuta el ciclo completo de calidad antes de commitear: changelog → scope → commit → push.
No esperes que el usuario pida cada paso — hazlos todos en orden.

## Paso 1 — Estado actual
Ejecuta `git status` y `git diff` (staged y unstaged). Si no hay cambios, termina aquí.

## Paso 2 — CHANGELOG automático
Sin preguntar, lee `git diff HEAD` para ver qué cambió y actualiza `CHANGELOG.md`:
- Clasifica cada cambio: Añadido / Cambiado / Corregido / Eliminado
- Inserta las entradas bajo `## [Unreleased]`
- No repitas entradas ya documentadas
- Solo omite este paso si CHANGELOG.md ya fue actualizado en este ciclo de trabajo

## Paso 3 — Verificación de scope automática
Sin preguntar, lee `CLAUDE.md` y revisa el diff contra los límites del proyecto:
- Si hay algo ❌ fuera de scope: detente, explica el conflicto y espera instrucción del usuario
- Si hay algo ⚠️ dudoso: menciona la duda brevemente y sigue si el usuario no objeta
- Si todo ✅ está bien: continúa sin comentario

## Paso 4 — Commit
Revisa los últimos 5 commits con `git log --oneline -5` para mantener el estilo.

Redacta el mensaje siguiendo el formato del proyecto:
```
tipo: descripción corta en imperativo (máx. 72 caracteres)

- detalle 1 (qué y por qué, no el cómo)
- detalle 2

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
Tipos: `feat`, `fix`, `docs`, `build`, `refactor`, `test`, `chore`

Muestra el mensaje propuesto. Si el usuario aprueba (o no responde en 10s de un flujo automático), continúa.

## Paso 5 — Ejecutar
```bash
git add <solo los archivos relacionados con el cambio, nunca git add .>
git commit -m "..."
git push
```

Confirma con el hash del commit y la URL del push.

## Reglas
- Nunca uses `git add .` o `git add -A`
- Nunca uses `--no-verify`
- Si hay archivos que no deben subirse (CSVs de telemetría, `.env`, datos privados), adviértelo antes de agregar
- El paso 2 y el paso 3 siempre se ejecutan — no los omitas aunque el usuario no los pida
