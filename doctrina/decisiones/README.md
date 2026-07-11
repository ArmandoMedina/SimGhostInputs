# Decisiones de la doctrina (ADRs heredados)

Estos ADRs viajan **con** la doctrina: registran cómo se organizó, publicó y consume el corpus (`doctrina/` + disparos). Se heredaron del repo interno de doctrina con sus números originales (ver ADR [0004 de Jidoka](../../docs/decisions/0004-centralizacion-del-conocimiento.md)); las rutas se ajustaron a este repo y los nombres de repos internos se citan como "laboratorio de campo" (frontera NDA). Las decisiones **del proyecto Jidoka** viven aparte, en [`docs/decisions/`](../../docs/decisions/).

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-repo-propio-separado.md) | La doctrina nació en repo propio, separada de la plantilla y del archivo de chats | aceptada |
| [0002](0002-sin-api-propia-como-gobierno.md) | El gobierno no es una API/MCP propio — mismo modo de falla que las memorias | aceptada |
| [0003](0003-doctrina-se-consume-via-disparos.md) | La doctrina se consume vía disparos (mensajes de gate), no vía lectura | aceptada |
| [0004](0004-anonimizacion-de-fuentes.md) | Las fuentes se anonimizan mecánicamente in-place antes de publicar | aceptada |

> Nota: el corpus `fuentes/` que estos ADRs citan **no** se heredó a Jidoka (su historial de origen arrastra datos de entorno personal — incluidos metadatos de commit: author y trailers de sesión —, por lo que cualquier publicación futura exige historia nueva o filter-repo: decisión humana irreversible, pendiente). La doctrina de este repo es self-contained sin él: las citas están verificadas en [`../citas-verificadas.md`](../citas-verificadas.md).
>
> **Qué hay dentro del corpus** (para que la decisión futura no exija reabrir el archivo): una sesión de investigación del 2026-07-04 con 7 frentes — (1) mapeo de la metodología del laboratorio de campo; (2) benchmark de sustratos de enforcement (veredicto: no existe sustrato que la IA domine mejor que git/GitHub); (3) linaje pre-IA; (4) estado del discurso 2024-2026; (5) la tesis dual; (6) doctrina de aviación; (7) pasada adversarial de modos de falla. La tabla de sustituciones de la anonimización ya está aplicada en el HEAD del repo de origen.
