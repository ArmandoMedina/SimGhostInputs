---
tipo: componente
tecnologia: NiceGUI
administrador: proceso local del usuario (ventana de escritorio nativa)
estado: vigente
version_minima: 3.14
dependencia: "[ui-ng]"
---

# NiceGUI

## Propósito
UI web v2.0 en ventana de escritorio nativa (pywebview). Es una **capa delgada sobre `fantasma/core/`**, igual que Streamlit lo era antes: todo el "cerebro" (cálculos) vive en `core/`, ya testeado, y la UI solo presenta. Entry point: `fantasma-ng`. Se empaqueta como instalador Windows doble-clic.

## Archivos clave
- `ng_app.py` — entry point NiceGUI v2.0 (router principal + CSS global).
- `ng_state.py` — `AppState`; estado per-connection en `app.storage.client`.
- `ng_step0.py`–`ng_step4.py` — los pasos del wizard (5 pasos, portados de Streamlit).
- `ng_helpers.py` — constantes, CSS vars y helpers compartidos.

## Estado / storage
- In-memory **per-connection** (`app.storage.client`). Sin persistencia a disco.
- Diferencia clave con Streamlit: **no hay `st.session_state`** — el estado es un proxy Python (`AppState`) sobre `app.storage.client`.

## Modo de entrega
- `native=True` — ventana pywebview embebida; el usuario no ve el browser.
- `native=False` solo en desarrollo / macOS / Linux.

## Verificación
- Fixture `user` de `nicegui.testing` (equivalente a `AppTest` de Streamlit).
- `pytest_plugins = ['nicegui.testing']` en `tests/ui/conftest.py`.

## Empaquetado
- `nicegui-pack` → `dist/SimGhostInputs/`.
- Inno Setup (`tools/installer.iss`) → instalador `.exe` doble-clic.

## Decisión de fondo
- NiceGUI como framework de UI, enmienda al ADR 0010 ([ADR 0018](../../docs/decisions/0018-framework-ui-nicegui.md)). Benchmark: [`benchmark-ui-framework.md`](../../docs/benchmark-ui-framework.md).

## Relacionado con
- [[streamlit]] (predecesor en legacy)
- [[arquitectura]]
