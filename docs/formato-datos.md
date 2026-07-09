# Formato de datos

Referencia técnica del formato interno y los archivos de entrada/salida. Útil para contribuir importadores o consumir las salidas desde otras herramientas.

## Canales canónicos

Todo importador convierte a este modelo (`fantasma/core/lap.py`):

| Canal | Unidad | Obligatorio | Notas |
| :-- | :-- | :-- | :-- |
| `time` | s | ✅ | desde el inicio del segmento |
| `dist` | m | ✅ | desde el inicio del segmento. En MoTeC i2 requiere marcar **«Include Distance Data»** al exportar; sin este canal el motor se detiene con un aviso claro (no se sintetiza desde la velocidad — [ADR 0017](decisions/0017-distancia-canal-requerido.md)) |
| `speed` | km/h | recomendado | |
| `throttle` | % (0-100) | recomendado | |
| `brake` | % (0-100) | recomendado | |
| `steering` | grados | recomendado | **negativo = izquierda** |
| `gear` | - | recomendado | entero; discreto en el remuestreo |
| `glat` | G | opcional | convención del logger (en MoTeC/AMS2: positivo = izquierda) |
| `glong` | G | opcional | |
| `rpm` | rpm | opcional | |
| `alt` | m | opcional | habilita el cálculo de pendiente por curva |

## Separación de vueltas

`split_laps()` corta el outing por, en orden de preferencia:
1. **Beacons** del log MoTeC (`Beacon Markers` en los metadatos) — la primera y última porción se marcan como out-lap/in-lap incompletas;
2. cambios del canal `lap_number`;
3. reinicios del canal de distancia (caída > 100m).

`fastest_lap()` elige la vuelta completa más rápida entre las que miden ≥90% de la más larga.

## Convención de distancia

- Metro **0 = inicio de la vuelta** (cruce de meta).
- La comparación se hace **por distancia**, no por tiempo: remuestreo de ambas vueltas a una rejilla uniforme (5m por defecto, `--step`).
- Interpolación lineal para canales continuos; valor anterior para discretos (`gear`).

## Detección de curvas (resumen del algoritmo)

