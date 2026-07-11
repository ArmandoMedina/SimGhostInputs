# La homologación — cómo el conocimiento de los proyectos asciende al método

> El método no se escribe en abstracto: se **cosecha** de proyectos reales. La homologación es el ritual que sube lo aprendido en un repo hijo al repo del método — y la razón de que Jidoka exista. Heredado del andamio del linaje (su protocolo `/homologa`), donde se rodó como comando ejecutable, no como doctrina en prosa: *"la doctrina en prosa no se lee; un comando se ejecuta"*. Récord: ADR [0005](../docs/decisions/0005-exprimido-final-del-linaje.md).

## El protocolo, en cinco pasos

1. **Inventario por subagentes.** Qué piezas tiene el hijo, qué estado tiene el método, y —lo más valioso— **los dolores de las bitácoras**: *lo que el dueño corrigió más de una vez es lo que la metodología debe prevenir*.
2. **Clasificación con el cliente.** Cada pieza recibe un destino: **asciende** / **se descarta con registro** (el porqué queda escrito) / **espera maduración**.
3. **Criterio-no-copia.** Lo que asciende se **neutraliza**: auto-desactivable, ajustable vía manifiesto, y *nada hardcodea el layout de un hijo*. Se homologa el **método**, no el inventario de piezas — que dos hijos adopten grados distintos es legítimo, no deuda.
4. **Frontera NDA antes de cada commit.** Grep de términos del trabajo (clientes, personas, datos de entorno) sobre lo que va a subir. Y la regla dura: **lo pusheado se reescribe, no se parcha** — un secreto en el historial no se arregla con un commit encima.
5. **Un ADR por decisión**, citando origen, dolor y descartes. Cierre con verificación del propio repo + release.

## La regla 2–3 de maduración

> **Lo que uses 2–3 veces asciende a estable. Lo que no toques en 2–3 proyectos, pódalo sin culpa.**

El método distingue su **núcleo estable** de su **resto experimental (🧪)** — y lo declara. Una estructura completa *parece* madura aunque nadie la haya usado (*method-fiction*): se madura con el uso, no en teoría. El uso revela lo que sobra **y** lo que falta.

## Lo que la homologación NO es

- **No es sincronización automática.** Subtree/submódulo contradicen el criterio-no-copia: el hijo adopta con juicio, no recibe pushes del método.
- **No es uniformar.** Tres grados reales de adopción convivieron en el linaje sin que ninguno fuera "el atrasado".
- **No es solo copiar hacia arriba.** El conocimiento sube *como máquina antes que como prosa*… **pero el conocimiento no espera a la máquina**: la lección asciende hoy; el hook, con su sprint.
