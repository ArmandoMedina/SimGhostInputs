Actualiza CHANGELOG.md con los cambios recientes del proyecto.

Pasos:
1. Ejecuta `git diff HEAD --stat` y `git diff --cached --stat` para ver qué archivos cambiaron.
2. Para cada archivo modificado relevante (`.py`, `.md` de docs, `pyproject.toml`, `setup.ps1`), lee el diff completo con `git diff HEAD -- <archivo>` para entender qué cambió exactamente.
3. Clasifica cada cambio según Keep a Changelog:
   - **Añadido** — funcionalidad nueva
   - **Cambiado** — cambios en funcionalidad existente
   - **Corregido** — corrección de bugs
   - **Eliminado** — funcionalidad eliminada
   - **Seguridad** — vulnerabilidades corregidas
4. Redacta entradas concisas en español, en primera persona del plural ("Añade X", "Corrige Y"). Una línea por cambio, con contexto suficiente para que un usuario externo entienda el impacto sin leer el código.
5. Inserta las entradas bajo `## [Unreleased]` en `CHANGELOG.md`, respetando el formato existente. Si la sección `[Unreleased]` no existe, créala encima del primer release.
6. No repitas entradas que ya estén documentadas.
7. Muéstrame el diff del CHANGELOG antes de guardarlo y pídeme confirmación si hay dudas sobre cómo clasificar algún cambio.