1. **V-Min**: mínimo local de velocidad con prominencia ≥3 km/h en ventana de ±1.2s.
2. **Kink**: pico de |G lateral| > 2.2 sostenido, sin V-Min en ±80m (curvas rápidas sin frenada).
3. **Segmentación**: cada curva solo analiza su tramo (punto medio con las curvas vecinas, con tope de 450 m hacia atrás y 350 m hacia adelante) — evita contaminarse con la frenada de la curva siguiente. **Excepción — la detección de frenada usa su propia ventana** (punto 4): el punto medio caía en mitad de la zona de frenado cuando la curva anterior era un kink sin frenada y truncaba el inicio real de la frenada. El resto de hitos (ápex, turn-in, gas, coast) sigue usando el segmento por punto medio.
4. **Frenada real (fases)**: la frenada se busca en una ventana que arranca **justo después del ápex de la curva previa** (no en el punto medio), con el mismo tope de 450 m hacia atrás. Los puntos con `brake` > `brake_on` se agrupan en **bloques**, y los bloques consecutivos se funden en **fases** cuando el hueco temporal entre ellos es menor que `phase_gap_s` (0.5 s por defecto) **y** el coche sigue desacelerando en el hueco (una suelta breve del pedal para rotar, no una acción distinta); un toque de freno aislado que quedó lejos, o tras el cual el coche re-aceleró, queda en su propia fase. El piso de intensidad `brake_strong` (50% por defecto — el freno de verdad, el que evita pasarse de curva) es un **filtro**: se **descartan** las fases que no lo alcanzan. Entre las fases que quedan, `brake_start` ancla en la **primera muestra de la de pico máximo**; ante empate de pico, la **más tardía** (la que entra al ápex); si **ninguna** fase alcanza el piso, la **última fase cronológica**. El porqué: el cue marca dónde empezar a **cargar el pedal hacia el máximo freno** aprovechando la transferencia de peso, así que gana la pisada de mayor intensidad, no la última. Un blip débil y previo del trail braking queda por debajo del piso y **no adelanta** el hito.
   - **Propiedad de la frenada entre curvas vecinas**: cada curva es **dueña** de toda fase de frenada posterior al ápex de su vecina previa; nada anterior a ese ápex se le atribuye (no se roba la frenada de la anterior). Un kink sin frenada **no absorbe** la frenada de la curva siguiente —esa frenada cae después del ápex del kink— ni al revés. Así la frenada real (p. ej. tras un kink rápido) ya no se trunca en el borde del segmento.
   - **Invariante de `segment_m`** ([ADR 0031](decisions/0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md), Opción A): `segment_m` es una **banda aproximada de vecindad del V-Min** —útil para agregar métricas de zona (V-Min, slip, conteo de ABS)— y **NO** un contrato de contención. `brake_start` **puede preceder** a `segment_m[0]` cuando la curva anterior es un kink (su ventana de frenada arranca tras el ápex previo, más atrás que el punto medio del segmento). Los módulos que consumen `segment_m` **no deben asumir que los hitos caen dentro del segmento**: la verdad autoritativa de dónde ocurre cada cosa son los hitos, no el segmento.
   - **La ventana de frenada NO se publica; el consumidor la deriva** ([ADR 0031](decisions/0031-propiedad-de-la-frenada-y-contrato-de-segment-m.md), Opción A). La ventana ampliada donde se busca la frenada es `[max(prev_apex, apex − BRAKE_LOOKBACK_M), apex]` (`BRAKE_LOOKBACK_M = 450`, semántica `lo < dist <= hi`), pero **`extract_milestones` no la escribe en el dict de la curva** —el ADR 0031 rechazó explícitamente exponer un campo `brake_window_m` (Opción C): duplica información ya implícita en `brake_start` e invita a bugs de "usé el campo equivocado". Cuando `compare()` mide la frenada del piloto (`_corner_metrics`), **reconstruye** esa misma ventana con la misma fórmula y el mismo helper (`select_brake_phase`) a partir de los hitos que la curva ya trae —el ápex propio y el de la curva previa—, de modo que referencia y piloto se miden con la misma vara. Matiz: el consumidor reconstruye la frontera con el **ápex publicado** (`milestones.apex.d`, que es el V-Min), mientras que la detección de la referencia usó el ápex del evento interno de `detect_corners`; coinciden en la selección de fase pero no necesariamente en el metro exacto de la frontera. Los límites se redondean a enteros en ambos lados para que sean byte-idénticos: esa es la condición para que `d_brake_m == 0` cuando piloto y referencia son la misma vuelta. Medir al piloto con el segmento en vez de con esta ventana producía banderas `"frenada"` espurias.
5. Hitos: `brake_start`, `turn_in` (**cruce ascendente** de |volante|>8° hacia el lado de la curva: la muestra previa está por debajo del umbral y la actual por encima, para que el volante residual de una curva encadenada del mismo sentido —que entra ya por encima del umbral y solo decrece— no dispare un turn-in espurio; se busca desde `brake_start` —o el inicio del segmento si la curva no frena— hasta el ápex, **no** acotado a `segment_m[0]`: si la frenada precede al segmento, el turn-in que la sigue también puede caer antes de `segment_m[0]` y acotarlo lo perdería), `brake_release` (<2%, tras el final de la **última fase cronológica** de frenada: si hay una reaplicación suave después de la frenada fuerte, el release cae después de ella, no en el hueco intermedio), `throttle_on` (>5% **sostenido**: ancla en el primer punto donde el throttle cruza el umbral y se mantiene por encima durante `throttle_on_window_s` (0.3s por defecto) — igual criterio y misma ventana que `full_throttle`, para que un roce fugaz de pedal, ej. freno-motor o ruido, no gane el hito frente a la aceleración real), `apex` (V-Min), `full_throttle` (≥98% sostenido, misma ventana de `throttle_on_window_s`), `g_lat_max`, `lift` (en curvas sin freno), `coast_start`/`coast_end` (ver punto 6bis). Cada hito lleva `d` (m), `t` (s), `v` (km/h). La ventana de sostenimiento se define en **tiempo** (segundos), no en conteo de muestras: se convierte a muestras con el `dt` real de la vuelta, igual que las ventanas de `detect_corners` (§1-2) — así queda calibrada correctamente en telemetría con frecuencia de muestreo distinta de 50 Hz.
6. **Overlap**: si `throttle_on.d < brake_release.d`, se registra `overlap_m` (solape gas/freno). El solape se mide contra el `throttle_on` sostenido (punto 5), no contra el primer roce de pedal, así que `overlap_m` puede variar si el gas real entra más tarde que un blip inicial.
7. **Coast**: tramo entre el fin de la frenada (`brake_release`, o `lift` en curvas sin freno) y el `throttle_on` sostenido donde el piloto no toca ni freno ni gas (`throttle` y `brake` ambos por debajo de sus umbrales, `throttle_on` y `brake_on` respectivamente). Si existe hueco se marcan `coast_start` (primer punto del tramo) y `coast_end` (último). Si el gas se solapa con el freno (overlap, ver punto 6) no hay hueco y no se emite coast.
8. **Pendiente**: si hay canal `alt`, gradiente ±100m alrededor del ápex → `slope` (subida/bajada/plano) y `slope_pct`.

