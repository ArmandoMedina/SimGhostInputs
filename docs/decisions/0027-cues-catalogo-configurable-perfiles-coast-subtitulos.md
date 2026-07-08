# ADR 0027 — Cues como catálogo configurable con prioridad, perfiles compartibles, coast y subtítulos quemados (enmienda a los ADR 0024, 0025 y 0026)

- **Estado:** Aceptada · enmendada por [ADR 0028](0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md) (2026-07-08)
- **Fecha:** 2026-07-08

> **Enmienda (ADR 0028):** el slot `gear` deja de estar "documentado pero sin implementar" —
> queda implementado, acotado a subtítulo (`sound=False`, sin audio todavía). El esquema de
> config de cue suma el campo `sound` junto a `enabled`/`priority`. Los valores por defecto de
> `DEFAULT_CONFIG` (prioridades) y `DEFAULT_FREQS` (frecuencias) cambian; el modelo de catálogo
> configurable, prioridad por cue y perfiles compartibles de este ADR **sigue vigente sin
> cambio**.

## Contexto

Con el modelo del [ADR 0026](0026-cues-frenada-universal-countdown-oportunista.md) en producción
(frenada protegida, countdown oportunista, fuera el tono de apex), el PO revisó una cinta de
estudio y reportó dos cosas que reencuadran el diseño de los cues:

1. **Borrar el apex fue demasiado destructivo.** El 0026 retiró el tono de apex de `PLAN_CUES`
   porque "no suma de oído". Pero eso lo apaga **para todos**: el PO reconoció que habrá pilotos
   que quieran *solo* apex + cambio de marcha, o *solo* coast. Lo correcto no es borrar un cue,
   es **apagarlo por defecto y dejar que el usuario lo prenda**. El set de cues debía dejar de ser
   una lista hardcodeada y pasar a ser un **catálogo configurable**.

2. **El "inicio de acelerador" caía en el metro equivocado (317 en vez de 393).** El milestone
   `throttle_on` se anclaba en el **primer** instante que el acelerador cruzaba 5%, **sin exigir
   que se sostuviera** (`fantasma/core/corners.py`). Un roce fugaz de pedal (freno-motor, ruido)
   en el metro ~317 ganaba, y la aceleración real y sostenida (~393) se ignoraba. Detrás había un
   hueco de modelado: la fase de **coast** (ni freno ni gas) no existía en `core/` — el motor
   asumía "fin de frenada → inicio de gas", sin nombrar el tramo de inercia entre medias.

Además, dos consecuencias de diseño que el PO pidió explícitamente:

- **La prioridad también es del usuario.** Cuando dos cues caen a menos de `min_gap_m`, la regla de
  cabida del 0024 tira al de menor prioridad — pero esas prioridades vivían **hardcodeadas** en
  `_corner_candidates` (p. ej. `throttle_on`=85). Si el usuario elige *qué* cues quiere, debe poder
  decidir *quién gana* cuando hay saturación. La prioridad por cue pasa a vivir en el perfil.
- **Los perfiles se comparten.** La configuración de cues no es preferencia privada de navegador:
  se exporta/importa como **JSON portable** para que la comunidad arme y comparta "packs" de cues,
  con el mismo espíritu que los *track packs* de `CONTRIBUTING.md` §7.

Por último, este release **absorbe la #32** (subtítulos de cues quemados en la cinta de estudio),
que estaba en una rama aparte y nunca llegó a `master` con ADR propio. Su ADR se consolida aquí.

## Decisión

