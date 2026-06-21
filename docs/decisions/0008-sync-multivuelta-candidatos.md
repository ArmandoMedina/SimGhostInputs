# ADR 0008 — Auto-sync para video multi-vuelta: candidatos + selección obligatoria del usuario

- **Estado:** Aceptada
- **Fecha:** 2026-06-21
- **Enmienda a:** [ADR 0001 — auto-detección del offset de sincronía](0001-sync-offset.md)

## Contexto

El `auto_sync` (ADR 0001) correlaciona el audio del motor del video contra la telemetría de
**una** vuelta y toma el pico de correlación. Funciona para videos de **una sola vuelta**.

En el QA real (2026-06-21, carrera de 9 vueltas en Nordschleife) se reprodujo el fallo que el
ADR 0001 ya anticipaba en §Limitaciones conocidas (la ventana de búsqueda era de ±300 s): la
vuelta rápida (la 5) empezaba a ~27 min del inicio del video, **fuera** de los ±300 s, así que
el sync pegó el HUD de la vuelta 5 sobre la **vuelta 1** del video — y lo hizo **en silencio**.

La causa de fondo es física: **el audio del motor no distingue una vuelta de otra** en el
mismo circuito/auto (suenan casi idénticas). Por eso la correlación produce **un pico por
vuelta**, todos de altura parecida. Ninguna ventana de búsqueda arregla eso: ampliarla solo
cambia el modo de fallo (de "siempre la vuelta 1" a "una vuelta impredecible" o "z bajo →
aborta"). Ver discusión en el chat del 2026-06-21.

## Decisión

Auto-sync en dos niveles:

1. **Buscar candidatos en todo el video, no en ±300 s.** Detectar *todos* los picos fuertes de
   la correlación (uno por vuelta), rankearlos por calidad (z) y quedarse con los mejores.
2. **Si los candidatos quedan parejos (ambiguo), no adivinar: el usuario elige.** Se le
   presentan los candidatos con su minuto en el video (`mm:ss`) y su calidad, y selecciona cuál
   es su vuelta. Si hay un único candidato claro, se usa automáticamente como antes.

**En la UI la selección es bloqueante:** ante ambigüedad, el flujo **no continúa** hasta que el
usuario elige una vuelta. No hay default silencioso.

## Razones

- El pico más alto **no** es fiable con vueltas idénticas: el ruido puede hacer que gane una
  vuelta equivocada. Detectar que hay *varios* candidatos parejos es la señal honesta de "no se
  puede decidir solo".
- Pegar mal **en silencio** es el peor resultado: el usuario obtiene un video desincronizado sin
  saber por qué. Un selector obligatorio convierte un fallo invisible en una decisión consciente.
- El sistema hace el trabajo pesado (encontrar y ubicar los candidatos en el video); el usuario
  solo confirma cuál — mucho menos fricción que pedirle el segundo exacto a mano.

## El camino que NO se toma (y por qué tienta)

- **Solo ampliar `_SEARCH_SEC` (quitar/subir el límite).** Tienta porque el ADR 0001 ya lo
  apuntaba y es de una línea. NO basta: con multi-vuelta hay varios picos parejos; ampliar la
  búsqueda hace que el `argmax` elija uno impredecible o que el z se desplome y aborte. No
  distingue vueltas. (Sí ayuda en el caso del ADR 0001: **una** vuelta con preámbulo largo.)
- **Confiar en "mejorar el método" para acertar siempre solo.** Tienta porque sería invisible
  para el usuario. NO se puede garantizar: el audio no contiene información para separar vueltas
  idénticas. El ranking sube la probabilidad de acierto, pero el fallback humano es el único
  ancla que nunca falla. Por eso el Nivel 2 es obligatorio, no opcional.
- **Dejar un default silencioso en la UI** ("ya elegí la #1 por ti, sigue"). NO: reintroduce el
  pegado-mal-en-silencio que motivó este ADR. La selección debe bloquear.

## Consecuencias

- `sync.py` expone `sync_candidates(video, lap)` → candidatos rankeados + flag `ambiguous`.
  `auto_sync` se mantiene (compat) como "toma el mejor candidato".
- CLI `compose`: si es ambiguo, lista los candidatos y pide elegir (o re-correr con `--offset`).
- UI Paso 4: selector bloqueante ante ambigüedad.
- **Honestidad sobre el Nivel 1:** el ranking usa la correlación existente (que ya pondera la
  forma completa de la vuelta); no hay una señal mágica nueva que separe vueltas idénticas. Si
  en la práctica el #1 no acierta seguido, el Nivel 2 cubre igual. A medir con más datos.
- **Pendiente:** validar la detección de pausa también sobre el offset elegido por el usuario
  (hoy se valida en el camino automático). Menor.
