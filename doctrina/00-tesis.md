# 00 — La tesis

## La ley del muro

> **Un mecanismo de gobierno es muro real si y solo si el punto de control vive FUERA del LLM.
> Si depende de que el modelo coopere, no es muro.**

| Vive FUERA del LLM → muro real | Depende del LLM → no es muro |
|---|---|
| Claude Code hooks (`PreToolUse` deny/ask, `Stop`) | Memorias, CLAUDE.md, comandos de arranque (prosa que "debería leer") |
| GitHub required checks + branch protection + required reviews | Guardrails que usan un LLM para juzgar a otro LLM |
| OPA/Cedar interceptando tool-calls (PEP) | Structured output / Pydantic (validan forma; la corrección re-pregunta al modelo) |
| Linters/validadores deterministas en hook/CI | Una API propia que la IA llama voluntariamente |

Corolarios probados en la práctica (el laboratorio de campo del linaje):

- Los mecanismos voluntarios (comando `/arranca`, subagentes, memorias, repetir reglas en prosa)
  fallaron todos. Los hooks ganaron **porque no le piden permiso a la IA**. Confesión textual del
  propio hook anti-memoria del laboratorio: *"se hizo cumplir con hook porque repetirla no funcionó
  (4 veces en las sesiones reales de ESTE repo)"*.
- El éxito no era de git-la-tecnología. Git regaló tres cosas que hay que nombrar para portarlas:
  (1) un **choke point** (el acto de commit/push como momento discreto de "esto se envía"),
  (2) un **diff** (saber qué cambió), (3) **fluidez nativa** (la IA opera git de fábrica, sin
  reaprenderlo cada sesión). Cualquier sustrato alternativo debe proveer los tres.
- Construir una API/MCP propia como capa de gobierno **reintroduce el problema que se resolvió**:
  la IA no la conoce de fábrica → la reaprende cada sesión → amnesia y bifurcación de vuelta.
  (Decisión congelada en `../decisiones/0002-sin-api-propia-como-gobierno.md`.)

## La tesis dual (los dos pájaros)

1. **Pájaro 1 — la IA como actor gobernado.** La rigidez completa (gates deterministas, evidencia
   obligatoria, checklists, required checks server-side) cae sobre el robot. No hay costo de
   dignidad: a la IA se le puede exigir como a una máquina porque lo es.
2. **Pájaro 2 — la misma IA capacita al humano en el momento.** Linaje: EPSS (Electronic
   Performance Support Systems, Gloria Gery, 1991) — incrustar la ayuda en el flujo de trabajo
   para que el trabajador no necesite entrenamiento previo ni memoria. La IA es la primera
   implementación realmente capaz de esa idea.

El movimiento propio: **la mejor tradición de calidad siempre quiso proteger al humano** (Deming
punto 8 "drive out fear", punto 12 "quita las barreras que roban el orgullo del trabajo"; el pilar
"respeto por las personas" de Toyota), pero imponer disciplina de proceso al humano siempre tuvo
costo de dignidad. **Poner la disciplina en un actor sin dignidad que reclamar resuelve esa
tensión de un siglo.** El humano recibe repetibilidad y no-dependencia-de-memoria sin volverse
robot.

## La línea que no se cruza

> **Relevar al humano de la carga de memoria y procedimiento; preservarlo —y protegerlo— como
> portador de juicio. La IA carga lo cuadrado; el humano conserva lo que no se puede cuadrar,
> y sigue siendo el gate de verdad.**

Por qué es vital: **en prosa no existe el test verde.** Los validadores deterministas (Vale,
JSON Schema, linters) gatean forma, consistencia y completitud estructural — jamás verdad.
El único gate de correctitud en trabajo no-código es el humano. Si el pájaro 2 deskilla al humano
hasta el sello de goma, el sistema entero se queda sin árbitro (ver `03-aviacion.md`: es el guion
de AF447). Diseño correcto: la IA le **sube** el juicio al humano (muestra el porqué, lo obliga a
decidir con contexto, ancla la capacitación en el artefacto versionado, no en su memoria de
modelo); nunca se lo **sustituye**.

## El límite honesto

Nada de esto es técnicamente nuevo — cada mecanismo tiene décadas (ver linajes en `01-` y `02-`).
Lo defendible es: (a) que funciona en la práctica con un agente concreto (el laboratorio de campo), y (b) la síntesis
integrada que nadie ha escrito (ver `06-fronteras.md`). El resto se cita, no se reclama.
