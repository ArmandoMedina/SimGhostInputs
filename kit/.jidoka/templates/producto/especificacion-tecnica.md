---
tipo: especificacion_tecnica
clave: TEC-<ORIGEN>-<NUM>
tecnologia: <PostgreSQL | API | ETL | ...>
estado: en_definicion
---

# TEC-<CLAVE> — <Nombre de la implementación>

## Contexto técnico
<Breve explicación de la solución técnica aplicada (ej. particionamiento, caching, windowing).>

## Arquitectura de datos / flujo técnico
<Diagrama simple o descripción de los saltos de datos entre tablas o sistemas.>

## Implementación (código / query)
```sql
-- Código real, queries optimizados o pseudo-código.
```

## Estrategia de mantenimiento
- **Frecuencia:** <ej. cada 30 min, mensual, bajo demanda.>
- **Impacto:** <ej. carga de CPU, locks, ventana de mantenimiento.>

## Vinculado con
- [[<capacidad que esta especificación resuelve>]]

<!--
Una ESPECIFICACION TECNICA es del lado del COMO (Ingenieria): la implementacion concreta
que resuelve una capacidad. Siempre queda VINCULADA a la capacidad funcional que satisface
(por eso '## Vinculado con', no 'Relacionado con'). Campos del frontmatter:
  tipo: especificacion_tecnica
  clave      -> identificador estable TEC-<ORIGEN>-<NUM>
  tecnologia, estado
Borra este comentario al usar la plantilla.
-->
