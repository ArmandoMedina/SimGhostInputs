---
tipo: proceso
producto: <producto o solución>
archivo_fuente: <nombre>.drawio
estado: en_definicion
---

# <Nombre del proceso / BPMN>

> Vista de runtime: cómo fluye el trabajo entre piezas. Prefiere un diagrama Mermaid embebido; usa `.drawio` solo para BPMN complejo.

## Diagrama
```mermaid
flowchart LR
  A[<paso>] --> B[<paso>] --> C[<resultado>]
```
<O, si es BPMN complejo: [[<Nombre>.drawio]]>

## Resumen del flujo
1. <Paso 1.>
2. <Paso 2.>
3. <Paso 3.>

## Dominios / módulos que toca
- [[<dominio o módulo>]]

## Relacionado con
- [[<producto o solución>]]

<!--
tipo: proceso · producto · archivo_fuente · estado. Diagrama de flujo de un proceso real.
Si es simple, Mermaid embebido gana (viaja con el repo). Borra este comentario.
-->
