# ADR 0004 — Las fuentes se anonimizan mecánicamente in-place antes de publicar

- Estado: aceptada (2026-07-09) · heredado del repo interno de doctrina

## Contexto

El repo de doctrina es privado, diseñado para publicarse. La auditoría de confidencialidad
previa a la publicación (la pasada que exige [`../07-receta-de-traslado.md`](../07-receta-de-traslado.md),
§frontera NDA) encontró datos del entorno personal del autor dentro de las fuentes: el nombre de
usuario local en rutas, el UUID de la sesión del agente y una ruta de disco con el nombre de una
carpeta local. Nada de eso es contenido NDA del trabajo (se verificó: no hay clientes, montos ni
procesos de negocio), pero sí es información del entorno privado que no debe publicarse.

El conflicto: las fuentes estaban declaradas **inmutables** ("sin pérdida"), con transcript
"íntegro, letra por letra". Anonimizar rompe la letra de esa regla; publicar sin anonimizar
rompe la frontera de confidencialidad. Opciones:

- (a) **Anonimizar in-place, mecánicamente y documentado**: reemplazo global de cadenas
  exactas, con tabla de sustituciones publicada junto a las fuentes.
- (b) **Excluir las fuentes de la publicación** (moverlas fuera del repo o a carpeta ignorada).
- (c) No hacer nada y decidirlo a mano en cada publicación.

## Decisión

Opción (a): anonimización mecánica in-place, documentada. La regla de inmutabilidad se
precisa, no se deroga: **el contenido sustantivo del transcript (mensajes, razonamiento,
resultados de investigación) sigue siendo intocable**; la única edición permitida es el
reemplazo global de identificadores del entorno personal, declarado en una tabla de
sustituciones. Identificadores sin vínculo con la persona o la máquina (UUIDs de mensajes,
slugs aleatorios de sesión) se quedan como están.

## Por qué

- **Menos destructivo y reversible.** El original queda en la historia privada de git; la
  anonimización es un commit revertible. Excluir las fuentes (b) amputaría la trazabilidad que
  el propio método predica: [`../citas-verificadas.md`](../citas-verificadas.md) manda resolver
  discrepancias contra el chat fuente, y el ADR 0001 justifica el repo porque "fuente y síntesis
  viajan juntas".
- **La inmutabilidad protege el contenido, no las rutas.** El valor de la fuente es qué se
  investigó y qué respondió el modelo — ninguna cita de la doctrina carga peso sobre un nombre
  de usuario ni un UUID de sesión.
- **Mecánico y auditable.** Reemplazo de cadenas exactas, sin juicio línea por línea: el diff
  es verificable por inspección y la tabla de sustituciones lo declara públicamente.

## El camino que NO se toma

Reescribir la historia de git. La anonimización limpia el HEAD, no los commits anteriores: la
pasada de confidencialidad exige revisar "contenido E historial", así que **la estrategia de
publicación del historial (historia nueva, squash o filter-repo) es una decisión pendiente del
humano** — es irreversible y no la toma un agente.

---

*Posdata de Jidoka (2026-07-10): esta es la razón por la que el corpus de fuentes NO ascendió a
Jidoka (ADR [0004 de Jidoka](../../docs/decisions/0004-centralizacion-del-conocimiento.md)) — su
historial de origen sigue sin limpiarse. Y es el mismo principio por el que Jidoka nació con
historial limpio y sus commits públicos no llevan trailer de sesión (ADR 0003 de Jidoka).*