## Esquema de corners JSON

`fantasma detect` produce (y `--corners` consume):

```json
{
  "corners": [
    {
      "id": "C07",
      "name": "Curva del puente",        // opcional, lo añades tú
      "kind": "vmin",                     // vmin | kink
      "direction": "left",
      "segment_m": [7048, 7487],
      "no_brake": false,
      "overlap_m": 1,                     // solo si existe
      "max_steering_deg": 31.8,
      "slope": "bajada", "slope_pct": -6.7,
      "delta_s": 9.84,
      "milestones": {
        "brake_start": {"d": 7167, "t": 133.9, "v": 142, "gear": 2, "brake_pct": 100},
        "turn_in":     {"d": 7204, "t": 134.8, "v": 110, "gear": 1},
        "brake_release":{"d": 7236, "t": 135.7, "v": 77},
        "throttle_on": {"d": 7220, "t": 135.2, "v": 90, "throttle_pct": 17},
        "apex":        {"d": 7233, "t": 135.6, "v": 76, "gear": 1, "g_lat": 2.42},
        "full_throttle":{"d": 7349, "t": 139.1, "v": 118, "gear": 2},
        "g_lat_max":   {"d": 7230, "g_lat": 2.5}
        // coast_start/coast_end: solo si hay hueco entre brake_release y
        // throttle_on (no en este ejemplo, que tiene overlap_m)
      },
      "tolerances": {"brake_start_m": 10, "vmin_kmh": 4}   // opcional, para avisos
    }
  ]
}
```

Campos extra (`voice_name`, `description`, `coaching_priority`...) se conservan y son libres — otras herramientas pueden usarlos.

## Cambios de marcha (`gear_shifts`)

`fantasma detect` calcula, además de `corners`, los cambios de marcha de la vuelta que se le pasa: `detect_gear_shifts(lap, min_hold_s=0.15)` (`fantasma/core/corners.py`) recorre **toda la vuelta** (no por curva — un cambio de marcha puede caer en cualquier punto, dentro o fuera de una curva) comparando el canal `gear` muestra a muestra, con un debounce de `min_hold_s` segundos: un cambio candidato solo se confirma si la marcha nueva se sostiene ese tiempo antes de volver a cambiar, para descartar blips de una sola muestra. `corners_detected.json` agrega la clave `gear_shifts` junto a `corners`:

```json
{
  "corners": [...],
  "gear_shifts": [
    {"distance": 1745, "gear_from": 3, "gear_to": 4}
  ]
}
```

- `distance` (m, entero redondeado) — punto de la vuelta donde se confirma el cambio.
- `gear_from` / `gear_to` (entero) — marcha antes/después; `0` = neutro, negativo = reversa (mismo criterio que el canal `gear`).
- Lista ordenada por `distance`.

`fantasma pacenotes` (`cmd_pacenotes`) lee `gear_shifts` del JSON de curvas y lo pasa a `build_pack(..., gear_shifts=...)`; si el archivo no trae la clave (`corners_detected.json` de una versión anterior, o una lista plana de curvas sin envoltorio), se asume lista vacía — no revienta. En la UI (`fantasma-ng`), `AppState.gear_shifts` se calcula siempre sobre la vuelta de **referencia** (Pasos 1/2/3), coherente con la regla de producto "estudio = referencia; en vivo = RPM real del piloto" del `ROADMAP.md`. Alimenta el cue `gear` (ver esquema de configuración de cues abajo) — [ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md).

## Esquema de configuración de cues (perfiles)

