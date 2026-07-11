# La auditoría en rama — el ritual de revisión grande

> Para lo que un `/code-review` no alcanza: antes de un release, tras varios sprints, o cuando el repo huele a deuda. Probado en el linaje (una auditoría integral de 21 auditores) y en el propio Jidoka (el cierre del Sprint 1 fue exactamente esto). Es la versión "grande" de la revisión por robots — el humano sigue revisando el demo, no el diff.

## El ritual, por tiempos

1. **Rama propia** (`audit/<fecha>` o el cierre del sprint): la auditoría produce cambios y récord, no opiniones sueltas.
2. **Fan-out de auditores por área.** Subagentes independientes, cada uno con un área acotada (código por dominio, gates, docs/SSOT, seguridad, CI). Cada auditor entrega hallazgos con evidencia (ruta + línea + por qué), no impresiones.
3. **Síntesis con dedupe y reconciliación.** Un sintetizador consolida los reportes: deduplica (en el caso real: ~190 hallazgos brutos → ~65), **reconcilia contradicciones con la regla "gana la evidencia más directa"**, y recalibra todo a una escala única de severidad. Los hallazgos con raíz común se cuentan como **familia de drift** (1 crítico + N instancias, no N hallazgos sueltos) — y la remediación preferida es **matar la fuente, no parchear instancias**: en el caso real, retirar una UI entera cerró 10 hallazgos de un golpe.
4. **Paquetes de remediación** ordenados (R1, R2, …): trabajo agrupado por tema y prioridad, no una lista plana.
5. **Veredictos GO/NO-GO separados por acción.** Mergear no es lo mismo que taggear un release: cada acción irreversible recibe su propio veredicto. Y el GO puede ser **condicionado** a un paquete ("GO al merge condicionado a R1; NO-GO al tag").
6. **"Descartado a propósito."** Lo que NO se va a arreglar se lista con su porqué — evita inflar el backlog y deja el juicio registrado.
7. **"Decisiones que necesitan al humano"** se separan del trabajo autónomo. La IA ejecuta lo suyo; lo que exige juicio del cliente sale como checklist, nunca enterrado en prosa (lección pagada: un pendiente en prosa se cayó una sesión entera).

## Las reglas

- **Hallazgo sin evidencia no cuenta.** Igual que el Gemba: el artefacto, no la palabra.
- **La severidad la asigna la síntesis, no cada auditor** — 21 escalas distintas no son una escala.
- **La auditoría también se audita**: sus arreglos pasan por los mismos gates que cualquier cambio (el check `andon` no distingue quién empuja).
- **Se audita que las barreras muerdan, no que existan.** Cuatro modos de teatro observados en el linaje: un mensaje que promete un verificador inexistente ("el CI re-verifica esto" — no había CI); un área de la ley apuntando a rutas que ya no existen (gate dormido de facto durante 4 sprints); un auditor que "pasa" porque no hay nada que auditar (aprobación en vacío); y suites verdes que solo corren si la IA se acuerda.

## La corrida nocturna desatendida

> El protocolo general de trabajo sin humano presente —las dos lanes `[agente]`/`[humano]`, la prioridad, el click-it-down, el fail-safe— vive ahora en [`desatendido.md`](desatendido.md) (aplica a cualquier actividad, no solo auditar) y en el comando `/jidoka:desatendido`. Aquí queda su primera aplicación: la auditoría nocturna.

La variante sin humano presente, rodada en el linaje. Difiere del ritual interactivo en cuatro piezas:

1. **Reconocimiento con veredicto completo:** la corrida reporta también lo re-verificado y **sano**, y confirma o refuta pistas previas — no solo hallazgos. Un informe que solo lista problemas no dice qué se revisó.
2. **AGENDA persistente entre corridas**, con prioridad declarada (seguridad y fugas > corrección > robustez > salud de docs > estilo), cada ítem cerrado con su evidencia inline, secciones de severidad **vacías a propósito** cuando no hay nada, y regla de vida: es un archivo temporal — se retira cuando la agenda queda vacía.
3. **PENDIENTES con etiquetas [humano]/[agente]:** las decisiones que la corrida NO debe tomar sola salen como lista donde el agente deja preparado lo delegable y nombra exactamente qué firma el humano.
4. **Las reglas duras de lo desatendido:** una corrida sin humano **no hace cambios que exijan re-validación con datos que solo el humano tiene** (mitigación quirúrgica hoy; el upgrade, como pendiente humano con checklist). Y **el agente desatendido no edita sus propios gates** — cuando el harness se lo negó, rodearlo por shell habría sido exactamente el anti-patrón que la doctrina condena; los cambios a gates se dejan como borrador para una sesión humana.