Un solo release coherente (rama `feat/cues-configurables`, absorbe #29 y #32) con cinco piezas:

1. **Catálogo de cues configurable (`DEFAULT_CONFIG` en `pacenotes.py`).** Cada tipo de cue tiene
   `enabled` + `priority`. El `DEFAULT_CONFIG` reproduce **exactamente** el comportamiento del 0026
   (mismos tipos activos, mismas prioridades que antes vivían hardcodeadas → no-regresión). El
   **apex vuelve al catálogo, apagado por defecto** (reencuadra el 0026: el cue no se borra, se
   apaga). Se añade el cue **`coast`** (apagado, con flag `solo_sin_frenada`) y un **slot `gear`**
   documentado pero **sin implementar** (la detección de marcha es follow-up). La config se threadea
   por `build_pack → build_tone_pack → plan_tone_events → _corner_candidates`.

2. **Prioridad configurable en la cabida.** La prioridad de cada candidato sale de `cue_config`, no
   de un literal en `_corner_candidates`. Subir la prioridad de un cue cambia quién gana la colisión
   de gap. La **frenada protegida sigue siendo universal** (el 0026 no se toca en eso): ninguna
   config la puede tirar. El **countdown sigue oportunista** (opción acotada): se puede apagar y su
   prioridad es metadata, pero **no pelea por espacio en la cabida** — hacerlo pelear invertiría el
   diseño validado de oído del 0026; si el PO algún día quiere que el 3-2-1 desplace otros cues, es
   un cambio aparte y más riesgoso.

3. **Modelado del coast + fix del anclaje de `throttle_on` (`core/corners.py`).** `throttle_on`
   ahora exige **sostenibilidad** (umbral + N muestras sostenidas, el mismo patrón que ya usaba
   `full_throttle`): el roce del metro 317 deja de contar y el cue ancla en la aceleración real
   (~393). Se detecta la fase **coast** (`throttle < umbral` ∧ `brake < umbral` entre
   `brake_release`/`lift` y el `throttle_on` sostenido) y se emiten los milestones `coast_start` /
   `coast_end`. El cue de coast marca **una sola vez** en `coast_start` (el fin del hueco no es una
   acción del piloto).

4. **Formato de perfil compartible (`fantasma/viz/cue_profiles.py`).** Esquema JSON pequeño y
   versionado (`schema`, `version`, `name`, `description`, lista `cues` con `{type, enabled,
   priority, …}`), con `load`/`save`/`list` y **degradación con gracia** ante JSON malformado o de
   terceros (tipos desconocidos se ignoran, campos inválidos → `ValueError` acotado, nunca crashea
   el Paso 5). Carpeta-librería en `~/.simghostinputs/cue-profiles`, más import/export a ruta libre.

5. **Subtítulos de cues quemados + ventana adaptativa (absorbe #32).** `build_cue_ass` rotula cada
   cue del pack (etiqueta con color por tipo + nombre de curva) sincronizado con su tono, más una
   leyenda; `compose_video(..., burn_cue_subs=True)` lo quema en el mismo encode. El pack ya viene
   filtrado por `cue_config`, así que **solo se rotulan los cues habilitados** (coast incluido,
   etiqueta "inercia"). La **duración de cada rótulo es adaptativa**: dura hasta el siguiente cue
   (menos un respiro), acotada entre un mínimo legible y un máximo, en vez de la ventana fija de
   1.5 s de la #32 que apagaba el rótulo antes de tiempo.

Implementado en la rama `feat/cues-configurables`: WS-1 `5bc17f9`+`3215095` (motor: coast + fix
317/393), WS-2 `1d62758`+`229c93e` (catálogo + prioridad), WS-3 `d742513` (formato de perfil),
WS-4 `f947a9d`+`6a61ce5`+`39cefb6` (UI Paso 5), WS-5 `ef2d8cc` (subtítulos + ventana adaptativa).

## Razones

- **Apagar no es borrar.** El valor de un cue depende del piloto: quitarle a todos un sonido que a
  algunos les sirve es una decisión de producto que no le toca al motor. Un catálogo con default
  sensato da lo mejor de ambos: el 0026 sigue siendo el comportamiento de fábrica, pero deja de ser
  una jaula.
- **El 317/393 era un bug de fondo, no de subtítulo.** El subtítulo solo mostraba fielmente un metro
  equivocado. Arreglar el anclaje de `throttle_on` en el motor (sostenibilidad) y **nombrar el
  coast** cierra la causa raíz; el subtítulo se re-ancla solo. Reusar el patrón de `full_throttle`
  evita inventar un umbral nuevo que calibrar.
- **Quien elige qué suena, elige qué gana.** Si el usuario arma su pack, la resolución de colisiones
  tiene que respetar su orden. Mantener la frenada protegida fuera de la cabida preserva la garantía
  de seguridad del 0026 sin congelar el resto.
- **Perfiles portables = comunidad.** Un JSON compartible convierte la configuración en un artefacto
  que se publica y se reusa, igual que los track packs. La degradación con gracia es requisito, no
  adorno: el Paso 5 va a cargar JSON de terceros y no puede caerse por uno mal armado.

## El camino que NO se toma (y por qué tienta)

- **Dejar el apex borrado (0026 tal cual).** Es lo más simple y ya estaba hecho, pero cierra la
  puerta a los packs "solo apex" que el PO quiere habilitar. El costo de reincorporarlo apagado es
  mínimo (una entrada en `DEFAULT_CONFIG`) y el beneficio es un modelo abierto.
- **Arreglar el 317 solo en el subtítulo (acortar/mover la ventana).** Tentador porque el síntoma se
  ve en el subtítulo, pero deja el tono sonando en el metro equivocado y el coast sin nombrar. Es
  tapar el defecto, no resolverlo.
- **Hacer que el countdown pelee por cabida como un cue más.** Coherente con "todo configurable",
  pero invierte el diseño oportunista del 0026 (el countdown cede espacio, no lo disputa) y con la
  prioridad 100 por defecto ganaría todas las colisiones, cambiando el comportamiento base. Se deja
  como metadata apagable; el cambio de fondo, si se pide, es otro ADR.
- **Persistir el perfil en `app.storage` del navegador.** Más barato que un formato de archivo, pero
  no se comparte ni sobrevive a un reinstall. El pedido explícito era "packs de comunidad" → archivo
  portable.
- **Implementar ya la detección de cambio de marcha.** Requiere leer el canal de marcha de la
  telemetría y decidir el umbral del cue; es una tarea propia. Se deja el slot en el catálogo y la
  detección como follow-up (prioridad mínima, pedido del PO).

## Consecuencias

- Se gana: el usuario elige en el Paso 5 qué cues suenan y con qué prioridad, con perfiles
  cargables/guardables/compartibles; el apex vuelve como opción; el tramo 317→393 ya no dice "inicio
  de acelerador" (es coast o silencio) y la aceleración ancla en el metro real; el subtítulo es
  visible durante su evento; la #32 llega a `master` con ADR.
- Se pierde / cuesta: más superficie de configuración que mantener (catálogo, perfiles, UI); el
  esquema de perfil es un contrato que versionar. Deudas anotadas al [ROADMAP](../../ROADMAP.md):
  (a) `throttle_on_window`/`full_throttle` cuentan en **muestras fijas**, no normalizadas por tasa de
  muestreo (mal a ≠50 Hz); (b) el coast no se emite si hay frenada sin `brake_release` (trail-braking
  al borde del segmento).
- **Enmienda al 0026:** el apex deja de estar borrado y vuelve al catálogo apagado; las prioridades
  de cue dejan de estar hardcodeadas. La frenada protegida y el countdown oportunista **siguen
  vigentes** — este ADR los preserva, no los revierte.
- **Enmienda al 0024/0025:** la prioridad que alimenta el gap global ahora es configurable por cue;
  la frenada protegida y el "el 3 es el ya" siguen en pie.
- Tests en `tests/core/` (317/393, coast), `tests/viz/test_pacenotes.py` (catálogo filtrable,
  default sin regresión, prioridad cambia la colisión, subtítulos + ventana adaptativa + coast),
  `tests/viz/test_cue_profiles.py` (round-trip, rechazo de JSON inválido) y `tests/ui/` (Paso 5).
