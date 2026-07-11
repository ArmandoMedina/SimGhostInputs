# Los asientos — roles acotados, no enjambre

> Una sola sesión que lee 50 archivos, corre tests y escribe docs se llena de contexto y se degrada (*context rot*). La cura es repartir el trabajo en **asientos**: cada uno con UNA responsabilidad y un "lo que NO hace" explícito. Heredado del andamio del linaje y probado en producción (ADR [0004](../docs/decisions/0004-centralizacion-del-conocimiento.md)).

## Asiento ≠ skill

Un **asiento** es el rol que alguien ocupa (el *quién*); una **skill** es un comportamiento disparable con límites escritos (el *cómo*). Un asiento puede ocuparse **en la sesión principal**, **como subagente** o **como agente de plataforma** (fuera del repo). Por eso tres asientos NO son skills:

- El **orquestador** — es la sesión misma: decide y teje, delega lo pesado. Su antipatrón tiene nombre: *el orquestador desarrollando* — picar código en el hilo principal lo envenena.
- El **desarrollador** — es el trabajo por defecto: escribir código. (Un repo puede *persona-ficarlo* como skill de delegación si le conviene disparar el mismo asiento con sus límites y su "Entorno" cada vez — ver *Personalizar el casting* abajo — pero por defecto no es skill.)
- El **devops** — es el agente de **plataforma/máquina**, no del repo: VMs, SSH, sandboxes, CI, deploys, secretos, `core.hooksPath`, branch protection, config de la cuenta. No es skill porque su dominio es la máquina, no el código, y **no vive en el repo** (vive en la config de plataforma/cuenta).

Convención 🎭: cuando el orquestador hace en sesión el trabajo de otro asiento, lo **anuncia** (`🎭 Asiento: <rol> (en sesión) — <por qué>`) — así se distingue la elección deliberada del olvido.

## El menú de asientos

Menú, no molde: cada arquetipo de repo enciende solo los que merece.

| Asiento | Dueño de | Lo que NO hace |
|---|---|---|
| **orquestador** | decidir y tejer; delegar lo pesado | picar código en el hilo principal |
| **desarrollador** | escribir el código | — |
| **escribano** | sincronizar docs↔código según la ley ([blast-radius](../tools/blast-radius.json)) | no decide alcance; no inventa decisiones (eso es un ADR) |
| **validador** | correr pruebas y juzgar **solo lo ambiguo** que el test no resuelve | no re-valida lo que un test ya cubre; no toca lo visual |
| **revisor-visual** | aceptación UI/UX, evidencia en `qa_runs/` | no juzga lógica; **es checkpoint, no portero** — "¿se ve bien?" la responde el humano |
| **arquitecto-doc** *(opcional, arquetipo doc-heavy)* | formato, jerarquía y consistencia del grafo de docs | no decide negocio; conserva, no inventa alcance |
| **devops** *(agente de plataforma, no skill del repo)* | la máquina y el entorno: VMs, SSH, sandbox, CI, deploys, secretos, `core.hooksPath`, branch protection, config de cuenta | no toca el código de negocio ni decide producto; no vive en el repo |

Los asientos como skills ejecutables llegan en el **Sprint 2** ([ROADMAP](../ROADMAP.md)). El conocimiento de qué es cada uno no espera a la máquina.

## Personalizar el casting (maquinaria neutral + persona opcional)

Los roles vienen **neutrales a propósito** (`escribano`, `validador`, `revisor-visual`, `arquitecto-doc`, `devops`) para que el método público sirva a cualquiera. **En tu repo real, mapéalos a personas si te sirve** — un casting con nombres los vuelve memorables y deja claro quién valida qué. Versionar `.claude/` es lo que permite que ese casting **viva en el repo**, no en la cabeza de cada quien.

La regla que lo vuelve una sola metodología y no dos: **la maquinaria es neutral; el nombre es una capa cosmética encima.**

- **Neutral (nunca cambia):** la ley (`tools/blast-radius.json`) usa el token de rol genérico (`rol: revisor-visual`); los hooks filtran por ese token; los marcadores y la lógica son genéricos. Ahí vive el método — uno solo.
- **Persona (opcional, por repo):** renombras la carpeta del skill y su `name:` (`skills/revisor-visual/` → `skills/mariana/`, cuyo `SKILL.md` dice "soy Mariana, el asiento revisor-visual"). El comportamiento es idéntico; solo cambia la etiqueta.

| Rol del método | Casting (ejemplo) | Vive como |
|---|---|---|
| orquestador | Mau | la sesión principal (no es skill) |
| desarrollador | Ahiram | el trabajo por defecto (opcionalmente un skill de delegación) |
| devops | Oscar | agente de plataforma (no vive en el repo) |
| `validador` | Charbel | `skills/<nombre>/` |
| `revisor-visual` | Mariana | `skills/<nombre>/` |
| `arquitecto-doc` | Armando | `skills/<nombre>/` |
| `escribano` | Escribano | `skills/<nombre>/` |

