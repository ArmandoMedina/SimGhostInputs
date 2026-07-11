---
tipo: modelo_datos
clave: TBL-<ORIGEN>-<NUM>
tecnologia: <PostgreSQL | MySQL | archivo CSV | ...>
estado: en_definicion
---

# TBL-<CLAVE> — <Nombre de la tabla / entidad>

## Propósito
<Qué guarda esta tabla/entidad y para qué, en una frase.>

## Campos
| Campo | Tipo | Obligatorio | Significado |
|---|---|--:|---|
| `<campo>` | `<tipo>` | Sí/No | <qué representa, en lenguaje de negocio> |

## Llaves e índices
- **Llave primaria:** `<campo>`
- **Llaves foráneas:** `<campo>` → [[<otra tabla>]]
- **Índices / unicidad:** <ej. índice único sobre correo>

## Administrado por
- [[<componente dueño, ej. la base de datos>]]

## Vinculado con
- [[<capacidad o especificación que usa esta tabla>]]

<!--
Un MODELO DE DATOS es del lado del COMO: describe la ALACENA (que se guarda y como esta
organizado), distinto de la ESPECIFICACION TECNICA, que es la RECETA (la logica que la llena).
En lenguaje de negocio cuando se pueda; el detalle fisico exacto va donde el riesgo lo pida.
Campos del frontmatter:
  tipo: modelo_datos
  clave      -> identificador estable TBL-<ORIGEN>-<NUM>
  tecnologia, estado
Borra este comentario al usar la plantilla.
-->
