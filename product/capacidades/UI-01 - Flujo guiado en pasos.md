---
tipo: capacidad
clave: UI-01
modulo: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# UI-01 - Flujo guiado en pasos

## Módulo
- [[UI - Interfaz NiceGUI]]

## Propósito funcional
Guiar al usuario a través del pipeline completo (cargar archivos, comparar, generar overlay, componer video) mediante una interfaz de escritorio nativa paso a paso sin requerir el CLI. La única implementación activa desde v2.0 es la UI NiceGUI (`fantasma-ng`).

## Actor principal
Usuario (piloto o ingeniero de datos) que abre la app con `fantasma-ng` (NiceGUI, ventana nativa).

## Entradas funcionales
- Archivos de telemetría (referencia y piloto) cargados en el Paso 0.
- Parámetros de análisis seleccionados en cada paso.

## Salidas funcionales
- Resultados del análisis visibles en el navegador.
- Archivos generados (report.md, CSVs, PNG, video) en el directorio de salida.

## Reglas de negocio
- `main_page` (`ng_app.py`) sirve la página `/` y `navigate(step)` limpia y re-renderiza el contenido; el estado por sesión vive en `AppState` (`ng_state.py`), un proxy sobre `app.storage.user`.
- La barra lateral agrupa la navegación en «Principal» (Inicio, Importar, Análisis) y «Salidas» (Overlay, Video, Pace Notes); `_step_done(state, i)` marca el progreso usando `flow_chosen`, `ref_lap`, `summary`, `last_overlay`, `last_compose_video` y `last_pacenotes`.
- Todo lo que hace la UI es equivalente a lo que ofrece el CLI.

## Criterios de aceptación
- Dado que no existe `flow_chosen` en AppState (sesión nueva), cuando se renderiza el sidebar, entonces el paso 0 no aparece marcado como completado (✅).
- Dado que `flow_chosen` existe en AppState y el usuario navega al paso 1, cuando se renderiza el sidebar, entonces el paso 0 aparece como completado (✅).
- Dado que `last_compose_video` existe en AppState, cuando se renderiza el sidebar, entonces el paso 4 aparece como completado (✅).
- Dado que el usuario pulsa «🔄 Nueva sesión» en el sidebar, cuando se procesa la acción, entonces el AppState se limpia y la app vuelve al paso 0.

### Interfaz NiceGUI (`fantasma-ng`, v2.0)
- Dado que el usuario abre la interfaz NiceGUI (`fantasma-ng`), cuando la app carga (`main_page` en `/`), entonces se muestra el selector de flujo (Paso 0) con las tres opciones disponibles («Solo análisis», «Solo overlay», «Video con HUD»).
- Dado que el usuario está en cualquier paso, cuando usa la barra lateral (secciones «Principal» y «Salidas»), entonces puede navegar entre Inicio, Importar, Análisis, Overlay y Video y `navigate()` re-renderiza el contenido sin recargar la página.
- Dado que el usuario elige un flujo y pulsa «Empezar → Ir a Importar», cuando se procesa la acción, entonces `state.flow_chosen` pasa a True y la app navega al Paso 1.
- Dado que el estado de sesión vive en `AppState` (`app.storage.user`, sucesor de `st.session_state`), cuando `_step_done(state, i)` evalúa el progreso, entonces se apoya en `flow_chosen`, `ref_lap`, `summary`, `last_overlay` y `last_compose_video`.
- Dado que ninguna opción de flujo debe aparecer pre-seleccionada al cargar la app, cuando el usuario todavía no ha hecho clic, entonces el Paso 0 no debe marcar ningún flujo como «✓ Seleccionado» (criterio **pendiente**: hoy el flujo por defecto se muestra seleccionado — corrección F-01 registrada en `docs/ux-patterns.md`).

## Dependencias funcionales
- [[IMP-MTC-01 - Importar CSV de MoTeC i2]]
- [[IMP-GEN-01 - Importar CSV genérico con mapeo]]
- [[NRM-03 - Remuestrear por distancia]]
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[UI-04 - Generar pace notes desde la UI]]

## Fuera de alcance
- Front de escritorio custom: **implementado como NiceGUI v2.0** ([ADR 0018](../../docs/decisions/0018-framework-ui-nicegui.md), enmienda al [ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md)), empaquetado nativo con `native=True`.

## Verificación
- `tests/ui/test_ng_step0.py` · `test_step0_hero_visible`, `test_step0_flow_cards_visible`, `test_step0_question_label`, `test_step0_start_button_visible` — Paso 0 muestra el hero, las tres tarjetas de flujo y el botón «Empezar».
- `tests/ui/test_ng_step1.py` — Paso 1 (Importar).
- Cobertura de navegación entre pasos y `_step_done` en NiceGUI — **pendiente**.

## Relacionado con
- [[Interfaz de usuario]]

> **Nota:** Los criterios de los pasos individuales están en [[UI-02 - Avisos del motor visibles en la UI]].
