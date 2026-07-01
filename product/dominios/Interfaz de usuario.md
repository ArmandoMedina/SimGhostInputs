---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Interfaz de usuario

## Producto
- Fantasma

## Propósito
Dar una **interfaz gráfica local** como capa delgada sobre el CLI, para que un piloto sin terminal pueda recorrer el flujo paso a paso (cargar → comparar → overlay → componer) sin que sus datos salgan de su máquina. Desde v2.0 la UI principal es NiceGUI (`fantasma-ng`, nativa via pywebview); Streamlit permanece como implementación legacy (`fantasma ui`).

## Alcance
- Flujo en pasos 0-4 (carga, comparación, overlay, composición).
- Drill-down accionable por curva en el Paso 2.
- Avisos visibles del motor (autos distintos, delta sospechoso, falta ffmpeg).
- "CLI primero": todo lo de la UI se puede hacer en terminal.

**Fuera de alcance:** lógica de cálculo (vive en el motor `core/`, no en la UI).

## Módulos
- [[UI - Interfaz NiceGUI]] (principal, v2.0 — pasos 0-4, nativa)
- [[UI - Interfaz Streamlit]] (legacy — pasos 0-4)

## Relacionado con
- [[Reportería]]
- [[streamlit]]
- [Patrones de UX](../../docs/ux-patterns.md)
