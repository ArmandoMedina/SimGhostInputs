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
- [[UI - Interfaz Streamlit]]

## Propósito funcional
Guiar al usuario a través del pipeline completo (cargar archivos, comparar, generar overlay, componer video) mediante una interfaz web paso a paso sin requerir el CLI. Existen dos implementaciones: la UI Streamlit legacy (`fantasma ui`) y la UI NiceGUI de v2.0 (`fantasma-ng`), interfaz principal desde el merge de v2.0.

## Actor principal
Usuario (piloto o ingeniero de datos) que abre la app con `fantasma ui` (Streamlit) o `fantasma-ng` (NiceGUI, principal en v2.0).

## Entradas funcionales
- Archivos de telemetría (referencia y piloto) cargados en el Paso 0.
- Parámetros de análisis seleccionados en cada paso.

## Salidas funcionales
- Resultados del análisis visibles en el navegador.
- Archivos generados (report.md, CSVs, PNG, video) en el directorio de salida.

## Reglas de negocio
- La aplicación Streamlit (`app.py`) debe inicializar sin excepción cuando streamlit está instalado.
- El router de pasos (`nav_step` en session_state) determina qué paso se renderiza.
- En NiceGUI, `main_page` (`ng_app.py`) sirve la página `/` y `navigate(step)` limpia y re-renderiza el contenido; el estado por sesión vive en `AppState` (`ng_state.py`), un proxy sobre `app.storage.user` que sustituye a `st.session_state`.
- En NiceGUI la barra lateral agrupa la navegación en «Principal» (Inicio, Importar, Análisis) y «Salidas» (Overlay, Video); `_step_done(state, i)` marca el progreso usando `flow_chosen`, `ref_lap`, `summary`, `last_overlay` y `last_compose_video`.
- Todo lo que hace la UI es equivalente a lo que ofrece el CLI.

## Criterios de aceptación
- Dado que streamlit está instalado, cuando se ejecuta `app.py` vía `AppTest`, entonces la aplicación inicializa sin lanzar ninguna excepción.
- Dado que no existe `flow_chosen` en session_state (sesión nueva), cuando se renderiza el sidebar, entonces el paso 0 no aparece marcado como completado (✅).
- Dado que `flow_chosen` existe en session_state y el usuario navega al paso 1, cuando se renderiza el sidebar, entonces el paso 0 aparece como completado (✅).
- Dado que `last_compose_video` existe en session_state, cuando se renderiza el sidebar, entonces el paso 4 aparece como completado (✅).
- Dado que el usuario pulsa «🔄 Nueva sesión» en el sidebar, cuando se procesa la acción, entonces el session_state se limpia y la app vuelve al paso 0.

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

## Fuera de alcance
- Front de escritorio custom: **implementado como NiceGUI v2.0** ([ADR 0018](../../docs/decisions/0018-framework-ui-nicegui.md), enmienda al [ADR 0010](../../docs/decisions/0010-framework-ui-streamlit.md)), empaquetado nativo con `native=True`.

## Verificación
### Streamlit (legacy)
- `tests/ui/test_app_smoke.py` · `test_app_starts_without_exception` — arranque sin excepción.
- `tests/ui/test_app_smoke.py` · `test_paso0_no_marcado_en_sesion_nueva` — B-01: `_step_done(0)` usa `flow_chosen`.
- `tests/ui/test_app_smoke.py` · `test_paso0_marcado_cuando_flow_chosen` — B-01: confirmación explícita marca el paso.
- `tests/ui/test_app_smoke.py` · `test_paso4_marcado_cuando_video_compuesto` — B-02: `_step_done(4)` usa `last_compose_video`.

### NiceGUI (v2.0)
- `tests/ui/test_ng_step0.py` · `test_step0_hero_visible`, `test_step0_flow_cards_visible`, `test_step0_question_label`, `test_step0_start_button_visible` — Paso 0 muestra el hero, las tres tarjetas de flujo y el botón «Empezar».
- `tests/ui/test_ng_step1.py` — Paso 1 (Importar).
- Cobertura de navegación entre pasos y `_step_done` en NiceGUI — **pendiente**.

## Relacionado con
- [[Interfaz de usuario]]

> **Nota:** El test `test_app_starts_without_exception` cubre únicamente que la app arranca; los criterios de los pasos individuales están en [[UI-02 - Avisos del motor visibles en la UI]].
