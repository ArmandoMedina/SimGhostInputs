# ADR 0031 — Propiedad de la frenada y contrato de `segment_m` (enmienda a ADR 0025, 0026 y 0028)

- **Estado:** Aceptada
- **Fecha:** 2026-07-09

## Contexto

El motor de curvas (`fantasma/core/corners.py`) publica para cada curva un `segment_m = [lo, hi]`.
Para toda curva que no es la primera, `lo = max((apex_prev + ad) / 2, ad - 450)` — el punto medio
entre el ápex de la vecina anterior y el propio, con un tope de look-back de 450 m
(`corners.py:169-171`). Históricamente **todos** los hitos (`brake_start`, `turn_in`,
`brake_release`, `coast_*`) se buscaban DENTRO de ese segmento: `segment_m` funcionaba como
**contrato de contención** —"los hitos de esta curva caen entre `lo` y `hi`"— y los consumidores
lo daban por bueno.

Esta rama (`fix/pacenotes-frenada-y-countdown`) rompió ese contrato **a propósito**, y con razón.
Cuando la curva anterior es un **kink** (curva rápida sin frenada), el punto medio entre ápices cae
DESPUÉS de que la frenada real de la curva siguiente ya empezó, y el detector anclaba el
`brake_start` decenas de metros tarde. El PO lo detectó de oído en cuatro frenadas reales del
Nordschleife (metros 721, 1042, 3541, 20065) y dijo, textualmente, que con eso "vas a matar al
piloto". Se introdujo una segunda ventana solo para buscar la frenada,
`brake_lo = max(apex_prev, ad - 450)` (`corners.py:187`), que arranca justo tras el ápex de la
vecina previa en vez de en el punto medio.

Resultado: existen ahora **dos** nociones de "dónde empieza la curva", y `brake_start` puede caer
FUERA del `segment_m` que la propia curva declara suyo. Magnitud medida sobre la vuelta de
referencia real (BMW M4 GT3 Nordschleife, 55 curvas; `qa_runs/2026-07-09-revalidacion-corners/`,
`tabla6_invariante_segment_m_C.csv`): **7 curvas violan la invariante, con desfase máximo de 64 m**
(C54: `brake_start=20065` vs `segment_m[0]=20129`; le siguen C12 con 29 m, C14 con 26 m, C15 con
13 m). El propio docstring de `extract_milestones` ya declara la invariante rota como aceptada
(`corners.py:150-154`), pero sin decidir qué hacen los consumidores con ella.

**Consecuencias reales sobre los consumidores de `segment_m`** (cada una verificada contra el
código actual, HEAD `6908d7d`):

- `fantasma/core/compare.py:322` (`_corner_metrics`) acota los datos del piloto a `segment_m` SIN
  margen, mientras el hito de la referencia sale de la ventana ancha. El resultado es un `d_brake_m`
  asimétrico (`compare.py:391`) que puede levantar una bandera de coaching `"frenada"` espuria
  (tolerancia 15 m, `compare.py:407`). **Se está arreglando en paralelo con un helper compartido**
  (fuera del alcance de este ADR).
- `fantasma/viz/overlay.py:115` (`_corner_at`) elige la curva "actual" del HUD con
  `lo <= dist <= hi` sobre `segment_m`. Durante la frenada extendida, el HUD etiqueta la curva
  ANTERIOR mientras el pace note ya pertenece a la SIGUIENTE: el video dice una cosa y la pantalla
  otra durante cientos de metros. **NO está arreglado.**
- `fantasma/viz/charts.py:53-54` (`plot_corner`) recorta la traza al segmento con un padding FIJO
  de 120 m (`pad_m=120`). Si el desfase superara los 120 m, la gráfica truncaría el inicio de la
  frenada en silencio. Hoy el desfase máximo medido es 64 m (< 120), así que **no trunca todavía**,
  pero la defensa es incidental: depende de que ninguna curva pase de 120 m, no de una regla.
  Contrasta con `charts.py:374-377`, que sí deriva su ventana del hito (`min(ref_bd, drv_bd) - 80`)
  y por eso es inmune por diseño. **NO está arreglado.**
