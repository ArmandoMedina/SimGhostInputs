# El modo desatendido — cómo el agente trabaja solo, y seguro

> Cuando el agente trabaja **sin un humano presente** —una corrida nocturna, una tarea larga mientras duermes, un pase autónomo de limpieza o construcción— la pregunta no es *"¿qué puede hacer?"* sino *"¿qué NO debe decidir solo?"*. Este es el protocolo. Aplica a **cualquier actividad**, no solo a auditar (la [auditoría en rama](auditoria.md) es solo dónde apareció primero). Heredado del linaje (la corrida nocturna real: cerró un CVE y un XSS sola, y dejó cada decisión que no le tocaba en una lista).

## La ley del modo desatendido

> **Automatiza alto la adquisición y el análisis; mantén baja la decisión y la ejecución de lo irreversible.**

Es el mismo eje de la aviación ([`doctrina/03`](../doctrina/03-aviacion.md), LOA de dos ejes) y los disparos [`decision-queda-en-humano`](../kit/.jidoka/disparos/) y [`click-it-down`](../kit/.jidoka/disparos/): reunir evidencia, resumir, buscar, arreglar lo mecánico → el agente. Firmar lo irreversible → el humano. Subir el nivel en la etapa de decisión fabrica sellos de goma.

## Las dos lanes (físicas, separadas)

Toda corrida desatendida reparte su trabajo en **dos bitácoras**, no una:

| Lane | Qué va aquí | Quién actúa |
|---|---|---|
| **`[agente]`** | Lo **mecánico, reversible y autorizado**: arreglar un bug con test, sincronizar un doc, correr una suite, un refactor con verde. Cada ítem con su **criterio de verificación** ("3 suites verdes + smoke"). | El agente lo ejecuta **solo**, en su rama. |
| **`[humano]`** | Lo que exige **juicio, es irreversible, o pide credenciales/datos que solo el humano tiene**. | El agente **prepara** lo delegable y **nombra exactamente qué firma el humano**; no lo ejecuta. |

Dentro de la lane humana, cada ítem marca con etiquetas literales qué paso es `[humano]` (decide) y qué puede dejar listo una corrida `[agente]` (ejecuta *después* de decidido). Ejemplo real: *"upgrade de la librería: **[humano]** decide si se hace (re-validación con datos que solo el dueño tiene); **[agente]** hace el swap una vez decidido."*

## La prioridad se declara arriba

La corrida trabaja en orden de valor, declarado y visible: **seguridad y fugas > corrección > robustez > salud de docs > estilo**. Las secciones de baja prioridad quedan **vacías a propósito** cuando no hay nada — el agente **no infla la agenda** para parecer productivo.

## Las reglas duras (pagadas en el linaje)

1. **Click-it-down ante la sorpresa.** Si algo se complica o el resultado sorprende, el agente **baja** el nivel: de ejecutar a *dejar preparado y esperar al humano*. No pelea dentro del modo automático mientras la situación se degrada.
2. **Nada irreversible sin el humano.** Reescribir historia de git, publicar, desplegar, borrar, tocar secretos, mergear a `main`: van a la lane `[humano]`, siempre.
3. **El agente NO edita sus propios gates.** Un cambio a `tools/blast-radius.json`, a los hooks o al CI se deja como **borrador para una sesión humana** — rodear la negativa del harness por shell sería el anti-patrón exacto que la doctrina condena. Quien se autoregula no es una barrera.
4. **Reconocimiento con veredicto completo.** La corrida reporta también lo que revisó y encontró **sano**, no solo los problemas. Un informe que solo lista fallas no dice qué se cubrió (y esconde la aprobación-en-vacío).
5. **Fail-safe y auto-limpieza.** Las bitácoras son temporales (rama `auto/<fecha>` o similar) y **se retiran cuando su lane queda vacía**. Lo durable migra a su doc dueño (ADR / HANDOFF / CHANGELOG); las lanes no son historial.

## La forma ejecutable

El comando **`/jidoka:desatendido`** corre un pase autónomo produciendo el par de lanes (molde en [`kit/.jidoka/templates/desatendido.md`](../kit/.jidoka/templates/desatendido.md)). El humano, al volver, lee la lane `[humano]` —corta, priorizada, cada ítem con quién firma— y decide sin releer todo. Es el Gemba del trabajo desatendido: el humano revisa el resultado y las decisiones pendientes, no el diff.
