# ADR 0009 — Unidad de medida del desgaste acumulado: carga de deslizamiento (integral), no el promedio

- **Estado:** Aceptada (implementada 2026-06-22)
- **Fecha:** 2026-06-22

## Contexto

La enmienda del **ADR 0004** (2026-06-22) decidió mostrar el desgaste acumulado en **dos
vistas** —en el overlay el acumulado *de la vuelta* y en las gráficas el de *stint*— pero
dejó **abierta la unidad base**. Hoy conviven dos cosas que no son la misma:

- `slip_index` (en `core/wear.py`) es un **promedio**: el exceso medio de deslizamiento por
  muestra en un tramo. Es una **intensidad** ("qué tan duro").
- `wear_budget` acumula esos promedios **por vuelta** (`Σ slip_index`).

Para un acumulado que crezca de forma **aditiva** curva → vuelta → stint (lo que el usuario
esperaba: "si gasté 3.1 en una curva y 2.0 en la siguiente, llevo 5.1") hace falta fijar qué
cantidad se suma. Promediar no es aditivo: el promedio de dos tramos de distinto largo no es
la suma de sus promedios.

## Decisión

La base de acumulación es una cantidad **extensiva**: la **carga de deslizamiento**.

```
carga = Σ ( max(0, |slip| − banda_muerta) × Δdistancia )
```

Es decir, el **área bajo la curva** del exceso de slip a lo largo del tramo, **integrada
sobre la distancia** (metros), no el promedio.

- **`slip_index` (promedio) se mantiene** como métrica de **intensidad**: el DESLIZ del HUD y
  la dureza por curva. Responde *"¿dónde castigo la goma?"*.
- **La carga (integral) es la base de TODO acumulado**: el readout corrido del overlay
  (acumulado de la vuelta) y la gráfica de stint. Responde *"¿cuánto llevo gastado?"*.
- Se integra sobre **distancia**, no sobre tiempo.

## Razones

- **Aditiva.** La integral es aditiva sobre tramos: carga(curva 1) + carga(curva 2) =
  carga(las dos juntas). Encadena limpio curva → vuelta → stint sin trucos — justo el modelo
  mental del usuario.
- **Físicamente correcta.** El desgaste de goma es, en esencia, **distancia de patinaje**
  (cuánto resbaló la goma contra el asfalto). Integrar el slip sobre los metros recorridos es
  precisamente eso. Un medidor de gasolina mide *cuánto*, no *qué tan fuerte*.
- **Independiente del muestreo.** Una suma cruda de muestras crece con los Hz; la integral
  sobre distancia es estable (una curva gasta lo mismo a 20 o a 60 Hz).
- **Composable entre las dos vistas.** El acumulado al final de una vuelta en el overlay = lo
  que esa vuelta aporta a la gráfica de stint. Cierra la consideración abierta del ADR 0004.

## El camino que NO se toma (y por qué tienta)

- **Acumular el promedio (`slip_index`).** Tienta porque ya existe y es la métrica actual. NO:
  promediar no es aditivo entre tramos de distinto largo, y sumar promedios por vuelta es
  dimensionalmente turbio. El promedio mide **intensidad**, no **cantidad**; para "cuánto
  llevo gastado" es la métrica equivocada.
- **Suma cruda de muestras (sin × distancia).** Tienta por simple. NO: depende del sample
  rate — a 60 Hz daría el doble que a 30 Hz para el mismo desgaste real.
- **Integrar sobre tiempo en vez de distancia.** Tienta porque el slip se mide por muestra en
  el tiempo. NO: el tiempo distorsiona por velocidad y laptime; la distancia hace la carga
  comparable entre vueltas del mismo circuito. (Integrar slip% sobre distancia ya es ∝
  distancia de patinaje, que es lo físico.)

## Consecuencias

- **Se gana:** un acumulado **aditivo y composable** curva → vuelta → stint, físicamente
  interpretable, base común de las dos vistas del ADR 0004.
- **Se recalibra:** los umbrales `yellow`/`red`/`burst` del ADR 0004 **cambian de escala**
  (ya no son el 0–5 de intensidad sino una integral mayor). No es pérdida: esos umbrales ya
  eran arbitrarios y el ADR 0004 dice que se calibran a mano con telemetría real.
- **`wear_budget` cambia de insumo:** acumulará **cargas** (extensivas) por vuelta en lugar de
  `slip_index` (promedios). `slip_index` queda solo como indicador de intensidad.
- **Documentación al usuario (obligatoria al implementar):** la `hud-reference.md` —y donde
  se muestre la métrica— **debe distinguir explícitamente** el **DESLIZ** (intensidad
  instantánea: *qué tan duro castigas la goma AHORA*) de la **carga acumulada** (*cuánto
  llevas gastado*), porque es fácil que el usuario las confunda. Riesgo señalado por Armando
  el 2026-06-22.
## Implementación (2026-06-22)

- `core.wear.slip_load(lap, d0, d1)` — función pura que calcula la carga (extensiva,
  integrada sobre distancia). Test de aditividad incluido (`tests/core/test_wear.py`).
- **Overlay:** campo **GASTO** en la franja del HUD (acumulado de la vuelta, piloto vs
  `ref`); cumsum de la carga sobre la rejilla de 1 m en `viz/overlay.py`.
- **`fantasma wear`:** migrado de `slip_index` (promedio) a `slip_load` (carga) —
  **cierra la consideración abierta de unidades**: ahora el acumulado de stint y el del
  overlay usan la misma base. Los umbrales `--yellow/--red/--burst` pierden su default
  (la carga escala con la longitud del circuito; se calibran empíricamente).
- Validado con telemetría real (BMW M4 GT3, Nordschleife): GASTO ~257 vs ref ~237 al
  final de la vuelta, frente a DESLIZ ~1.8 — las escalas confirman que cantidad e
  intensidad no se confunden.