- En `corners.py`, al buscar `turn_in` solo dentro del segmento se perdía un turn-in legítimo: C14,
  cuyo volante cruza el umbral de 8° en ~4845 m, entre `brake_start=4824` y `segment_m[0]=4850`
  (`tabla2_turn_in.csv`). **Ya arreglado**: la búsqueda de `turn_in` arranca ahora en `brake_start`,
  no en `segment_m[0]` (`corners.py:259-272`). El arreglo es una CONSECUENCIA directa de haber roto
  la invariante, no una casualidad.

### El criterio de producto que manda sobre todo esto

Dicho por el PO, y que gobierna la semántica de la frenada: **todos los sonidos se generan de la
vuelta de REFERENCIA**, para que el piloto haga imaginería mental con el video y, al llegar a pista
con CrewChief, los sonidos le resulten familiares y adopte los puntos de frenada correctos. **El cue
de frenada es el que evita que el piloto se pase y se mate; su función es llevar el pedal al máximo
freno aprovechando la transferencia de peso** (regla registrada en `ROADMAP.md` y en el
[ADR 0030](0030-modos-estudio-en-vivo-que-ancla-cada-cue.md)). De ahí que "dónde empieza la frenada"
no sea una cuestión geométrica sino perceptiva: el cue debe sonar donde el piloto empieza a cargar
el pedal hacia el máximo.

## Decisión

Se fijan tres cosas que hasta hoy vivían solo en el código o en un docstring, sin decisión escrita.

### 1. `segment_m` deja de ser contrato de contención (Opción A)

`segment_m` es una **banda aproximada de vecindad del V-Min**, útil para agregar métricas de zona
(V-Min del piloto, slip, conteo de ABS). **NO garantiza que los hitos de la curva caigan dentro de
ella.** La verdad autoritativa de "dónde ocurre cada cosa" son los **hitos** (`brake_start`,
`turn_in`, `apex`, …). Todo consumidor que necesite la ventana de frenada debe derivarla del hito
`brake_start`, no de `segment_m[0]`. Queda pendiente auditar y arreglar `overlay.py` y `charts.py`
bajo esta regla (registrado como deuda en `ROADMAP.md`).

### 2. Regla de propiedad de la frenada

**Cada curva es dueña de toda fase de frenada posterior al ápex de su vecina previa.** La frontera
de propiedad es el ápex anterior (`brake_lo = max(apex_prev, ad - 450)`, `corners.py:187`): nada
antes de ese ápex se le atribuye a la curva (no se roba la frenada de la vecina), y un kink sin
frenada nunca absorbe la frenada de la curva siguiente (esa frenada cae DESPUÉS del ápex del kink).

**Límite conocido, escrito aquí para que nadie lo redescubra a golpes:** el trail-braking real se
extiende PASADO el ápex, así que el arrastre de freno de la curva anterior cae, en metros, dentro de
la ventana de la siguiente. Hoy eso no contamina el `brake_start` de la siguiente porque el filtro
de intensidad lo descarta (el arrastre viene SOLTANDO freno y no vuelve a alcanzar `brake_strong`).
Eso es una **defensa incidental, no una decisión**: si algún día se baja `brake_strong` o se cambia
el criterio de selección de fase, el arrastre de la vecina podría colarse como inicio de frenada de
la siguiente. La propiedad "por ápex previo" acota el metro; la limpieza fina la hace el filtro de
intensidad, y ambos deben moverse con conciencia el uno del otro.

### 3. Semántica de `brake_start` (qué muestra es el punto de frenada)

