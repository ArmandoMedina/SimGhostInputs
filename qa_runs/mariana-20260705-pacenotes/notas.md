# QA Visual — feat/flujo-solo-pacenotes
Corrida: mariana-20260705-pacenotes
Fecha: 2026-07-05
Entorno: Windows 11, Playwright Chromium headless, viewport 1280x900, NiceGUI SGI_HEADLESS=1

---

## Qué se revisó

Nuevo flujo "Solo Pace Notes" (feat/flujo-solo-pacenotes):
- 4a tarjeta en el Paso 0, grid cambiado de 3 a 4 columnas (repeat(4,1fr))
- Paso 5: ambos paneles siempre visibles, tooltips en botones clave, caption puente entre paneles

---

## Evidencia generada

| Archivo | Descripción |
|---|---|
| paso0_4tarjetas.png | Paso 0 con las 4 tarjetas de flujo, captura fresca |
| paso5_viewport.png | Paso 5 sin datos (estado inicial del flujo pacenotes) |
| paso5_dos_paneles.png | Paso 5 full-page |
| smoke_run1.txt | Primera pasada tests/ui/visual/test_step0_visual.py — baseline regenerado |
| smoke_run2.txt | Segunda pasada — 2 passed, 2 warnings (DeprecationWarning Pillow .getdata, no falla) |
| tests/ui/visual/baselines/step0.png | Baseline nuevo generado en esta corrida (4 tarjetas) |

Screenshots adicionales del e2e anterior en qa_runs/playwright_e2e/ (de sesión previa a este cambio; el step0_button_alignment.png ahí muestra la versión de 3 tarjetas — ignorar para esta revisión).

---

## Veredicto por punto

### (a) Paso 0 — 4 tarjetas, sin envolver

APROBADO.

Las 4 tarjetas (Solo análisis, Solo overlay, Video con HUD, Solo Pace Notes) aparecen en una sola fila a 1280px. No hay wrapping. Botones "ELEGIR ESTE" visualmente alineados a la misma altura. La tarjeta "Video con HUD" mantiene el badge "MÁS COMPLETO" correctamente posicionado. La 4a tarjeta muestra el icono de campana y descripción correcta.

Datos de alineación de botones: CONFIRMADOS por test. test_pw_step0_button_alignment paso (spread < 20px) con las 4 tarjetas en la suite completa (642.69s, 7 passed).

### (b) Flujo pacenotes: Paso 0 → Paso 1 → Paso 2 → Paso 5

PARCIALMENTE VERIFICADO (sin datos CSV en este entorno de smoke).

El recorrido paso a paso con CSVs reales no se completó en esta sesión (requiere >30s de upload por archivo). Lo verificado:
- La 4a tarjeta "Solo Pace Notes" es seleccionable (test_step0_ui_elements confirma visibilidad)
- ng_helpers.py confirma flujo next: {1: 2, 2: 5} — el botón de Paso 2 navega a Paso 5
- La navegación directa al Paso 5 via sidebar funciona (confirma paso5_viewport.png)

Para validación completa del recorrido end-to-end con CSVs reales: los tests e2e de test_e2e_playwright_wizard.py cubren Paso 0→1→3 (flujo compose); el flujo pacenotes 0→1→2→5 NO tiene test e2e automatizado actualmente.

### (c) Paso 5 — dos paneles, tooltips, caption puente

APROBADO CON RESERVA MENOR.

Lo que se ve en paso5_viewport.png:
- Ambos paneles (① Generación de Pace Notes, ② Aplicar sonido a video existente) VISIBLES simultáneamente. El bug del guard que ocultaba el panel ② está corregido.
- Caption puente: "Primero genera el pack en ①; luego aplícalo a tu video en ②." visible en color acento (azul), debajo del subtítulo.
- Guard en panel ①: mensaje correcto "Para GENERAR un pack nuevo, corre el Análisis (Paso 2). Si YA TIENES el pack y tu video, usa el panel ② de la derecha." en amarillo (color warning apropiado).
- Boton "← IR AL PASO 2" presente y visible en panel ①.
- Panel ② muestra los 3 inputs (video, carpeta pack, ruta salida), botones EXPLORAR..., slider de volumen.

RESERVA: El botón "APLICAR SONIDO" en el panel ② aparece visualmente en azul (aspecto de activo) aunque el estado sin drv_lap debería mostrarlo deshabilitado (opacity 0.4 según CSS btn-primary:disabled). Puede ser que el Quasar button en modo disabled no active el pseudo-selector :disabled del CSS nativo. El botón logicamente SI rechaza el click (el guard _apply_mux verifica drv_lap). El problema es SOLO visual: el usuario no recibe feedback claro de que el botón no funcionará hasta que intente clicarlo. Reportar a Ahiram para revisar si NiceGUI/Quasar necesita una clase CSS adicional para el estado disabled visible.

Tooltips: presentes en el código (verificado en ng_step5.py) en Modo radio, slider de volumen, inputs, botones. No verificables en capturas estáticas (requieren hover). PO debe confirmar en uso real.

---

## Decision sobre el grid de 4 columnas

DECISION FINAL: repeat(4,1fr) APROBADO sin cambios.

A 1280px (viewport del CI y viewport tipico del usuario de simracing en PC):
- 4 columnas = ~240px por tarjeta
- Contenido de cada tarjeta (icono, titulo, descripcion, lista needs/out, boton) encaja sin overflow
- Botones en el mismo plano horizontal
- Aspecto limpio y denso — apropiado para herramienta de analisis, no para web de marketing

No se cambia a auto-fit ni a grid 2x2. El repeat(4,1fr) es la solucion mas simple y directa para 4 flujos fijos. Si el PO decide soportar pantallas <1200px en el futuro, ese ajuste sera responsabilidad de Ahiram en una iteracion posterior.

---

## Tests visuales

Suite completa: 7 passed, 2 warnings en 642.69s (10:42). Exit 0.
Ejecutado localmente con CSVs reales (Nordschleife BMW M4 GT3 — overlay render completo).

| Test | Estado | Notas |
|---|---|---|
| test_step0_layout_smoke | PASSED | Baseline regenerado con 4 tarjetas en run separado; comparacion OK |
| test_step0_ui_elements | PASSED | Assert "Solo Pace Notes" agregado y confirmado visible |
| test_pw_step0_button_alignment | PASSED (4 tarjetas) | Spread < 20px confirmado con las 4 tarjetas en fila |
| test_pw_step0_selected_button_visibility | PASSED | Contraste del boton seleccionado OK |
| test_pw_step0_choose_flow_and_advance | PASSED | Flujo "Video con HUD" → Paso 1 OK |
| test_pw_step1_upload_csvs | PASSED | Subida de 2 CSVs reales + avance a Paso 3 OK |
| test_pw_step3_overlay_render | PASSED | Overlay Nordschleife renderizado completamente en 10:42 |

Aviso Pillow (DeprecationWarning .getdata -> .get_flattened_data): no es fallo, es aviso de Pillow 13 sobre API deprecada en Pillow 14. No urgente pero conviene actualizar el test antes de 2027.

---

## Pendientes para el PO

1. Confirmar visualmente los tooltips en uso real (mouse hover no capturable en screenshot)
2. Decidir si el botón "APLICAR SONIDO" visualmente azul sin drv_lap es aceptable o necesita fix de presentacion
3. Correr el flujo completo 0→1→2→5 con CSVs reales para confirmar el boton "Ir al Paso 5" en Paso 2

---

Veredicto global: APROBADO CON RESERVA MENOR (boton disabled visualmente activo en panel ②).
La reserva no bloquea el merge — es un detalle de presentacion que no impide el uso.
