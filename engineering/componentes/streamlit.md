---
tipo: componente
tecnologia: Streamlit
administrador: proceso local del usuario (localhost)
estado: obsoleto
---

# Streamlit

> **Obsoleto (v2.0):** Streamlit fue retirado. Los archivos `ui/{app,step0-4,_helpers}.py` y los tests AppTest asociados han sido eliminados. La UI activa es [[nicegui]] (`fantasma-ng`). Ver [ADR 0018](../../docs/decisions/0018-framework-ui-nicegui.md) y [ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md).

## Propósito
Interfaz gráfica local (extra opcional `ui`). Es una **capa delgada sobre el CLI** ("CLI primero"): todo lo que hace la UI se puede hacer en terminal. Corre en localhost; los datos nunca salen de la máquina.

## Funciones clave
- Router en `fantasma/ui/app.py`; los pasos 0-4 en `step0.py`…`step4.py`; lógica compartida en `_helpers.py`.
- El "cerebro" (cálculos) vive en `core/`, que ya está testeado; la UI solo presenta. Por eso casi todo es testeable sin la UI ([ADR 0003](../../docs/decisions/0003-testing.md)).

## Datos que administra / procesa
- Estado de sesión de la UI (archivos cargados, selección de vueltas, offset de sync). Efímero, en memoria del proceso.

## Conectividad y protocolos
- HTTP local (Streamlit server). Retirado en v2.0; ya no se instala ni se lanza.

## Verificación
- Smoke de arranque (`AppTest`, Tier 4) + smoke visual de layout del Paso 0 (Playwright, [ADR 0012](../../docs/decisions/0012-playwright-smoke-visual-ui.md)). Lo subjetivo es checkpoint de Mariana ([ADR 0014](../../docs/decisions/0014-gate-ux-ui.md)).

## Decisión de fondo
- Streamlit en v1.0; evaluar front de escritorio custom diferido a v2.0 ([ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md)). Restricción heredada: mantener `core/` desacoplado de la UI.

## Relacionado con
- [[nicegui]] (sucesor, UI principal en v2.0)
- [[arquitectura]]
- [Patrones de UX](../../docs/ux-patterns.md)
