# Evidencia e2e — recorrido "Solo Pace Notes" 0→1→2→5

> Cierra el punto (b) que quedó **parcialmente verificado** en `notas.md` de Mariana: el
> recorrido completo con CSVs reales, no solo el salto al Paso 5 vía sidebar. Ejecutado en
> sesión por Mau (a petición del PO) con Playwright headless contra `fantasma.ui.ng_app`.

## Datos usados (material real)
- **Referencia:** `GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv` (6:18.40, 3 vueltas).
- **Piloto:** `GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv`.
- Misma pista (Nordschleife 2025), comparación válida.

## Recorrido verificado (todo OK)
1. Paso 0 → tarjeta **"Solo Pace Notes"** seleccionada → "Empezar → Ir a Importar".
2. Paso 1 → subir referencia + piloto → "Cargar y ver análisis →".
3. Paso 2 → `compare()` corrió (tabla, delta bar, gg, summary) → apareció el botón
   **"Ir al Paso 5 — Pace Notes →"**.
4. Click → **Paso 5 alcanzado** con breadcrumb ✓ Inicio · ✓ Importar · ✓ Análisis.
5. Paso 5: **ambos paneles visibles**, caption puente ①→②, directorio de CrewChief
   autocompletado, botón "Aplicar sonido" **atenuado** (disabled, faltan video/pack — fix OK).
6. **Sin errores JS de página.**

Capturas: `05_paso2_analisis.png`, `06_paso5.png` (y `04_paso1_cargado.png`).

## Hallazgo (baja prioridad)
Subir los **dos CSV casi simultáneos** (~500 ms de diferencia, programático) hizo que el
segundo `on_upload` se perdiera mientras el primero (MoTeC grande) aún se procesaba: la
referencia cargó pero "Tu vuelta de hoy" quedó vacía. Con subida **secuencial** (esperar la
confirmación de la referencia antes de subir el piloto) funcionó a la primera. Un usuario real
sube secuencialmente, así que es un borde raro; anotado como deuda en ROADMAP/HANDOFF.

## Veredicto
Recorrido 0→1→2→5 **APROBADO** — el "Ir al Paso 5" y el flujo completo funcionan con datos reales.
