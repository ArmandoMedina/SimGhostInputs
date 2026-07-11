# Doctrina — el porqué (Poka-yoke)

> El **porqué** citable de Jidoka. La IA **no lee esto** en su trabajo diario ([ADR 0003 de la doctrina](decisiones/0003-doctrina-se-consume-via-disparos.md)): la doctrina le llega compilada como **disparos** — mensajes de gate en el momento del disparo (`kit/.jidoka/disparos/`). Esto es para los humanos: el fundamento verificable del método.

## La tesis en una línea

**Un mecanismo de gobierno es muro real si y solo si el punto de control vive FUERA del LLM.** Si depende de que el modelo coopere, no es muro — es una sugerencia.

Sobre esa ley, la tesis dual (los dos pájaros): la disciplina cae sobre el robot (sin dignidad que reclamar); el juicio se preserva en el humano. La línea que no se cruza: relevar al humano de *memoria y procedimiento*, protegerlo como portador de *juicio*.

## Mapa

| Archivo | Qué contiene |
|---|---|
| [`00-tesis.md`](00-tesis.md) | La ley del muro (fuera vs dentro del LLM) y la tesis dual |
| [`01-linaje-manufactura.md`](01-linaje-manufactura.md) | Poka-yoke, jidoka, Deming, queso suizo, checklists, forcing functions |
| [`02-linaje-software.md`](02-linaje-software.md) | Maker-checker, Fagan, CI, Design by Contract, DoD; la IA como actor CMM nivel 1 |
| [`03-aviacion.md`](03-aviacion.md) | Bainbridge, Endsley, AF447; el juicio humano como último gate; deny/ask (Airbus/Boeing) |
| [`04-como-se-pudre.md`](04-como-se-pudre.md) | Los seis modos de falla: fatiga de alertas, Goodhart, teatro, normalización de la desviación |
| [`05-instrumentacion.md`](05-instrumentacion.md) | Leading vs lagging, TIP (capture-test), el tablero mínimo de 5 series |
| [`06-fronteras.md`](06-fronteras.md) | Qué es reclamable, qué se cita, qué se corrigió |
| [`07-receta-de-traslado.md`](07-receta-de-traslado.md) | Portar el método a cualquier actividad: las 6 preguntas y los 5 mínimos |
| [`citas-verificadas.md`](citas-verificadas.md) | El ledger de verificación adversarial contra fuente primaria |
| [`decisiones/`](decisiones/) | Los ADRs de la doctrina misma: por qué repo propio, por qué NO una API de gobierno, por qué disparos y no lectura, cómo se anonimiza |

> Las citas que cargan peso estructural fueron verificadas contra fuente primaria por agentes adversariales. Ante discrepancia, manda el ledger (`citas-verificadas.md`).
