---
tipo: capacidad
clave: UI-02
modulo: UI
dominio: Interfaz de usuario
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# UI-02 - Avisos del motor visibles en la UI

## Módulo
- [[UI - Interfaz Streamlit]]

## Propósito funcional
Asegurar que los avisos del motor de análisis (autos distintos, delta sospechoso, ffmpeg ausente) sean visibles en la interfaz, de modo que el usuario no interprete un resultado inválido como válido.

## Actor principal
Sistema (la UI detecta condiciones de aviso y las presenta al usuario en el paso correspondiente).

## Entradas funcionales
- `summary["avisos"]` del motor de comparación (Paso 2).
- Resultado de la detección de ffmpeg en el sistema (Paso 4).

## Salidas funcionales
- Widget `st.warning` visible en el Paso 2 cuando el summary contiene avisos (Streamlit).
- Widget `st.error` visible en el Paso 4 cuando ffmpeg no está instalado (Streamlit).
- En NiceGUI (`ng_step2.py`): etiqueta de advertencia (⚠, estilo amarillo) por cada aviso de `summary["avisos"]` al inicio del Paso 2.
- En NiceGUI (`ng_step4.py`): etiqueta de error con `color:var(--danger)` que menciona "ffmpeg" y su comando de instalación cuando ffmpeg no está en el PATH.

## Reglas de negocio
- Los avisos de autos distintos y delta sospechoso que llegan en el summary deben materializarse como `st.warning` en el Paso 2 (Streamlit) y como etiqueta de advertencia (⚠) en NiceGUI (`ng_step2.py` recorre `summary.get("avisos")`).
- Si ffmpeg no está en el PATH al cargar el Paso 4, se muestra un `st.error` (Streamlit) / etiqueta de error NiceGUI con el nombre "ffmpeg" y el comando de instalación para la plataforma del usuario (Windows `winget`, macOS `brew`, Linux `apt`), y el formulario de composición no se renderiza.
- Si no se detectaron curvas en la vuelta (`rows=[]`), el Paso 2 muestra un `st.info` con la instrucción de re-exportar incluyendo el canal de distancia (Streamlit); en NiceGUI el aviso de canal de distancia ausente se muestra en el Paso 1 (`_NO_DIST_MSG` en `ng_step1.py`) y la tabla del Paso 2 muestra «Sin datos de curvas» si `rows` está vacío.
- En ningún caso la ausencia de ffmpeg, curvas vacías o la presencia de avisos debe producir una excepción no capturada.

## Criterios de aceptación
- Dado que las vueltas comparadas tienen metadato `Vehicle` distinto, cuando se renderiza el Paso 2, entonces aparece al menos un widget de advertencia que menciona "autos distintos".
- Dado que ffmpeg no está instalado en el sistema, cuando se navega al Paso 4, entonces aparece un widget de error que menciona "ffmpeg".
- Dado que `rows=[]` en session_state al renderizar el Paso 2, cuando no se detectaron curvas, entonces aparece un widget informativo que menciona "curvas".

### Interfaz NiceGUI (`fantasma-ng`, v2.0)
- Dado que el usuario usa la interfaz NiceGUI (`fantasma-ng`) y las vueltas comparadas traen avisos en `summary["avisos"]` (autos distintos, delta sospechoso), cuando se renderiza el Paso 2 (`ng_step2.py`), entonces cada aviso aparece como una etiqueta de advertencia (⚠) al inicio del paso.
- Dado que el usuario usa la interfaz NiceGUI y ffmpeg no está instalado, cuando navega al Paso 4 (`ng_step4.py`), entonces aparece un mensaje de error que menciona "ffmpeg" con el comando de instalación de su plataforma y el resto del formulario de composición no se renderiza (`return` temprano).
- Dado que el usuario usa la interfaz NiceGUI y sube un CSV sin canal de distancia, cuando lo carga en el Paso 1, entonces se muestra el aviso `_NO_DIST_MSG` indicando que debe re-exportar desde MoTeC i2 con «Include Distance Data».

## Dependencias funcionales
- [[CMP-03 - Avisar de comparación inválida]]

## Fuera de alcance
- Avisos de calidad de auto-sync (visible en el Paso 3, no cubierto por los tests actuales).

## Verificación
### Streamlit (legacy)
- `tests/ui/test_step2_avisos.py` · `test_paso2_muestra_aviso_autos_distintos` — avisos del motor en Paso 2.
- `tests/ui/test_step2_avisos.py` · `test_paso2_aviso_cuando_no_hay_curvas` — F-10: estado vacío cuando `rows=[]`.
- `tests/ui/test_step4_ffmpeg.py` · `test_paso4_avisa_si_falta_ffmpeg` — aviso de ffmpeg ausente en Paso 4.

### NiceGUI (v2.0)
- `tests/ui/test_ng_step2.py` — avisos del motor de `summary["avisos"]` visibles en el Paso 2 NiceGUI — **pendiente de crear**.
- `tests/ui/test_ng_step4.py` — aviso de ffmpeg ausente en el Paso 4 NiceGUI — **pendiente de crear**.

## Relacionado con
- [[Interfaz de usuario]]