`DEFAULT_CONFIG` (`fantasma/viz/pacenotes.py`) y los perfiles JSON compartibles que consume `profile_to_config` (`fantasma/viz/cue_profiles.py`) describen cada tipo de cue de pace notes con:

| Campo | Tipo | Significado |
| :-- | :-- | :-- |
| `enabled` | bool | si se generan candidatos de ese tipo en `plan_tone_events` |
| `priority` | int | gana el hueco cuando dos cues compiten por el mismo espacio (gap mínimo global) |
| `sound` | bool | si el candidato se sintetiza a WAV en `build_tone_pack` (campo nuevo, [ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)). `False` = el cue solo se subtitula (`build_cue_ass`): no genera audio y su entry de `metadata.json` queda con `fileNames`/`recordingNames` `[]` — **una entry así NO es embarcable a CrewChief** (revienta en pista: ver «Pack de pace notes de CrewChief» abajo). Default `True` para todo el catálogo salvo `gear` |
| `solo_sin_frenada` | bool | solo aplica a `coast`: no compite en curvas que ya tienen frenada |

El cue `gear` (cambio de marcha, `{"enabled": False, "priority": 75, "sound": False}`) es el primero del catálogo con `sound=False`: no se sintetiza a WAV, solo aparece en el subtítulo quemado con la etiqueta `"cambio a Nª"` (ver la tabla de colores en `docs/hud-reference.md`). Un perfil de terceros puede forzar `sound: true` en cualquier cue; `profile_to_config` coacciona el campo a `bool` igual que `enabled`/`solo_sin_frenada`.

**Corrección 2026-07-08 (enmienda a ADR 0028):** un cue con `sound=False` **NO** participa en la resolución de cabida/prioridad (gap mínimo global) contra cues que sí suenan — `plan_tone_events` resuelve el gap mínimo en DOS grupos independientes (sonoros vs. mudos) y los recombina después. Motivo: `gear` es de vuelta completa (decenas de cambios de marcha por vuelta) y, al compartir pool con cues de audio esporádicos como `coast`, los desplazaba por completo en zonas sin relación alguna con un cambio de marcha (QA 2026-07-08, ver enmienda en el ADR). `brake` (protegido) siempre cuenta como sonoro para este corte, sin importar lo que diga su campo `sound` resuelto — es la única garantía cruzada que R1 no puede perder ante un perfil de terceros que fuerce `sound: false` en `brake`. Dos cues mudos cercanos entre sí (p. ej. una racha de reducciones) sí compiten por cabida entre ellos, para que sus subtítulos no se amontonen.

## Pack de pace notes de CrewChief (`metadata.json`)

`fantasma pacenotes` (`build_pack`, `fantasma/viz/pacenotes.py`) genera un pack que consume CrewChief V4: **un `metadata.json` por game/clase-de-coche/pista** con un array `entries` (una entry = un cue anclado a un metro de pista) más los WAV. El **formato canónico completo y el mecanismo de disparo** son dueño del [ADR 0002](decisions/0002-crewchief-pacenotes.md) (enmienda 2026-07-09), reconciliado contra el fuente real de CrewChief V4 (`DriverTrainingService.cs`, commit `84fe63b`); aquí solo se fijan las dos reglas que tocan el **formato de datos**:

