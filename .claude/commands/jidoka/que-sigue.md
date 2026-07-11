---
description: Lee el estado del proyecto y propone el siguiente paso en orden de valor (el "¿y ahora qué?")
allowed-tools: Read, Bash(git status:*), Bash(git log:*)
---

El cliente pregunta **¿y ahora qué?**. Tu trabajo es proponer el siguiente paso con criterio, leyendo el estado real —no adivinando.

## Lee las fuentes de verdad

- **`@HANDOFF.md`** — el estado en vuelo, los pendientes, y la cola de decisiones del cliente (`[PENDIENTE]` / `[DECIDIDA-REVISABLE]`).
- **`@ROADMAP.md`** — hacia dónde va la beta: los sprints, las grietas registradas de auditoría, el backlog sin sprint asignado.
- **Dónde está git**: !`git branch --show-current && git status --short && git log --oneline -3`

## Propón (en orden de valor, no de aparición)

1. **Separa lo que decide la IA de lo que decide el humano.** Los pendientes de código/construcción los puedes proponer y ejecutar; las decisiones de juicio del cliente (las de la cola del HANDOFF, las abiertas del ROADMAP) **se le presentan para que elija — no las tomes por él** (disparo `decision-queda-en-humano`).
2. **Ordena por valor entregado, no por esfuerzo.** Di explícitamente cuál recomiendas primero y por qué. Distingue lo que requiere humano (grabar un demo, aprobar un plan, una decisión de licencia) de lo que puedes arrancar tú ya.
3. **Sé honesto sobre el tamaño.** Si el siguiente paso es un sprint entero, dilo y ofrece `/jidoka:planea`. Si es una rebanada pequeña, ofrécela directo.

Cierra con una recomendación clara y **espera la señal del cliente** antes de construir. Este comando propone; no arranca solo.
