---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Interfaz de usuario

## Producto
- Fantasma

## Propósito
Dar una **interfaz gráfica local** (Streamlit) como capa delgada sobre el CLI, para que un piloto sin terminal pueda recorrer el flujo paso a paso (cargar → comparar → overlay → componer) sin que sus datos salgan de su máquina.

## Alcance
- Flujo en pasos 0-4 (carga, comparación, overlay, composición).
- Avisos visibles del motor (autos distintos, delta sospechoso, falta ffmpeg).
- "CLI primero": todo lo de la UI se puede hacer en terminal.

**Fuera de alcance:** lógica de cálculo (vive en el motor `core/`, no en la UI); front de escritorio custom (diferido a v2.0, [ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md)).

## Módulos
- UI — Interfaz Streamlit (pasos 0-4)

## Relacionado con
- [[Reportería]]
- [[streamlit]]
- [Patrones de UX](../../docs/ux-patterns.md)