- **Disparo solo por distancia.** CrewChief dispara cada entry por el **cruce puro** de `distanceRoundTrack` (`checkDistanceAndPlayIfNeeded`, :133): no lee velocidad, RPM, marcha ni tiempo. Los campos extra que emitimos por entry (`lapNumber`, `minimumSpeed`, `maximumSpeed`, `minimumYawAngle`, `maximumYawAngle`, `playAllInOrder`) **no existen en la clase `MetaDataEntry`** y CrewChief los descarta en silencio (Newtonsoft, `MissingMemberHandling.Ignore`): son **parse-safe, no filtros funcionales**. Corolario ya fijado en el [ADR 0030](decisions/0030-modos-estudio-en-vivo-que-ancla-cada-cue.md): un cue de estado del motor (cambio de marcha por RPM) **no viaja en el pack por construcción** — no hay campo donde anclarlo.
- **Invariante dura — `recordingNames` y `fileNames` no vacías y del mismo largo, por entry.** Una entry con listas **vacías** revienta CrewChief en pista (`getRandomRecordingName` indexa `recordingNames[0]` con `Count == 0` → `ArgumentOutOfRangeException`, sin `catch` hasta el hilo principal); con largos **distintos** revienta al cargar (`fileNames[i]`). Por eso **un cue mudo no debe embarcar su entry con listas `[]`** en el pack exportable. Hoy el único cue mudo (`gear`, `sound=False`) sale con `enabled=False` por defecto, así que el pack por defecto no lleva esa entry; pero un perfil que habilite un cue mudo la produciría (`_metadata_entry` con `filename=None` deja las listas `[]`, `fantasma/viz/pacenotes.py:1432`) — deuda latente anotada en el [ADR 0002](decisions/0002-crewchief-pacenotes.md#enmienda-2026-07-09--reconciliación-con-el-fuente-real-de-crewchief-v4).

## API pública de `fantasma.core`

El paquete declara `__all__` con los símbolos de uso externo: `Lap`, `samples`, `detect_corners`, `extract_milestones`, `compare`, `corner_coaching`, `delta_trace`, `resample` y el módulo `wear`. Funciones internas de `wear` (`_slip_index`, `_assist_count`, `_tyre_temp_avg`) llevan el prefijo `_` y no forman parte de la API estable.

`samples(lap)` — convierte un `Lap` en lista de dicts `[{canal: valor, ...}]` por muestra; útil para consumir la telemetría desde scripts externos.

`corner_coaching(row, trace)` — interpreta una fila de `corners_compare.csv` junto con la traza metro a metro (`delta.csv`) y devuelve un dict de drill-down por curva. Es aritmética pura: prioriza acciones como punto de frenada, intensidad de freno, V-Min, gas 100%, G lateral y marcha/RPM si los canales existen. Si falta `gear`, `glat` u otro canal opcional, omite esa sección sin inventar valores.

## Salidas de `compare`

**`delta.csv`** — una fila por paso de la rejilla: `dist`, `delta_t` (s, positivo = el piloto pierde), y `ref_*`/`drv_*` para `speed`, `throttle`, `brake`, `steering`, `gear`, `rpm` y, si están presentes en el archivo, `glat`/`glong`. Solo se escriben las columnas de los canales que existen.

**`corners_compare.csv`** — una fila por curva: `id`, `name`, `segment_start_m`, `segment_end_m`, `apex_d`, `ref_vmin`, `drv_vmin`, `drv_vmin_d`, `d_vmin`, `ref_brake_d`, `drv_brake_d`, `d_brake_m` (positivo = el piloto frena más tarde), `ref_gas100_d`, `drv_gas100_d`, `d_gas100_m`, `time_lost` (s, delta acumulado entre los extremos del segmento), `flags`; y, cuando el archivo trae canales de rueda/ABS, `ref_slip`/`drv_slip` (proxy de desgaste por curva) y `ref_abs`/`drv_abs` (activaciones de ABS en el segmento). Las columnas dependen de los datos disponibles.

**`corner_coaching` (dict interno de drill-down)** — no crea un archivo nuevo; se calcula desde `corner_rows` + `trace`. Campos principales: `status` (`loss`, `gain`, `neutral`), `summary`, `actions`, `segment_m`, y secciones `braking`, `apex`, `throttle`, `lateral`, `gear`. Cada sección aparece vacía si no hay canales suficientes.

**`summary` (dict interno de `compare()`)** — incluye desde v1.0 el campo `avisos` (lista de strings): mensajes de diagnóstico emitidos durante la comparación. Actualmente puede contener:

- `"delta sospechosamente grande (X s sobre vuelta de Y s): ¿la referencia y el piloto son del mismo circuito?"` — se emite cuando `abs(total_delta) > ref_laptime * 0.5`. Indica que los datos probablemente no son del mismo circuito.
- `"autos distintos: <ref> (ref) vs <piloto> (piloto)"` — aviso informativo cuando ambas vueltas tienen metadato `Vehicle` y difieren. Solo se emite si el metadato está disponible en los dos archivos; si falta en alguno, la degradación es silenciosa.
- `"piloto más rápido que la referencia (X.X s de ventaja): ¿tienes la referencia y el piloto al revés?"` — se emite cuando `total_delta < -1.0` (el piloto es más de 1 s más rápido que la referencia). Indica probable inversión de los archivos de referencia y piloto.
