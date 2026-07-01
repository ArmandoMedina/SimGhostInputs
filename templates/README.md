# Plantillas — formatos listos para copiar

Estos son los formatos canónicos del método (la capa *reference* de Diátaxis). Copia el que necesites a su carpeta, renómbralo con su clave y llénalo. **No inventes una estructura nueva si ya hay un formato aplicable** — si un formato te queda corto, mejóralo aquí, no crees uno paralelo.

Cada plantilla trae frontmatter (para Obsidian) y `## Relacionado con` con `[[wikilinks]]`.

### Capa QUÉ — jerarquía funcional (sombrero Producto)

| Plantilla | Nivel | Va en | Para qué |
|---|---|---|---|
| [`ecosistema.md`](ecosistema.md) | Ecosistema | `product/ecosistema/` | El universo donde vive todo (fantasma-inputs + fantasma-live). |
| [`solucion.md`](solucion.md) | Solución | `product/soluciones/` | Un producto visto desde el problema del usuario. |
| [`dominio.md`](dominio.md) | Dominio | `product/dominios/` | Un área de responsabilidad con reglas propias. |
| [`modulo.md`](modulo.md) | Módulo | `product/modulos/` | Una pieza funcional dentro de un dominio. |
| [`capacidad.md`](capacidad.md) | Capacidad | `product/capacidades/` | La unidad atómica: algo que el sistema puede hacer. |
| [`requerimiento.md`](requerimiento.md) | Entrada | `product/requerimientos/` | Historia de usuario en crudo, por clasificar. |
| [`proceso.md`](proceso.md) | Runtime | `product/procesos/` | Un flujo de punta a punta (BPMN / Mermaid). |

### Capa CÓMO — arquitectura (sombrero Ingeniería)

| Plantilla | Va en | Para qué |
|---|---|---|
| [`componente.md`](componente.md) | `engineering/componentes/` | Un sistema/servicio/BD real que soporta las capacidades. |
| [`especificacion-tecnica.md`](especificacion-tecnica.md) | `engineering/especificaciones/` | La implementación concreta que resuelve una capacidad. |
| [`modelo-de-datos.md`](modelo-de-datos.md) | `engineering/modelos-de-datos/` | La estructura de datos (modelo, esquema, salidas). |

### Transversal

| Plantilla | Va en | Para qué |
|---|---|---|
| [`glosario.md`](glosario.md) | `docs/glosario.md` | Lenguaje ubicuo: un término, un significado. |
| [`plan-de-trabajo.md`](plan-de-trabajo.md) | `docs/planes/` (efímero) | Plan persistido para tareas largas con IA: sobrevive al corte de tokens y se borra al cerrar (ADR 0019). |

> Qué significa cada nivel y cuándo usar cada uno: [`engineering/README.md`](../engineering/README.md) y [`product/README.md`](../product/README.md). El porqué de adoptar esta estructura: [ADR 0015](../docs/decisions/0015-estructura-product-engineering.md).

## Relacionado con
- [[capacidad]]
- [[dominio]]
