---
description: Corre un pase de trabajo AUTÓNOMO (sin humano presente) repartiendo lo ejecutable de lo que exige juicio — las dos lanes [agente]/[humano]
argument-hint: "[el alcance del pase: qué revisar/construir/limpiar]"
allowed-tools: Read, Bash(git status:*), Bash(git branch:*), Bash(git log:*)
---

Vas a trabajar **sin un humano presente**. La regla no es "¿qué puedo hacer?" sino **"¿qué NO debo decidir solo?"**. Sigue el protocolo de `kanban/desatendido.md`.

Alcance del pase: **$ARGUMENTS**

## 1. Rama y reconocimiento

- Trabaja en una **rama dedicada** (`auto/<fecha>` o el nombre que el alcance sugiera). Nada de esto toca `main`.
- **Reconoce primero:** inventaría lo que está sano y confirma/refuta pistas antes de tocar nada. Un informe que solo lista problemas no dice qué revisaste.

## 2. Reparte en las dos lanes (usa `@kit/.jidoka/templates/desatendido.md`)

Ordena todo por prioridad declarada: **seguridad y fugas > corrección > robustez > salud de docs > estilo**. Las secciones sin nada se dejan **vacías a propósito** — no infles la agenda.

- **Lane `[agente]`** — lo **mecánico, reversible y autorizado**: arreglar un bug con su test, sincronizar un doc dueño, correr una suite, un refactor con verde. Cada ítem con su **criterio de verificación**. Ejecuta estos **tú**, cada uno commiteable y verde.
- **Lane `[humano]`** — lo que exige **juicio, es irreversible, o pide credenciales/datos que solo el humano tiene**. **NO lo ejecutes.** Déjalo listo: nombra exactamente qué firma el humano (`[humano]`) y qué puede hacer una corrida después (`[agente]`).

## 3. Las reglas duras (no negociables)

- **Click-it-down:** si algo se complica o el resultado sorprende, **baja** el nivel — de ejecutar a dejar preparado y esperar. No pelees dentro del modo automático (disparo `click-it-down`).
- **Nada irreversible sin el humano:** reescribir historia, publicar, desplegar, borrar, tocar secretos, mergear a `main` → siempre a la lane `[humano]` (disparo `decision-queda-en-humano`).
- **NO edites tus propios gates:** un cambio a `tools/blast-radius.json`, a los hooks o al CI se deja como **borrador para una sesión humana**. Rodear la negativa del harness por shell es el anti-patrón que la doctrina condena.
- **Evidencia-no-palabra:** cada ítem `[agente]` cerrado se anota con su verificación real (test verde, corrida), no con "listo".

## 4. Cierre

- Lo durable migra a su doc dueño: una decisión → un ADR; estado en vuelo → `HANDOFF.md`; lo enviado → `CHANGELOG.md`. Las lanes son temporales — se retiran cuando quedan vacías.
- Deja la lane `[humano]` **corta y priorizada** arriba de todo: es lo primero que el humano lee al volver. Ese es el Gemba del trabajo desatendido.
