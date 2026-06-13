Crea un commit bien formado con intención clara y sube los cambios.

Pasos:
1. Ejecuta `git status` y `git diff` (staged y unstaged) para ver el estado completo.
2. Verifica que `CHANGELOG.md` esté actualizado: si hay archivos `.py` modificados y CHANGELOG no está entre los cambios, avisa y pregunta si continuar o ejecutar primero `/changelog`.
3. Revisa los últimos 5 commits con `git log --oneline -5` para mantener el estilo del proyecto.
4. Redacta el mensaje de commit siguiendo el formato del proyecto:
   - Primera línea: `tipo: descripción corta en imperativo` (máx. 72 caracteres)
     - Tipos: `feat`, `fix`, `docs`, `build`, `refactor`, `test`, `chore`
   - Líneas de detalle (si aplica): bullets con el qué y el porqué, no el cómo
   - Trailer: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
5. Muéstrame el mensaje de commit propuesto y pide confirmación antes de ejecutarlo.
6. Con confirmación: `git add` de los archivos relevantes, `git commit` y `git push`.
7. Confirma con el hash del commit y la URL del push.

Reglas:
- Nunca uses `git add .` o `git add -A` — agrega solo los archivos relacionados con el cambio.
- Nunca uses `--no-verify`.
- Si hay archivos que no deben subir (datos privados, `.env`, CSVs de telemetría), adviértelo antes de agregar.