**La autoridad la da la ley, no el nombre** — quién puede cambiar qué como fuente de verdad se declara en `blast-radius.json` (el campo `rol` de cada área), no en cómo llamaste al skill. Por eso dos repos con castings distintos siguen corriendo *la misma metodología*: la maquinaria que juzga es idéntica; solo difieren las etiquetas de las personas. Cero metodologías paralelas.

## Model-routing: no uses Ferrari para ir por tortillas

El orquestador elige el modelo según la tarea: **pequeño** para lo mecánico, **medio** para juicio acotado, **grande** para decisiones con trade-offs. Si dudas entre dos, sube uno.

## Las reglas duras (pagadas con incidentes reales del linaje)

1. **La lectura voluminosa SIEMPRE va a un subagente.** El subagente quema *su* contexto y devuelve solo el veredicto. Caso real: dos transcripts de ~250 KB leídos en el hilo principal degradaron la sesión entera.
2. **Sobre-orquestar también es error.** No todo merece subagente — y **no todo rol merece hook**. Caso real: se decidió NO cablear el rol de validación numérica porque *"sus tests SON el asiento; cablearlo sería sobre-orquestar"*.
3. **El paralelismo tiene tope.** Caso real: 5 subagentes con worktree en paralelo agotaron la cuota de la sesión; nació un gate determinista de concurrencia. El entusiasmo también se gobierna. Y el diseño de ese gate enseña tres cosas: el criterio de "pesado" es un **campo existente de la llamada**, no un juicio de la IA (*"pedirle a la sesión que se autorregule no es una barrera, es esperanza"*); la ventana de tiempo **se autolimpia** en vez de depender de un evento de cierre que puede no llegar; y vive en la config de la **cuenta**, no del repo — porque gobierna cuota de cuenta.
4. **Delegación coherente.** Caso real: commit delegado a un subagente pero push hecho en sesión — la mitad de la ceremonia no cuenta. Si delegas una cadena, delega la cadena.
5. **Una sola sesión escritora por working tree.** Caso real: el commit de una sesión paralela dejó **ciegos** los Stop hooks de la otra (solo ven lo no commiteado) y produjo un lost-update del HANDOFF. La segunda sesión es solo-lectura o se lleva su propio worktree; el HANDOFF tiene un solo dueño a la vez.

## Qué va a subagente vs qué se queda — el criterio en un vistazo

Las reglas de arriba son los *porqués*; esto es el criterio operativo para no dudar en el momento (el hueco que un cliente nombró: *"la regla existe pero no es obvio cuándo aplica"*). La pregunta no es "¿puede un subagente hacerlo?" sino **"¿el hilo principal pierde más de lo que gana si lo hace él?"**

| Va a **subagente** | Se queda **en sesión** (y se anuncia 🎭) |
|---|---|
| **Lectura voluminosa**: explorar árboles, leer transcripts o muchos archivos (regla 1) | **Decidir y tejer**: el trabajo propio del orquestador, y la síntesis de los veredictos que devuelven los subagentes |
| Trabajo **aislado** que devuelve un veredicto: una búsqueda, una auditoría, un análisis | Edición quirúrgica **acoplada** con bucle TDD editar→correr→arreglar sobre los mismos archivos — un subagente devuelve una vez y el bucle se rompe |
| Trabajo en **otro working tree** (otro repo o un worktree) — mantiene la sesión como escritora única (regla 5) | Cambios cortos cuyo contexto **ya vive en el hilo**: re-explicárselo a un subagente cuesta más que hacerlo |
| Mutación de archivos **en paralelo** que chocarían — con el tope de concurrencia de la regla 3 | — |

**Default cuando dudas:** lectura y trabajo pesado o aislado → subagente; si lo haces tú en sesión, **anúncialo** (`🎭 Asiento: <rol> (en sesión) — <por qué>`), para que sea elección deliberada y no olvido. Y no caigas al otro extremo (regla 2): sobre-orquestar —mandar a subagente lo trivial y acoplado— también degrada.

*Ejemplo trabajado (una sesión real):* construir el lazo de sincronización labs↔Jidoka (ADR 0012) se repartió así — la exploración de dos repos y el cableado del lab hijo (**otro árbol**) fueron a **subagentes**; el motor y su self-test, **acoplados por TDD** sobre los mismos tres archivos, se hicieron **en sesión bajo `🎭 desarrollador+validador`**. Ni todo al hilo (lo envenena) ni todo a subagentes (sobre-orquestar): cada pieza donde pesa menos.

## La ley que gobierna todo el reparto

> **El determinismo bloquea; el juicio orquesta; nada irreversible se automatiza sin checkpoint humano.**

El cálculo crítico lo hace un motor determinista con tests, nunca un LLM. El gate se evalúa sobre el **artefacto** (el diff, el archivo, el log), no sobre confiar en el agente — por eso en Jidoka no existen archivos de auto-firma ("el rol X validó"): lo que se cuela, se atrapa.
