# ADR 0002 — Nada de API/MCP propio como capa de gobierno; sustrato git/GitHub + hooks

- Estado: aceptada (2026-07-04) · heredado del repo interno de doctrina

## Contexto

Para portar la metodología de gates (probada en el laboratorio de campo) a trabajo no-código
(p. ej. un equipo de soporte con IA como coworker), se evaluó construir una API o MCP propio que
actuara como "githook" del nuevo dominio. Se corrió un benchmark en 4 frentes: enforcement,
validadores no-código, gobernanza de agentes, sustratos de trabajo.

## Decisión

**Se mata la opción de API/MCP propio como capa de gobierno.** Stack: git/GitHub como sustrato
(docs-as-code; el merge es la publicación), hooks del agente como muro local (`PreToolUse`
ask/deny, `Stop`), required checks + required reviews + CODEOWNERS como muro server-side,
Vale/JSON Schema/linters como validadores de forma en hook y CI.

## Por qué

1. Una API propia que la IA llama voluntariamente tiene el mismo modo de falla que las memorias:
   depende de cooperación del modelo → no es muro (ley del muro, [`../00-tesis.md`](../00-tesis.md)).
2. La IA no conoce la API de fábrica → la reaprende cada sesión → reintroduce amnesia y
   bifurcación, exactamente lo que los gates resolvieron.
3. No existe a 2026 sustrato multi-persona con gate inmutable que la IA domine mejor que
   git/GitHub — ni para trabajo no-código (benchmark verificado).

## Matiz que sobrevive

MCP como **puente delgado** hacia artefactos cautivos en sistemas propietarios (CRM/ticketing)
es a veces inevitable. Regla: el puente transporta, el muro decide, y el muro (hook/required
check/OPA) vive fuera del modelo y DELANTE de esa tool. Mantener el puente aburrido y
convencional.

## El camino que NO se toma

- API/MCP de validación que la IA "debe llamar".
- Meter a la IA a operar Jira/ServiceNow/Zendesk como sustrato primario (los conoce mucho peor
  que git; obliga a construir el MCP que se quería evitar).
