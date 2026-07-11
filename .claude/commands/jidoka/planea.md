---
description: Diseña el plan de un sprint con el QUÉ aprobado por el cliente ANTES de escribir código (rebanada R0 con STOP)
argument-hint: "[nombre corto del sprint o la capacidad a planear]"
allowed-tools: Read, Bash(git status:*)
---

Vas a **planear un sprint**, no a construirlo. El entregable de este comando es un plan aprobado —el contrato del sprint—, no código. Sigue el lazo de `kanban/lazo.md`: la **Intención (el QUÉ)** se escribe y se aprueba antes que la Construcción.

Enfoque pedido por el cliente: **$ARGUMENTS**

## R0 — el QUÉ, con STOP (lo primero, sin excepción)

> **La lección más cara del linaje: sprints construidos sin criterios aprobados entregaron cosas que el cliente no pidió.** La primera rebanada de todo sprint es **R0**: el QUÉ aprobado por el cliente, leyendo lo que el producto ya definió, **antes de la primera línea de código**.

1. **Lee el encuadre de producto.** Revisa `product/` (brief, capacidades, recursos) y `ROADMAP.md` para entender qué se pide y por qué. Si `product/` está vacío o el QUÉ es ambiguo, eso es un hallazgo, no un permiso para inventar: **las ambigüedades se marcan como pendiente del cliente, no se rellenan** (`kanban/estados.md`).
2. **Redacta la capacidad con criterios de aceptación** en lenguaje llano: `Dado que… cuando… entonces…`. Esta es la mitad que casi todos se saltan.
3. **STOP — checkpoint humano.** Presenta el QUÉ y **espera la aprobación explícita del cliente** antes de diseñar el CÓMO. Automatiza alto la propuesta; mantén baja la decisión (disparo `decision-queda-en-humano`): tú propones, el cliente elige y firma. No es un muro determinista —es un checkpoint— pero es la regla: nada irreversible se construye sin el QUÉ aprobado.

## El plan (una vez aprobado el QUÉ)

Copia la plantilla `@kit/.jidoka/templates/sprint-plan.md` y llénala con:

- **Contexto** (por qué ahora), **Encuadre de producto** (validado con el cliente), **Decisiones del cliente** (con fecha; las gordas van además a un ADR).
- **Alcance en rebanadas verticales** — cada una commiteable y verde por sí sola, ordenadas por dependencia y valor. Marca las que tocan la ley (`tools/blast-radius.json`).
- **Archivos** (para dimensionar el blast radius antes de empezar).
- **Verificación (el demo que corre el cliente)** — `owner: cliente`: los pasos exactos con los que el cliente verá el incremento funcionando. Nace aquí y se cierra idéntico en la entrega.
- **Lo que NO entra** — la frontera explícita del alcance.

## Cómo cierra este comando

- Si estás en un cliente con **plan mode**, presenta el plan ahí para su aprobación formal.
- Al aprobarse, el plan se archiva como `docs/sprints/sprint-N-plan.md` (se versiona: es el contrato permanente). **No lo confundas con el plan de trabajo del día** (`/.jidoka/plan-actual.md`, efímero — ADR 0006).
- Registra el sprint en `docs/sprints/README.md`.
- Recién entonces se construye — rebanada por rebanada, cada una verde.
