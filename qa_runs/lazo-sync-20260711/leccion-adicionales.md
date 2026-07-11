# Lecciones adicionales (draft) — cosechadas del campo de SGI (ADR 0019)

> Dos lecciones de campo, ya pagadas en este repo, que el método neutral de Jidoka podría
> absorber. Draft para revisión humana; formato del template `leccion.md`; anonimizado
> (frontera-nda). **No presentadas aún.** Ambas nacieron como enmiendas al ADR 0019 de SGI.

---

## Lección A — La evidencia de QA debe ser durable en git (`git add -f`), no solo satisfacer el hook

### La lección, en una frase

Un gate visual/QA que verifica el **working tree** (¿existe el artefacto?) se satisface con un
archivo que luego **nunca llega a git** — el veredicto queda inauditable desde la historia; commitear
lo citado con `git add -f qa_runs/<corrida>/` debe ser **paso obligatorio del cierre**, no una
recomendación.

### Dónde la pagaste

Caso de un repo donde `qa_runs/` está gitignoreado (el bulto no se versiona). El hook de QA visual
verificaba el working tree, así que un "visual PASS" pre-merge pasaba el gate con evidencia que vivía
**solo en la laptop**: `git ls-files qa_runs/` mostraba **0 artefactos** (solo el README). El veredicto
citado en el HANDOFF/CHANGELOG apuntaba a un directorio que **no existía en git**. Mismo principio de
"sin auto-firmas": un veredicto sin artefacto **durable** no vale.

### Qué haría Jidoka distinto

Elevar a paso obligatorio del ritual de cierre: **todo veredicto que cite una corrida de QA debe
forzar al commit su evidencia citada** con `git add -f qa_runs/<corrida>/<archivo>` (solo lo citado,
no el bulto). El gemba-stop / revisor-visual podría además chequear que el directorio citado **exista
en `git ls-files`**, no solo en el working tree — así el gate mide lo durable, no lo efímero.
Regla 2-3: **un uso real** (esperando su segundo).

---

## Lección B — El tope de agentes "pesados" concurrentes debe ser un hook determinista, no el juicio del orquestador

### La lección, en una frase

Pedirle al orquestador que se autorregule cuántos subagentes pesados lanza "no es una barrera, es
esperanza": la misma sesión bajo presión de avance repite el exceso — el tope debe vivir en un **hook
determinista** que cuente un proxy de campo (`isolation: "worktree"`), no en el criterio de la IA.

### Dónde la pagaste

Caso de un orquestador que lanzó **5 subagentes worktree** en paralelo (cada uno
explora+codea+testea+abre PR) más su propio hilo; el conjunto **agotó la cuota de sesión de la cuenta**
de golpe y los 5 fallaron a mitad de tarea ("session limit"). El trabajo no se perdió (cada worktree
conserva su diff en disco), pero mostró que "yo decido cuántos lanzo" **no escala**. Se resolvió con un
hook `PreToolUse` con `matcher: "Agent"` que cuenta lanzamientos con `isolation: "worktree"` en una
ventana móvil y **deniega** al pasar el tope — config de máquina/cuenta, fuera del repo.

### Qué haría Jidoka distinto

Documentar en la doctrina de orquestación el patrón: **topar la concurrencia de agentes pesados con un
hook determinista fuera del repo**, usando `isolation: "worktree"` como proxy de "pesado" (correlaciona
1:1 con el patrón que rompe la cuota; los agentes de solo-lectura como Explore/research no cuentan). El
principio general —"una barrera es una barrera, no una autoevaluación"— ya es doctrina Jidoka para los
gates de código; esta lección lo extiende al **presupuesto de cómputo/cuota**. Regla 2-3: **un uso
real** (esperando su segundo).
