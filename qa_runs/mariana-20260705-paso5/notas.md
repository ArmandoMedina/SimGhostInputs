# Mariana — QA visual del PR 3 (Paso 5 + breadcrumbs) — 2026-07-06

**Harness:** `capture.py` (NiceGUI headless + Playwright, datos reales de Nordschleife).
Corrida final `07:49–07:52` en verde con **esperas deterministas** (el texto del aviso debe
aparecer, no un sleep). Corridas previas fallaron y eso destapó un bug real (abajo).

## Evidencia (10 capturas)

| # | Qué demuestra |
|---|---|
| 01–02 | Flujo "Solo Pace Notes" elegido; breadcrumb de **4 pasos** (Inicio › Importar › Análisis › Pace Notes) — sin Overlay/Video |
| 03–04 | Carga real de referencia+piloto; breadcrumb del flujo se mantiene en el Paso 2 |
| 05 | Paso 5 con breadcrumb correcto llegando por «🔔 Generar Pace Notes» (botón que antes NO navegaba — fix navigate/await) |
| 06 | **Leyenda de tonos** desplegada: 7 tonos con frecuencia y significado, brake 1000 Hz ≠ countdown 660-770-880, "~3.5 s antes" derivado del motor |
| 07 | Checkbox «Todas las curvas» marca → **Top N deshabilitado** (binding declarativo) |
| 08 | Caption bajo «Aplicar sonido»: "Falta: el video, la carpeta del pack." |
| 09 | Video con sidecar de OTRA vuelta → **⚠ amarillo**: "se compuso con una vuelta de 8:20.00 (otra_carrera.csv); la cargada dura 6:34.05. El mux se negará" (laptimes con `_fmt_lap`) |
| 10 | Video con sidecar correcto → **✓ verde** "Video verificado" y botón «Aplicar sonido» habilitado |

## Bug real destapado por esta captura

Las 3 primeras corridas fallaron porque el aviso del sidecar iba "una acción atrás": los
refreshes cableados a `.on("update:model-value")` corren ANTES de que NiceGUI asigne
`element.value`, así que leían el valor anterior. Afectaba también al botón «Componer
video» del Paso 4 y a la vista previa del HUD (pre-existentes). Corregido migrando todo a
`on_value_change`; regla asentada en `docs/ux-patterns.md`. La corrida final en verde con
esperas deterministas es la prueba de la corrección.

## Checkpoint (vuelve al PO)

Lo determinista está verde. Juicio pendiente del PO: ¿la leyenda se entiende?, ¿el texto del
aviso ⚠ es claro?, ¿el flujo de 4 pasos se siente correcto? (revisar las capturas o el app).
