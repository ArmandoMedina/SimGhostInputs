---
tipo: indice
estado: en_definicion
---

# Producto — el QUÉ y el PORQUÉ

Esta capa describe **comportamiento esperado**, no implementación. Sombrero de **Producto/PO** (Mau + el humano). El CÓMO vive en [`../engineering/`](../engineering/).

> El **norte** del producto (alcance dentro/fuera, nicho, principios, landscape) sigue siendo [`../PRODUCT_BRIEF.md`](../PRODUCT_BRIEF.md) — esta jerarquía lo **despliega** en piezas navegables, no lo duplica. El estado vivo y el camino a v1.0 viven en [`../ROADMAP.md`](../ROADMAP.md).

## Cómo se organiza el QUÉ

De lo más amplio a lo más concreto (jerarquía funcional):

```text
Ecosistema → Solución → Dominio → Módulo → Capacidad
```

- **Ecosistema** — el universo: `fantasma-inputs` (este repo) + `fantasma-live` (futuro, separado). → [`ecosistema/`](ecosistema/)
- **Solución** — los dos productos del repo: Análisis Post-Tanda y Overlay de Video (ver `PRODUCT_BRIEF §5`). → [`soluciones/`](soluciones/)
- **Dominio** — un área con reglas propias: importación, normalización/comparación, detección de curvas, visualización/HUD, sincronía, composición, UI, desgaste. → [`dominios/`](dominios/)
- **Módulo** — una pieza funcional dentro de un dominio, con clave `FAM-MOD`. → [`modulos/`](modulos/)
- **Capacidad** — la unidad atómica con criterios de aceptación, clave `FAM-MOD-NN`. → [`capacidades/`](capacidades/)
- **Requerimientos** — bandeja de entrada + `backlog.md` (lo diferido del ROADMAP). → [`requerimientos/`](requerimientos/)
- **Procesos** — flujos de punta a punta (el pipeline CSV→análisis→overlay→compose). → [`procesos/`](procesos/)

Cada nota lleva **estado** (`en_definicion`, `vigente`…) y **prioridad** (MoSCoW). El estado **modula el gate**: una capacidad `en_definicion` solo pide consistencia documental; una `vigente` ya espera su criterio como test.

## Criterios de aceptación (Gherkin)

Toda capacidad se prueba contra criterios en este formato — y el test ES el criterio, ejecutable (ver [`../engineering/pruebas.md`](../engineering/pruebas.md)):

```
Dado que <contexto>, cuando <acción>, entonces <resultado esperado>.
```

## Estructura física

Las notas se agrupan por tipo; las relaciones se tejen con `[[wikilinks]]`, no con anidamiento de carpetas (así Obsidian dibuja el grafo). Formatos para copiar en [`../templates/`](../templates/).

## Relacionado con
- [[arquitectura]]
- [[glosario]]
