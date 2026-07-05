# ADR 0021 — Flujo "Solo Pace Notes"

- **Estado:** Aceptada
- **Fecha:** 2026-07-05
- **Autor:** Armando Medina
- **Relacionada con:** [ADR 0002](0002-crewchief-pacenotes.md), [ADR 0014](0014-gate-ux-ui.md)

## Contexto

La UI NiceGUI tiene un wizard de 6 pasos (0-5). El Paso 5 (Pace Notes) está
implementado y funcional desde v2.0, pero ninguno de los tres flujos de `_FLOWS`
lo incluye en su secuencia:

- `analisis` → Paso 1 → Paso 2 (análisis solo, sin salidas audiovisuales)
- `overlay`  → Paso 1 → Paso 2 → Paso 3 (overlay sin video)
- `compose`  → Paso 1 → Paso 2 → Paso 3 → Paso 4 (overlay + video compuesto)

El flujo por defecto (`compose`) arranca en el Paso 3 (overlay), de modo que
quien solo quiere pace notes se ve arrastrado a generar un overlay que no
necesita. Alcanzar el Paso 5 requiere picar el enlace del sidebar o el botón
🔔 del Paso 2, ambos invisibles para un usuario nuevo.

El PO reportó el caso real: "tengo un video con overlay ya hecho y solo quiero
ponerle pace notes". El Paso 5 era, en la práctica, un paso huérfano.

Hay además un defecto de guard en el propio Paso 5: el panel "Aplicar sonido
a video existente" (panel derecho, mux standalone) se ocultaba cuando no había
flujo que llegara hasta ese paso, en vez de mostrarse siempre que el paso fuera
accesible.

## Decisión

1. **Nuevo flujo `solo_pacenotes`**: tarjeta en el Paso 0 (selector de flujo)
   con ruta Importar(1) → Análisis(2) → Pace Notes(5). Los Pasos 3 y 4
   (overlay y compose) se saltan.

2. **Corrección del guard del Paso 5**: el panel "Aplicar sonido a video
   existente" se muestra siempre que el paso sea accesible, sin depender de
   que el flujo activo sea `compose`.

3. **Guía y tooltips en el Paso 5**: indicaciones contextuales que explican
   qué CSV cargar y por qué se necesitan dos vueltas.

El cambio es **aditivo**: los flujos `analisis`, `overlay` y `compose` no se
modifican ni en ruta ni en comportamiento.

## Razones

- **La fricción es real y evitable.** El caso "tengo overlay; solo quiero pace
  notes" es un flujo legítimo al que no hay ruta directa. Añadir la tarjeta
  elimina la fricción sin tocar lo que ya funciona.

- **No se puede simplificar el flujo más allá de 3 pasos.** Las pace notes se
  derivan de COMPARAR DOS VUELTAS: la selección y prioridad de qué curvas
  suenan usa `time_lost` y los deltas de velocidad que solo produce
  `compare()` (`core/compare.py`, filtro `time_lost > 0` en
  `viz/pacenotes.py`). El Paso 2 (análisis) es donde corre ese compare.
  Saltárselo produciría un pack con 0 notas. Los Pasos 1 y 2 son obligatorios;
  los Pasos 3 y 4 (overlay y video) no lo son.

- **Reutilizar los pasos existentes es correcto por DRY.** El import y el
  análisis ya tienen su UX completa, sus guards y su manejo de estado. Añadir
  una copia dentro del Paso 5 sería duplicar esa maquinaria.

## El camino que NO se toma (y por qué tienta)

- **Dejar el Paso 5 huérfano (status quo).** Tienta porque "ya existe un
  botón en el Paso 2 y un enlace en el sidebar". Se descarta: la fricción fue
  reportada con un caso real — los puntos de acceso existentes son invisibles
  para un usuario nuevo y no reflejan que "pace notes" es un destino de
  primera clase.

- **CSV único en el Paso 5 (idea inicial del PO).** Tienta porque simplifica
  la UX al máximo: un solo archivo, un solo paso. Se descarta: con una sola
  vuelta `compare()` no tiene referencia contra la que medir `time_lost`, el
  pack sale con 0 entradas. Requerirla cambia la definición del producto.

- **Mini-import (2 CSVs + compare) embebido en el Paso 5.** Tienta porque
  encapsula todo el flujo en un único paso sin pasar por el wizard previo. Se
  descarta: duplicaría la maquinaria completa de los Pasos 1 y 2 — carga de
  archivos, detección de vuelta rápida, rendering del resumen — en contra de
  DRY y del dolor declarado como priority-1 del repo.

- **Pace notes de una sola vuelta: top-N curvas por severidad geométrica.**
  Tienta como "simplificación del producto": sin referencia, se priorizan las
  curvas más lentas en valor absoluto. Se descarta en el alcance de este ADR:
  cambia qué es una pace note (deja de ser "dónde pierdes tiempo respecto a
  tu referencia") y convierte este arreglo de fricción de flujo en una feature
  de producto nueva. Queda anotada como posible evolución futura.

## Consecuencias

- **Se gana:** el usuario que solo quiere pace notes tiene un flujo directo y
  visible desde el Paso 0. El panel de mux standalone del Paso 5 deja de
  ocultarse por error de guard. Los tooltips reducen la curva de aprendizaje
  del paso.

- **Se pierde / costo:** un cuarto flujo en `_FLOWS` que mantener; la tarjeta
  del Paso 0 suma una opción más (4 tarjetas en vez de 3). Riesgo menor: si en
  el futuro se añaden pace notes de vuelta única (alternativa descartada
  arriba), ese flujo futuro ya no converge con este.

- **Validación pendiente (Mariana):** la nueva tarjeta del Paso 0 y la guía
  del Paso 5 deben pasar el gate visual ([ADR 0014](0014-gate-ux-ui.md)) antes
  de considerarse cerradas.
