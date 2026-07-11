# ADR 0001 — La doctrina vive en repo propio, separado de la plantilla y del archivo de chats

- Estado: aceptada (2026-07-04) · heredado del repo interno de doctrina

## Contexto

El aprendizaje de la investigación del 2026-07-04 (gobierno determinista de agentes) necesitaba
un artefacto durable. Candidatos: (a) meterlo en la plantilla de proyectos (la capa de método ya
existente), (b) archivarlo en el archivo personal de chats valiosos, (c) repo propio.

## Decisión

Repo propio de doctrina, privado, diseñado para publicarse. Contiene fuente cruda + síntesis
+ ledger de verificación + disparos compilados.

## Por qué

- **Caducidad y audiencia distintas.** La plantilla es algo que cada proyecto clona: debe
  seguir liviana; 100k+ tokens de corpus de investigación la inflarían. El archivo de chats
  guarda fuentes, no síntesis citables.
- **Unidad publicable.** El propósito es reclamar el framing (ver [`../06-fronteras.md`](../06-fronteras.md)).
  Publicar la doctrina no debe arrastrar ni la plantilla ni los chats personales.
- **Trazabilidad sin pérdida.** Fuente y síntesis juntas en un repo: la síntesis cita rutas de
  las fuentes; ante duda, se lee la fuente letra por letra.

## El camino que NO se toma

Duplicar la doctrina dentro de la plantilla. La plantilla **consume**: referencia esta doctrina y
copia los disparos a sus hooks. Una sola fuente de verdad del porqué.

---

*Posdata de Jidoka (2026-07-10): esta decisión se cumplió una segunda vez — Jidoka también consume la doctrina copiándola embebida (ADR [0001 de Jidoka](../../docs/decisions/0001-la-fusion-jidoka.md)), sin arrastrar fuentes ni chats.*
