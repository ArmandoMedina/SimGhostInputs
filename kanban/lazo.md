# El lazo — Intención → Construcción → Verificación → Registro

> Dirigir software —lo escriba un humano o una IA— es el mismo lazo de control. El sprint ([README](README.md)) es el ritmo; **este lazo es lo que gira adentro** de cada rebanada. Heredado del andamio interno del linaje (ADR [0001](../docs/decisions/0001-la-fusion-jidoka.md), ADR [0004](../docs/decisions/0004-centralizacion-del-conocimiento.md)).

```
Intención ──▶ Construcción ──▶ Verificación ──▶ Registro
(capacidad     (el código)     (tests +          (ADR ·
 + criterios)                   correr la app)    CHANGELOG ·
                                                  HANDOFF)
```

## Paso 0 — ¿Exploras o consolidas?

**No declaras la fase: la marca dónde estás en git. El acto de commitear ES consolidar.** Mientras exploras, nada de la maquinaria corre (el código puede tirarse, las notas van `en_definicion`); al consolidar, el cambio incluye su test y su decisión. Commit libre mientras las docs queden completas; el push espera el OK humano. Es anti-fatiga aplicado a la exploración: los gates no persiguen borradores.

## Los cuatro tiempos

1. **Intención (el QUÉ).** Di qué debe hacer, en lenguaje llano, y cómo sabrás que se cumple: una **capacidad** con **criterios de aceptación** (`Dado que… cuando… entonces…`). Es la mitad que casi todos se saltan — y la lección más cara del linaje: *sprints construidos sin criterios aprobados terminaron entregando cosas que el cliente no pidió*. El QUÉ se escribe **antes** de construir, no después.
2. **Construcción (el CÓMO).** Tú o la IA escriben el código. En rebanadas verticales, cada paso commiteable y verde.
3. **Verificación.** Los criterios se vuelven **tests**, y corres la app. Aquí confirmas que la intención se cumplió **sin tener que leer el código** — la mitad que vuelve seguro el vibe coding. El veredicto lo da el artefacto (test verde, demo corriendo), nunca la palabra del agente. La doctrina completa de este tiempo (dos capas, entrada hostil, cerrar por medición) vive en [`verificacion.md`](verificacion.md).
4. **Registro.** Lo no obvio que decidiste queda escrito, para que la próxima sesión (tú en 6 meses, o una IA sin memoria) tenga continuidad.

## El Registro se reparte por caducidad

No todo lo que se registra vive lo mismo. Cada cosa tiene un doc dueño:

| Caducidad | Doc dueño | Qué guarda |
|---|---|---|
| **Permanente** | ADR (`docs/decisions/`) | El **porqué** de cada decisión — incluido el camino que NO se tomó |
| **Lo enviado** | `CHANGELOG.md` | Qué cambió, versión a versión |
| **Efímero** | `HANDOFF.md` | Dónde voy, qué falta — **se llena al cerrar, se lee y se LIMPIA al abrir.** Es estado en vuelo, no historial; lo atendido se borra |

Tres reglas finas del Registro, pagadas en el linaje:

- **Las decisiones de JUICIO del cliente tienen cola propia** en el HANDOFF (estados `[PENDIENTE]` / `[DECIDIDA-REVISABLE]`), con la aclaración explícita de que *no son de código — nada está bloqueado*. Así el juicio humano pendiente ni se pierde entre deuda técnica ni frena el avance.
- **Una regla enterrada en un ítem tachado del backlog no la lee nadie.** Si algo gobierna decisiones futuras, asciende a donde se decide (un ADR), no se queda en un `[x]` resuelto. Caso real: una regla vivió en el backlog y el cliente tuvo que re-explicarla sesión tras sesión hasta que se hizo ADR.
- **Romper una invariante a propósito tiene protocolo:** el ADR redefine el contrato; se auditan TODOS los consumidores con estado individual (arreglado / NO arreglado / en paralelo); y se nombran los **límites conocidos** ("escritos para que nadie los redescubra a golpes") y las **defensas incidentales** — protecciones que funcionan por accidente y se romperían al mover otra pieza.

## Podar — la otra mitad de registrar

**Una nota vieja que ya no es verdad es *peor* que no tenerla, porque alguien la va a creer.** La regla: cierra con trazabilidad lo que ya no vive; elimina solo el andamiaje que nunca fue contenido; **si dudas entre borrar y marcar → marca**. Cada artefacto se poda a su manera: los ejemplos se borran; las notas pasan a `fuera_de_alcance`; los ADRs se marcan *reemplazados*, nunca se borran; el backlog resuelto se marca con referencia, nunca se vacía. Cadencia: en cada release — y al reemplazar una decisión, en el mismo momento.

## El kit mínimo

Para muchos proyectos, esto es *todo* lo que hace falta: un brief de producto + capacidades con criterios + código con tests + ADRs + un mapa de arquitectura para no perderte cuando crezca. Lo demás es expansión opcional.

## Las dos reglas que gobiernan el lazo

- **La disciplina escala con el riesgo.** Un experimento personal no merece la ceremonia de un sistema regulado. Es un menú, no un molde.
- **Avisa temprano, bloquea al final.** Los gates locales avisan mientras trabajas; el muro real (CI + required check) bloquea al mergear. Ver [`andon/`](../andon/).

## Menú, no molde — el criterio operativo

La pregunta-guía para saber cuánta ceremonia merece un repo: **¿alguien que necesita cambiar o confiar en esto lo entiende sin preguntarte?** No → documenta más; sí → menos. Tres señales lo modulan: cuántas manos tocan el repo, qué tipo de reglas carga, y si habrá traspaso o auditoría. Para un experimento de usar-y-tirar, sáltate todo: README de 3 líneas.

Y el caso que invierte la intuición: **si el dueño no lee el código, la documentación deja de ser opcional.** Su subconjunto de control sin lectura es: ADRs + mapa de arquitectura + capacidades con criterios + tests — *auditar por verificación, no por lectura*. El mismo lazo sirve a los dos mundos; lo único que cambia es cuánto te apoyas en la Verificación.
