---
tipo: modulo
clave: <FAM-MOD, ej. IMP-MTC>
dominio: <dominio al que pertenece>
producto: <producto o solución>
estado: en_definicion
prioridad: Por definir
---

# <CLAVE> - <Nombre del módulo>

## Dominio
- [[<dominio>]]

## Propósito del módulo
<Qué responsabilidad funcional agrupa este módulo y para qué.>

## Alcance
<Qué incluye este módulo.>

**No cubre:**
- <Elemento fuera de alcance 1.>

## Regla funcional
<Un enunciado único que resume la condición central que el módulo debe garantizar.>

## Secuencia funcional
<Opcional: cómo se encadena con otros módulos.>
- **Módulo anterior:** [[<módulo previo>]] o `No aplica`
- **Módulo siguiente:** [[<módulo siguiente>]] o `No aplica`

## Capacidades
- [[<FAM-MOD-01> - <Nombre>]]
- [[<FAM-MOD-02> - <Nombre>]]

## Dependencias funcionales
- [[<módulo o capacidad del que depende>]] o `No aplica`

## Relacionado con
- [[<dominio>]]

<!--
Campos del frontmatter:
  tipo: modulo
  clave          → prefijo estable del módulo (FAM-MOD); sus capacidades heredan FAM-MOD-NN
  dominio        → dominio padre
  producto       → producto o solución
  estado         → en_definicion | en_revision | vigente | pausado | fuera_de_alcance
  prioridad      → Must Have | Should Have | Could Have | Won't Have | Por definir
Borra este comentario al usar la plantilla.
-->
