Revisa si los cambios propuestos o recientes están dentro del scope y respetan la arquitectura del proyecto.

Pasos:
1. Lee `CLAUDE.md` para tener presentes los límites, invariantes y filosofía del proyecto.
2. Lee `git diff HEAD` y `git status` para ver los cambios actuales. Si el usuario describió un cambio propuesto (aún no implementado), evalúalo desde esa descripción.
3. Para cada archivo o módulo modificado/propuesto, evalúa estos criterios:

   **Scope:**
   - ¿Está dentro de las funcionalidades listadas en "Lo que ESTÁ dentro del scope"?
   - ¿Toca algo listado explícitamente como "Fuera del scope"?

   **Arquitectura:**
   - ¿Respeta la dependencia unidireccional (`importers` → `core` → `viz`)?
   - ¿Añade dependencias obligatorias donde debería ser opcional?
   - ¿Introduce estado global, base de datos o llamadas de red en `core/`?
   - ¿Incluye o referencia datos privados del usuario (telemetrías, referencias)?

   **Filosofía:**
   - ¿Es compatible con AGPL-3.0 (sin dependencias con licencias incompatibles)?
   - ¿Mantiene el principio "trae tus propios datos"?
   - ¿Duplica funcionalidad de CrewChief u otras herramientas ya establecidas?

4. Emite un veredicto por cambio o módulo afectado:
   - ✅ **En scope** — cumple todo
   - ⚠️ **Dudoso** — explica qué criterio roza y cómo ajustarlo
   - ❌ **Fuera de scope** — explica el conflicto y propón cómo descartar o reformular

5. Si hay ⚠️ o ❌, sugiere concretamente cómo ajustar el cambio para que cumpla, o confirma que debe descartarse.
6. Termina con un resumen de una línea: "El cambio está dentro del scope" o "El cambio necesita ajustes en [área]".