Los puntos con `brake > brake_on` (10) se agrupan en bloques y los bloques se funden en **FASES**:
dos bloques consecutivos separados por menos de `phase_gap_s` (0.5 s) se funden **si el coche sigue
desacelerando** en el hueco (una suelta breve para rotar, no una acción distinta). El piso
`brake_strong` (50) es un **FILTRO**: descarta las fases que no lo alcanzan. Entre las fases que
sobreviven al filtro, **`brake_start` ancla en la primera muestra de la fase de PICO MÁXIMO**; ante
empate de pico, la más tardía (la que entra al ápex). Si ninguna fase alcanza el piso, la última
fase cronológica (`corners.py:221-227`).

**Por qué "pico máximo" y no "la última fuerte":** una fase temprana al 100 % seguida de otra al
90 % es UNA sola frenada que el piloto modula, no dos frenazos; el cue debe sonar cuando empieza a
cargar el pedal hacia el máximo, no a mitad. Elegir "la última que supera el piso" rompía C05 sobre
la vuelta real —lo movía de 1042 (el primer frenazo duro, el que el PO considera correcto) a 1117,
**75 m tarde**— porque C05 tiene dos fases fuertes seguidas (100 % en 1042, 90 % en 1117) y ambas
superan el piso (`qa_runs/2026-07-09-revalidacion-corners/diagnostico.md`, Tabla 1; commit `534fdae`
implementaba "la última fuerte" y el commit `6908d7d` lo corrigió a "pico máximo").

`brake_release`, en cambio, se ancla al final de la ÚLTIMA fase cronológica (no la ganadora), para
que una reaplicación suave posterior a la fase fuerte no adelante el release al hueco intermedio;
como consecuencia física esperada del trail-braking, el release puede caer pasado el ápex.

## Razones

- **La frenada pertenece a la curva que frena; esa es la verdad física.** El punto medio entre
  ápices es una heurística de reparto que falla exactamente cuando la vecina previa no frena (kink).
  Anclar `brake_start` a una ventana que arranca en el ápex previo respeta la física; forzarlo a
  vivir dentro de `segment_m` lo falsea. Entre "la geometría del segmento es sagrada" y "el metro de
  frenada es sagrado", manda el metro de frenada: es el cue que evita que el piloto se pase.
- **Elegir Opción A y no C (publicar `brake_window_m`) porque la ventana ya es recuperable del
  hito.** Un consumidor que quiere "dónde empieza la frenada" tiene ya `brake_start`; publicar además
  la ventana de detección interna (`brake_lo..ad`) duplica información y crea el problema de "¿qué
  campo uso?". Y no resuelve el fallo de fondo de `overlay.py`: qué curva "posee" un metro dado para
  etiquetar el HUD es una decisión de hitos (la curva es suya desde su `brake_start`), no de un
  segundo rango. C es explícito y no rompe nada, pero paga superficie sin cerrar el problema real.
- **Elegir A y no B (corregir `lo` solo en el caso del kink) porque B tiene blast radius amplio y
  pelea con la física.** B cambiaría el `segment_m` de muchas curvas y reabriría código de detección
  recién liberado, para reconstruir una invariante que la realidad no respeta: un kink genuinamente
  no frena, así que la frenada de la curva siguiente genuinamente empieza antes del punto medio.
  Detectar "¿la vecina previa es un kink sin frenada?" para mover `lo` es frágil; aceptar que los
  hitos mandan y `segment_m` solo aproxima es más simple y más verdadero.
- **"Pico máximo" es el criterio del PO traducido a algoritmo.** El cue marca dónde empezar a cargar
  el pedal hacia el máximo freno aprovechando la transferencia de peso. Cuando hay dos frenazos
  fuertes seguidos, el inicio de la carga hacia el máximo es el PRIMER pico alto, no el segundo. El
  dato C05 (1042 vs 1117) es la prueba medida de que "la última fuerte" contradice el criterio.
- **El filtro de intensidad y la propiedad por ápex previo son dos capas distintas.** La propiedad
  acota QUÉ metros mirar (desde el ápex previo); el filtro decide QUÉ fase cuenta como frenada de
  verdad. Escribir ambas evita que una sesión futura crea que basta con una.

