---
tipo: modulo
clave: <FAM-MOD, ej. LIS-CON>
dominio: <dominio al que pertenece>
producto: <producto o solución>
estado: en_definicion
prioridad: Por definir
---

# <CLAVE> - <Nombre del módulo>

## Dominio
- [[<dominio>]]

## Propósito del módulo
<Qué agrupa este módulo y para qué. Una o dos frases.>

## Alcance
<Qué cubre.>

**No cubre:**
- <Lo que queda fuera — y a qué módulo pertenece si aplica.>

## Regla funcional
<La regla transversal que gobierna a todas las capacidades del módulo, si existe.>

## Secuencia funcional
- **Módulo anterior:** [[<módulo previo>]] o `No aplica`
- **Módulo siguiente:** [[<módulo siguiente>]] o `No aplica`

## Escenarios E2E
<Opcional: flujos que cruzan varias capacidades.>
### <nombre del escenario>
- Capacidades participantes: [[<FAM-MOD-01 - Nombre>]] → [[<FAM-MOD-02 - Nombre>]]

## Capacidades
- [[<FAM-MOD-01 - Nombre de la capacidad>]]

## Dependencias funcionales
- <Otro módulo o componente del que depende.> o `No aplica`

## Relacionado con
- [[<dominio>]]

<!--
tipo: modulo · clave FAM-MOD (prefijo estable; sus capacidades heredan FAM-MOD-NN) ·
dominio · producto · estado · prioridad. Un modulo agrupa capacidades afines.
Borra este comentario al usar la plantilla.
-->
