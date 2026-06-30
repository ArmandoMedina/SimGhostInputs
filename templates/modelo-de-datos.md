---
tipo: modelo_datos
clave: TBL-<ORIGEN>-<NUM>
tecnologia: <objeto Python | CSV | JSON | ...>
estado: en_definicion
---

# TBL-<CLAVE> — <Nombre de la entidad / archivo>

## Propósito
<Qué guarda esta estructura y para qué, en una frase.>

## Campos
| Campo | Tipo | Obligatorio | Significado |
|---|---|--:|---|
| `<campo>` | `<tipo>` | Sí/No | <qué representa> |

## Llaves e índices
- **Índice maestro:** `<campo>` (ej. la distancia)
- **Relaciones:** `<campo>` → [[<otra entidad>]]

## Administrado por
- [[<componente o módulo dueño>]]

## Vinculado con
- [[<capacidad o especificación que usa esta estructura>]]

<!--
Un MODELO DE DATOS es del lado del CÓMO: describe la ALACENA (qué se guarda y cómo está
organizado), distinto de la ESPECIFICACIÓN TÉCNICA, que es la RECETA (la lógica que la llena).
Borra este comentario al usar la plantilla.
-->
