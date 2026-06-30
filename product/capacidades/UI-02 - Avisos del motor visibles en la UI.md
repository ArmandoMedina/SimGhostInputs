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
- Widget `st.warning` visible en el Paso 2 cuando el summary contiene avisos.
- Widget `st.error` visible en el Paso 4 cuando ffmpeg no está instalado.

## Reglas de negocio
- Los avisos de autos distintos y delta sospechoso que llegan en el summary deben materializarse como `st.warning` en el Paso 2.
- Si ffmpeg no está en el PATH al cargar el Paso 4, se muestra un `st.error` con el nombre "ffmpeg" y el comando de instalación para la plataforma del usuario (Windows/macOS/Linux), y el formulario de composición no se renderiza.
- Si no se detectaron curvas en la vuelta (`rows=[]`), el Paso 2 muestra un `st.info` con la instrucción de re-exportar incluyendo el canal de distancia.
- En ningún caso la ausencia de ffmpeg, curvas vacías o la presencia de avisos debe producir una excepción no capturada.

## Criterios de aceptación
- Dado que las vueltas comparadas tienen metadato `Vehicle` distinto, cuando se renderiza el Paso 2, entonces aparece al menos un widget de advertencia que menciona "autos distintos".
- Dado que ffmpeg no está instalado en el sistema, cuando se navega al Paso 4, entonces aparece un widget de error que menciona "ffmpeg".
- Dado que `rows=[]` en session_state al renderizar el Paso 2, cuando no se detectaron curvas, entonces aparece un widget informativo que menciona "curvas".

## Dependencias funcionales
- [[CMP-03 - Avisar de comparación inválida]]

## Fuera de alcance
- Avisos de calidad de auto-sync (visible en el Paso 3, no cubierto por los tests actuales).

## Verificación
- `tests/ui/test_step2_avisos.py` · `test_paso2_muestra_aviso_autos_distintos` — avisos del motor en Paso 2.
- `tests/ui/test_step2_avisos.py` · `test_paso2_aviso_cuando_no_hay_curvas` — F-10: estado vacío cuando `rows=[]`.
- `tests/ui/test_step4_ffmpeg.py` · `test_paso4_avisa_si_falta_ffmpeg` — aviso de ffmpeg ausente en Paso 4.

## Relacionado con
- [[Interfaz de usuario]]