## El camino que NO se toma (y por qué tienta)

- **Restaurar la invariante de contención "arreglando" `lo` (Opción B).** Tienta porque devuelve
  una sola noción de "dónde empieza la curva" y hace felices a los consumidores actuales sin
  tocarlos. Se descarta: cambia el `segment_m` de muchas curvas (blast radius amplio sobre datos que
  ya consume `compare`, `overlay`, `charts` y los tests), y sobre todo restaura una invariante que la
  física no sostiene cuando la vecina previa es un kink.
- **Publicar `brake_window_m` junto a `segment_m` (Opción C).** Tienta porque es aditivo y no rompe
  nada. Se descarta: la ventana de frenada ya está implícita en el hito `brake_start`; un segundo
  campo invita a bugs de "usé el campo equivocado" y no resuelve la ambigüedad de propiedad del HUD.
- **Anclar `brake_start` a "la última fase que supera el piso".** Es lo que haría quien lea "el punto
  de frenada es donde el piloto frena de verdad justo antes de la curva" sin pensar en el trail
  braking modulado. Se descarta con dato: rompía C05 (+75 m). La última fase fuerte es a menudo el
  reapoyo de freno a mitad de una frenada modulada, no su inicio.
- **Bajar `brake_strong` para "capturar más frenadas".** Tienta cuando una curva de frenada suave se
  queda sin cue. Se descarta aquí como advertencia acoplada a la regla de propiedad: bajar el piso
  reabre la puerta al arrastre de trail-braking de la curva ANTERIOR, que hoy queda descartado justo
  por ese piso (ver "límite conocido" arriba).

## Consecuencias

- **`segment_m` queda documentado como banda de vecindad, no como contención.** Gana: la frenada
  pertenece a la curva que frena; el motor deja de anclar `brake_start` tarde tras un kink. Pierde:
  los consumidores que asumían contención quedan expuestos y hay que auditarlos.
- **Deuda abierta, registrada en `ROADMAP.md`:** `overlay.py` (`_corner_at`, etiqueta la curva
  anterior durante la frenada extendida) y `charts.py` (`plot_corner`, padding fijo de 120 m que hoy
  no trunca porque el desfase máximo es 64 m, pero es una defensa incidental) deben derivar su
  ventana del hito, como ya hace `charts.py:374-377`. `compare.py` se arregla en paralelo con un
  helper compartido.
- **La regla de propiedad de la frenada tiene un límite conocido y escrito** (trail-braking pasado el
  ápex, hoy tapado por el filtro de intensidad). No es un bug abierto sobre la vuelta real medida,
  pero sí una restricción a respetar si se toca `brake_strong` o el criterio de selección de fase.
- **Enmienda a los [ADR 0025](0025-countdown-ancla-en-la-frenada.md),
  [ADR 0026](0026-cues-frenada-universal-countdown-oportunista.md) y
  [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md):** los tres anclan el
  tono de frenada y el countdown al "metro exacto de la frenada" (`brake_d` / `brake_start`; ver
  `0025` §Decisión, `0026:38`, `0028:197`) pero **tratan ese metro como un dato dado** — ninguno
  define QUÉ muestra es cuando la curva tiene varias fases de freno o cuando la vecina previa es un
  kink. Este ADR **consagra esa definición** (agrupación en fases, filtro `brake_strong`, selección
  por pico máximo, y la ventana ampliada que rompe la contención de `segment_m`). El "3 es el ya" y
  el anclaje del countdown en la frenada real de esos ADR **siguen vigentes sin cambio**: lo que este
  ADR fija es dónde está exactamente ese "ya".
- Pendiente de validar: el juicio de oído del PO sobre la cinta regenerada con `6908d7d` (C05 de
  vuelta en 1042, C14 con turn_in). La corrección del blast radius en `overlay.py`/`charts.py` es
  trabajo de código (Ahiram), no de este ADR.
