# Templates — los formatos probados del ritual

> Estructuras que sobrevivieron sprints reales en el linaje (no se diseñaron en abstracto: cada sección existe porque faltó alguna vez). Se **copian**, no se redactan de cero — copiar la plantilla es la tarea 0 de cualquier doc nuevo.

| Plantilla | Para qué | ¿Se versiona? |
|---|---|---|
| [`sprint-plan.md`](sprint-plan.md) | El plan que apruebas en plan mode. **El plan aprobado ES el sprint** | **Sí** — se archiva en `docs/sprints/` (es el contrato) |
| [`sprint-entrega.md`](sprint-entrega.md) | El récord de cierre: qué se entregó, la evidencia, el Kaizen | **Sí** — es el récord |
| [`plan-de-trabajo.md`](plan-de-trabajo.md) | Plan persistido para una tarea larga que puede morir a media ejecución | **No** — es efímero (lección del linaje: versionarlo creó contradicción entre plan y realidad). Vive fuera de git y se borra al terminar |
| [`adr.md`](adr.md) | Una decisión y su porqué — incluido el camino que NO se tomó | **Sí** — permanente, y se lista en su índice en el mismo commit |

## Ownership por sección

Las plantillas de sprint declaran secciones con **dueño**. La regla que importa: la sección de **"Verificación (el demo que corre el cliente)"** y la revisión del stakeholder son **del cliente** — los agentes las proponen, nunca las dan por cumplidas. *"Hecho" = el cliente lo vio funcionar.*
