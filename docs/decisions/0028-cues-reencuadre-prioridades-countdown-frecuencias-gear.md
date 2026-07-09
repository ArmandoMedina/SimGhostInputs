# ADR 0028 — Reencuadre de prioridades, countdown uniforme, frecuencias y cue `gear` solo-subtítulo (enmienda a los ADR 0025 y 0027)

- **Estado:** Aceptada · enmendada el mismo día (ver abajo) y por [ADR 0032](0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md) (2026-07-09)
- **Fecha:** 2026-07-08

> **Enmienda (mismo día, 2026-07-08, post-QA de esta misma cinta):** el punto 4 de "Cambio de
> marcha" más abajo quedó mal — `gear` **no** debe participar en la resolución global de
> cabida/prioridad junto con cues de audio. Al regenerar la cinta con `gear` habilitado, los
> ~110 cambios de marcha de la vuelta (mudos, prioridad 75) desplazaron por completo los eventos
> `coast` (prioridad 20) en zonas sin ninguna relación con un cambio de marcha — un cue sin WAV no
> tiene por qué competir por "cabida de audio". Fix real: `plan_tone_events` resuelve el gap
> mínimo en dos grupos independientes (sonoros vs. mudos, según el campo `sound` ya resuelto) y
> los recombina después; `brake` (protegido) siempre cuenta como sonoro para este corte pase lo
> que pase con su `sound` resuelto. El mismo corte se aplicó al timeline del countdown de frenada
> (`brake_tic`), que tenía el mismo bug un choke-point más abajo. Detalle técnico y ejemplo en
> `docs/formato-datos.md` (sección "Cambios de marcha"). El resto de este ADR (prioridades,
> countdown uniforme, frecuencias, `gear` acotado a subtítulo) sigue vigente sin cambio.

> **Enmienda (2026-07-09) — deuda de `detect_gear_shifts` evaluada y cerrada, no se extrae.** La
> línea 144-150 de abajo dejaba anotada la deuda de reusar el patrón de "ventana sostenida" de
> `throttle_on`/`full_throttle` en `detect_gear_shifts`. Se reevaluó explícitamente al cerrar el
> ciclo de deuda técnica del ROADMAP: la conclusión original de este ADR se **confirma y se
> cierra**, no se relanza. Los dos patrones no son intercambiables — `throttle_on`/`full_throttle`
> son un umbral continuo sostenido evaluado con ventana fija hacia adelante; `detect_gear_shifts`
> es una transición discreta entre enteros de marcha con debounce de confirmación — forzar un
> helper único por similitud superficial ("ambos sostienen una condición N muestras") arriesgaría
> tocar código de producción reciente (el cue `gear`, en release) sin beneficio funcional real,
> exactamente el antipatrón que este mismo ADR ya evitó al no ampliar el diff. Checkbox
> correspondiente en `ROADMAP.md` marcado como resuelto (evaluado, no código).

> **Enmienda ([ADR 0032](0032-regla-de-cabida-del-countdown-solo-cede-lo-que-puede-ceder.md),
> 2026-07-09):** el split sonoro/mudo de la timeline del `brake_tic` (enmienda del mismo día,
> arriba) sigue vigente, pero **dentro del pool sonoro** se corrige qué cuenta como espacio
> ocupado para un tic. Antes, cualquier cue sonoro cercano lo tumbaba; ahora solo lo bloquean las
> **frenadas protegidas** y los **tics de otras curvas**, y un cue sonoro no protegido (turn_in,
> throttle_on, full_throttle, brake_release) **cede su hueco al tic** (con rastro en `plan.json`).
> La invariante de seguridad no cambia: un tic nunca desplaza una frenada protegida. El resto de
> este ADR (prioridades, countdown uniforme, frecuencias, `gear` solo-subtítulo) sigue vigente.

## Contexto

