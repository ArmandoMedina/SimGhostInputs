# 07 — Receta de traslado: montar el sistema en cualquier actividad

Guía operativa para portar la doctrina a una actividad nueva (soporte, operación financiera,
KB, reportes, lo que sea). Caso de referencia implementado: **caso F** — un proceso financiero
diario real, gobernado con este método en 2026-07. Por la frontera NDA (ver abajo), aquí se
cita solo a nivel método; los detalles del negocio viven en el repo del trabajo.

## Las 6 preguntas, en orden

**1. ¿Cuál es el artefacto?** Lo que el trabajo produce, con forma inspeccionable (archivo,
tabla, texto). Sin artefacto no hay dónde poner la pared — un chat en tiempo real sin momento
discreto de "esto se manda" no se puede gatear con este método.
*Caso F: una tabla diaria que se envía a un canal de mensajería.*

**2. ¿Cuál es el choke point?** El acto discreto de "esto se envía / se cierra / se publica".
Ahí, y solo ahí, se sienta el gate. Si la acción es una tool de la IA → `PreToolUse`; si es un
merge → required check; si es un botón humano → checklist bloqueante antes del botón.
*Caso F: el envío. El gate corre ANTES, porque el error es caro e irreversible.*

**3. ¿Qué es mecánico y qué es juicio?** Separar con la palanca LOA de dos ejes: la máquina
adquiere y analiza ALTO (reúne datos, calcula, valida forma); el humano decide y firma (la
decisión se queda BAJA). Lo mecánico-verificable → **deny** (Airbus); lo que requiere juicio →
**ask** con override (Boeing). Y lo verdaderamente crítico no lo produce un LLM: lo produce un
motor determinista con tests, la IA solo orquesta.
*Caso F: el número lo hace un motor con tests que reproduce el histórico, nunca el LLM. Los
checks mecánicos quedaron deny; los de juicio, ask.*

**4. ¿Dónde vive el estado?** En artefactos del repo con dueño por caducidad — nunca en la
memoria de la IA ni en la cabeza del humano: lo permanente → ADR; lo enviado → CHANGELOG; el
camino → ROADMAP; lo efímero → HANDOFF (se limpia al abrir); reglas de negocio → product/.
La regla se cablea (hook anti-memoria), no se pide.
*Caso F: HANDOFF + ADRs + doc-gate §8 que BLOQUEA tocar código sin su doc dueño.*

**5. ¿Cómo se mide que el gate vive?** Desde el día 1, leading indicators, no cuenta de
accidentes: tiempo de revisión, tasa de aprobación, desacuerdos reportados, intercepciones
reales. Cuando el flujo es estable, capture-test tipo TIP (trampas plantadas con fail-safe y
Just Culture). La prueba de vida: ¿cuándo fue la última vez que el gate rechazó algo real?
*Caso F: tablero de 5 series + TIP aprobado a ~2-3 trampas/mes.*

**6. ¿Cómo se mantiene vivo el juicio del humano?** Práctica manual programada, en calma
(SAFO 13002) — no cuando el sistema se cae ni cuando el límite de tokens pega. Y la IA capacita
**desde el artefacto** (señala el instructivo/runbook versionado), no desde su memoria de modelo.
*Caso F: día manual programado — el operador arma la tabla a mano y la compara contra el motor;
el diff es la lección en ambas direcciones.*

## Los mínimos no negociables (si falta uno, el sistema es teatro)

1. El gate vive **fuera** del modelo (hook / CI / check server-side) — nunca "instrucciones".
   Nota de plan, pagada: el muro server-side puede tener costo de suscripción (branch
   protection en repos privados de GitHub exige plan Pro; 403 en Free). Presupuestarlo, y
   mientras no esté, decir honesto que las barreras son disciplina, no garantía.
2. El gate lee el **artefacto**, no la palabra del agente (ni la del humano).
3. Lo irreversible lleva **checkpoint humano** con capacidad real de veto (tiempo, información,
   poder) — si no, fabricaste un chivo expiatorio (moral crumple zone), no un juez.
4. Pocas alarmas y buenas — un gate ruidoso muere de disuse en semanas.
5. Alguien mira el tablero — un gate sin instrumentar se pudre en silencio.

## Anti-patrones (todos ya pagados)

- **API/MCP propio como gobierno** → la IA no lo conoce, lo reaprende cada sesión (ADR 0002).
- **"Ponlo en el CLAUDE.md / repítele la regla"** → la prosa falló 4 veces; el hook, ninguna.
- **Gate solo cliente-side** → `--no-verify` existe y los agentes lo usan (issue #40117).
- **Medir "el gate se ejecutó"** en vez de "el gate atrapó algo" → Goodhart; teatro.
- **El humano revisa TODO** → vigilance decrement; revisará nada. Reservarlo para el choke point.
- **La IA "aprende" el proceso en su memoria** → amnesia reintroducida; el proceso vive en el
  instructivo versionado.

## Orden de montaje (el que siguió el caso F)

1. Motor/validadores deterministas de lo mecánico, con tests contra casos reales (backtest).
2. Choke point + checklist de checks deny/ask, decidida por el dueño del riesgo (él marca).
3. **Prueba de humo del gate contra el artefacto real, ANTES de estrenarlo.** Pagada en el
   caso F: la primera corrida real cazó un bug del propio gate (un encabezado suelto que
   confundía al parser de layout) y confirmó el bloqueo correcto de un artefacto desactualizado
   — en la misma corrida. Quien valida también se valida.
4. Doc-gate y estado en artefactos (HANDOFF/ADR/§8) + hooks de sesión.
5. Tablero de leading indicators (CSV basta para empezar).
6. TIP y día manual — cuando el flujo ya es estable (fail-safe implementado y testeado ANTES
   que el generador de trampas).

Lección de campo del caso F: los checks genéricos siempre necesitan **excepciones del negocio
cableadas con nombre** (allá: un valor negativo que es normal para una contraparte, un literal
a mano que es esperado en otra). La excepción tolerada en silencio o hace gritar al gate en
falso (fatiga) o lo afloja para todos.

## La frontera NDA (regla de este repo y de todo traslado)

Este repo es **personal**. Las lecciones de los casos de campo del trabajo cruzan hacia acá
**solo a nivel método, anonimizadas**: nunca nombres de clientes, empleados, procesos, montos,
proveedores, canales, rutas ni nombres de repos del trabajo. El caso se cita como "caso N";
sus detalles viven en su propio repo, del lado correcto del NDA. La misma regla aplica al
portar hacia cualquier otro artefacto personal (starter, notas, publicaciones): **el método es
tuyo; el negocio es del cliente.** Antes de publicar cualquier cosa de este repo: pasada de
revisión de confidencialidad sobre contenido E historial.