Con el catálogo configurable del [ADR 0027](0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md)
en producción (PR #35), el PO vio la cinta de estudio `2_estudio_coast_ADR0027.mp4` y reportó, con
dato concreto, cinco problemas de la mezcla de audio/subtítulos más un tema de overlay:

1. **Contador de frenada muy lento y a veces no completa los 3 sonidos.** El diseño vigente
   (`DEFAULT_COUNTDOWN_S = 3.5`, [ADR 0025](0025-countdown-ancla-en-la-frenada.md)) reparte el
   anticipo en fracciones (`COUNTDOWN_SCALE = (0.75, 0.875)`) sobre un anticipo total de 3.5 s, lo
   que da ~1.75 s por gap — perceptualmente arrastrado y, cerca del clamp, irregular.
2. **Metro 1745: cambio de marcha sin sonar ni subtitular.** No era un bug de prioridad ni de
   cabida — el cue `gear` seguía siendo el slot reservado y sin implementar que el ADR 0027 dejó
   como follow-up explícito.
3. **Overlay demasiado grande, tapa el video.** No es cambio de código: el control ya existe
   (`ng_step4.py:425`, slider 0.25×-1.5×, default 1.0×); se resuelve usando 0.5× al renderizar la
   próxima cinta, no toca este ADR.
4. **Muchas curvas sin `turn_in`.** Sospecha de prioridad: `turn_in` vivía con prioridad 60,
   compitiendo en desventaja contra `throttle_on` (85) y `full_throttle` (75).
5. **Los sonidos se parecen demasiado**, con un dato exacto: el primer tic del countdown sonaba a
   la misma frecuencia que `turn_in` (660 Hz ambos).
6. **Pedido de reordenar prioridades**: freno y gas arriba, `turn_in` en su propio escalón,
   countdown/soltar-freno/coast como oportunistas ("solo si cabe").

Todo esto corre sobre el mismo modelo del ADR 0027 (catálogo configurable, prioridad por cue,
frenada protegida universal) — este ADR no lo reabre, ajusta sus valores por defecto y cierra el
slot `gear` que quedó pendiente.

## Decisión

Cuatro cambios en `fantasma/viz/pacenotes.py` y uno nuevo en `fantasma/core/corners.py`, todos
confirmados por el PO vía `AskUserQuestion`:

1. **Nueva tabla de prioridades en `DEFAULT_CONFIG`**: `brake=100` (protegido, sin cambio),
   `throttle_on=95`, `full_throttle=90`, `turn_in=70`, `brake_countdown=50`, `brake_release=45`,
   `coast=20`. `gear` entra con `priority=75` (entre `full_throttle` y `turn_in`). `apex` queda
   igual (`90`, apagado por defecto) — el PO no lo mencionó y sigue sin ser urgente aunque empate
   en número con `full_throttle`.

2. **Countdown de frenada con gap uniforme.** `DEFAULT_COUNTDOWN_GAP_S = 0.75` reemplaza
   `DEFAULT_COUNTDOWN_S = 3.5`: los tres sonidos (tic1 → tic2 → frenada) quedan separados por 0.75 s
   parejos en vez de fracciones de un anticipo total. `_countdown_lead_m` calcula
   `lead_m = v/3.6 * countdown_gap_s * 2` (dos gaps), acotado a `[min_lead_m=30, max_lead_m=250]`
   metros — bajan de `[60, 350]` porque con el gap nuevo el lead total baja de ~3.5 s a ~1.5 s y los
   clamps viejos casi siempre recortaban, rompiendo la uniformidad. El reparto de `lead_m` en tics
   (fracciones `(1.0, 0.5)` de `COUNTDOWN_SCALE`) no se toca: como ambos gaps resultantes son
   `lead_m/2`, salen siempre iguales entre sí por construcción, sin depender del valor exacto de
   `lead_m` tras el clamp.

3. **Tabla de frecuencias reajustada (`DEFAULT_FREQS`)**, corrigiendo la colisión real reportada:
   `brake_countdown: 800` (tics resultantes 600/700, antes 660/770), `brake: 1000` (protegido, sin
   cambio), `brake_release: 820`, `turn_in: 500` (antes 660 — libera la colisión con el tic),
   `apex: 400`, `full_throttle: 320` (antes 180, separa el clúster con `throttle_on`/`gas`),
   `throttle_on: 250`, `gas: 220`, `gas_100: 190`, `coast: 160`, `gear: 650` (asignada en el fix de
   code review, ver más abajo). Punto de partida calculado (ratios ≥1.14 entre consecutivos, sin
   colisiones exactas), pendiente de validar de oído con la próxima cinta.

4. **Cue `gear` (cambio de marcha) implementado, acotado a subtítulo — sin sonido todavía.**
   `detect_gear_shifts(lap, min_hold_s=0.15)` (`fantasma/core/corners.py`) recorre la vuelta de
   referencia COMPLETA (no por curva — arquitectura lap-wide, distinta de cómo se detectan curvas),
   compara `gear` entre muestras consecutivas con debounce anti-blip, y devuelve
   `[{"distance", "gear_from", "gear_to"}, ...]` ordenado por distancia. Wireado end-to-end: CLI
   (`cmd_detect` escribe `data["gear_shifts"]`, `_load_corners_json` lo extrae, `cmd_pacenotes` lo
   pasa a `build_pack(..., gear_shifts=...)`) y UI NiceGUI (`ng_state.AppState.gear_shifts`,
   poblado en los tres puntos donde el Paso 1/2/3 llaman `detect_corners(ref_lap)`, reenviado a
   `build_pack` en el Paso 5). Usa siempre la vuelta de **referencia**, coherente con la regla de
   producto ya vigente en `ROADMAP.md` ("estudio = referencia; en vivo = RPM real del piloto — es
   la única excepción a nunca generar cues desde la vuelta del piloto").

   El cue se apaga por defecto (`DEFAULT_CONFIG["gear"] = {"enabled": False, "priority": 75,
   "sound": False}`) y **no genera audio**: `build_tone_pack` consulta
   `_cue_sound_enabled(cue_config, cue)` antes de llamar `_render_cue`/escribir WAV; si es `False`
   (nuevo campo `sound` en el esquema de config de cue, default `True`), la entrada de metadata sale
   con `fileNames`/`recordingNames: []` y `build_cue_ass` la subtitula igual. `gear` entra a
   `plan_tone_events` y participa en el `sort` global, pero **no** compite por el gap mínimo contra
   cues de audio — ver enmienda arriba: los `sound=False` resuelven su cabida en un pool aparte de
   los `sound=True`, para no desplazar audio real solo por ser mudos y frecuentes. No entra a
   `corners_plan["selected"]` — mismo criterio que `brake_tic`, porque no pertenece a ninguna curva.
   `MILESTONE_LABELS["gear"] = "cambio de marcha"`, `CUE_SUB_COLORS["cambio de marcha"] = magenta`.

Implementado en `feat/cues-configurables`: `8b5b8cc` (motor: prioridades, countdown, frecuencias,
`detect_gear_shifts` + wiring CLI + mecanismo `sound`), `8c63089` (cierra el wiring desde la UI
NiceGUI, que es el flujo que de verdad evalúa el PO), `da7f337` (6 bugs de un `/code-review` de
alto esfuerzo sobre lo anterior).

## Razones

- **El contrato perceptivo (ADR 0025) sigue siendo "el 3 es el ya"; lo que cambia es el ritmo, no
  el ancla.** Sustituir un anticipo total por fracciones por un gap fijo entre sonidos es más fácil
  de calibrar de oído (un solo número, 0.75 s) y elimina el efecto "arrastrado" que reportó el PO
  sin tocar el punto de anclaje del countdown en la frenada real.
- **La prioridad es del usuario, y aun así necesita un default sensato.** El ADR 0027 movió la
  prioridad a config; este ADR ajusta los valores por defecto con los que arranca todo perfil nuevo,
  a partir de un reporte de oído concreto, no de un rediseño del mecanismo.
- **`gear` se implementó solo-subtítulo, no con audio, porque el costo de una frecuencia nueva mal
  calibrada es alto y el beneficio de tener el subtítulo ya es real.** Meter un tono nuevo al
  catálogo sin QA de oído arriesga repetir exactamente el problema #5 que originó este ADR (sonidos
  que se confunden). El subtítulo por sí solo ya resuelve el síntoma reportado ("cambio de marcha
  sin... subtitular"); el sonido es un incremento posterior, de menor riesgo si se hace por
  separado.
- **`sound` se generalizó como campo de config del cue, no como un `if cue == "gear"` hardcodeado**,
  porque el mecanismo — "este tipo de cue participa en cabida/prioridad y se subtitula, pero no
  sintetiza WAV" — no es específico de `gear`: es la primera vez que el catálogo separa "qué suena"
  de "qué se subtitula" (antes ambos eran 100% la misma lista de eventos), y otros cues futuros
  pueden necesitar la misma separación sin que el motor tenga que aprenderse cada tipo por nombre.
  Es la razón por la que un `/code-review` de alto esfuerzo pudo encontrar y corregir el bug #5 (la
  ausencia de `DEFAULT_FREQS["gear"]`) como caso general de "cualquier perfil de terceros puede
  forzar `sound=true` en `gear`" y no como caso especial de un cue en particular.
- **`detect_gear_shifts` es lap-wide y no por curva** porque un cambio de marcha no está atado a
  una curva — ocurre en rectas, en la salida de curva, en zonas sin milestone alguno. Forzarlo al
  modelo por-curva de `detect_corners` habría requerido inventar una curva "contenedora" artificial
  para cada cambio sin curva cerca.

## El camino que NO se toma (y por qué tienta)

- **Implementar ya el sonido de `gear` junto con el subtítulo.** Es la lectura literal más simple
  del pedido del PO ("cambio de marcha sin sonar ni subtitular") y lo que tentaría a una sesión
  nueva: arreglar las dos mitades del síntoma a la vez. El PO lo descartó explícitamente en esta
  sesión ("acotado a subtítulo — sin sonido todavía, para no meter una frecuencia nueva sin QA de
  oído"). El slot de sonido queda abierto (`sound=False` es reversible con una línea de config), no
  cerrado.
- **Hardcodear `if cue == "gear": skip audio` en `build_tone_pack`.** Más rápido de escribir que un
  campo de esquema nuevo, pero encierra la excepción en el nombre del cue en vez del comportamiento:
  el próximo cue silencioso (o un perfil de terceros que quiera lo mismo con otro tipo) tendría que
  repetir el `if`. El campo `sound` en `DEFAULT_CONFIG`/`cue_profiles.py` deja el mecanismo genérico,
  coherente con cómo el ADR 0027 ya generalizó `enabled`/`priority`.
- **Reusar el patrón de "ventana sostenida" de `throttle_on`/`full_throttle` para `detect_gear_shifts`.**
  Habría sido más consistente con el resto de `core/corners.py`, pero `detect_gear_shifts` resuelve
  un problema distinto (transición discreta entre valores enteros de marcha, con debounce de
  confirmación hacia adelante) y no un umbral continuo sostenido. Se dejó como **deuda explícita**
  señalada por el `/code-review` (`da7f337`): el archivo termina con dos patrones de "sostenimiento"
  distintos para problemas parecidos. No se corrigió en este release — decisión deliberada de no
  ampliar el diff — queda anotada en `ROADMAP.md` a cargo del Escribano.
- **Reusar `overlay.py:t_gear_val` para la etiqueta de marcha en vez de la nueva `_gear_label`
  (`pacenotes.py`).** Mismo motivo: es la limpieza correcta (evitar la duplicación N/R/número de
  marcha en dos módulos), pero el `/code-review` la señaló como deuda de mantenibilidad, no como
  bug — no se tocó para no ampliar el diff del release. Queda anotada para el Escribano/ROADMAP.
- **Dejar los clamps del countdown en `[60, 350]`.** Es lo que el ADR 0025 fijó y lo que una sesión
  nueva leería como vigente. Con el gap uniforme de 0.75 s el lead total baja a ~1.5 s: mantener los
  clamps viejos habría recortado casi cualquier lead calculado y roto la uniformidad recién ganada.
  Se bajan a `[30, 250]` como parte de este mismo reencuadre.

## Consecuencias

- Se gana: el countdown suena parejo y completo (gap fijo de 0.75 s en vez de fracciones sobre un
  anticipo de 3.5 s); `turn_in` compite con prioridad propia (70) en vez de perder sistemáticamente
  contra `throttle_on`/`full_throttle`; ningún par de cues activos por defecto comparte frecuencia
  exacta; el cambio de marcha (metro 1745 y análogos) ya trae subtítulo "cambio a Nª" sin necesidad
  de audio nuevo; el mecanismo `sound` queda disponible para cualquier cue futuro que necesite la
  misma separación entre "suena" y "se subtitula".
- Se pierde / cuesta: el `lead_m` del countdown ya no representa directamente "tiempo de reacción
  total" (era la lectura del ADR 0025) sino "dos gaps de 0.75 s" — un lector del ADR 0025 sin este
  reencuadre entendería mal el propósito de `lead_m`; ver enmienda abajo. `detect_gear_shifts` suma
  un tercer patrón de detección lap-wide en `core/corners.py`, distinto del patrón por-curva y del
  patrón de ventana sostenida — más superficie que mantener, deuda anotada, no resuelta.
- **6 bugs reales** encontrados por un `/code-review` de alto esfuerzo sobre esta implementación,
  corregidos en `da7f337`: el debounce de `detect_gear_shifts` se comparaba consigo mismo y
  aceptaba cualquier blip de 1 muestra como cambio real; la UI no calculaba `gear_shifts` cuando el
  usuario subía un `corners.json` a mano (gap de wiring); `_gear_shift_event` no tenía guardas
  defensivas ante un `gear_shifts` malformado; los eventos `gear` no pasaban por el guard
  `distance <= 0` que sí aplica al resto de candidatos; faltaba `DEFAULT_FREQS["gear"]` (reabría la
  colisión de frecuencias que este mismo ADR corrige, si un perfil de terceros fuerza `sound=true`);
  y la detección sincrónica del Paso 1 corría bloqueando el hilo del event loop de NiceGUI.
- **Deuda anotada, no corregida** (deliberado, para no ampliar el diff): `detect_gear_shifts`
  reimplementa el patrón de "ventana sostenida" en vez de reusar el de `throttle_on`/
  `full_throttle` (mismo archivo); `_gear_label` (`pacenotes.py`) duplica la lógica N/R/número de
  marcha que ya existe en `overlay.py:t_gear_val`. Sigue el Escribano vía `ROADMAP.md`.
- **Enmienda al ADR 0025**: el "3 es el ya" y el anclaje del countdown en la frenada real **siguen
  vigentes sin cambio**. Lo que se enmienda es la fórmula que reparte el anticipo: `DEFAULT_COUNTDOWN_S`
  (anticipo total, fracciones `(0.75, 0.875)`) queda reemplazado por `DEFAULT_COUNTDOWN_GAP_S`
  (gap uniforme entre sonidos consecutivos) y los clamps de `_countdown_lead_m` bajan de
  `[60, 350]` a `[30, 250]` metros. Una sesión que lea el ADR 0025 solo debe saber que el valor
  `3.5` y la lectura "anticipo total en segundos" ya no son la fuente de verdad del ritmo — lo es
  este ADR.
- **Enmienda al ADR 0027**: el slot `gear` deja de estar "documentado pero sin implementar" — queda
  implementado y acotado a subtítulo (`sound=False`). El campo `sound` se suma al esquema de config
  de cue descrito en el punto 1 y 4 del ADR 0027 (`enabled`, `priority`, ahora también `sound`); el
  resto del modelo de catálogo/prioridad/perfiles del 0027 no se toca. El audio de `gear` sigue como
  follow-up (`ROADMAP.md`), ahora con el subtítulo ya resuelto.
- Pendiente de validar: juicio de oído del PO sobre la nueva mezcla (countdown, tabla de
  frecuencias) en la próxima cinta de estudio (overlay a 0.5×, `ROADMAP.md`/`HANDOFF.md` llevan el
  seguimiento del render); si `turn_in` sigue ausente en curvas después de subir su prioridad a 70,
  la causa puede ser el gate propio de `_corner_candidates` (`turn_cfg["enabled"] and turn and
  turn.get("d") is not None and loss >= 0.25`) y no la prioridad — a confirmar con esa misma cinta
  antes de tocarlo.
